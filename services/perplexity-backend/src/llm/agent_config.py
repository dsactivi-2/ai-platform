"""LLM model configuration for the Perplexity OSS application.

Supports any OpenAI-compatible API (OpenAI, Groq, Together, OpenRouter, etc.)
via the OPENAI_BASE_URL environment variable.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── LLM Provider Configuration ──────────────────────────────────────────

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.x.ai/v1")
OPENAI_MODEL_REASONING = os.getenv("OPENAI_MODEL_REASONING", "grok-4-latest")
OPENAI_MODEL_FAST = os.getenv("OPENAI_MODEL_FAST", "grok-4-latest")

AGENT_MODEL_MAP = {
    "answer_generation": OPENAI_MODEL_REASONING,
    "query_planning": OPENAI_MODEL_REASONING,
    "query_rephrase": OPENAI_MODEL_FAST,
    "search_query": OPENAI_MODEL_FAST,
    "related_questions": OPENAI_MODEL_FAST,
}
