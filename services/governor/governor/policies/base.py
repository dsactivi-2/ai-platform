"""Base policy interface for governance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PolicyPhase(str, Enum):
    """Phase when a policy should be evaluated."""

    PRE_EXECUTION = "pre_execution"  # Before function execution
    POST_EXECUTION = "post_execution"  # After function execution
    BOTH = "both"  # Both before and after


class PolicyResult(BaseModel):
    """Result of a policy evaluation."""

    # Policy info
    policy_name: str
    policy_type: str

    # Result
    passed: bool
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    # Actions
    should_block: bool = False  # Should block execution
    should_approve: bool = False  # Should request approval
    should_warn: bool = False  # Should warn but allow

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(
        cls,
        policy_name: str,
        policy_type: str,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> PolicyResult:
        """Create a successful policy result."""
        return cls(
            policy_name=policy_name,
            policy_type=policy_type,
            passed=True,
            message=message or "Policy check passed",
            **kwargs,
        )

    @classmethod
    def failure(
        cls,
        policy_name: str,
        policy_type: str,
        message: str,
        should_block: bool = True,
        **kwargs: Any,
    ) -> PolicyResult:
        """Create a failed policy result."""
        return cls(
            policy_name=policy_name,
            policy_type=policy_type,
            passed=False,
            message=message,
            should_block=should_block,
            **kwargs,
        )

    @classmethod
    def approval_required(
        cls,
        policy_name: str,
        policy_type: str,
        message: str,
        **kwargs: Any,
    ) -> PolicyResult:
        """Create a policy result that requires approval."""
        return cls(
            policy_name=policy_name,
            policy_type=policy_type,
            passed=False,
            message=message,
            should_approve=True,
            should_block=True,
            **kwargs,
        )


class Policy(ABC):
    """
    Base class for all governance policies.

    Policies define rules that must be satisfied before, during, or after
    function execution. They can validate inputs, check permissions,
    enforce rate limits, audit operations, or require approval.
    """

    def __init__(self, name: Optional[str] = None, phase: PolicyPhase = PolicyPhase.PRE_EXECUTION):
        """
        Initialize the policy.

        Args:
            name: Optional name for the policy (defaults to class name)
            phase: When the policy should be evaluated
        """
        self.name = name or self.__class__.__name__
        self.phase = phase

    @abstractmethod
    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """
        Evaluate the policy.

        Args:
            execution_id: Unique ID of the execution
            function_name: Name of the governed function
            inputs: Function inputs (args and kwargs)
            outputs: Function outputs (None for pre-execution)
            context: Additional context data

        Returns:
            PolicyResult indicating if the policy passed or failed
        """
        pass

    def get_policy_type(self) -> str:
        """Get the type of this policy."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name}, phase={self.phase})"
