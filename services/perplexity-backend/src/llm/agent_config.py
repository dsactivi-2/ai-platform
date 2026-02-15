"""OpenAI model configuration for the Perplexity OSS application."""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── OpenAI Model Configuration ──────────────────────────────────────────

OPENAI_MODEL_REASONING = os.getenv("OPENAI_MODEL_REASONING", "gpt-4.1-mini")
OPENAI_MODEL_FAST = os.getenv("OPENAI_MODEL_FAST", "gpt-4.1-nano")

AGENT_MODEL_MAP = {
    "answer_generation": OPENAI_MODEL_REASONING,
    "query_planning": OPENAI_MODEL_REASONING,
    "query_rephrase": OPENAI_MODEL_FAST,
    "search_query": OPENAI_MODEL_FAST,
    "related_questions": OPENAI_MODEL_FAST,
}
