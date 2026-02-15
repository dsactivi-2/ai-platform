"""Rate limiting policy for throttling and quotas."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any, Dict, Optional

from governor.policies.base import Policy, PolicyPhase, PolicyResult


class RateLimitPolicy(Policy):
    """
    Policy for rate limiting and quota enforcement.

    Supports token bucket and sliding window rate limiting strategies.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        max_calls: int = 100,
        window_seconds: int = 60,
        per_user: bool = False,
        burst_size: Optional[int] = None,
        user_key: str = "user.id",
    ):
        """
        Initialize rate limit policy.

        Args:
            name: Policy name
            max_calls: Maximum number of calls allowed in the window
            window_seconds: Time window in seconds
            per_user: If True, apply rate limit per user; if False, globally
            burst_size: Optional burst size for token bucket (defaults to max_calls)
            user_key: Key path in context to extract user ID (e.g., "user.id")
        """
        super().__init__(name=name, phase=PolicyPhase.PRE_EXECUTION)
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.per_user = per_user
        self.burst_size = burst_size or max_calls
        self.user_key = user_key

        # Sliding window storage: key -> list of timestamps
        self._windows: Dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """Evaluate rate limit policy."""
        context = context or {}

        # Determine rate limit key
        if self.per_user:
            # Extract user ID from context
            user_id = self._get_nested_value(context, self.user_key)
            if not user_id:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Cannot apply per-user rate limit: user ID not found at '{self.user_key}'",
                    should_block=False,
                    should_warn=True,
                )
            rate_key = f"{function_name}:{user_id}"
        else:
            rate_key = function_name

        # Check rate limit
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Clean up old timestamps
            self._windows[rate_key] = [
                ts for ts in self._windows[rate_key] if ts > window_start
            ]

            # Check if limit exceeded
            current_count = len(self._windows[rate_key])
            if current_count >= self.max_calls:
                oldest_ts = min(self._windows[rate_key]) if self._windows[rate_key] else now
                retry_after = int(oldest_ts + self.window_seconds - now) + 1

                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Rate limit exceeded: {current_count}/{self.max_calls} calls in {self.window_seconds}s",
                    details={
                        "current_count": current_count,
                        "max_calls": self.max_calls,
                        "window_seconds": self.window_seconds,
                        "retry_after_seconds": retry_after,
                        "rate_key": rate_key,
                    },
                )

            # Record this call
            self._windows[rate_key].append(now)

        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message=f"Rate limit check passed: {current_count + 1}/{self.max_calls} calls",
            details={
                "current_count": current_count + 1,
                "max_calls": self.max_calls,
                "remaining": self.max_calls - current_count - 1,
            },
        )

    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get value from nested dict using dot notation (e.g., 'user.id')."""
        keys = key_path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limit counters.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key:
            self._windows.pop(key, None)
        else:
            self._windows.clear()
