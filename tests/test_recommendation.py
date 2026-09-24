"""Unit tests for the 7-field recommendation contract, operator modes, and mandatory ABSTAIN gate (RCMD-01, RCMD-02, RCMD-03)."""

import pytest
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.regimes import RegimeType
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode
from process_guardian.root_cause.analyzer import RootCauseAnalyzer
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.intervention.surrogate import InterventionSurrogateModel
from process_guardian.intervention.optimizer import InterventionOptimizer
from process_guardian.intervention.recommendation import RecommendationEngine, BANNED_DOGMATIC_WORDS
from process_guardian.intervention.schemas import InterventionRecommendation


@pytest.fixture
def recommender_fixture():
    """Setup full pipeline up to thermal drift intervention evaluation."""
    pipeline = TelemetryPipeline()
    sim_healthy = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    healthy_records = [pipeline.process(sim_healthy.step()) for _ in range(60)]

    builder = FingerprintBuilder()
    fp = builder.fit(healthy_records)

    risk_model = QualityRiskModel(fingerprint=fp)
    root_cause = RootCauseAnalyzer()
    sentinel = DriftSentinel(fingerprint=fp, min_warmup_cycles=5)
    surrogate = InterventionSurrogateModel(quality_risk_model=risk_model)
    optimizer = InterventionOptimizer(surrogate_model=surrogate)
    recommender = RecommendationEngine(min_confidence_threshold=0.65)

    # Injected thermal drift advanced to high-risk state (cycle 25)
    sim_drift = InjectionMoldingSimulator(seed=123, base_regime=RegimeType.THERMAL_DRIFT)
    drift_records = []
    for _ in range(25):
        r = pipeline.process(sim_drift.step())
        risk_model.predict(r)
        sentinel.evaluate(r)
        drift_records.append(r)
    drift_record = drift_records[-1]
    drift_out = sentinel.evaluate(drift_record)
    risk_out = risk_model.predict(drift_record)
    root_out = root_cause.analyze(drift_record, fp, drift_out, risk_out)

    return {
        "fingerprint": fp,
        "risk_model": risk_model,
        "optimizer": optimizer,
        "recommender": recommender,
        "drift_record": drift_record,
        "drift_out": drift_out,
        "risk_out": risk_out,
        "root_out": root_out,
        "healthy_record": healthy_records[-1],
    }


def test_seven_field_recommendation_contract(recommender_fixture):
    """Test all 7 fields are present, populated, and conform strictly to RCMD-01."""
    recommender = recommender_fixture["recommender"]
    optimizer = recommender_fixture["optimizer"]
    fp = recommender_fixture["fingerprint"]
    drift_record = recommender_fixture["drift_record"]
    drift_out = recommender_fixture["drift_out"]
    risk_out = recommender_fixture["risk_out"]
    root_out = recommender_fixture["root_out"]

    table = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table,
        risk_output=risk_out,
        drift_output=drift_out,
        root_cause_report=root_out,
    )

    # RCMD-01: Exactly 7 required core fields
    # 1. ACTION
    assert rec.action is not None and len(rec.action) > 5
    assert "ADJUST barrel_temp_z3" in rec.action
    assert "-3.0°C" in rec.action or "-2." in rec.action

    # 2. WHY
    assert rec.why is not None and len(rec.why) > 10
    assert "Zone 3" in rec.why or "contributor" in rec.why

    # 3. EVIDENCE
    assert rec.evidence is not None and len(rec.evidence) > 5
    assert "z-score" in rec.evidence

    # 4. EXPECTED EFFECT
    assert rec.expected_effect is not None and len(rec.expected_effect) > 10
    assert "reduces predicted defect risk" in rec.expected_effect

    # 5. CONFIDENCE
    assert 0.0 <= rec.confidence <= 1.0
    assert rec.confidence >= 0.65

    # 6. OPERATING LIMIT
    assert rec.operating_limit is not None and len(rec.operating_limit) > 10
    assert "satisfies machine safety" in rec.operating_limit or "recipe" in rec.operating_limit

    # 7. RECOVERY CHECK
    assert rec.recovery_check is not None and len(rec.recovery_check) > 10
    assert "within 3 cycles" in rec.recovery_check

    # Metadata checks
    assert rec.operator_mode == "RECOMMEND_ACTION"
    assert rec.is_abstain is False
    assert rec.candidate_id == "A1"


def test_operator_mode_selection(recommender_fixture):
    """Test 3 operator modes based on risk state and confidence (RCMD-02)."""
    recommender = recommender_fixture["recommender"]
    optimizer = recommender_fixture["optimizer"]
    fp = recommender_fixture["fingerprint"]
    drift_record = recommender_fixture["drift_record"]

    # 1. Low risk -> NORMAL_MONITORING
    low_risk_out = QualityRiskOutput(
        cycle_index=1,
        timestamp=drift_record.timestamp,
        risk_probability=0.12,
        confidence=0.92,
        risk_state=RiskState.LOW,
        operator_mode=OperatorMode.NORMAL_MONITORING,
        contract_compliant=True,
    )
    table_low = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec_low = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table_low,
        risk_output=low_risk_out,
    )
    assert rec_low.operator_mode == "NORMAL_MONITORING"
    assert rec_low.action == "CONTINUE_MONITORING"
    assert rec_low.is_abstain is False

    # 2. Medium risk -> REQUEST_QC_SAMPLE
    med_risk_out = QualityRiskOutput(
        cycle_index=2,
        timestamp=drift_record.timestamp,
        risk_probability=0.52,
        confidence=0.88,
        risk_state=RiskState.MEDIUM,
        operator_mode=OperatorMode.REQUEST_QC_SAMPLE,
        contract_compliant=True,
    )
    table_med = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec_med = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table_med,
        risk_output=med_risk_out,
    )
    assert rec_med.operator_mode == "REQUEST_QC_SAMPLE"
    assert rec_med.action == "REQUEST_QC_SAMPLE"
    assert rec_med.is_abstain is False

    # 3. High risk + high confidence -> RECOMMEND_ACTION
    high_risk_out = QualityRiskOutput(
        cycle_index=3,
        timestamp=drift_record.timestamp,
        risk_probability=0.95,
        confidence=0.85,
        risk_state=RiskState.HIGH,
        operator_mode=OperatorMode.INTERVENE_RECOMMENDED,
        contract_compliant=False,
    )
    table_high = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec_high = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table_high,
        risk_output=high_risk_out,
    )
    assert rec_high.operator_mode == "RECOMMEND_ACTION"
    assert rec_high.is_abstain is False


def test_mandatory_abstain_on_low_confidence(recommender_fixture):
    """Test ABSTAIN safety gate triggers when confidence < 0.65 or actions infeasible (RCMD-03)."""
    recommender = recommender_fixture["recommender"]
    optimizer = recommender_fixture["optimizer"]
    fp = recommender_fixture["fingerprint"]
    drift_record = recommender_fixture["drift_record"]

    # High risk but LOW CONFIDENCE (e.g. 0.55 < 0.65)
    low_conf_out = QualityRiskOutput(
        cycle_index=10,
        timestamp=drift_record.timestamp,
        risk_probability=0.92,
        confidence=0.55,  # Below 0.65 threshold
        risk_state=RiskState.HIGH,
        operator_mode=OperatorMode.ABSTAIN_AND_MONITOR,
        contract_compliant=False,
    )
    table = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec_abstain = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table,
        risk_output=low_conf_out,
    )

    # RCMD-03: ABSTAIN is a product feature — system must refuse to act
    assert rec_abstain.operator_mode == "ABSTAIN_AND_MONITOR"
    assert rec_abstain.is_abstain is True
    assert rec_abstain.action == "ABSTAIN_AND_MONITOR"
    assert rec_abstain.abstain_reason is not None
    assert "Low epistemic confidence" in rec_abstain.abstain_reason
    assert "withheld" in rec_abstain.why.lower()


def test_epistemic_honesty_linting(recommender_fixture):
    """Test rejection of dogmatic and non-empirical claims."""
    recommender = recommender_fixture["recommender"]

    # Verify that a recommendation containing a banned certainty word is caught
    bad_rec = InterventionRecommendation(
        action="ADJUST barrel_temp_z3 BY -3.0°C",
        why="This will guarantee defect elimination.",
        evidence="barrel_temp_z3 elevated",
        expected_effect="Reduces risk to 0",
        confidence=0.90,
        operating_limit="Within recipe",
        recovery_check="Check after 3 cycles",
        operator_mode="RECOMMEND_ACTION",
        is_abstain=False,
        cycle_index=1,
        timestamp="2026-09-24T12:00:00Z",
    )

    with pytest.raises(ValueError, match="Epistemic honesty violation"):
        recommender._lint_epistemics(bad_rec)
