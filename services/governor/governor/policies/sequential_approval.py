"""Sequential multi-stage approval policy for governance pipelines."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, List, Optional

from governor.policies.base import Policy, PolicyPhase, PolicyResult


ApprovalCallback = Callable[[str, str, Dict[str, Any]], Coroutine[Any, Any, bool]]


class ApprovalStage:
    """
    Represents a single approval stage in a sequential pipeline.

    Each stage has:
    - Stage name (e.g., "AI Safety Team", "Security Team")
    - List of approvers for that stage
    - Optional timeout
    - Optional auto-approve condition
    """

    def __init__(
        self,
        name: str,
        approvers: List[str],
        timeout_seconds: Optional[int] = 3600,
        on_timeout: str = "reject",
        require_reason: bool = False,
        auto_approve_condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        description: Optional[str] = None,
    ):
        """
        Initialize an approval stage.

        Args:
            name: Stage name (e.g., "AI Safety Review")
            approvers: List of approver identifiers for this stage
            timeout_seconds: How long to wait for approval
            on_timeout: What to do on timeout: "reject", "approve", or "escalate"
            require_reason: Whether approver must provide a reason
            auto_approve_condition: Function that can auto-approve based on inputs
            description: Optional description of what this stage checks
        """
        self.name = name
        self.approvers = approvers
        self.timeout_seconds = timeout_seconds
        self.on_timeout = on_timeout
        self.require_reason = require_reason
        self.auto_approve_condition = auto_approve_condition
        self.description = description or f"{name} approval"


class SequentialApprovalPolicy(Policy):
    """
    Multi-stage sequential approval policy.

    Enforces a pipeline of approval stages where each stage must be
    approved before moving to the next. Example:

    Stage 1: AI Safety Team → Stage 2: Security Team → Stage 3: Legal Team

    Each stage can have:
    - Different approvers
    - Different timeouts
    - Different auto-approve conditions
    - Custom descriptions

    Use cases:
    - AI model deployment (Safety → Security → Legal → Executive)
    - Financial transactions (Manager → Finance → CFO)
    - Code deployment (Tech Lead → Security → DevOps)
    - Data access (Team Lead → Privacy → Compliance)
    """

    def __init__(
        self,
        stages: List[ApprovalStage],
        name: Optional[str] = None,
        stop_on_reject: bool = True,
        approval_callback: Optional[ApprovalCallback] = None,
    ):
        """
        Initialize sequential approval policy.

        Args:
            stages: List of approval stages (executed in order)
            name: Policy name (defaults to "SequentialApproval")
            stop_on_reject: Stop pipeline if any stage rejects (vs continue to all)
            approval_callback: Custom async callback for approval logic
        """
        super().__init__(
            name=name or "SequentialApproval",
            phase=PolicyPhase.PRE_EXECUTION
        )
        self.stages = stages
        self.stop_on_reject = stop_on_reject
        self.approval_callback = approval_callback

        # Track current stage during execution
        self._current_stage_index = 0
        self._stage_results: Dict[str, Dict[str, Any]] = {}

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """
        Evaluate sequential approval policy.

        Processes each stage in order:
        1. Check auto-approve condition
        2. If not auto-approved, require manual approval
        3. Track results for each stage
        4. Move to next stage only if current stage approved
        """
        context = context or {}

        # Get resume state if this is a continuation
        resume_stage = context.get("resume_from_stage", 0)
        if resume_stage > 0:
            self._current_stage_index = resume_stage

        all_stages_passed = True
        stage_details = []

        # Process each stage sequentially
        for stage_idx, stage in enumerate(self.stages):
            # Skip stages we've already completed (for resume scenarios)
            if stage_idx < self._current_stage_index:
                continue

            stage_result = await self._evaluate_stage(
                stage=stage,
                stage_index=stage_idx,
                execution_id=execution_id,
                function_name=function_name,
                inputs=inputs,
                context=context,
            )

            # Store stage result
            self._stage_results[stage.name] = stage_result
            stage_details.append(stage_result)

            # Check if stage passed
            if not stage_result["passed"]:
                all_stages_passed = False

                if self.stop_on_reject:
                    # Stop pipeline immediately
                    return PolicyResult.failure(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message=f"Stage '{stage.name}' rejected - pipeline stopped",
                        details={
                            "failed_stage": stage.name,
                            "stage_index": stage_idx,
                            "total_stages": len(self.stages),
                            "stage_results": stage_details,
                        }
                    )

            # If stage requires approval (not auto-approved), we need to pause here
            if stage_result.get("approval_required", False):
                self._current_stage_index = stage_idx
                return PolicyResult.approval_required(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Stage {stage_idx + 1}/{len(self.stages)}: {stage.name} - Approval required from {', '.join(stage.approvers)}",
                    details={
                        "current_stage": stage.name,
                        "stage_index": stage_idx,
                        "total_stages": len(self.stages),
                        "approvers": stage.approvers,
                        "timeout_seconds": stage.timeout_seconds,
                        "on_timeout": stage.on_timeout,
                        "execution_id": execution_id,
                        "function_name": function_name,
                        "inputs": inputs,
                        "completed_stages": stage_details[:-1],  # All except current
                        "resume_from_stage": stage_idx + 1,  # Next stage to resume from
                    }
                )

        # All stages passed
        if all_stages_passed:
            return PolicyResult.success(
                policy_name=self.name,
                policy_type=self.get_policy_type(),
                message=f"All {len(self.stages)} approval stages passed",
                details={
                    "stage_results": stage_details,
                    "total_stages": len(self.stages),
                }
            )
        else:
            return PolicyResult.failure(
                policy_name=self.name,
                policy_type=self.get_policy_type(),
                message="One or more stages rejected",
                details={
                    "stage_results": stage_details,
                    "total_stages": len(self.stages),
                }
            )

    async def _evaluate_stage(
        self,
        stage: ApprovalStage,
        stage_index: int,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate a single approval stage."""

        # Check auto-approve condition first
        if stage.auto_approve_condition:
            try:
                if stage.auto_approve_condition(inputs):
                    return {
                        "stage_name": stage.name,
                        "stage_index": stage_index,
                        "passed": True,
                        "auto_approved": True,
                        "approvers": stage.approvers,
                        "message": f"Stage '{stage.name}' auto-approved",
                    }
            except Exception as e:
                # If auto-approve check fails, fall through to manual approval
                pass

        # Use custom approval callback if provided
        if self.approval_callback:
            try:
                approved = await self.approval_callback(execution_id, function_name, inputs)
                return {
                    "stage_name": stage.name,
                    "stage_index": stage_index,
                    "passed": approved,
                    "auto_approved": False,
                    "via_callback": True,
                    "approvers": stage.approvers,
                    "message": f"Stage '{stage.name}' {'approved' if approved else 'rejected'} via callback",
                }
            except Exception as e:
                return {
                    "stage_name": stage.name,
                    "stage_index": stage_index,
                    "passed": False,
                    "error": str(e),
                    "approvers": stage.approvers,
                    "message": f"Stage '{stage.name}' callback error: {e}",
                }

        # Otherwise, require manual approval
        return {
            "stage_name": stage.name,
            "stage_index": stage_index,
            "passed": False,
            "approval_required": True,
            "approvers": stage.approvers,
            "timeout_seconds": stage.timeout_seconds,
            "on_timeout": stage.on_timeout,
            "message": f"Stage '{stage.name}' requires manual approval from {', '.join(stage.approvers)}",
        }

    def reset(self) -> None:
        """Reset the policy state (for testing or reuse)."""
        self._current_stage_index = 0
        self._stage_results = {}
