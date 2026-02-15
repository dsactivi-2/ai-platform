"""Advanced search functionality using OpenAI for multi-step query planning and execution."""

import asyncio
from typing import AsyncIterator, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from auth import AuthenticatedUser
from chat import rephrase_query_with_context, extract_search_terms, apply_date_range_filter
from llm.openai_llm import OpenAIAgents
from prompts import (
    build_answer_generation_system_prompt,
    build_query_planning_system_prompt,
    build_search_query_system_prompt,
    QUERY_PLANNING_SCHEMA,
    SEARCH_QUERY_SCHEMA,
)
from related_queries import generate_related_queries
from schemas import (
    AgentFinishStream,
    AgentQueryPlanStream,
    AgentReadResultsStream,
    AgentSearchFullResponse,
    AgentSearchQueriesStream,
    AgentSearchStep,
    AgentSearchStepStatus,
    BeginStream,
    ChatRequest,
    ChatResponseEvent,
    FinalResponseStream,
    RelatedQueriesStream,
    SearchResponse,
    SearchResult,
    SearchResultStream,
    StreamEndStream,
    StreamEvent,
    TextChunkStream,
)
from search.search_service import perform_search
from utils import PRO_MODE_ENABLED


class QueryPlanStep(BaseModel):
    id: int = Field(..., description="Unique id of the step")
    step: str
    dependencies: list[int] = Field(
        ...,
        description="List of step ids that this step depends on information from",
        default_factory=list,
    )


class QueryPlan(BaseModel):
    steps: list[QueryPlanStep] = Field(
        ..., description="The steps to complete the query", max_length=4
    )


class QueryStepExecution(BaseModel):
    search_queries: list[str] | None = Field(
        ...,
        description="The search queries to complete the step",
        min_length=1,
        max_length=3,
    )


class StepContext(BaseModel):
    step: str
    context: str


def format_step_context(step_contexts: list[StepContext]) -> str:
    return "\n".join(
        [f"Step: {step.step}\nContext: {step.context}" for step in step_contexts]
    )


async def ranked_search_results_and_images_from_queries(
    queries: list[str],
    time_range: str = None,
    num_results: int = 10,
    start_date: str = None,
    end_date: str = None,
) -> tuple[list[SearchResult], list[str]]:
    # Apply custom date range filters to all queries if provided
    filtered_queries = [
        apply_date_range_filter(query, start_date=start_date, end_date=end_date)
        for query in queries
    ]

    search_responses: list[SearchResponse] = await asyncio.gather(
        *(perform_search(query, time_range=time_range, num_results=num_results) for query in filtered_queries)
    )
    all_search_results = [response.results for response in search_responses]
    all_images = [response.images for response in search_responses]

    # interleave the search results, for fair ranking
    ranked_results: list[SearchResult] = [
        result for results in zip(*all_search_results) for result in results if result
    ]
    unique_results = list({result.url: result for result in ranked_results}.values())

    images = list({image: image for images in all_images for image in images}.values())
    return unique_results, images


def build_context_from_search_results(search_results: list[SearchResult]) -> str:
    context = "\n".join(str(result) for result in search_results)
    return context[:7000]


def format_context_with_steps(
    search_results_map: dict[int, list[SearchResult]],
    step_contexts: dict[int, StepContext],
) -> str:
    context = "\n".join(
        f"Everything below is context for step: {step_contexts[step_id].step}\nContext: {build_context_from_search_results(search_results_map[step_id])}\n{'-'*20}\n"
        for step_id in sorted(step_contexts.keys())
    )
    context = context[:10000]
    return context


async def stream_pro_search_objects(
    request: ChatRequest,
    openai_agents: OpenAIAgents,
    query: str,
    session=None,
) -> AsyncIterator[ChatResponseEvent]:
    import uuid
    session_id = request.session_id or str(uuid.uuid4())

    # ── Query Planning ───────────────────────────────────────────────
    query_planning_llm = openai_agents.get_query_planning_llm()
    print("Using OpenAI query planning for query breakdown")

    from datetime import datetime
    now = datetime.now()
    current_datetime = now.strftime("%A, %B %d, %Y %I:%M %p")

    planning_system_prompt = build_query_planning_system_prompt(current_datetime)
    plan_result = await query_planning_llm.structured_complete(
        system_prompt=planning_system_prompt,
        user_message=f"Query: {query}\n\nReturn the query plan:",
        response_format=QUERY_PLANNING_SCHEMA,
    )
    query_plan = QueryPlan(**plan_result)
    print(query_plan)

    yield ChatResponseEvent(
        event=StreamEvent.AGENT_QUERY_PLAN,
        data=AgentQueryPlanStream(steps=[step.step for step in query_plan.steps]),
    )

    step_context: dict[int, StepContext] = {}
    search_result_map: dict[int, list[SearchResult]] = {}
    image_map: dict[int, list[str]] = {}
    agent_search_steps: list[AgentSearchStep] = []

    for idx, step in enumerate(query_plan.steps):
        step_id = step.id
        is_last_step = idx == len(query_plan.steps) - 1
        dependencies = step.dependencies

        relevant_context = [step_context[id] for id in dependencies]

        if not is_last_step:
            # ── Search Query Generation ──────────────────────────────
            search_query_llm = openai_agents.get_search_query_llm()
            print(f"Using OpenAI search query agent for step {step_id}")

            search_query_system_prompt = build_search_query_system_prompt(current_datetime)
            search_user_message = (
                f"User's original query: {query}\n\n"
                f"Context from previous steps:\n{format_step_context(relevant_context)}\n\n"
                f"Current step to execute: {step.step}\n\n"
                f"Generate search queries for this step."
            )

            step_result = await search_query_llm.structured_complete(
                system_prompt=search_query_system_prompt,
                user_message=search_user_message,
                response_format=SEARCH_QUERY_SCHEMA,
            )
            query_step_execution = QueryStepExecution(**step_result)
            search_queries = query_step_execution.search_queries
            if not search_queries:
                raise HTTPException(
                    status_code=500,
                    detail="There was an error generating the search queries",
                )

            yield ChatResponseEvent(
                event=StreamEvent.AGENT_SEARCH_QUERIES,
                data=AgentSearchQueriesStream(
                    queries=search_queries, step_number=step_id
                ),
            )

            (
                search_results,
                image_results,
            ) = await ranked_search_results_and_images_from_queries(
                search_queries,
                time_range=request.time_range,
                num_results=request.max_results,
                start_date=request.start_date,
                end_date=request.end_date
            )
            search_result_map[step_id] = search_results
            image_map[step_id] = image_results

            yield ChatResponseEvent(
                event=StreamEvent.AGENT_READ_RESULTS,
                data=AgentReadResultsStream(
                    results=search_results, step_number=step_id
                ),
            )
            context = build_context_from_search_results(search_results)
            step_context[step_id] = StepContext(step=step.step, context=context)

            agent_search_steps.append(
                AgentSearchStep(
                    step_number=step_id,
                    step=step.step,
                    queries=search_queries,
                    results=search_results,
                    status=AgentSearchStepStatus.DONE,
                )
            )
        else:
            # ── Final Synthesis Step ─────────────────────────────────
            yield ChatResponseEvent(
                event=StreamEvent.AGENT_FINISH,
                data=AgentFinishStream(),
            )

            yield ChatResponseEvent(
                event=StreamEvent.BEGIN_STREAM,
                data=BeginStream(query=query),
            )

            # Get 12 results total, distributed evenly across dependencies
            relevant_result_map: dict[int, list[SearchResult]] = {
                id: search_result_map[id] for id in dependencies
            }
            DESIRED_RESULT_COUNT = 12
            total_results = sum(
                len(results) for results in relevant_result_map.values()
            )
            results_per_dependency = min(
                DESIRED_RESULT_COUNT // len(dependencies),
                total_results // len(dependencies),
            )
            for id in dependencies:
                relevant_result_map[id] = search_result_map[id][:results_per_dependency]

            search_results = [
                result for results in relevant_result_map.values() for result in results
            ]

            # Remove duplicates
            search_results = list(
                {result.url: result for result in search_results}.values()
            )
            images = [image for id in dependencies for image in image_map[id][:2]]

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

            # ── Stream Answer ────────────────────────────────────────
            answer_llm = openai_agents.get_answer_generation_llm()
            print("Using OpenAI answer generation for final synthesis")

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
                search_context=format_context_with_steps(search_result_map, step_context),
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

            yield ChatResponseEvent(
                event=StreamEvent.FINAL_RESPONSE,
                data=FinalResponseStream(message=full_response),
            )

            agent_search_steps.append(
                AgentSearchStep(
                    step_number=step_id,
                    step=step.step,
                    queries=[],
                    results=[],
                    status=AgentSearchStepStatus.DONE,
                )
            )

            # Database disabled - no persistence
            thread_id = None

            yield ChatResponseEvent(
                event=StreamEvent.STREAM_END,
                data=StreamEndStream(
                    thread_id=thread_id,
                    session_id=session_id
                ),
            )
            return


async def stream_pro_search_qa(
    request: ChatRequest, session=None, user: Optional[AuthenticatedUser] = None
) -> AsyncIterator[ChatResponseEvent]:
    try:
        if not PRO_MODE_ENABLED:
            raise HTTPException(
                status_code=400,
                detail="Pro mode is not enabled. Set PRO_MODE_ENABLED=true to enable.",
            )

        openai_agents = OpenAIAgents()

        # Rephrase query with conversation context if this is a follow-up
        query = request.query
        if request.session_id:
            query = await rephrase_query_with_context(request.query, openai_agents)

        print(f"[Pro Search] Original query: {request.query}")
        if query != request.query:
            print(f"[Pro Search] Rephrased to: {query}")

        # Try pro search, fallback to regular search if it fails
        try:
            async for event in stream_pro_search_objects(
                request, openai_agents, query, session
            ):
                yield event
                await asyncio.sleep(0)
        except Exception as pro_error:
            # Pro search failed - log and fallback to regular search
            print(f"Pro search failed: {pro_error}")
            print("   Falling back to regular search mode...")

            # Import and use regular search
            from chat import stream_qa_objects
            async for event in stream_qa_objects(
                request=request,
                session=session,
                user=user
            ):
                yield event
                await asyncio.sleep(0)

    except Exception as e:
        detail = str(e).strip() if str(e).strip() else f"Pro search processing error: {type(e).__name__}"
        print(f"Error in stream_pro_search_qa: {detail}")
        raise HTTPException(status_code=500, detail=detail)
