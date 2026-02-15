"""Authorization policy for access control."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set

from governor.policies.base import Policy, PolicyPhase, PolicyResult


class AuthorizationPolicy(Policy):
    """
    Policy for authorization and access control.

    Supports role-based access control (RBAC), attribute-based access control (ABAC),
    and custom authorization functions.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        required_roles: Optional[Set[str]] = None,
        required_permissions: Optional[Set[str]] = None,
        custom_authorizer: Optional[Callable[[Dict[str, Any]], bool]] = None,
        context_key: str = "user",
        require_approval_on_failure: bool = False,
    ):
        """
        Initialize authorization policy.

        Args:
            name: Policy name
            required_roles: Set of roles, user must have at least one
            required_permissions: Set of permissions, user must have all
            custom_authorizer: Custom authorization function
            context_key: Key in context to find user/principal info
            require_approval_on_failure: Request approval instead of blocking
        """
        super().__init__(name=name, phase=PolicyPhase.PRE_EXECUTION)
        self.required_roles = required_roles or set()
        self.required_permissions = required_permissions or set()
        self.custom_authorizer = custom_authorizer
        self.context_key = context_key
        self.require_approval_on_failure = require_approval_on_failure

    async def evaluate(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """Evaluate authorization policy."""
        context = context or {}

        # Get user/principal from context
        principal = context.get(self.context_key)
        if not principal:
            if self.require_approval_on_failure:
                return PolicyResult.approval_required(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message="No principal found in context, approval required",
                    details={"context_key": self.context_key},
                )
            return PolicyResult.failure(
                policy_name=self.name,
                policy_type=self.get_policy_type(),
                message=f"No principal found in context (key: {self.context_key})",
                details={"context_key": self.context_key},
            )

        # Extract roles and permissions
        user_roles = set(principal.get("roles", []))
        user_permissions = set(principal.get("permissions", []))

        # Check required roles (user must have at least one)
        if self.required_roles:
            if not user_roles.intersection(self.required_roles):
                if self.require_approval_on_failure:
                    return PolicyResult.approval_required(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message=f"User lacks required roles, approval required",
                        details={
                            "required_roles": list(self.required_roles),
                            "user_roles": list(user_roles),
                        },
                    )
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"User lacks required roles",
                    details={
                        "required_roles": list(self.required_roles),
                        "user_roles": list(user_roles),
                    },
                )

        # Check required permissions (user must have all)
        if self.required_permissions:
            missing_permissions = self.required_permissions - user_permissions
            if missing_permissions:
                if self.require_approval_on_failure:
                    return PolicyResult.approval_required(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message=f"User lacks required permissions, approval required",
                        details={
                            "missing_permissions": list(missing_permissions),
                            "user_permissions": list(user_permissions),
                        },
                    )
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"User lacks required permissions",
                    details={
                        "missing_permissions": list(missing_permissions),
                        "user_permissions": list(user_permissions),
                    },
                )

        # Custom authorization logic
        if self.custom_authorizer:
            try:
                authorized = self.custom_authorizer(
                    {
                        "principal": principal,
                        "inputs": inputs,
                        "context": context,
                        "execution_id": execution_id,
                        "function_name": function_name,
                    }
                )
                if not authorized:
                    if self.require_approval_on_failure:
                        return PolicyResult.approval_required(
                            policy_name=self.name,
                            policy_type=self.get_policy_type(),
                            message="Custom authorizer denied access, approval required",
                        )
                    return PolicyResult.failure(
                        policy_name=self.name,
                        policy_type=self.get_policy_type(),
                        message="Custom authorizer denied access",
                    )
            except Exception as e:
                return PolicyResult.failure(
                    policy_name=self.name,
                    policy_type=self.get_policy_type(),
                    message=f"Authorization error: {e}",
                    details={"error": str(e)},
                )

        return PolicyResult.success(
            policy_name=self.name,
            policy_type=self.get_policy_type(),
            message="Authorization passed",
            details={
                "user_roles": list(user_roles),
                "user_permissions": list(user_permissions),
            },
        )
