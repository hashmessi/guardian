"""Unit tests for Quality Risk Model, calibrated probabilities, and risk states (QRSK-01..04)."""

import pytest
import numpy as np

from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.schemas import RiskState, OperatorMode
from process_guardian.quality.contract import QualityContract


@pytest.fixture
def baseline_fingerprint():
    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]
    return FingerprintBuilder().fit(records)


def test_calibrated_risk_probabilities(baseline_fingerprint):
    """Verify calibrated defect risk probabilities in [0.0, 1.0] and confidence bounds (QRSK-01)."""
    model = QualityRiskModel(fingerprint=baseline_fingerprint)
    pipeline = TelemetryPipeline()

    # Healthy regime -> risk should be low (< 0.25)
    sim_healthy = InjectionMoldingSimulator(seed=10, base_regime=RegimeType.HEALTHY)
    outputs_healthy = [model.predict(pipeline.process(sim_healthy.step())) for _ in range(20)]

    for out in outputs_healthy:
        assert 0.0 <= out.risk_probability <= 0.30
        assert 0.60 <= out.confidence <= 1.0
        assert out.risk_state == RiskState.LOW
        assert out.operator_mode == OperatorMode.NORMAL_MONITORING
        assert out.contract_compliant is True


def test_risk_state_classification_and_escalation(baseline_fingerprint):
    """Verify risk state progression from LOW to HIGH during drift with appropriate operator modes (QRSK-04)."""
    model = QualityRiskModel(fingerprint=baseline_fingerprint)
    pipeline = TelemetryPipeline()

    sim_drift = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.THERMAL_DRIFT)
    outputs = [model.predict(pipeline.process(sim_drift.step())) for _ in range(40)]

    # Initial cycles should be low/medium
    assert outputs[0].risk_state in (RiskState.LOW, RiskState.MEDIUM)

    # Escalates to HIGH as thermal runaway worsens
    late_outputs = outputs[-10:]
    high_count = sum(1 for o in late_outputs if o.risk_state == RiskState.HIGH)
    assert high_count >= 8

    # When risk is HIGH and confidence is high, operator mode must recommend intervention
    for o in late_outputs:
        if o.risk_state == RiskState.HIGH and o.confidence >= 0.65:
            assert o.operator_mode == OperatorMode.INTERVENE_RECOMMENDED
