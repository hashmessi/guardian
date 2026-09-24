"""Pydantic v2 schemas for Drift Sentinel outputs, signal drift details, and metrics."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SignalDriftDetail(BaseModel):
    """Detailed statistical breakdown for a single signal."""
    signal_name: str
    current_value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    ewma_value: float
    ewma_breached: bool
    cusum_pos: float
    cusum_neg: float
    cusum_breached: bool
    slope_per_cycle: float
    is_drifting: bool


class DriftMetrics(BaseModel):
    """Aggregate multi-method statistical diagnostic metrics."""
    ewma_breached: bool
    cusum_breached: bool
    multivariate_distance: float
    multivariate_threshold: float
    multivariate_breached: bool
    max_z_score: float
    consecutive_drift_count: int


class DriftOutput(BaseModel):
    """
    Standardized Drift Sentinel evaluation output.
    
    Contains overall drift state, continuous calibrated severity score,
    estimated lead cycles before limit breach, and contributing signal ranking.
    """
    cycle_index: int
    timestamp: str
    drift: bool = Field(description="True if statistical drift confirmed by persistence gate")
    severity: float = Field(ge=0.0, le=1.0, description="Continuous severity score between 0.0 and 1.0")
    lead_cycles: Optional[int] = Field(default=None, description="Estimated lead cycles before envelope breach")
    signals: List[str] = Field(default_factory=list, description="Drifting signals ranked by deviation magnitude")
    details: Dict[str, SignalDriftDetail] = Field(default_factory=dict)
    metrics: DriftMetrics
