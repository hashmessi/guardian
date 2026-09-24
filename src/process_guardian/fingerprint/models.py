"""Pydantic v2 schemas for process fingerprint baselines and operating envelopes."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from process_guardian.adapter.schemas import EnrichedContext


class SignalStats(BaseModel):
    """Empirical distribution statistics for a single process variable."""
    mean: float
    std: float
    min_val: float
    max_val: float
    p01: float = Field(description="1st percentile")
    p99: float = Field(description="99th percentile")
    iqr: float = Field(description="Interquartile range (p75 - p25)")


class OperatingEnvelope(BaseModel):
    """Validated operating boundaries derived from empirical process distributions."""
    lower_limit: float = Field(description="Action limit: mu - 3*sigma")
    upper_limit: float = Field(description="Action limit: mu + 3*sigma")
    warning_lower: float = Field(description="Warning limit: mu - 2*sigma")
    warning_upper: float = Field(description="Warning limit: mu + 2*sigma")


class ProcessFingerprint(BaseModel):
    """
    Context-specific process fingerprint.
    
    Encapsulates what 'normal' looks like for a unique machine + mold + part + recipe
    configuration, avoiding brittle global thresholds.
    """
    fingerprint_id: str
    context_key: str = Field(description="Unique key: machine:mold:part:recipe:version")
    context: EnrichedContext
    sample_count: int
    created_at: str

    # Signal-level distributions and envelopes
    signal_stats: Dict[str, SignalStats]
    operating_envelopes: Dict[str, OperatingEnvelope]

    # Multivariate structure for Mahalanobis / Hotelling T^2 distance
    feature_names: List[str]
    mean_vector: List[float]
    inv_cov_matrix: List[List[float]] = Field(description="Regularized inverse covariance matrix")
