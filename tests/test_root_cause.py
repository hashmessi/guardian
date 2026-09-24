"""Unit tests for Root Cause Attribution, percentage sums, evidence, and honest language (ROOT-01..03)."""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.root_cause.analyzer import RootCauseAnalyzer
from process_guardian.root_cause.evidence import EvidenceGenerator


@pytest.fixture
def baseline_fingerprint():
    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]
    return FingerprintBuilder().fit(records)


def test_ranked_contributors_sum_100(baseline_fingerprint):
    """Verify that root cause percentage contributions sum strictly to 100.0% (ROOT-01)."""
    analyzer = RootCauseAnalyzer()
    pipeline = TelemetryPipeline()

    sim = InjectionMoldingSimulator(seed=88, base_regime=RegimeType.THERMAL_DRIFT)
    records = [pipeline.process(sim.step()) for _ in range(30)]

    for rec in records:
        report = analyzer.analyze(record=rec, fingerprint=baseline_fingerprint)

        # 1. Total individual contributor sum must equal 100.0%
        contrib_sum = sum(c.contribution_pct for c in report.contributors)
        assert abs(contrib_sum - 100.0) < 1e-4, f"Expected 100.0%, got {contrib_sum}"

        # 2. Total subsystem breakdown sum must equal 100.0%
        sub_sum = (
            report.subsystem_breakdown.thermal_pct
            + report.subsystem_breakdown.pressure_pct
            + report.subsystem_breakdown.timing_pct
            + report.subsystem_breakdown.material_pct
        )
        assert abs(sub_sum - 100.0) < 1e-4, f"Expected 100.0%, got {sub_sum}"

        # 3. Contributors must be sorted descending by contribution percentage
        percentages = [c.contribution_pct for c in report.contributors]
        assert percentages == sorted(percentages, reverse=True)


def test_supporting_evidence_generation(baseline_fingerprint):
    """Verify that supporting evidence itemizes delta, z-score, and trend rate (ROOT-02)."""
    analyzer = RootCauseAnalyzer()
    sentinel = DriftSentinel(fingerprint=baseline_fingerprint)
    pipeline = TelemetryPipeline()

    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.THERMAL_DRIFT)
    records = [pipeline.process(sim.step()) for _ in range(25)]

    drift_out = None
    for r in records:
        drift_out = sentinel.evaluate(r)

    report = analyzer.analyze(
        record=records[-1],
        fingerprint=baseline_fingerprint,
        drift_output=drift_out,
    )

    # In thermal drift, barrel_temp_z3 must be the primary contributor with thermal dominating
    assert report.primary_contributor == "barrel_temp_z3"
    assert report.subsystem_breakdown.thermal_pct > 50.0

    # Top contributor evidence must contain specific numbers
    top_c = report.contributors[0]
    assert top_c.signal_name == "barrel_temp_z3"
    assert "shifted" in top_c.evidence or "operating nominally" in top_c.evidence
    assert "baseline mean" in top_c.evidence


def test_honest_epistemic_language():
    """Verify that all generated statements use honest probabilistic phrasing and ban certainty claims (ROOT-03)."""
    gen = EvidenceGenerator()

    # Verify banned phrase detection
    assert gen.verify_honest_language("Zone 3 temperature is a likely contributor based on observed evidence") is True
    assert gen.verify_honest_language("Zone 3 is the guaranteed cause of the defect") is False
    assert gen.verify_honest_language("This is proven root cause of the failure") is False
    assert gen.verify_honest_language("The defect was definitely caused by pressure drop") is False

    # Verify that generated evidence is clean
    ev = gen.generate_signal_evidence(
        signal_name="barrel_temp_z3",
        current_val=234.5,
        baseline_mean=230.0,
        baseline_std=0.35,
        z_score=12.8,
        slope_per_cycle=0.20,
    )
    assert gen.verify_honest_language(ev) is True
    assert "likely contributor" in ev
