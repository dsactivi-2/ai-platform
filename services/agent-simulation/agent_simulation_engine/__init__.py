"""
Agent Simulation Engine SDK

Official Python SDK for the Lyzr Agent Simulation Engine (A-Sim) platform.

Usage:
    from agent_simulation_engine import ASIMEngine

    engine = ASIMEngine(api_key="studio-api-key")

    # Create an environment
    env = engine.environments.create(agent_id="...", name="My Tests")

    # Generate personas and scenarios
    personas = engine.personas.generate(env.environment_id)
    scenarios = engine.scenarios.generate(env.environment_id)

    # Generate simulations
    job = engine.simulations.generate(env.environment_id)

    # Check job status
    status = engine.jobs.get_status(env.environment_id, job.job_id)
"""

from .client import ASIMEngine
from .exceptions import (
    ASIMError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ConnectionError,
)
from .models import (
    # Request Models
    EnvironmentCreateRequest,
    PersonaRequest,
    ScenarioRequest,
    SimulationRequest,
    GenerateSimulationsRequest,
    GenerateEvaluationsRequest,
    AgentHardeningRequest,
    ContinueEvaluationRunRequest,
    # Response Models
    Environment,
    EnvironmentCreateResponse,
    Persona,
    PersonasResponse,
    Scenario,
    ScenariosResponse,
    Simulation,
    SimulationsResponse,
    SimulationGenerateResponse,
    Evaluation,
    EvaluationsResponse,
    EvaluationGenerateResponse,
    EvaluationRun,
    EvaluationRound,
    EvaluationRunSummary,
    EvaluationRunsResponse,
    EvaluationRoundResponse,
    JobStatus,
    JobSummary,
    TaskInfo,
    HardeningResponse,
    AgentConfig,
    ContinueRunResponse,
    DashboardStats,
)

__version__ = "0.1.0"
__all__ = [
    # Engine
    "ASIMEngine",
    # Exceptions
    "ASIMError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ConnectionError",
    # Request Models
    "EnvironmentCreateRequest",
    "PersonaRequest",
    "ScenarioRequest",
    "SimulationRequest",
    "GenerateSimulationsRequest",
    "GenerateEvaluationsRequest",
    "AgentHardeningRequest",
    "ContinueEvaluationRunRequest",
    # Response Models
    "Environment",
    "EnvironmentCreateResponse",
    "Persona",
    "PersonasResponse",
    "Scenario",
    "ScenariosResponse",
    "Simulation",
    "SimulationsResponse",
    "SimulationGenerateResponse",
    "Evaluation",
    "EvaluationsResponse",
    "EvaluationGenerateResponse",
    "EvaluationRun",
    "EvaluationRound",
    "EvaluationRunSummary",
    "EvaluationRunsResponse",
    "EvaluationRoundResponse",
    "JobStatus",
    "JobSummary",
    "TaskInfo",
    "HardeningResponse",
    "AgentConfig",
    "ContinueRunResponse",
    "DashboardStats",
]
