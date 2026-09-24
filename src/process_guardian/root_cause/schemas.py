"""Schemas for Root Cause Evidence analysis and contributor reports."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ContributorItem(BaseModel):
    """Ranked likely contributor with percentage attribution and supporting evidence (ROOT-01, ROOT-02)."""
    signal_name: str = Field(..., description="Signal identifier, e.g., barrel_temp_z3")
    display_name: str = Field(..., description="Human-readable parameter name")
    category: str = Field(..., description="Process subsystem category: Thermal, Pressure, Timing, Material")
    contribution_pct: float = Field(..., ge=0.0, le=100.0, description="Attributed percentage contribution")
    evidence: str = Field(..., description="Empirical evidence statement formulated in honest language")
    z_score: float = Field(..., description="Standardized deviation from baseline")
    slope_per_cycle: float = Field(..., description="Estimated rate of change per cycle")


class SubsystemAttribution(BaseModel):
    """Aggregate percentage breakdown by physical process subsystem (ROOT-01)."""
    thermal_pct: float = Field(..., ge=0.0, le=100.0, description="Barrel heating & nozzle dynamics")
    pressure_pct: float = Field(..., ge=0.0, le=100.0, description="Injection, packing, cavity peak pressure")
    timing_pct: float = Field(..., ge=0.0, le=100.0, description="Cycle, cooling, and injection timing")
    material_pct: float = Field(..., ge=0.0, le=100.0, description="Resin moisture and ambient environment")


class RootCauseReport(BaseModel):
    """Comprehensive root-cause evidence report with strictly honest epistemics (ROOT-01..03)."""
    cycle_index: int = Field(..., description="Cycle index analyzed")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    
    primary_contributor: str = Field(..., description="Top ranked likely contributor parameter")
    subsystem_breakdown: SubsystemAttribution = Field(..., description="Category breakdown summing to 100%")
    contributors: List[ContributorItem] = Field(..., description="Ranked list of contributors summing strictly to 100.0%")
    
    honest_language_compliant: bool = Field(
        ...,
        description="True if all output statements conform to honest probabilistic language standards"
    )
    summary_statement: str = Field(..., description="Synthesized honest summary of observed evidence")
