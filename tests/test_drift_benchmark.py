"""Benchmark validation of early warning lead time on demo and baseline regimes (DRFT-03)."""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel


def test_lead_time_in_demo_scenario():
    """
    Verify that Drift Sentinel detects process drift at least 5 cycles before
    the first quality defect / contract breach occurs in the primary demo scenario (DRFT-03).
    """
    # 1. Fit fingerprint on pristine healthy baseline cycles
    sim_baseline = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=42)
    pipeline_base = TelemetryPipeline()
    baseline_records = [pipeline_base.process(sim_baseline.step()) for _ in range(60)]
    fingerprint = FingerprintBuilder().fit(baseline_records)

    # 2. Run the primary demo scenario with dedicated telemetry pipeline
    sim_demo = build_demo_scenario(seed=42)
    pipeline_demo = TelemetryPipeline()
    sentinel = DriftSentinel(fingerprint=fingerprint, min_warmup_cycles=10, persistence_required=2)

    first_drift_cycle = None
    first_defect_cycle = None
    alert_signals = []

    # Run up to intervention point (cycle 442)
    for c_idx in range(1, 443):
        raw_cycle = sim_demo.step()
        record = pipeline_demo.process(raw_cycle)
        drift_output = sentinel.evaluate(record)

        # Track first confirmed drift alert
        if drift_output.drift and first_drift_cycle is None:
            first_drift_cycle = record.cycle_index
            alert_signals = list(drift_output.signals)

        # Track first ground-truth defect
        if record.defect_flag and first_defect_cycle is None:
            first_defect_cycle = record.cycle_index

    # Assertions
    # Drift event was injected at cycle 420
    assert first_drift_cycle is not None, "Drift Sentinel failed to detect drift"
    assert first_drift_cycle >= 420, f"Drift alerted prematurely at cycle {first_drift_cycle}"
    assert first_drift_cycle <= 434, f"Drift detection was too late (cycle {first_drift_cycle})"

    # Defect occurred after drift had progressed
    assert first_defect_cycle is not None, "No defect occurred in demo scenario"
    assert first_defect_cycle > first_drift_cycle, "Defect occurred before or simultaneously with drift alert"

    # Lead time calculation
    lead_time = first_defect_cycle - first_drift_cycle
    print(f"\n[DEMO BENCHMARK RESULT] Injected: 420 | Alerted: {first_drift_cycle} | Defect: {first_defect_cycle} | Lead Time: {lead_time} cycles")

    # PS02 core requirement: lead time >= 5 cycles
    assert lead_time >= 5, f"Expected lead time >= 5 cycles, got {lead_time} cycles"

    # Verify signal attribution
    assert alert_signals[0] == "barrel_temp_z3", f"Expected barrel_temp_z3 as primary contributor, got {alert_signals}"


def test_multi_regime_drift_detection():
    """Verify drift detection across diverse regimes: pressure drift, moisture drift, and cycle instability."""
    # Baseline
    sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=50, seed=77)
    pipeline_base = TelemetryPipeline()
    fingerprint = FingerprintBuilder().fit([pipeline_base.process(sim_base.step()) for _ in range(50)])

    test_regimes = [
        (RegimeType.PRESSURE_DRIFT, ["peak_pressure", "injection_pressure"]),
        (RegimeType.MOISTURE_DRIFT, ["material_moisture"]),
        (RegimeType.CYCLE_INSTABILITY, ["cycle_time", "cooling_time"]),
    ]

    for regime, expected_signals in test_regimes:
        sim = build_regime_scenario(regime, cycles=30, seed=88)
        pipeline_regime = TelemetryPipeline()
        sentinel = DriftSentinel(fingerprint=fingerprint)

        detected = False
        for _ in range(30):
            record = pipeline_regime.process(sim.step())
            output = sentinel.evaluate(record)
            if output.drift:
                detected = True
                assert any(s in output.signals for s in expected_signals) or output.metrics.multivariate_breached
                break

        assert detected, f"Failed to detect drift in regime {regime.value}"
