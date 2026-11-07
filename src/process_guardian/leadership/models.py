"""Data contracts and schemas for Process Guardian Leadership Incident Brief."""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


FinalState = Literal["VERIFIED_RECOVERY", "QC_HOLD", "ESCALATION_REQUIRED"]


class StoryStep(BaseModel):
    """One of the 4 steps in the executive visual story."""
    step_num: int = Field(ge=1, le=4)
    title: str
    subtitle: str
    detail: str
    status: str  # "PASSED", "CONTAINED", "ESCALATED", "ACTIVE"
    metrics: Dict[str, Any] = Field(default_factory=dict)


class TriggeredSignal(BaseModel):
    """Telemetry or human-channel signal triggering incident response."""
    name: str
    label: str
    value: Any
    unit: str
    status: str  # "DRIFTING", "NORMAL", "ATTESTED", "HELD"
    deviation: Optional[str] = None


class RootCauseShare(BaseModel):
    """Attribution breakdown of the incident drivers."""
    signal: str
    label: str
    percentage: float


class DecisionEvidence(BaseModel):
    """Technical and operational evidence backing the decision."""
    triggered_signals: List[TriggeredSignal]
    root_cause_shares: List[RootCauseShare]
    risk_score: float
    risk_state: str
    recommended_action: str
    selected_action: str
    quality_disposition: str
    safety_justification: str


class BusinessImpact(BaseModel):
    """Quantified operational and economic consequences of the decision."""
    detection_lead_time_cycles: int
    lead_time_description: str
    suspect_parts_contained: int
    baseline_suspect_parts: int
    suspect_reduction_pct: float
    modeled_scrap_avoided: int
    baseline_scrap_parts: int
    actual_scrap_parts: int
    modeled_cost_avoided_inr: float
    baseline_loss_inr: float
    actual_loss_inr: float
    recovery_time_cycles: int
    production_improvement: str
    disclaimer: str = "Modeled controlled-scenario estimate — not plant-validated savings."
    is_savings_invented: bool = False


class AuditTrailItem(BaseModel):
    """Cryptographically verifiable or sequenced audit log entry."""
    timestamp: str
    cycle: int
    actor: str
    event: str
    hash_digest: str


class DivergencePoint(BaseModel):
    """Trajectory comparison point between status quo and Process Guardian."""
    cycle: int
    status_quo_scrap: int
    guardian_scrap: int
    status_quo_risk: float
    guardian_risk: float


class LeadershipFactPacket(BaseModel):
    """Small, read-only fact packet sent to Gemini for structured briefing."""
    scenario_id: str
    scenario_title: str
    final_state: FinalState
    outcome_theme: str
    dominant_signal: Optional[str]
    triggered_signals: List[str]
    detection_lead_time_cycles: int
    recommendation: str
    operator_action: str
    suspect_parts_contained: int
    modeled_scrap_avoided: int
    modeled_cost_avoided_inr: float
    recovery_time_cycles: int
    next_action_directive: str


class AISummaryOutput(BaseModel):
    """Strict JSON structured schema returned by Gemini 3.8 Flash."""
    headline: str
    executive_summary: str
    decision_rationale: str
    impact_statement: str
    next_action: str


class LeadershipTakeaway(BaseModel):
    """Executive summary rendered on the brief, tagged with source."""
    headline: str
    executive_summary: str
    decision_rationale: str
    impact_statement: str
    next_action: str
    source: Literal["gemini-3.8-flash", "deterministic_template"]
    model_version: str = "gemini-3.8-flash"
    timestamp: str


class LeadershipReportContext(BaseModel):
    """Complete data payload for the Leadership Incident Brief screen."""
    scenario_id: str
    scenario_title: str
    display_title: str
    category: str
    final_state: FinalState
    final_state_label: str
    headline: str
    story_steps: List[StoryStep]
    decision_evidence: DecisionEvidence
    business_impact: BusinessImpact
    leadership_takeaway: LeadershipTakeaway
    next_action: str
    next_action_detail: str
    divergence_points: List[DivergencePoint]
    audit_trail: List[AuditTrailItem]
    epistemic_disclaimer: str = "CONTROLLED SIMULATION · REPRODUCIBLE MODELLED EVIDENCE"

