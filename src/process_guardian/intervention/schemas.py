"""Schemas and data models for intervention candidates, constraints, optimization, and recommendations."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Categorical intervention candidate action type (INTV-01)."""
    DO_NOTHING = "DO_NOTHING"                     # A0: Continue monitoring
    TEMP_ADJUST = "TEMP_ADJUST"                   # A1: Barrel temperature adjustment
    PRESSURE_ADJUST = "PRESSURE_ADJUST"           # A2: Holding / injection pressure adjustment
    CYCLE_TIME_ADJUST = "CYCLE_TIME_ADJUST"       # A3: Cooling / cycle timing adjustment
    MATERIAL_INSPECT_PURGE = "MATERIAL_INSPECT_PURGE" # A4: Material inspection, drying, purge


class CandidateAction(BaseModel):
    """Structured operational intervention candidate (INTV-01)."""
    action_id: str = Field(..., description="Action identifier: A0, A1, A2, A3, A4")
    action_type: ActionType = Field(..., description="Intervention category")
    name: str = Field(..., description="Human-readable title")
    target_signal: Optional[str] = Field(default=None, description="Primary telemetry variable targeted")
    delta_value: float = Field(default=0.0, description="Proposed adjustment increment")
    unit: str = Field(default="", description="Engineering unit (°C, bar, s, %)")
    cost_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized economic cost C in [0, 1]")
    disruption_weight: float = Field(default=0.0, ge=0.0, le=1.0, description="Normalized operational disruption D in [0, 1]")
    description: str = Field(default="", description="Operational explanation of the candidate action")


class ConstraintBounds(BaseModel):
    """Lower and upper bounds for an operational limit."""
    min_val: float
    max_val: float

    def contains(self, val: float) -> bool:
        return self.min_val <= val <= self.max_val


class MachineSafetyLimits(BaseModel):
    """Physical hardware safety limits for injection molding equipment (INTV-02)."""
    limits: Dict[str, ConstraintBounds] = Field(
        default_factory=lambda: {
            "barrel_temp_z1": ConstraintBounds(min_val=170.0, max_val=260.0),
            "barrel_temp_z2": ConstraintBounds(min_val=180.0, max_val=270.0),
            "barrel_temp_z3": ConstraintBounds(min_val=190.0, max_val=275.0),
            "barrel_temp_z4": ConstraintBounds(min_val=190.0, max_val=275.0),
            "barrel_temp_z5": ConstraintBounds(min_val=190.0, max_val=275.0),
            "nozzle_temp": ConstraintBounds(min_val=190.0, max_val=280.0),
            "injection_pressure": ConstraintBounds(min_val=50.0, max_val=180.0),
            "peak_pressure": ConstraintBounds(min_val=60.0, max_val=190.0),
            "hold_pressure": ConstraintBounds(min_val=30.0, max_val=120.0),
            "cooling_time": ConstraintBounds(min_val=5.0, max_val=45.0),
            "cycle_time": ConstraintBounds(min_val=15.0, max_val=75.0),
            "material_moisture": ConstraintBounds(min_val=0.00, max_val=0.50),
        }
    )


class RecipeLimits(BaseModel):
    """Approved part recipe specification limits (INTV-02)."""
    limits: Dict[str, ConstraintBounds] = Field(
        default_factory=lambda: {
            "barrel_temp_z1": ConstraintBounds(min_val=200.0, max_val=225.0),
            "barrel_temp_z2": ConstraintBounds(min_val=210.0, max_val=235.0),
            "barrel_temp_z3": ConstraintBounds(min_val=220.0, max_val=240.0),
            "barrel_temp_z4": ConstraintBounds(min_val=225.0, max_val=245.0),
            "barrel_temp_z5": ConstraintBounds(min_val=225.0, max_val=245.0),
            "nozzle_temp": ConstraintBounds(min_val=230.0, max_val=250.0),
            "injection_pressure": ConstraintBounds(min_val=95.0, max_val=135.0),
            "peak_pressure": ConstraintBounds(min_val=122.0, max_val=148.0),
            "hold_pressure": ConstraintBounds(min_val=50.0, max_val=80.0),
            "cooling_time": ConstraintBounds(min_val=10.0, max_val=18.0),
            "cycle_time": ConstraintBounds(min_val=24.0, max_val=34.0),
            "material_moisture": ConstraintBounds(min_val=0.005, max_val=0.10),
        }
    )


class StepLimits(BaseModel):
    """Maximum permitted parameter change per single intervention step (INTV-02)."""
    limits: Dict[str, float] = Field(
        default_factory=lambda: {
            "barrel_temp_z1": 3.0,
            "barrel_temp_z2": 3.0,
            "barrel_temp_z3": 3.0,
            "barrel_temp_z4": 3.0,
            "barrel_temp_z5": 3.0,
            "nozzle_temp": 3.0,
            "injection_pressure": 8.0,
            "peak_pressure": 10.0,
            "hold_pressure": 6.0,
            "cooling_time": 2.0,
            "cycle_time": 3.0,
            "material_moisture": 0.05,
        }
    )


class ConstraintCheckResult(BaseModel):
    """Result of multi-boundary safety and envelope validation (INTV-02)."""
    is_feasible: bool = Field(..., description="True if action satisfies all operational and safety constraints")
    safety_ok: bool = Field(..., description="True if within hardware safety boundaries")
    recipe_ok: bool = Field(..., description="True if within approved part recipe tolerances")
    envelope_ok: bool = Field(..., description="True if within fingerprint operating envelope (mu +- 3*sigma)")
    step_ok: bool = Field(..., description="True if within maximum single adjustment step delta")
    direction_ok: bool = Field(..., description="True if adjustment opposes the observed drift")
    proposed_value: Optional[float] = Field(default=None, description="Projected parameter value post-action")
    violations: List[str] = Field(default_factory=list, description="Specific constraint violations detected")


class ActionEvaluation(BaseModel):
    """Simulated outcome and multi-objective scoring for a candidate action (INTV-03..05)."""
    candidate: CandidateAction
    constraint_check: ConstraintCheckResult
    pre_intervention_risk: float
    post_intervention_risk: float
    risk_reduction: float
    cost: float
    disruption: float
    objective_score: float
    rank: int = Field(default=1)
    is_selected: bool = Field(default=False)


class InterventionComparisonTable(BaseModel):
    """Comparison table of all evaluated candidate actions (INTV-05)."""
    cycle_index: int
    baseline_risk: float
    evaluations: List[ActionEvaluation]
    recommended_action_id: Optional[str] = None
    table_summary: str = ""


class InterventionRecommendation(BaseModel):
    """
    Seven-Field Structured Recommendation Contract (RCMD-01, RCMD-02, RCMD-03).
    
    Strictly conforms to the 7 required fields:
    ACTION, WHY, EVIDENCE, EXPECTED EFFECT, CONFIDENCE, OPERATING LIMIT, RECOVERY CHECK.
    """
    # 7-field contract
    action: str = Field(..., description="Exact parameter, direction, and magnitude of adjustment or ABSTAIN")
    why: str = Field(..., description="Root-cause justification linking drift diagnosis to defect risk")
    evidence: str = Field(..., description="Empirical quantitative deviations, z-scores, and trend rates")
    expected_effect: str = Field(..., description="Estimated post-intervention quality risk drop")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Epistemic confidence score in [0.0, 1.0]")
    operating_limit: str = Field(..., description="Verification of safety, recipe, and envelope boundaries")
    recovery_check: str = Field(..., description="Concrete criteria to verify recovery in Phase 5")

    # Metadata & decision status
    operator_mode: str = Field(..., description="Operator guidance mode (NORMAL_MONITORING, REQUEST_QC_SAMPLE, RECOMMEND_ACTION, ABSTAIN_AND_MONITOR)")
    is_abstain: bool = Field(default=False, description="True if system refused automated recommendation")
    abstain_reason: Optional[str] = Field(default=None, description="Detailed justification if system abstained")
    cycle_index: int = Field(..., description="Cycle index evaluated")
    timestamp: str = Field(..., description="Evaluation timestamp")
    candidate_id: Optional[str] = Field(default=None, description="Identifier of selected candidate (e.g. A1)")
