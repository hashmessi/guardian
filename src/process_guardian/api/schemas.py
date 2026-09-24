"""Pydantic REST API request and response schemas for Process Guardian."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from process_guardian.state_machine.schemas import ProcessState
from process_guardian.containment.schemas import DispositionType


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==========================================
# 1. Ingestion Schemas (API-01)
# ==========================================

class CycleIngestRequest(BaseModel):
    """Payload for ingesting a single cycle of injection-molding telemetry."""
    cycle_index: Optional[int] = Field(None, description="Optional explicit cycle index. If omitted, sequential increment is used.")
    machine_id: str = Field("IMM-01", description="Machine identifier")
    mold_id: str = Field("MOLD-18", description="Active mold identifier")
    part_id: str = Field("AUTO-HOUSING-A", description="Part identifier")
    recipe_id: str = Field("RCP-12", description="Recipe identifier")
    timestamp: Optional[str] = Field(default_factory=_utc_now_iso, description="ISO timestamp")
    telemetry: Dict[str, Any] = Field(..., description="Key-value dictionary of raw sensor readings")


class BatchCycleIngestRequest(BaseModel):
    """Payload for batch telemetry ingestion."""
    cycles: List[Dict[str, Any]] = Field(..., description="List of raw or normalized cycle telemetry dictionaries")


class CycleIngestResponse(BaseModel):
    """Response returned after processing a cycle through the closed decision loop."""
    cycle_index: int
    machine_id: str
    state: str
    drift_detected: bool
    drift_severity: float
    quality_risk_pct: float
    process_stability_pct: float
    disposition: str
    is_suspect: bool
    recommendation_available: bool
    transitions: List[Dict[str, Any]] = Field(default_factory=list)


class BatchCycleIngestResponse(BaseModel):
    """Response returned after batch cycle ingestion."""
    total_processed: int
    start_cycle: int
    end_cycle: int
    current_state: str
    suspect_cycle_count: int


class EventIngestRequest(BaseModel):
    """Request to inject or log an operational event (e.g. drift injection, material lot change)."""
    event_type: str = Field(..., description="e.g., 'THERMAL_DRIFT_INJECTED', 'MATERIAL_LOT_CHANGE', 'OPERATOR_NOTE'")
    cycle_index: Optional[int] = Field(None, description="Target or current cycle index")
    machine_id: str = Field("IMM-01", description="Machine identifier")
    severity: str = Field("HIGH", description="'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'INFO'")
    signals: List[str] = Field(default_factory=list, description="Associated telemetry signals")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event parameters or injection metadata")


class EventIngestResponse(BaseModel):
    """Response after recording an event."""
    event_id: str
    status: str
    cycle_index: int
    recorded_at: str


class CheckpointCreateRequest(BaseModel):
    """Request to snapshot current orchestrator and machine state."""
    checkpoint_name: str = Field(..., description="Descriptive checkpoint label (e.g., 'baseline_pre_drift')")
    machine_id: str = Field("IMM-01", description="Machine identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional extra context")


class CheckpointResponse(BaseModel):
    """Response with checkpoint confirmation."""
    checkpoint_name: str
    machine_id: str
    cycle_index: int
    state: str
    timestamp: str


# ==========================================
# 2. Process State Schemas (API-02)
# ==========================================

class ProcessCurrentResponse(BaseModel):
    """Real-time process status, stability score, and current telemetry bars (Screen 1 support)."""
    machine_id: str
    mold_id: str
    part_id: str
    recipe_id: str
    current_cycle: int
    state: str
    process_stability_pct: float
    quality_risk_pct: float
    drift_status: str
    signals: Dict[str, float]
    timestamp: str


class ProcessFingerprintResponse(BaseModel):
    """Baseline distributions and normal operating envelope for active context."""
    context_key: str
    machine_id: str
    mold_id: str
    part_id: str
    recipe_id: str
    sample_count: int
    signal_means: Dict[str, float]
    signal_stds: Dict[str, float]
    signal_envelopes: Dict[str, Dict[str, float]]


class ProcessDriftResponse(BaseModel):
    """Drift Sentinel multi-detector status and lead-cycle analysis."""
    machine_id: str
    current_cycle: int
    drift: bool
    severity: float
    lead_cycles: int
    contributing_signals: List[str]
    detectors: Dict[str, Any]


# ==========================================
# 3. Quality Schemas (API-03)
# ==========================================

class RootCauseContributorItem(BaseModel):
    signal_name: str
    percentage: float
    subsystem: str
    direction: str
    evidence_text: str


class QualityRiskResponse(BaseModel):
    """Calibrated quality risk probability, confidence, and ranked root cause contributors."""
    machine_id: str
    cycle_index: int
    risk_probability: float
    risk_percentage: float
    confidence: float
    risk_state: str
    operator_mode: str
    root_cause_isolated: bool
    contributors: List[RootCauseContributorItem] = Field(default_factory=list)


class QualityContractResponse(BaseModel):
    """Active Quality Contract specifications and dimensional limits."""
    contract_code: str
    part_id: str
    recipe_id: str
    target_weight_g: float
    weight_tolerance_g: float
    weight_min_g: float
    weight_max_g: float
    max_sink_mark_mm: float
    allow_flash: bool
    target_cycle_time_s: float
    cycle_time_tolerance_s: float
    specifications: Dict[str, Any]


# ==========================================
# 4. Intervention Schemas (API-04)
# ==========================================

class CandidateSimulationItem(BaseModel):
    action_id: str
    name: str
    target_signal: Optional[str]
    delta_value: float
    unit: str
    cost: float
    disruption: float
    predicted_risk: float
    is_feasible: bool
    is_selected: bool


class InterventionSimulateRequest(BaseModel):
    """Request to run what-if surrogate simulation for candidate corrective actions."""
    machine_id: str = Field("IMM-01", description="Machine identifier")
    custom_candidates: Optional[List[Dict[str, Any]]] = Field(None, description="Optional custom candidate actions")


class InterventionSimulateResponse(BaseModel):
    """Outcome of surrogate response surface optimization."""
    machine_id: str
    cycle_index: int
    pre_intervention_risk: float
    candidates: List[CandidateSimulationItem]
    recommended_action_id: str


class RecommendationResponse(BaseModel):
    """Standardized 7-field recommendation contract response."""
    recommendation_id: str
    machine_id: str
    cycle_index: int
    action: str
    why: str
    evidence: Union[Dict[str, Any], str]
    expected_effect: str
    confidence: float
    operating_limit: str
    recovery_check: str
    is_abstain: bool
    abstain_reason: Optional[str] = None
    operator_mode: str
    candidate_comparison: List[CandidateSimulationItem] = Field(default_factory=list)


class InterventionApplyRequest(BaseModel):
    """Request to enact an intervention in demo / operator-authorized mode."""
    machine_id: str = Field("IMM-01", description="Machine identifier")
    action_id: Optional[str] = Field(None, description="Action ID to apply (e.g., 'A1'). If omitted, recommended action is used.")
    applied_by: str = Field("DEMO_OPERATOR", description="Operator name or identifier")


class InterventionApplyResponse(BaseModel):
    """Confirmation of enacted intervention and initialization of recovery verification."""
    machine_id: str
    cycle_index: int
    action_id: str
    status: str
    new_state: str
    message: str


class InterventionHistoryItem(BaseModel):
    cycle_index: int
    action_id: str
    applied_by: str
    timestamp: str
    pre_intervention_risk: float
    status: str


class InterventionHistoryResponse(BaseModel):
    machine_id: str
    applications: List[InterventionHistoryItem]


# ==========================================
# 5. Recovery & Containment Schemas (API-05)
# ==========================================

class RecoveryStatusResponse(BaseModel):
    """Post-intervention recovery verifier tracking."""
    machine_id: str
    cycle_index: int
    is_monitoring: bool
    recovery_status: str
    release_decision: str
    parameter_movement_confirmed: bool
    observed_shift: Optional[float] = None
    target_shift: Optional[float] = None
    risk_before: float
    risk_current: float
    stability_before: float
    stability_current: float
    consecutive_stable_cycles: int
    required_stable_cycles: int
    summary_message: str


class ContainmentWindowResponse(BaseModel):
    """Suspect production window boundaries and scrap reduction metrics."""
    machine_id: str
    last_known_good_cycle: Optional[int]
    suspect_start_cycle: Optional[int]
    suspect_end_cycle: Optional[int]
    suspect_cycle_count: int
    intervention_cycle: Optional[int]
    recovery_cycle: Optional[int]
    release_cycle: Optional[int]
    quarantine_cycles: List[int]
    estimated_scrap_saved_cycles: int


class ContainmentReleaseRequest(BaseModel):
    """Authorize release of suspect or post-recovery production."""
    machine_id: str = Field("IMM-01", description="Machine identifier")
    release_notes: str = Field("Verified post-recovery Quality Contract compliance.", description="Release authorization notes")
    operator_id: str = Field("QC_LEAD_01", description="Authorizing operator identifier")


class ContainmentReleaseResponse(BaseModel):
    machine_id: str
    status: str
    released_at: str
    message: str
