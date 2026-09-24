"""Unit tests for Quality Contract and Temporal Feature Engineering (QRSK-02, QRSK-03)."""

import pytest
import numpy as np

from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.quality.contract import QualityContract, ToleranceRange
from process_guardian.quality.features import TemporalFeatureExtractor


@pytest.fixture
def baseline_fingerprint():
    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]
    return FingerprintBuilder().fit(records)


def test_quality_contract_tolerances():
    """Verify Quality Contract tolerance evaluation on compliant and defective records (QRSK-03)."""
    contract = QualityContract()
    pipeline = TelemetryPipeline()
    sim_healthy = InjectionMoldingSimulator(seed=101, base_regime=RegimeType.HEALTHY)

    # Compliant healthy record
    rec_healthy = pipeline.process(sim_healthy.step())
    res_healthy = contract.evaluate(rec_healthy)

    assert res_healthy.is_compliant is True
    assert len(res_healthy.violations) == 0
    assert res_healthy.defect_risk_indicator == 0.0

    # Defective record (high thermal flash + underweight)
    sim_drift = InjectionMoldingSimulator(seed=102, base_regime=RegimeType.THERMAL_DRIFT)
    for _ in range(35):
        sim_drift.step()
    rec_defective = pipeline.process(sim_drift.step())
    res_defective = contract.evaluate(rec_defective)

    assert res_defective.is_compliant is False
    assert len(res_defective.violations) > 0
    assert res_defective.defect_risk_indicator > 0.50


def test_temporal_feature_extractor(baseline_fingerprint):
    """Verify rich temporal feature vector generation across rolling windows (QRSK-02)."""
    extractor = TemporalFeatureExtractor(fingerprint=baseline_fingerprint)
    feature_names = extractor.get_feature_names()

    # 15 signals * 10 features + 8 physics interactions = 158 features
    assert len(feature_names) == 158
    assert "barrel_temp_z3_z_fp" in feature_names
    assert "barrel_temp_z3_slope_w15" in feature_names
    assert "effective_melt_temp" in feature_names
    assert "pressure_transfer_ratio" in feature_names

    sim = InjectionMoldingSimulator(seed=202, base_regime=RegimeType.THERMAL_DRIFT)
    pipeline = TelemetryPipeline()

    vectors = []
    for _ in range(25):
        rec = pipeline.process(sim.step())
        feat_dict, vec = extractor.extract_features(rec)
        vectors.append(vec)
        assert len(vec) == len(feature_names)
        assert not np.isnan(vec).any()
        assert not np.isinf(vec).any()

    # Verify that zone-3 z-score and slope increase over time in thermal drift
    last_dict, last_vec = extractor.extract_features(pipeline.process(sim.step()))
    assert last_dict["barrel_temp_z3_z_fp"] > 2.0
    assert last_dict["barrel_temp_z3_slope_w15"] > 0.05
    assert last_dict["effective_melt_temp"] > 230.0
