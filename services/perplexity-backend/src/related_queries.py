"""Related queries generation using OpenAI LLM."""

from llm.openai_llm import OpenAILLM
from prompts import build_related_questions_system_prompt, RELATED_QUESTIONS_SCHEMA
from schemas import RelatedQueries, SearchResult


async def generate_related_queries(
    query: str, search_results: list[SearchResult], llm: OpenAILLM
) -> list[str]:
    """Generate related follow-up questions using structured completion."""
    context = "\n\n".join([str(result) for result in search_results])
    context = context[:4000]

    system_prompt = build_related_questions_system_prompt(
        user_query=query,
        search_context=context,
    )

    result = await llm.structured_complete(
        system_prompt=system_prompt,
        user_message="Generate 3 follow-up questions based on the question and context above.",
        response_format=RELATED_QUESTIONS_SCHEMA,
    )

    related = RelatedQueries(**result)
    return [q.lower().replace("?", "") for q in related.related_questions]
