"""Storage schemas, models, and Unified Event Object for Process Guardian."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GuardianEvent(BaseModel):
    """
    Unified Event Object Schema (STOR-02).
    Standardized payload for all operational, drift, risk, intervention, and recovery events.
    """
    event_id: str = Field(..., description="Unique event identifier (e.g., 'evt_00421')")
    machine_id: str = Field(..., description="Machine identifier (e.g., 'IMM_07')")
    mold_id: str = Field(..., description="Active mold identifier (e.g., 'MOLD_18')")
    part_id: str = Field(..., description="Part number/code (e.g., 'AUTO_HOUSING_A')")
    recipe_id: str = Field(..., description="Recipe code (e.g., 'RCP_12')")
    cycle_id: int = Field(..., description="Cycle index at which event occurred")
    timestamp: str = Field(..., description="ISO 8601 timestamp string")
    event_type: str = Field(..., description="Event classification (e.g., 'PROCESS_DRIFT', 'QUALITY_RISK_HIGH', 'INTERVENTION_APPLIED', 'RECOVERY_VERIFIED')")
    severity: str = Field(..., description="Severity level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL', 'INFO'")
    signals: List[str] = Field(default_factory=list, description="List of contributing signal names")
    quality_risk: float = Field(0.0, description="Calibrated defect risk probability (0.0 to 1.0)")
    confidence: float = Field(1.0, description="Epistemic confidence score (0.0 to 1.0)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary event metadata and telemetry snapshots")


# --- Topology Entities ---

class MachineRecord(BaseModel):
    id: str
    machine_name: str
    model: str
    tonnage: float
    plant_location: str
    status: str = "ACTIVE"
    created_at: str = Field(default_factory=_utc_now_iso)


class MoldRecord(BaseModel):
    id: str
    mold_code: str
    cavities: int = 1
    material_compatibility: str = "PA66-GF30"
    clamp_tonnage_required: float = 120.0
    created_at: str = Field(default_factory=_utc_now_iso)


class PartRecord(BaseModel):
    id: str
    part_number: str
    name: str
    description: str
    target_weight_g: float = 142.5
    created_at: str = Field(default_factory=_utc_now_iso)


class RecipeRecord(BaseModel):
    id: str
    recipe_code: str
    part_id: str
    mold_id: str
    machine_id: str
    target_temperature: float = 285.0
    target_pressure: float = 120.0
    target_cycle_time: float = 30.0
    parameters_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class MaterialRecord(BaseModel):
    id: str
    material_code: str
    name: str
    polymer_type: str = "PA66"
    target_moisture_pct: float = 0.12
    max_moisture_pct: float = 0.20
    density_g_cm3: float = 1.35
    created_at: str = Field(default_factory=_utc_now_iso)


# --- Cycle Telemetry Entity ---

class StoredCycleRecord(BaseModel):
    id: Optional[int] = None
    cycle_index: int
    machine_id: str
    mold_id: str
    part_id: str
    recipe_id: str
    timestamp: str
    barrel_temp_z1: float
    barrel_temp_z2: float
    barrel_temp_z3: float
    barrel_temp_z4: float
    nozzle_temp: float
    mold_temp: float
    injection_pressure: float
    holding_pressure: float
    back_pressure: float
    injection_speed: float
    screw_rpm: float
    cushion_position: float
    dosing_time: float
    injection_time: float
    cooling_time: float
    cycle_time: float
    ambient_temp: float
    ambient_humidity: float
    material_moisture_pct: float
    part_weight_g: float
    defect_flag: bool = False
    defect_type: Optional[str] = None
    raw_json: Dict[str, Any] = Field(default_factory=dict)


# --- Analytical & Decision Entities ---

class StoredFingerprintRecord(BaseModel):
    id: str
    context_key: str
    machine_id: str
    mold_id: str
    part_id: str
    recipe_id: str
    baseline_version: str
    sample_count: int
    stats_json: Dict[str, Any]
    envelope_json: Dict[str, Any]
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredQualityContractRecord(BaseModel):
    id: str
    contract_code: str
    part_id: str
    recipe_id: str
    target_weight_g: float
    weight_tolerance_g: float
    max_sink_mark_mm: float
    allow_flash: bool
    target_cycle_time_s: float
    cycle_time_tolerance_s: float
    specs_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredDriftEventRecord(BaseModel):
    id: Optional[int] = None
    event_id: str
    cycle_index: int
    machine_id: str
    timestamp: str
    drift: bool
    severity: float
    lead_cycles: int
    signals_json: List[str]
    details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredQualityPredictionRecord(BaseModel):
    id: Optional[int] = None
    event_id: str
    cycle_index: int
    machine_id: str
    risk_probability: float
    confidence: float
    risk_state: str
    operator_mode: str
    root_cause_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredInterventionCandidateRecord(BaseModel):
    id: Optional[int] = None
    recommendation_id: str
    action_id: str
    name: str
    target_signal: Optional[str] = None
    delta_value: float = 0.0
    unit: str = ""
    cost: float = 0.0
    disruption: float = 0.0
    estimated_risk: float = 0.0
    boundary_checked: bool = True
    is_selected: bool = False
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class StoredRecommendationRecord(BaseModel):
    id: Optional[int] = None
    recommendation_id: str
    event_id: str
    cycle_index: int
    machine_id: str
    action_id: str
    action_text: str
    why_text: str
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    expected_effect: str
    confidence: float
    operating_limit: str
    recovery_check: str
    is_abstain: bool = False
    abstain_reason: Optional[str] = None
    operator_mode: str = "DIRECT_RECOMMENDATION"
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredInterventionApplicationRecord(BaseModel):
    id: Optional[int] = None
    cycle_index: int
    machine_id: str
    action_id: str
    applied_by: str = "DEMO_OPERATOR"
    timestamp: str
    pre_intervention_risk: float
    target_delta: float
    status: str = "APPLIED"
    details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredRecoveryEventRecord(BaseModel):
    id: Optional[int] = None
    cycle_index: int
    machine_id: str
    intervention_id: Optional[str] = None
    recovery_status: str
    release_decision: str
    risk_before: float
    risk_after: float
    stability_before: float
    stability_after: float
    consecutive_stable_cycles: int
    summary_message: str
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredContainmentWindowRecord(BaseModel):
    id: Optional[int] = None
    machine_id: str
    last_known_good_cycle: Optional[int] = None
    suspect_start_cycle: Optional[int] = None
    suspect_end_cycle: Optional[int] = None
    suspect_cycle_count: int = 0
    intervention_cycle: Optional[int] = None
    recovery_cycle: Optional[int] = None
    release_cycle: Optional[int] = None
    quarantine_cycles_json: List[int] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredCheckpointRecord(BaseModel):
    id: Optional[int] = None
    checkpoint_name: str
    cycle_index: int
    machine_id: str
    timestamp: str
    state: str
    data_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)


class StoredAuditLogRecord(BaseModel):
    id: Optional[int] = None
    event_id: str
    cycle_index: int
    machine_id: str
    timestamp: str
    event_type: str
    severity: str
    description: str
    details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utc_now_iso)
