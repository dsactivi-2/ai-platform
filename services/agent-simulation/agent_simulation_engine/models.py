"""
Pydantic models for the Agent Simulation Engine SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==================== Request Models ====================

class EnvironmentCreateRequest(BaseModel):
    """Request model for creating an environment."""
    agent_id: str
    name: Optional[str] = None


class PersonaRequest(BaseModel):
    """Request model for creating a persona."""
    name: str
    description: str


class AddPersonasRequest(BaseModel):
    """Request model for adding multiple personas."""
    personas: List[PersonaRequest]


class ScenarioRequest(BaseModel):
    """Request model for creating a scenario."""
    name: str
    description: str


class AddScenariosRequest(BaseModel):
    """Request model for adding multiple scenarios."""
    scenarios: List[ScenarioRequest]


class SimulationRequest(BaseModel):
    """Request model for creating a simulation."""
    name: str
    user_input: str
    expected_output: str
    ground_truth: Optional[str] = None
    persona_id: Optional[str] = None
    scenario_id: Optional[str] = None
    environment_id: Optional[str] = None


class GenerateSimulationsRequest(BaseModel):
    """Request model for generating simulations."""
    scenario_ids: Optional[List[str]] = None
    persona_ids: Optional[List[str]] = None


class GenerateEvaluationsRequest(BaseModel):
    """Request model for generating evaluations."""
    evaluation_run_name: str
    simulation_ids: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    agent_config: Optional[Dict[str, Any]] = None


class AgentHardeningRequest(BaseModel):
    """Request model for agent hardening."""
    round_number: int
    evaluation_ids: Optional[List[str]] = None


class ContinueEvaluationRunRequest(BaseModel):
    """Request model for continuing an evaluation run."""
    round_number: int
    agent_config: Dict[str, Any]
    simulation_ids: Optional[List[str]] = None


# ==================== Response Models ====================

class Environment(BaseModel):
    """Environment response model."""
    id: str
    agent_id: str
    name: str
    user_id: Optional[str] = None
    status: Optional[str] = None
    scenarios_count: Optional[int] = None
    personas_count: Optional[int] = None
    simulations_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class EnvironmentCreateResponse(BaseModel):
    """Response model for environment creation."""
    environment_id: str
    agent_id: str
    name: str
    created_at: Optional[datetime] = None


class Persona(BaseModel):
    """Persona response model."""
    id: str
    environment_id: str
    name: str
    description: str
    created_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class PersonasResponse(BaseModel):
    """Response model for persona list."""
    personas: List[Persona]
    count: int


class Scenario(BaseModel):
    """Scenario response model."""
    id: str
    environment_id: str
    name: str
    description: str
    created_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class ScenariosResponse(BaseModel):
    """Response model for scenario list."""
    scenarios: List[Scenario]
    count: int


class Simulation(BaseModel):
    """Simulation response model."""
    id: str
    environment_id: str
    name: str
    user_input: str
    expected_output: str
    ground_truth: Optional[str] = None
    persona_id: Optional[str] = None
    scenario_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class SimulationsResponse(BaseModel):
    """Response model for simulation list."""
    simulations: List[Simulation]
    count: int


class TaskInfo(BaseModel):
    """Task information within a job."""
    task_id: Optional[str] = None
    scenario_name: Optional[str] = None
    persona_name: Optional[str] = None
    scenario_id: Optional[str] = None
    persona_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    simulation_id: Optional[str] = None
    simulation_name: Optional[str] = None
    state: str = "PENDING"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evaluation_id: Optional[str] = None

    class Config:
        extra = "allow"


class JobSummary(BaseModel):
    """Summary of job progress."""
    total: int
    pending: int
    running: int
    completed: int
    failed: int


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    environment_id: str
    progress: str
    summary: JobSummary
    tasks: List[TaskInfo]
    created_at: Optional[datetime] = None
    job_type: Optional[str] = None

    class Config:
        extra = "allow"


class GenerateJobResponse(BaseModel):
    """Response model for job generation (simulations/evaluations)."""
    message: str
    job_id: str
    environment_id: str
    total_tasks: int

    class Config:
        extra = "allow"


class SimulationGenerateResponse(GenerateJobResponse):
    """Response model for simulation generation."""
    personas_count: Optional[int] = None
    scenarios_count: Optional[int] = None


class EvaluationGenerateResponse(GenerateJobResponse):
    """Response model for evaluation generation."""
    evaluation_run_id: str
    agent_id: Optional[str] = None
    simulations_count: Optional[int] = None
    current_round: Optional[int] = None


class EvaluationScores(BaseModel):
    """Evaluation scores."""
    task_completion: Optional[float] = None
    hallucinations: Optional[float] = None
    answer_relevancy: Optional[float] = None

    class Config:
        extra = "allow"


class Evaluation(BaseModel):
    """Evaluation response model."""
    id: str
    environment_id: str
    simulation_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_input: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    agent_response: Optional[str] = None
    judgment: Optional[str] = None  # PASS or FAIL
    scores: Optional[Dict[str, float]] = None
    issues: Optional[List[str]] = None
    fixes: Optional[List[str]] = None
    feedback: Optional[str] = None
    reasoning: Optional[str] = None
    created_at: Optional[datetime] = None
    evaluation_time_ms: Optional[int] = None

    class Config:
        extra = "allow"


class EvaluationsResponse(BaseModel):
    """Response model for evaluation list."""
    evaluations: List[Evaluation]
    count: int


class SimulationResult(BaseModel):
    """Simulation result within an evaluation round."""
    simulation_id: str
    simulation_name: Optional[str] = None
    persona_name: Optional[str] = None
    scenario_name: Optional[str] = None
    judgment: Optional[str] = None
    scores: Optional[Dict[str, float]] = None
    issues: Optional[List[str]] = None
    fixes: Optional[List[str]] = None

    class Config:
        extra = "allow"


class EvaluationRound(BaseModel):
    """Evaluation round within an evaluation run."""
    round_number: int
    job_id: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    previous_agent_config: Optional[Dict[str, Any]] = None
    simulation_results: List[SimulationResult] = []
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class EvaluationRun(BaseModel):
    """Evaluation run response model."""
    id: str
    environment_id: str
    evaluation_run_name: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    metrics: Optional[List[str]] = None
    simulation_ids: Optional[List[str]] = None
    current_round: int = 1
    status: Optional[str] = None
    rounds: List[EvaluationRound] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class EvaluationRunSummary(BaseModel):
    """Summary of an evaluation run."""
    evaluation_run_id: str
    evaluation_run_name: Optional[str] = None
    environment_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    current_round: int
    total_rounds: int
    status: Optional[str] = None
    current_round_pass_count: Optional[int] = None
    current_round_fail_count: Optional[int] = None
    current_round_total: Optional[int] = None
    current_round_completed: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class EvaluationRunsResponse(BaseModel):
    """Response model for evaluation runs list."""
    evaluation_runs: List[EvaluationRunSummary]
    count: int


class RoundStatistics(BaseModel):
    """Statistics for an evaluation round."""
    total_simulations: int
    pass_count: int
    fail_count: int
    pass_rate: float
    is_completed: bool


class RoundMetadata(BaseModel):
    """Metadata for an evaluation round."""
    evaluation_run_id: str
    evaluation_run_name: Optional[str] = None
    environment_id: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class EvaluationRoundResponse(BaseModel):
    """Response model for getting a specific round."""
    round: EvaluationRound
    statistics: RoundStatistics
    metadata: RoundMetadata


class AgentConfig(BaseModel):
    """Agent configuration."""
    agent_role: Optional[str] = None
    agent_instructions: Optional[str] = None
    agent_goal: Optional[str] = None
    name: Optional[str] = None

    class Config:
        extra = "allow"


class HardeningResponse(BaseModel):
    """Response model for agent hardening."""
    message: str
    original_config: AgentConfig
    improved_config: AgentConfig


class ContinueRunResponse(BaseModel):
    """Response model for continuing an evaluation run."""
    message: str
    evaluation_run_id: str
    round_number: int
    job_id: str
    simulation_count: int


class SyncRoundResponse(BaseModel):
    """Response model for syncing round results."""
    message: str
    round: EvaluationRound
    results_count: int


# ==================== Dashboard Models ====================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_environments: int
    total_simulations: int
    total_evaluations: int
    average_pass_rate: float


class RecentEnvironment(BaseModel):
    """Recent environment summary."""
    id: str
    name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    personas_count: int
    scenarios_count: int
    simulations_count: int
    created_at: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        extra = "allow"


class RecentEnvironmentsResponse(BaseModel):
    """Response model for recent environments."""
    environments: List[RecentEnvironment]


class RecentEvaluation(BaseModel):
    """Recent evaluation summary."""
    id: str
    environment_id: str
    environment_name: Optional[str] = None
    simulation_id: Optional[str] = None
    simulation_name: Optional[str] = None
    persona_name: Optional[str] = None
    scenario_name: Optional[str] = None
    agent_id: Optional[str] = None
    judgment: Optional[str] = None
    scores: Optional[Dict[str, float]] = None
    feedback: Optional[str] = None
    agent_response: Optional[str] = None
    created_at: Optional[datetime] = None
    evaluation_time_ms: Optional[int] = None

    class Config:
        extra = "allow"


class RecentEvaluationsResponse(BaseModel):
    """Response model for recent evaluations."""
    evaluations: List[RecentEvaluation]
    count: int


class JobProgress(BaseModel):
    """Job progress information."""
    completed: int
    total: int
    percentage: float


class RecentJob(BaseModel):
    """Recent job summary."""
    id: str
    job_type: str
    environment_id: str
    environment_name: Optional[str] = None
    progress: JobProgress
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class RecentJobsResponse(BaseModel):
    """Response model for recent jobs."""
    jobs: List[RecentJob]


class ActiveEvaluationRun(BaseModel):
    """Active evaluation run summary."""
    id: str
    evaluation_run_name: Optional[str] = None
    environment_id: str
    environment_name: Optional[str] = None
    current_round: int
    total_rounds: int
    progress: JobProgress
    pass_count: int
    fail_count: int
    status: str
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = "allow"


class ActiveEvaluationRunsResponse(BaseModel):
    """Response model for active evaluation runs."""
    evaluation_runs: List[ActiveEvaluationRun]


class CancelJobResponse(BaseModel):
    """Response model for job cancellation."""
    message: str
    job_id: str
    summary: Dict[str, int]


class DeleteResponse(BaseModel):
    """Generic delete response."""
    message: str

    class Config:
        extra = "allow"
