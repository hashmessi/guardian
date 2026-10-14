"""Data models for Controlled Counterfactual Replay Canvas (CRPL-01, CRPL-02)."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CounterfactualStreamPoint(BaseModel):
    """Telemetry and operational state at an individual cycle within counterfactual stream."""
    cycle_index: int
    barrel_temp: float
    injection_pressure: float
    defect_risk: float = Field(..., ge=0.0, le=1.0)
    is_defective: bool
    state: str
    action_applied: Optional[str] = None
    is_quarantine: bool = False


class CounterfactualRun(BaseModel):
    """Execution output of an individual simulation replay mode."""
    mode: str = Field(..., description="'GUARDIAN_OFF' or 'GUARDIAN_ON'")
    name: str
    description: str
    total_cycles: int
    suspect_cycles: int
    scrap_parts_count: int
    quarantine_parts_count: int
    direct_scrap_cost: float
    quarantine_sorting_cost: float
    total_financial_loss: float
    stream: List[CounterfactualStreamPoint] = Field(default_factory=list)


class CounterfactualComparison(BaseModel):
    """Comparative delta analysis between Status Quo (Guardian OFF) and Dynamic Quality Reaction (Guardian ON)."""
    guardian_off: CounterfactualRun
    guardian_on: CounterfactualRun
    
    # Delta KPIs
    suspect_lot_reduction_pct: float = Field(..., description="Percentage reduction in suspect quarantined cycles")
    scrap_reduction_pct: float = Field(..., description="Percentage reduction in defective scrap parts")
    net_avoided_loss: float = Field(..., description="Net avoided financial loss in INR (Guardian OFF loss - Guardian ON loss)")
    timeline_divergence_cycle: int = Field(default=85, description="Cycle index where intervention causes trajectory divergence")
    
    epistemic_level: str = "LEVEL_4_CONTROLLED_COUNTERFACTUAL"
    epistemic_disclaimer: str = (
        "Level 4 Epistemic Model: Modeled deterministic counterfactual simulation running identical "
        "disturbance seeds. Demonstrates operational decision divergence between conventional wide-limit SPC "
        "and Process Guardian dynamic intervention."
    )
