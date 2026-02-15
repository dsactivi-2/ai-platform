"""OpenAI LLM implementation for the Perplexity OSS application.

Uses the official OpenAI Python SDK (v1.x+) with async support for
chat completions, streaming, and structured JSON output.
"""

import asyncio
import json
import os
from typing import AsyncGenerator, TypeVar

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
)

from .base import BaseLLM, CompletionResponse, CompletionResponseAsyncGen
from retry_utils import CircuitBreaker

T = TypeVar("T")

# ── Circuit Breakers (shared across all OpenAI LLM instances) ────────────────

openai_streaming_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0,
    success_threshold=2,
)

openai_completion_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    success_threshold=2,
)

# Transient errors that are safe to retry
RETRYABLE_ERRORS = (APITimeoutError, APIConnectionError, RateLimitError)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5  # seconds, doubles each attempt


class OpenAILLM(BaseLLM):
    """OpenAI-compatible Chat Completions implementation of BaseLLM.

    Works with any OpenAI-compatible API (OpenAI, Groq, Together, OpenRouter, etc.)
    Each instance targets a specific model. The caller provides system_prompt + user_message per request.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.timeout = timeout

        # Detect if we're using native OpenAI (supports json_schema) or a compatible provider
        self._is_openai_native = not self.base_url or "api.openai.com" in (self.base_url or "")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable or api_key parameter is required"
            )

        client_kwargs = {
            "api_key": self.api_key,
            "timeout": self.timeout,
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**client_kwargs)

    # ── Helper: build kwargs dict, filtering out None values ─────────────

    @staticmethod
    def _build_optional_kwargs(**kwargs) -> dict:
        """Return only the kwargs that have non-None values."""
        return {k: v for k, v in kwargs.items() if v is not None}

    # ── complete ─────────────────────────────────────────────────────────

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs,
    ) -> str:
        """Non-streaming chat completion.

        Args:
            system_prompt: System message content.
            user_message:  User message content.
            **kwargs:      Optional overrides (temperature, max_tokens).

        Returns:
            The assistant's response as a plain string.
        """
        if not openai_completion_breaker.should_allow_request():
            raise Exception(
                "OpenAI API circuit breaker is OPEN — service temporarily unavailable."
            )

        optional = self._build_optional_kwargs(
            temperature=kwargs.get("temperature"),
            max_tokens=kwargs.get("max_tokens"),
        )

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    **optional,
                )

                content = response.choices[0].message.content or ""
                openai_completion_breaker.record_success()
                print(f"OpenAI complete ({self.model}): {len(content)} chars")
                return content

            except RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    print(
                        f"⚠️ OpenAI attempt {attempt}/{MAX_RETRIES} failed "
                        f"({type(e).__name__}), retrying in {delay:.1f}s…"
                    )
                    await asyncio.sleep(delay)
                else:
                    openai_completion_breaker.record_failure()
                    raise Exception(
                        f"OpenAI API failed after {MAX_RETRIES} attempts: {e}"
                    ) from e

            except Exception as e:
                openai_completion_breaker.record_failure()
                raise Exception(
                    f"OpenAI API error: {type(e).__name__} — {e}"
                ) from e

        # Should never reach here, but satisfy the type checker
        if last_error:
            raise Exception(
                f"OpenAI API failed after {MAX_RETRIES} attempts"
            ) from last_error

    # ── astream ──────────────────────────────────────────────────────────

    async def astream(
        self,
        system_prompt: str,
        user_message: str,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion.

        Args:
            system_prompt: System message content.
            user_message:  User message content.
            **kwargs:      Optional overrides (temperature, max_tokens).

        Yields:
            Content delta strings as they arrive from the API.
        """
        if not openai_streaming_breaker.should_allow_request():
            raise Exception(
                "OpenAI API streaming circuit breaker is OPEN — "
                "service temporarily unavailable."
            )

        optional = self._build_optional_kwargs(
            temperature=kwargs.get("temperature"),
            max_tokens=kwargs.get("max_tokens"),
        )

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    stream=True,
                    **optional,
                )

                print(f"✅ OpenAI stream started ({self.model})")
                tokens_received = 0

                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        tokens_received += 1
                        yield delta.content

                openai_streaming_breaker.record_success()
                print(
                    f"✅ OpenAI stream completed ({tokens_received} chunks)"
                )
                return  # success — exit retry loop

            except RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    print(
                        f"⚠️ OpenAI stream attempt {attempt}/{MAX_RETRIES} "
                        f"failed ({type(e).__name__}), retrying in {delay:.1f}s…"
                    )
                    await asyncio.sleep(delay)
                else:
                    openai_streaming_breaker.record_failure()
                    raise Exception(
                        f"OpenAI streaming failed after {MAX_RETRIES} attempts: {e}"
                    ) from e

            except Exception as e:
                openai_streaming_breaker.record_failure()
                raise Exception(
                    f"OpenAI streaming error: {type(e).__name__} — {e}"
                ) from e

        if last_error:
            raise Exception(
                f"OpenAI streaming failed after {MAX_RETRIES} attempts"
            ) from last_error

    # ── structured_complete ──────────────────────────────────────────────

    async def structured_complete(
        self,
        system_prompt: str,
        user_message: str,
        response_format: dict,
        **kwargs,
    ) -> dict:
        """Structured completion with JSON output.

        For native OpenAI: uses json_schema mode for strict schema enforcement.
        For compatible providers (Groq, etc.): uses json_object mode with
        schema instructions appended to the system prompt.

        Args:
            system_prompt:   System message content.
            user_message:    User message content.
            response_format: JSON schema dict (name, strict, schema keys).
            **kwargs:        Optional overrides (temperature, max_tokens).

        Returns:
            Parsed JSON dict from the assistant's response.

        Raises:
            Exception: If the response cannot be parsed as valid JSON.
        """
        if not openai_completion_breaker.should_allow_request():
            raise Exception(
                "OpenAI API circuit breaker is OPEN — service temporarily unavailable."
            )

        optional = self._build_optional_kwargs(
            temperature=kwargs.get("temperature"),
            max_tokens=kwargs.get("max_tokens"),
        )

        # Build response_format and system prompt based on provider
        if self._is_openai_native:
            rf = {"type": "json_schema", "json_schema": response_format}
            effective_system_prompt = system_prompt
        else:
            # Groq and other providers: json_object mode + schema in prompt
            rf = {"type": "json_object"}
            schema_def = response_format.get("schema", response_format)
            schema_hint = json.dumps(schema_def, indent=2)
            effective_system_prompt = (
                f"{system_prompt}\n\n"
                f"You MUST respond with valid JSON matching this exact schema:\n"
                f"```json\n{schema_hint}\n```\n"
                f"Return ONLY the JSON object, no other text."
            )

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": effective_system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    response_format=rf,
                    **optional,
                )

                content = response.choices[0].message.content
                if not content:
                    raise Exception(
                        "OpenAI returned empty response for structured completion"
                    )

                result = json.loads(content)
                openai_completion_breaker.record_success()
                print(f"OpenAI structured_complete ({self.model}): parsed OK")
                return result

            except json.JSONDecodeError as e:
                # JSON parse errors are not transient — fail immediately
                openai_completion_breaker.record_failure()
                raise Exception(
                    f"OpenAI structured response is not valid JSON: {e}"
                ) from e

            except RETRYABLE_ERRORS as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    print(
                        f"⚠️ OpenAI structured attempt {attempt}/{MAX_RETRIES} "
                        f"failed ({type(e).__name__}), retrying in {delay:.1f}s…"
                    )
                    await asyncio.sleep(delay)
                else:
                    openai_completion_breaker.record_failure()
                    raise Exception(
                        f"OpenAI structured completion failed after "
                        f"{MAX_RETRIES} attempts: {e}"
                    ) from e

            except Exception as e:
                if "JSON" in str(e):
                    raise  # Don't retry JSON parse errors
                openai_completion_breaker.record_failure()
                raise Exception(
                    f"OpenAI structured completion error: "
                    f"{type(e).__name__} — {e}"
                ) from e

        if last_error:
            raise Exception(
                f"OpenAI structured completion failed after {MAX_RETRIES} attempts"
            ) from last_error


# ═════════════════════════════════════════════════════════════════════════════
# OpenAIAgents — manager for specialized LLM instances
# ═════════════════════════════════════════════════════════════════════════════


class OpenAIAgents:
    """Manager for specialized LLM instances using any OpenAI-compatible API.

    Creates one OpenAILLM per agent role, using the model mapping from
    ``agent_config.AGENT_MODEL_MAP``.  No network calls in __init__ —
    the LLM instances are lightweight wrappers around the AsyncOpenAI client.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable or api_key parameter is required"
            )

        from .agent_config import AGENT_MODEL_MAP

        self._answer_generation = OpenAILLM(
            model=AGENT_MODEL_MAP["answer_generation"],
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self._query_planning = OpenAILLM(
            model=AGENT_MODEL_MAP["query_planning"],
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self._query_rephrase = OpenAILLM(
            model=AGENT_MODEL_MAP["query_rephrase"],
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self._search_query = OpenAILLM(
            model=AGENT_MODEL_MAP["search_query"],
            api_key=self.api_key,
            base_url=self.base_url,
        )
        self._related_questions = OpenAILLM(
            model=AGENT_MODEL_MAP["related_questions"],
            api_key=self.api_key,
            base_url=self.base_url,
        )

        provider = self.base_url or "OpenAI"
        print(f"LLM initialized — provider: {provider}, models: {set(AGENT_MODEL_MAP.values())}")

    # ── Getter methods ───────────────────────────────────────────────────

    def get_answer_generation_llm(self) -> OpenAILLM:
        """LLM for main answer generation (reasoning model)."""
        return self._answer_generation

    def get_query_planning_llm(self) -> OpenAILLM:
        """LLM for pro-mode query planning (reasoning model)."""
        return self._query_planning

    def get_query_rephrase_llm(self) -> OpenAILLM:
        """LLM for rephrasing follow-up queries (fast model)."""
        return self._query_rephrase

    def get_search_query_llm(self) -> OpenAILLM:
        """LLM for extracting search terms (fast model)."""
        return self._search_query

    def get_related_questions_llm(self) -> OpenAILLM:
        """LLM for generating follow-up questions (fast model)."""
        return self._related_questions
