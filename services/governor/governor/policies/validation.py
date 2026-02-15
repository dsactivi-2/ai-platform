"""Validation policy for input/output validation."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from governor.policies.base import Policy, PolicyPhase, PolicyResult


class ValidationPolicy(Policy):
    """
    Policy for validating function inputs and outputs.

    Supports custom validation functions or Pydantic models for
    schema-based validation.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        phase: PolicyPhase = PolicyPhase.PRE_EXECUTION,
        input_validator: Optional[Callable[[Dict[str, Any]], bool]] = None,
        output_validator: Optional[Callable[[Any], bool]] = None,
        input_schema: Optional[type] = None,
        output_schema: Optional[type] = None,
        strict: bool = True,
    ):
        """
        Initialize validation policy.

        Args:
            name: Policy name
            phase: When to evaluate (pre/post/both)
            input_validator: Custom function to validate inputs
            output_validator: Custom function to validate outputs
            input_schema: Pydantic model for input validation
            output_schema: Pydantic model for output validation
            strict: If True, fail on validation errors; if False, warn
        """
        super().__init__(name=name, phase=phase)
        self.input_validator = input_validator
        self.output_validator = output_validator
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.strict = strict

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """Evaluate validation policy."""
        # Pre-execution: validate inputs
        if self.phase in (PolicyPhase.PRE_EXECUTION, PolicyPhase.BOTH) and outputs is None:
            return await self._validate_inputs(inputs)

        # Post-execution: validate outputs
        if self.phase in (PolicyPhase.POST_EXECUTION, PolicyPhase.BOTH) and outputs is not None:
            return await self._validate_outputs(outputs)

        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="No validation required for this phase",
        )

    async def _validate_inputs(self, inputs: Dict[str, Any]) -> PolicyResult:
        """Validate function inputs."""
        # Pydantic schema validation
        if self.input_schema:
            try:
                # Try to validate using Pydantic
                self.input_schema(**inputs)
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Input validation failed: {e}",
                    should_block=self.strict,
                    should_warn=not self.strict,
                    details={"error": str(e), "inputs": inputs},
                )

        # Custom validator
        if self.input_validator:
            try:
                is_valid = self.input_validator(inputs)
                if not is_valid:
                    return PolicyResult.failure(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Input validation failed: custom validator returned False",
                        should_block=self.strict,
                        should_warn=not self.strict,
                    )
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Input validation error: {e}",
                    should_block=self.strict,
                    should_warn=not self.strict,
                    details={"error": str(e)},
                )

        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="Input validation passed",
        )

    async def _validate_outputs(self, outputs: Any) -> PolicyResult:
        """Validate function outputs."""
        # Pydantic schema validation
        if self.output_schema:
            try:
                # Handle both single values and dicts
                if isinstance(outputs, dict):
                    self.output_schema(**outputs)
                else:
                    self.output_schema(value=outputs)
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Output validation failed: {e}",
                    should_block=self.strict,
                    should_warn=not self.strict,
                    details={"error": str(e)},
                )

        # Custom validator
        if self.output_validator:
            try:
                is_valid = self.output_validator(outputs)
                if not is_valid:
                    return PolicyResult.failure(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Output validation failed: custom validator returned False",
                        should_block=self.strict,
                        should_warn=not self.strict,
                    )
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Output validation error: {e}",
                    should_block=self.strict,
                    should_warn=not self.strict,
                    details={"error": str(e)},
                )

        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="Output validation passed",
        )
