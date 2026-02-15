"""Load policies from JSON and YAML configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from governor.policies.approval import ApprovalPolicy
from governor.policies.audit import AuditPolicy
from governor.policies.authorization import AuthorizationPolicy
from governor.policies.base import Policy, PolicyPhase
from governor.policies.rate_limit import RateLimitPolicy
from governor.policies.validation import ValidationPolicy


class PolicyLoader:
    """
    Load and parse policies from JSON or YAML configuration files.

    Supports externalized policy configuration for better separation
    of concerns and easier policy management.
    """

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> List[Policy]:
        """
        Load policies from a JSON or YAML file.

        Args:
            file_path: Path to the configuration file (.json or .yaml/.yml)

        Returns:
            List of Policy instances

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or invalid

        Example:
            ```python
            policies = PolicyLoader.load_from_file("governance.yaml")
            @govern(policies=policies)
            async def my_function():
                pass
            ```
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")

        # Read file content
        content = file_path.read_text()

        # Parse based on extension
        if file_path.suffix.lower() == ".json":
            config = json.loads(content)
        elif file_path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml

                config = yaml.safe_load(content)
            except ImportError:
                raise ImportError(
                    "YAML support requires 'pyyaml' package. "
                    "Install with: pip install pyyaml"
                )
        else:
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. "
                "Use .json, .yaml, or .yml"
            )

        return PolicyLoader.load_from_dict(config)

    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> List[Policy]:
        """
        Load policies from a dictionary configuration.

        Args:
            config: Dictionary with policy configurations

        Returns:
            List of Policy instances

        Raises:
            ValueError: If configuration is invalid

        Example:
            ```python
            config = {
                "policies": [
                    {"type": "validation", "strict": True},
                    {"type": "audit", "compliance_tags": ["SOC2"]}
                ]
            }
            policies = PolicyLoader.load_from_dict(config)
            ```
        """
        if "policies" not in config:
            raise ValueError("Configuration must contain 'policies' key")

        policies = []
        for policy_config in config["policies"]:
            policy = PolicyLoader._parse_policy(policy_config)
            if policy:
                policies.append(policy)

        return policies

    @staticmethod
    def _parse_policy(config: Dict[str, Any]) -> Optional[Policy]:
        """
        Parse a single policy configuration.

        Args:
            config: Policy configuration dictionary

        Returns:
            Policy instance or None if disabled
        """
        if not config.get("enabled", True):
            return None

        policy_type = config.get("type", "").lower()
        name = config.get("name")
        phase = PolicyLoader._parse_phase(config.get("phase", "pre_execution"))

        if policy_type == "validation":
            return PolicyLoader._create_validation_policy(config, name, phase)
        elif policy_type == "authorization":
            return PolicyLoader._create_authorization_policy(config, name)
        elif policy_type == "rate_limit":
            return PolicyLoader._create_rate_limit_policy(config, name)
        elif policy_type == "audit":
            return PolicyLoader._create_audit_policy(config, name, phase)
        elif policy_type == "approval":
            return PolicyLoader._create_approval_policy(config, name)
        else:
            raise ValueError(f"Unknown policy type: {policy_type}")

    @staticmethod
    def _parse_phase(phase_str: str) -> PolicyPhase:
        """Parse phase string to PolicyPhase enum."""
        phase_map = {
            "pre": PolicyPhase.PRE_EXECUTION,
            "pre_execution": PolicyPhase.PRE_EXECUTION,
            "post": PolicyPhase.POST_EXECUTION,
            "post_execution": PolicyPhase.POST_EXECUTION,
            "both": PolicyPhase.BOTH,
        }
        return phase_map.get(phase_str.lower(), PolicyPhase.PRE_EXECUTION)

    @staticmethod
    def _create_validation_policy(
        config: Dict[str, Any], name: Optional[str], phase: PolicyPhase
    ) -> ValidationPolicy:
        """Create ValidationPolicy from config."""
        return ValidationPolicy(
            name=name,
            phase=phase,
            strict=config.get("strict", True),
        )

    @staticmethod
    def _create_authorization_policy(
        config: Dict[str, Any], name: Optional[str]
    ) -> AuthorizationPolicy:
        """Create AuthorizationPolicy from config."""
        required_roles = config.get("required_roles", [])
        required_permissions = config.get("required_permissions", [])

        return AuthorizationPolicy(
            name=name,
            required_roles=set(required_roles) if required_roles else None,
            required_permissions=set(required_permissions) if required_permissions else None,
            context_key=config.get("context_key", "user"),
            require_approval_on_failure=config.get("require_approval_on_failure", False),
        )

    @staticmethod
    def _create_rate_limit_policy(
        config: Dict[str, Any], name: Optional[str]
    ) -> RateLimitPolicy:
        """Create RateLimitPolicy from config."""
        return RateLimitPolicy(
            name=name,
            max_calls=config.get("max_calls", 100),
            window_seconds=config.get("window_seconds", 60),
            per_user=config.get("per_user", False),
            burst_size=config.get("burst_size"),
            user_key=config.get("user_key", "user.id"),
        )

    @staticmethod
    def _create_audit_policy(
        config: Dict[str, Any], name: Optional[str], phase: PolicyPhase
    ) -> AuditPolicy:
        """Create AuditPolicy from config."""
        return AuditPolicy(
            name=name,
            phase=phase,
            log_inputs=config.get("log_inputs", True),
            log_outputs=config.get("log_outputs", True),
            sensitive_fields=config.get("sensitive_fields", []),
            compliance_tags=config.get("compliance_tags", []),
        )

    @staticmethod
    def _create_approval_policy(
        config: Dict[str, Any], name: Optional[str]
    ) -> ApprovalPolicy:
        """Create ApprovalPolicy from config."""
        return ApprovalPolicy(
            name=name,
            approvers=config.get("approvers", []),
            timeout_seconds=config.get("timeout_seconds", 3600),
            on_timeout=config.get("on_timeout", "reject"),
            require_reason=config.get("require_reason", False),
        )


# Convenience functions
def load_policies_from_file(file_path: Union[str, Path]) -> List[Policy]:
    """
    Load policies from a configuration file.

    Args:
        file_path: Path to JSON or YAML file

    Returns:
        List of Policy instances

    Example:
        ```python
        from governor import govern
        from governor.config import load_policies_from_file

        policies = load_policies_from_file("policies.yaml")

        @govern(policies=policies)
        async def my_function():
            pass
        ```
    """
    return PolicyLoader.load_from_file(file_path)


def load_policies_from_dict(config: Dict[str, Any]) -> List[Policy]:
    """
    Load policies from a dictionary.

    Args:
        config: Policy configuration dictionary

    Returns:
        List of Policy instances

    Example:
        ```python
        from governor import govern
        from governor.config import load_policies_from_dict

        config = {
            "policies": [
                {"type": "audit", "compliance_tags": ["SOC2"]},
                {"type": "rate_limit", "max_calls": 100}
            ]
        }

        policies = load_policies_from_dict(config)

        @govern(policies=policies)
        async def my_function():
            pass
        ```
    """
    return PolicyLoader.load_from_dict(config)
