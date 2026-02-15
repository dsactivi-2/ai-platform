"""Audit policy for compliance and logging."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from governor.policies.base import Policy, PolicyPhase, PolicyResult


class AuditPolicy(Policy):
    """
    Policy for audit logging and compliance tracking.

    Automatically logs execution details for compliance, debugging,
    and monitoring purposes.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        phase: PolicyPhase = PolicyPhase.BOTH,
        log_inputs: bool = True,
        log_outputs: bool = True,
        sensitive_fields: Optional[List[str]] = None,
        compliance_tags: Optional[List[str]] = None,
        custom_logger: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        """
        Initialize audit policy.

        Args:
            name: Policy name
            phase: When to audit (pre/post/both)
            log_inputs: Whether to log function inputs
            log_outputs: Whether to log function outputs
            sensitive_fields: List of field names to redact
            compliance_tags: Tags for compliance categorization (e.g., ["SOC2", "HIPAA"])
            custom_logger: Custom async logging function
        """
        super().__init__(name=name, phase=phase)
        self.log_inputs = log_inputs
        self.log_outputs = log_outputs
        self.sensitive_fields = sensitive_fields or []
        self.compliance_tags = compliance_tags or []
        self.custom_logger = custom_logger

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """Evaluate audit policy (always passes, just logs)."""
        context = context or {}

        # Build audit record
        audit_record: Dict[str, Any] = {
            "execution_id": execution_id,
            "function_name": function_name,
            "compliance_tags": self.compliance_tags,
        }

        # Add inputs (pre-execution or both)
        if self.log_inputs and (self.phase in (PolicyPhase.PRE_EXECUTION, PolicyPhase.BOTH)):
            audit_record["inputs"] = self._redact_sensitive(inputs)

        # Add outputs (post-execution or both)
        if self.log_outputs and outputs is not None and (
            self.phase in (PolicyPhase.POST_EXECUTION, PolicyPhase.BOTH)
        ):
            audit_record["outputs"] = self._redact_sensitive(outputs)

        # Add user info if available
        if "user" in context:
            user_info = context["user"]
            audit_record["user"] = {
                "id": user_info.get("id"),
                "email": user_info.get("email"),
                "roles": user_info.get("roles"),
            }

        # Custom logging
        if self.custom_logger:
            try:
                self.custom_logger(audit_record)
            except Exception as e:
                # Don't fail execution due to logging errors
                pass

        # Audit policy always passes (it's for logging, not blocking)
        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="Audit record created",
            details=audit_record,
        )

    def _redact_sensitive(self, data: Any) -> Any:
        """Redact sensitive fields from data."""
        if not self.sensitive_fields:
            return data

        if isinstance(data, dict):
            return {
                key: "***REDACTED***" if key in self.sensitive_fields else self._redact_sensitive(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._redact_sensitive(item) for item in data]
        else:
            return data
