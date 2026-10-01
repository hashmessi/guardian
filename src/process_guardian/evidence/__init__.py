"""Process Guardian Evidence & Grounding Module.

Provides external industrial benchmark dataset ingestion, empirical feature
correlation models, grounding benchmark reports, and 4-level epistemic evidence contracts.
"""

from process_guardian.evidence.benchmark_dataset import (
    BenchmarkDatasetSummary,
    BenchmarkSample,
    ExternalBenchmarkAdapter,
    FeatureCorrelation,
)

__all__ = [
    "BenchmarkSample",
    "BenchmarkDatasetSummary",
    "FeatureCorrelation",
    "ExternalBenchmarkAdapter",
]
