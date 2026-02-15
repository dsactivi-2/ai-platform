"""
governor: A clean, minimal governance library for agentic systems.

Provides state management, policy enforcement, human-in-the-loop approval,
and comprehensive event tracking for autonomous agents.
"""

from governor.decorator import govern
from governor.core.context import ExecutionContext, ExecutionStatus
from governor.core.state import StateSnapshot
from governor.policies.base import Policy, PolicyResult
from governor.policies.validation import ValidationPolicy
from governor.policies.authorization import AuthorizationPolicy
from governor.policies.rate_limit import RateLimitPolicy
from governor.policies.audit import AuditPolicy
from governor.policies.approval import ApprovalPolicy
from governor.policies.sequential_approval import SequentialApprovalPolicy, ApprovalStage
from governor.events.base import Event, EventType
from governor.events.emitter import EventEmitter
from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage
from governor.replay.engine import ReplayEngine
from governor.compliance.reporter import ComplianceReporter, ComplianceReport
from governor.compliance.gdpr import GDPRCompliance
from governor.compliance.soc2 import SOC2Compliance
from governor.config import load_policies_from_file, load_policies_from_dict

__version__ = "0.2.0"

__all__ = [
    # Main decorator
    "govern",
    # Core
    "ExecutionContext",
    "ExecutionStatus",
    "StateSnapshot",
    # Policies
    "Policy",
    "PolicyResult",
    "ValidationPolicy",
    "AuthorizationPolicy",
    "RateLimitPolicy",
    "AuditPolicy",
    "ApprovalPolicy",
    "SequentialApprovalPolicy",
    "ApprovalStage",
    # Events
    "Event",
    "EventType",
    "EventEmitter",
    # Storage
    "StorageBackend",
    "InMemoryStorage",
    # Replay
    "ReplayEngine",
    # Compliance
    "ComplianceReporter",
    "ComplianceReport",
    "GDPRCompliance",
    "SOC2Compliance",
    # Config
    "load_policies_from_file",
    "load_policies_from_dict",
]
