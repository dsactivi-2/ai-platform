"""Approval policy for human-in-the-loop governance."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, List, Optional

from governor.policies.base import Policy, PolicyPhase, PolicyResult


ApprovalCallback = Callable[[str, str, Dict[str, Any]], Coroutine[Any, Any, bool]]


class ApprovalPolicy(Policy):
    """
    Policy that requires human approval before execution.

    Pauses execution and waits for approval from designated approvers
    through webhooks, CLI, or custom callbacks.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        approvers: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = 3600,
        on_timeout: str = "reject",
        approval_callback: Optional[ApprovalCallback] = None,
        require_reason: bool = False,
        auto_approve_condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        """
        Initialize approval policy.

        Args:
            name: Policy name
            approvers: List of approver identifiers (emails, user IDs, etc.)
            timeout_seconds: How long to wait for approval (None = indefinite)
            on_timeout: What to do on timeout: "reject", "approve", or "escalate"
            approval_callback: Custom async callback for approval logic
            require_reason: Whether approver must provide a reason
            auto_approve_condition: Function that can auto-approve based on inputs
        """
        super().__init__(name=name, phase=PolicyPhase.PRE_EXECUTION)
        self.approvers = approvers or []
        self.timeout_seconds = timeout_seconds
        self.on_timeout = on_timeout
        self.approval_callback = approval_callback
        self.require_reason = require_reason
        self.auto_approve_condition = auto_approve_condition

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """Evaluate approval policy."""
        context = context or {}

        # Check auto-approve condition
        if self.auto_approve_condition:
            try:
                if self.auto_approve_condition(inputs):
                    return PolicyResult.success(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Auto-approved based on condition",
                        details={"auto_approved": True},
                    )
            except Exception as e:
                # If auto-approve check fails, fall through to manual approval
                pass

        # Use custom approval callback if provided
        if self.approval_callback:
            try:
                approved = await self.approval_callback(execution_id, function_name, inputs)
                if approved:
                    return PolicyResult.success(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Approved via custom callback",
                    )
                else:
                    return PolicyResult.failure(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Rejected via custom callback",
                    )
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Approval callback error: {e}",
                    details={"error": str(e)},
                )

        # Otherwise, require manual approval
        return PolicyResult.approval_required(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message=f"Approval required from: {', '.join(self.approvers) if self.approvers else 'any approver'}",
            details={
                "approvers": self.approvers,
                "timeout_seconds": self.timeout_seconds,
                "on_timeout": self.on_timeout,
                "execution_id": execution_id,
                "function_name": function_name,
                "inputs": inputs,
            },
        )
