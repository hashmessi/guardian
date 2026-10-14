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
    assert "univariate" in flaw_analysis["conclusion"].lower()


def test_multivariate_beats_univariate_at_equal_false_alarm_cost():
    """The core differentiator claim: more defects caught for the same false line stops.

    Both detectors are held to the same false-alarm rate on good parts, so this
    cannot be won by simply alarming more often.
    """
    flaw = ExternalBenchmarkAdapter.evaluate_machine_limits_flaw()
    univariate_catch = flaw["conventional_spc_catch_rate"]
    multivariate_catch = flaw["guardian_multivariate_catch_rate"]

    assert multivariate_catch > univariate_catch
    assert flaw["catch_rate_uplift_at_equal_cost"] > 1.0
    # Defects that machine limits accepted but the multivariate distance flagged.
    assert flaw["guardian_rescued_defects_count"] > 0
    assert flaw["data_provenance"] == "REPLICA_OF_PUBLISHED_DOE"


def test_detection_tradeoff_curve_is_monotonic():
    """A looser false-alarm budget must never catch fewer defects."""
    curve = ExternalBenchmarkAdapter.detection_tradeoff_curve()
    assert len(curve) >= 3

    budgets = [p["false_alarm_budget_pct"] for p in curve]
    caught = [p["defects_caught_pct"] for p in curve]
    assert budgets == sorted(budgets)
    assert caught == sorted(caught)


def test_benchmark_never_claims_measured_plant_data():
    """Provenance guard: the replica must not be published as measured parts."""
    summary = ExternalBenchmarkAdapter.get_summary()
    attribution = summary.source_attribution.lower()

    assert "replica" in summary.dataset_name.lower()
    assert "10.23728/b2share" in attribution  # real, resolvable DOI
    assert "measured" not in summary.dataset_name.lower()
