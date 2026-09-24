"""End-to-end integration and benchmark tests for Quality Risk & Root Cause Engine (QRSK-01..04, ROOT-01..03)."""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.quality.pipeline import QualityEngine
from process_guardian.quality.schemas import RiskState, OperatorMode


@pytest.fixture
def baseline_fingerprint():
    sim = InjectionMoldingSimulator = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=42)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]
    return FingerprintBuilder().fit(records)


def test_end_to_end_demo_risk_escalation(baseline_fingerprint):
    """
    Verify complete progression through the primary demo scenario:
    - Cycles 1..419: Low risk, normal monitoring, clean baseline
    - Cycle 420+: Injected thermal drift
    - Cycle 432: Sentinel confirms drift
    - Cycles 433..441: Quality risk escalates to HIGH, operator mode recommends intervention,
      and Root Cause accurately isolates zone-3 temperature as primary contributor (summing to 100%).
    """
    sim_demo = build_demo_scenario(seed=42)
    pipeline = TelemetryPipeline()
    sentinel = DriftSentinel(fingerprint=baseline_fingerprint)
    quality_engine = QualityEngine(fingerprint=baseline_fingerprint)

    drift_alert_cycle = None
    high_risk_cycle = None
    final_report = None

    for c_idx in range(1, 442):
        raw = sim_demo.step()
        record = pipeline.process(raw)
        drift_out = sentinel.evaluate(record)
        risk_out, rc_report = quality_engine.evaluate_cycle(record, drift_output=drift_out)

        # 1. Healthy baseline checks (first 100 cycles)
        if record.cycle_index <= 100:
            assert risk_out.risk_state == RiskState.LOW
            assert risk_out.operator_mode == OperatorMode.NORMAL_MONITORING
            assert risk_out.contract_compliant is True

        # Track first drift alert
        if drift_out.drift and drift_alert_cycle is None:
            drift_alert_cycle = record.cycle_index

        # Track first high quality risk
        if risk_out.risk_state == RiskState.HIGH and high_risk_cycle is None:
            high_risk_cycle = record.cycle_index

        if record.cycle_index == 441:
            final_report = rc_report
            # Near defect threshold, risk must be HIGH
            assert risk_out.risk_state == RiskState.HIGH
            assert risk_out.risk_probability >= 0.70
            assert risk_out.operator_mode == OperatorMode.INTERVENE_RECOMMENDED

    # Verify drift lead time before critical defect
    assert drift_alert_cycle is not None and drift_alert_cycle == 432
    assert high_risk_cycle is not None and high_risk_cycle >= 430

    # Verify root cause report on escalated cycle
    assert final_report is not None
    assert final_report.primary_contributor == "barrel_temp_z3"
    assert final_report.subsystem_breakdown.thermal_pct > 50.0
    assert final_report.honest_language_compliant is True

    # Check 100% normalization
    contrib_sum = sum(c.contribution_pct for c in final_report.contributors)
    assert abs(contrib_sum - 100.0) < 1e-4


def test_multi_regime_root_cause_attribution(baseline_fingerprint):
    """Verify accurate root-cause subsystem attribution across diverse physical drift regimes."""
    quality_engine = QualityEngine(fingerprint=baseline_fingerprint)

    regimes_to_test = [
        (RegimeType.PRESSURE_DRIFT, "Pressure", ["peak_pressure", "injection_pressure"]),
        (RegimeType.MOISTURE_DRIFT, "Material", ["material_moisture"]),
        (RegimeType.CYCLE_INSTABILITY, "Timing", ["cycle_time", "cooling_time"]),
    ]

    for regime, expected_category, expected_signals in regimes_to_test:
        sim = build_regime_scenario(regime, cycles=30, seed=55)
        pipeline = TelemetryPipeline()

        last_report = None
        for _ in range(30):
            record = pipeline.process(sim.step())
            _, rc_report = quality_engine.evaluate_cycle(record)
            last_report = rc_report

        assert last_report is not None
        # Verify 100% sum
        assert abs(sum(c.contribution_pct for c in last_report.contributors) - 100.0) < 1e-4

        # Primary contributor must be within expected signals
        assert last_report.primary_contributor in expected_signals or getattr(last_report.subsystem_breakdown, f"{expected_category.lower()}_pct") > 35.0
        assert last_report.honest_language_compliant is True
