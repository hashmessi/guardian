"""Tests for External Measured Injection Molding Benchmark Dataset Adapter (EVID-01)."""

import pytest
from process_guardian.evidence.benchmark_dataset import (
    BenchmarkDatasetSummary,
    BenchmarkSample,
    ExternalBenchmarkAdapter,
    FeatureCorrelation,
)


def test_benchmark_dataset_loads_564_samples():
    """Verify exactly 564 samples loaded with 282 PP and 282 ABS."""
    samples = ExternalBenchmarkAdapter.get_samples()
    assert len(samples) == 564

    pp_count = sum(1 for s in samples if s.material == "PP")
    abs_count = sum(1 for s in samples if s.material == "ABS")
    assert pp_count == 282
    assert abs_count == 282


def test_benchmark_dataset_quality_distribution():
    """Verify realistic defect distribution and OK/NOK flags."""
    summary = ExternalBenchmarkAdapter.get_summary()
    assert isinstance(summary, BenchmarkDatasetSummary)
    assert summary.total_parts == 564
    assert summary.ok_count > 450
    assert summary.nok_count > 0
    assert summary.scrap_rate_pct > 5.0  # Industry representative 8-15% defect test envelope
    assert "sink_marks" in summary.defect_breakdown
    assert "flash" in summary.defect_breakdown
    assert "short_shots" in summary.defect_breakdown


def test_feature_correlations_physics_soundness():
    """Verify feature correlations match injection molding physics."""
    summary = ExternalBenchmarkAdapter.get_summary()
    assert len(summary.top_correlations) >= 4

    top_feature = summary.top_correlations[0]
    assert isinstance(top_feature, FeatureCorrelation)
    assert abs(top_feature.correlation_with_defect) > 0.15
    assert len(top_feature.physics_rationale) > 10


def test_machine_limits_escape_rate_proves_conventional_spc_flaw():
    """Verify that single-variable +-3 sigma limits miss defective parts (EVID-01 core proof)."""
    flaw_analysis = ExternalBenchmarkAdapter.evaluate_machine_limits_flaw()
    assert flaw_analysis["total_defective_parts"] > 0
    assert flaw_analysis["escaped_defects_count"] > 0
    # Over 25% of defective parts pass univariate machine limit checks
    assert flaw_analysis["escaped_defects_percentage"] > 25.0
    assert flaw_analysis["guardian_multivariate_catch_rate"] > 90.0
    assert "multivariate sentinel" in flaw_analysis["conclusion"].lower()
