"""Unit tests for Drift Sentinel multi-method detection and noise rejection (DRFT-01, DRFT-02, DRFT-04)."""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel


@pytest.fixture
def baseline_fingerprint():
    """Create a high-confidence baseline fingerprint from 60 healthy cycles."""
    sim = InjectionMoldingSimulator(seed=101)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]
    return FingerprintBuilder().fit(records)


def test_statistical_drift_detectors(baseline_fingerprint):
    """Verify that multi-method detectors accurately flag process-state change under drift (DRFT-01)."""
    sentinel = DriftSentinel(fingerprint=baseline_fingerprint)
    sim = InjectionMoldingSimulator(seed=202)
    pipeline = TelemetryPipeline()

    # 1. Healthy stationary run - no drift
    healthy_records = [pipeline.process(sim.step()) for _ in range(25)]
    healthy_outputs = [sentinel.evaluate(r) for r in healthy_records]
    assert all(out.drift is False for out in healthy_outputs)
    assert sentinel.consecutive_drift_count == 0

    # 2. Inject progressive thermal drift
    sim.inject_event("thermal_drift", cycle=sim.current_cycle + 1, severity=1.5)
    drift_records = [pipeline.process(sim.step()) for _ in range(25)]
    drift_outputs = [sentinel.evaluate(r) for r in drift_records]

    # Drift should be detected well before 25 cycles
    confirmed_drifts = [out for out in drift_outputs if out.drift]
    assert len(confirmed_drifts) >= 10
    # Last cycle must be confirmed drift with EWMA or CUSUM breached
    last_out = drift_outputs[-1]
    assert last_out.drift is True
    assert last_out.metrics.ewma_breached or last_out.metrics.cusum_breached or last_out.metrics.multivariate_breached


def test_structured_drift_output(baseline_fingerprint):
    """Verify structured output schema with severity, lead cycles, and signal ranking (DRFT-02)."""
    sentinel = DriftSentinel(fingerprint=baseline_fingerprint)
    sim = InjectionMoldingSimulator(seed=303)
    pipeline = TelemetryPipeline()

    # Step until drift activates
    sim.inject_event("thermal_drift", cycle=1, severity=1.8)
    records = [pipeline.process(sim.step()) for _ in range(20)]
    outputs = [sentinel.evaluate(r) for r in records]

    drift_detected = [o for o in outputs if o.drift]
    assert len(drift_detected) > 0
    active_out = drift_detected[-1]

    # Verify structured fields
    assert active_out.drift is True
    assert 0.40 <= active_out.severity <= 1.0
    assert active_out.signals[0] == "barrel_temp_z3"
    assert "barrel_temp_z3" in active_out.details
    assert active_out.details["barrel_temp_z3"].z_score > 2.5
    assert active_out.lead_cycles is not None
    assert active_out.lead_cycles > 0


def test_false_alarm_rejection_on_noise(baseline_fingerprint):
    """Verify that zero false drift alarms are raised on high sensor jitter with zero mean shift (DRFT-04)."""
    sentinel = DriftSentinel(fingerprint=baseline_fingerprint)
    # SENSOR_NOISE has 5x variance on thermocouple/transducer without physical melt drift
    sim = InjectionMoldingSimulator(seed=404, base_regime=RegimeType.SENSOR_NOISE)
    pipeline = TelemetryPipeline()

    records = [pipeline.process(sim.step()) for _ in range(120)]
    outputs = [sentinel.evaluate(r) for r in records]

    # Must produce ZERO confirmed drift alerts
    drift_alerts = [out for out in outputs if out.drift]
    assert len(drift_alerts) == 0

    # Severity should remain safely low throughout
    for out in outputs:
        assert out.severity <= 0.35
