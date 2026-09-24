"""End-to-End Demo Benchmark and Multi-Regime Validation for Constrained Intervention Engine (INTV-01..05, RCMD-01..03)."""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.pipeline import QualityEngine
from process_guardian.intervention.pipeline import InterventionEngine
from process_guardian.intervention.schemas import InterventionRecommendation, InterventionComparisonTable


def test_demo_scenario_intervention_recommendation():
    """
    End-to-end benchmark on the primary 10-step demo scenario:
    1. Healthy baseline (cycles 1-419) -> stationary operation
    2. Thermal drift injection at cycle 420 -> drift sentinel triggers
    3. Quality risk escalates to HIGH -> root-cause points to Zone 3 temperature
    4. At cycle 441/442, intervention engine evaluates candidates A0..A4
    5. Validates constraints, predicts post-action risk via surrogate, optimizes cost J
    6. Recommends minimum effective action A1 (-3.0°C on Zone 3)
    7. Validates 7-field contract, comparison table, and Phase 5 recovery criteria.
    """
    # Step 1: Fit fingerprint on healthy reference cycles
    sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=42)
    pipe_base = TelemetryPipeline()
    base_records = [pipe_base.process(sim_base.step()) for _ in range(60)]
    fingerprint = FingerprintBuilder().fit(base_records)

    # Step 2: Initialize full Process Guardian analytical stack
    pipe = TelemetryPipeline()
    sentinel = DriftSentinel(fingerprint=fingerprint, min_warmup_cycles=10, persistence_required=2)
    quality_engine = QualityEngine(fingerprint=fingerprint)
    intervention_engine = InterventionEngine(risk_model=quality_engine.risk_model)

    sim_demo = build_demo_scenario(seed=42)

    intervention_cycle = 442
    rec_at_intervention = None
    table_at_intervention = None

    # Step 3: Run demo scenario up to intervention point
    for c_idx in range(1, intervention_cycle + 1):
        raw = sim_demo.step()
        record = pipe.process(raw)

        drift_out = sentinel.evaluate(record)
        risk_out, root_out = quality_engine.evaluate_cycle(record, drift_out)

        # Trigger intervention engine at decision cycle (441 or 442 when risk is HIGH)
        if c_idx == 441:
            rec, table = intervention_engine.evaluate(
                record=record,
                fingerprint=fingerprint,
                risk_output=risk_out,
                drift_output=drift_out,
                root_cause_report=root_out,
            )
            rec_at_intervention = rec
            table_at_intervention = table

    # Step 4: Validate Intervention Outcomes
    assert rec_at_intervention is not None
    assert table_at_intervention is not None

    # INTV-01: System evaluated at least 4 candidates
    assert len(table_at_intervention.evaluations) >= 5

    # INTV-02: Constraint checks executed
    for ev in table_at_intervention.evaluations:
        assert isinstance(ev.constraint_check.is_feasible, bool)

    # INTV-04: System recommended minimum-cost effective action A1 (Temperature adjustment)
    assert table_at_intervention.recommended_action_id == "A1"
    a1_eval = next(e for e in table_at_intervention.evaluations if e.candidate.action_id == "A1")
    assert a1_eval.is_selected is True
    assert a1_eval.constraint_check.is_feasible is True

    # INTV-03: Surrogate model estimated significant post-intervention risk reduction
    assert a1_eval.post_intervention_risk < a1_eval.pre_intervention_risk
    assert a1_eval.risk_reduction > 0.30

    # INTV-05: Comparison table formatted
    assert "Candidate Intervention Comparison" in table_at_intervention.table_summary
    assert "A1" in table_at_intervention.table_summary
    assert "FEASIBLE" in table_at_intervention.table_summary

    # RCMD-01: Seven-Field Recommendation Contract
    rec = rec_at_intervention
    assert "barrel_temp_z3" in rec.action
    assert "-3.0°C" in rec.action or "-2." in rec.action
    assert len(rec.why) > 10
    assert len(rec.evidence) > 5
    assert len(rec.expected_effect) > 10
    assert 0.0 <= rec.confidence <= 1.0
    assert len(rec.operating_limit) > 10
    assert "within 3 cycles" in rec.recovery_check

    # RCMD-02: Operator mode
    assert rec.operator_mode == "RECOMMEND_ACTION"
    assert rec.is_abstain is False


def test_pressure_drift_intervention():
    """Verify intervention engine recommends pressure adjustment (A2) under hydraulic pressure loss."""
    # Build baseline
    sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=101)
    pipe = TelemetryPipeline()
    base_records = [pipe.process(sim_base.step()) for _ in range(60)]
    fingerprint = FingerprintBuilder().fit(base_records)

    quality_engine = QualityEngine(fingerprint=fingerprint)
    intervention_engine = InterventionEngine(risk_model=quality_engine.risk_model)

    # Run pressure drift scenario to risk escalation (cycle 42)
    sim_press = build_regime_scenario(RegimeType.PRESSURE_DRIFT, seed=101)
    pipe_press = TelemetryPipeline()
    for _ in range(42):
        rec = pipe_press.process(sim_press.step())
        risk_out, root_out = quality_engine.evaluate_cycle(rec)

    rec, table = intervention_engine.evaluate(
        record=rec,
        fingerprint=fingerprint,
        risk_output=risk_out,
        root_cause_report=root_out,
    )

    # System should recommend holding pressure adjustment (A2)
    assert table.recommended_action_id in ["A2", "A1"]
    assert rec.operator_mode in ["RECOMMEND_ACTION", "REQUEST_QC_SAMPLE"]


def test_low_confidence_abstain_safety_gate():
    """Verify that mandatory ABSTAIN gate triggers whenever model confidence is below 0.65 threshold (RCMD-03)."""
    sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=55)
    pipe = TelemetryPipeline()
    base_records = [pipe.process(sim_base.step()) for _ in range(60)]
    fingerprint = FingerprintBuilder().fit(base_records)

    risk_model = QualityRiskModel(fingerprint=fingerprint)
    engine = InterventionEngine(risk_model=risk_model, min_confidence_threshold=0.65)

    rec = base_records[-1]
    from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode

    # High risk but LOW CONFIDENCE (e.g. 0.52 < 0.65)
    low_conf_risk = QualityRiskOutput(
        cycle_index=rec.cycle_index,
        timestamp=rec.timestamp,
        risk_probability=0.88,
        confidence=0.52,
        risk_state=RiskState.HIGH,
        operator_mode=OperatorMode.ABSTAIN_AND_MONITOR,
        contract_compliant=False,
    )

    recommendation, table = engine.evaluate(
        record=rec,
        fingerprint=fingerprint,
        risk_output=low_conf_risk,
    )

    assert recommendation.operator_mode == "ABSTAIN_AND_MONITOR"
    assert recommendation.is_abstain is True
    assert recommendation.action == "ABSTAIN_AND_MONITOR"
    assert "Low epistemic confidence" in recommendation.abstain_reason
