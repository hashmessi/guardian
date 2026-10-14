"""Data contracts and schemas for the Scenario Engine and Operational Validation."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

from process_guardian.counterfactual.models import CounterfactualComparison


class DisturbanceSpec(BaseModel):
    """Specification of an injected disturbance or process anomaly."""
    signal: str = Field(description="Target telemetry signal name (e.g. barrel_temp_z3, injection_pressure)")
    pattern: str = Field(description="Disturbance shape: linear_drift, step_shift, moisture_surge, noise_burst, persistent_drift")
    start_cycle: int = Field(ge=1, description="Cycle at which the disturbance begins")
    duration: Optional[int] = Field(default=None, description="Optional cycle duration, None means indefinite")
    severity: float = Field(default=1.0, ge=0.0, description="Severity scaling multiplier")
    rate: Optional[float] = Field(default=None, description="Drift slope per cycle (e.g. +0.25 C/cycle or -0.3 bar/cycle)")
    step_value: Optional[float] = Field(default=None, description="Discrete step magnitude for step shifts or biases")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional disturbance parameters")


class OperationalOverrideSpec(BaseModel):
    """Specification for shop-floor operational conditions and checkpoints."""
    initial_moisture_pct: Optional[float] = Field(
        default=None,
        description="Material hopper moisture level for resin gate evaluation"
    )
    initial_spray_overdue_cycles: Optional[int] = Field(
        default=None,
        description="Simulated cycles since last mold spray for maintenance checkpoint"
    )
    unseen_failure_pattern: bool = Field(
        default=False,
        description="Whether this scenario introduces out-of-distribution patterns triggering ABSTAIN"
    )
    human_channel_event_cycle: Optional[int] = Field(
        default=None,
        description="Cycle at which a human-channel operator note arrives (P1, scope_plan.md Sec.3)"
    )
    human_channel_event_text: Optional[str] = Field(
        default=None,
        description="Operator note text, parsed via llm/human_channel.py at replay time -- the same parser a live operator's text goes through"
    )
    intervention_ineffective: bool = Field(
        default=False,
        description="Whether the applied corrective action fails to reverse the process shift"
    )


class NarrativeMilestone(BaseModel):
    """Production replay lifecycle phase shown to the industrial evaluator."""
    phase: str = Field(description="Phase key: HEALTHY, DRIFT, INTERVENTION, RECOVERY, QC, RELEASE")
    label: str = Field(description="Human-readable title (e.g. 'Stable Baseline')")
    cycle_range: str = Field(description="Cycle range string (e.g. '1–300')")
    description: str = Field(description="Operational narrative explaining machine behavior")


class ExpectedOutcome(BaseModel):
    """Formal expected behavior for operational validation scorecard."""
    drift_expected: bool = Field(default=True)
    dominant_signal: Optional[str] = Field(default=None)
    action_class: Optional[str] = Field(
        default=None,
        description="temperature_adjustment, pressure_adjustment, material_checkpoint, operational_checkpoint, monitor, abstain"
    )
    recovery_expected: bool = Field(default=True)
    release_decision: str = Field(default="RELEASE_PERMITTED")  # RELEASE_PERMITTED, GATED_QC_REQUIRED, HOLD_QUARANTINE, MONITOR_ONLY
    allow_intervention: bool = Field(default=True)
    safety_invariants: List[str] = Field(
        default_factory=lambda: [
            "SAFE-01: Zero PLC write-back hooks",
            "SAFE-02: Operating envelope compliance",
            "SAFE-04: Modeled prototype evidence disclosure",
        ]
    )


class ScenarioDefinition(BaseModel):
    """Complete data-driven specification for an operational scenario."""
    scenario_id: str = Field(description="Unique scenario identifier (e.g. SCN-01-THERMAL)")
    name: str = Field(description="Code slug (e.g. thermal_drift)")
    title: str = Field(description="Display title (e.g. Scenario 01 — Thermal Drift)")
    category: str = Field(description="thermal, pressure, material, configuration, operational, compound, robustness, safety")
    is_hero: bool = Field(default=False, description="True for primary demo scenarios shown in main operator UI")
    description: str = Field(description="Problem statement and industrial significance")
    total_cycles: int = Field(default=500, ge=60, description="Total replay cycles")
    seed: int = Field(default=42, description="Deterministic pseudo-random seed")
    disturbances: List[DisturbanceSpec] = Field(default_factory=list)
    operational_overrides: Optional[OperationalOverrideSpec] = None
    expected_outcome: ExpectedOutcome = Field(default_factory=ExpectedOutcome)
    narrative: List[NarrativeMilestone] = Field(default_factory=list)


class ScenarioReplayCycle(BaseModel):
    """Telemetry and decision state for a single cycle in scenario replay."""
    cycle_index: int
    timestamp: str
    state: str
    barrel_temp_z3: float
    injection_pressure: float
    material_moisture: float
    quality_risk: float
    drift_detected: bool
    dominant_signal: Optional[str] = None
    action_applied: Optional[str] = None
    is_quarantine: bool = False
    is_defective: bool = False
    disposition: str = "ACCEPTED"


class PillarEvaluation(BaseModel):
    """Evaluation result for one of the 7 pillars of closed-loop operational validation."""
    passed: bool
    status_label: str
    detail: str
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ScenarioScorecard(BaseModel):
    """Objective industrial scorecard generated from scenario execution."""
    scenario_id: str
    scenario_title: str
    category: str
    total_cycles: int
    overall_passed: bool
    detection: PillarEvaluation
    diagnosis: PillarEvaluation
    intervention: PillarEvaluation
    recovery: PillarEvaluation
    containment: PillarEvaluation
    counterfactual_proof: PillarEvaluation
    summary: str
    disclaimer: str = "CONTROLLED SIMULATION · REPRODUCIBLE MODELLED EVIDENCE"


class ScenarioRunSummary(BaseModel):
    """Consolidated execution output for an operational scenario."""
    scenario: ScenarioDefinition
    scorecard: ScenarioScorecard
    stream: List[ScenarioReplayCycle]
    counterfactual: CounterfactualComparison
    total_cycles: int
    duration_cycles: int
    passed: bool
