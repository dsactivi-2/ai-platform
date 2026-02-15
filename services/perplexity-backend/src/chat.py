"""Chat functionality using OpenAI for AI-powered search and response."""

import asyncio
from typing import AsyncIterator, List, Optional

from fastapi import HTTPException

from auth import AuthenticatedUser
from llm.openai_llm import OpenAIAgents
from prompts import (
    build_answer_generation_system_prompt,
    build_query_rephrase_system_prompt,
    build_search_term_extraction_system_prompt,
)
from related_queries import generate_related_queries
from schemas import (
    BeginStream,
    ChatRequest,
    ChatResponseEvent,
    FinalResponseStream,
    Message,
    RelatedQueriesStream,
    SearchResult,
    SearchResultStream,
    StreamEndStream,
    StreamEvent,
    TextChunkStream,
)
from search.search_service import perform_search


def apply_date_range_filter(query: str, start_date: str = None, end_date: str = None) -> str:
    """
    Apply custom date range filters to a search query using Google-style operators.

    Args:
        query: The original search query
        start_date: Start date in YYYY-MM-DD format (appends 'after:' operator)
        end_date: End date in YYYY-MM-DD format (appends 'before:' operator)

    Returns:
        Modified query with date operators appended

    Example:
        apply_date_range_filter("AI research", "2022-11-01", "2023-07-31")
        -> "AI research after:2022-11-01 before:2023-07-31"
    """
    modified_query = query

    if start_date:
        modified_query += f" after:{start_date}"

    if end_date:
        modified_query += f" before:{end_date}"

    return modified_query


async def extract_search_terms(query: str, openai_agents: OpenAIAgents) -> str:
    """
    Extract the core search terms from a query using the fast LLM.
    The LLM understands what information to search for while ignoring output format instructions.
    """
    try:
        from datetime import datetime
        llm = openai_agents.get_query_rephrase_llm()
        now = datetime.now()
        current_datetime = now.strftime("%A, %B %d, %Y %I:%M %p")
        system_prompt = build_search_term_extraction_system_prompt(current_datetime)
        print("Using OpenAI to extract search terms from query")
        search_terms = (await llm.complete(system_prompt, query)).strip().replace('"', '')
        return search_terms if search_terms else query
    except Exception as e:
        print(f"Error in search term extraction, using original query: {e}")
        return query


async def rephrase_query_with_context(question: str, openai_agents: OpenAIAgents) -> str:
    """
    Rephrase user query to be standalone using the fast LLM.
    Replaces contextual references like "it", "that", "their" with concrete entities.
    """
    try:
        llm = openai_agents.get_query_rephrase_llm()
        system_prompt = build_query_rephrase_system_prompt()
        print("Using OpenAI to rephrase query")

        rephrased = (await llm.complete(system_prompt, question)).strip()

        # Clean up common prefixes
        rephrased = rephrased.replace('"', '').replace("'", '')
        for prefix in [
            'Rephrased query:', 'Rephrased Query:',
            'Rephrased question:', 'Rephrased Question:',
            'The rephrased question is:', 'Here is the rephrased question:',
        ]:
            if rephrased.startswith(prefix):
                rephrased = rephrased[len(prefix):].strip()

        print(f"Original: {question}")
        print(f"Rephrased: {rephrased}")
        return rephrased if rephrased else question
    except Exception as e:
        print(f"Error in query rephrasing: {e}")
        return question


def format_context(search_results: List[SearchResult]) -> str:
    """Format search results into a context string for the LLM."""
    return "\n\n".join(
        [f"Citation {i+1}. {str(result)}" for i, result in enumerate(search_results)]
    )


async def stream_qa_objects(
    request: ChatRequest, session: Optional[any] = None, user: Optional[AuthenticatedUser] = None
) -> AsyncIterator[ChatResponseEvent]:
    """Stream chat responses using OpenAI for search and answer generation."""
    try:
        import uuid
        openai_agents = OpenAIAgents()

        yield ChatResponseEvent(
            event=StreamEvent.BEGIN_STREAM,
            data=BeginStream(query=request.query),
        )

        # Generate or use provided session_id
        session_id = request.session_id or str(uuid.uuid4())

        # Rephrase the query with conversation context if this is a follow-up
        query = request.query
        if request.session_id:
            query = await rephrase_query_with_context(request.query, openai_agents)

        # Extract search terms from the contextualized query
        search_query = await extract_search_terms(query, openai_agents)

        # Apply custom date range filters if provided
        search_query = apply_date_range_filter(
            search_query,
            start_date=request.start_date,
            end_date=request.end_date
        )

        print(f"Original query: {request.query}")
        print(f"Session ID: {session_id}")
        print(f"Search terms extracted: {search_query}")

        search_response = await perform_search(
            search_query,
            time_range=request.time_range,
            num_results=request.max_results
        )

        search_results = search_response.results
        images = search_response.images

        related_queries_task = asyncio.create_task(
            generate_related_queries(
                query,
                search_results,
                openai_agents.get_related_questions_llm(),
            )
        )

        yield ChatResponseEvent(
            event=StreamEvent.SEARCH_RESULTS,
            data=SearchResultStream(
                results=search_results,
                images=images,
            ),
        )

        # Build system prompt for answer generation
        answer_llm = openai_agents.get_answer_generation_llm()
        from datetime import datetime
        now = datetime.now()
        current_datetime = now.strftime("%A, %B %d, %Y %I:%M %p")

        # Add date range context to user query if date filters are active
        query_with_context = query
        if request.start_date or request.end_date:
            if request.start_date and request.end_date:
                query_with_context = f"{query} (searching for results between {request.start_date} and {request.end_date})"
            elif request.start_date:
                query_with_context = f"{query} (searching for results from {request.start_date} onwards)"
            else:
                query_with_context = f"{query} (searching for results up to {request.end_date})"

        system_prompt = build_answer_generation_system_prompt(
            search_context=format_context(search_results),
            user_query=query_with_context,
            current_datetime=current_datetime,
        )

        full_response = ""
        async for token in answer_llm.astream(
            system_prompt=system_prompt,
            user_message="Please provide a comprehensive answer to the user's question based on the search context provided above.",
        ):
            full_response += token
            yield ChatResponseEvent(
                event=StreamEvent.TEXT_CHUNK,
                data=TextChunkStream(text=token),
            )

        related_queries = await related_queries_task

        yield ChatResponseEvent(
            event=StreamEvent.RELATED_QUERIES,
            data=RelatedQueriesStream(related_queries=related_queries),
        )

        # Database disabled - no persistence
        thread_id = None

        yield ChatResponseEvent(
            event=StreamEvent.FINAL_RESPONSE,
            data=FinalResponseStream(message=full_response),
        )

        yield ChatResponseEvent(
            event=StreamEvent.STREAM_END,
            data=StreamEndStream(
                thread_id=thread_id,
                session_id=session_id
            ),
        )

    except Exception as e:
        detail = str(e).strip() if str(e).strip() else f"Chat processing error: {type(e).__name__}"
        print(f"Error in stream_qa_objects: {detail}")
        raise HTTPException(status_code=500, detail=detail)
