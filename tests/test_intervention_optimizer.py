"""Unit tests for surrogate response surface modeling, multi-objective optimization, and comparison table (INTV-03, INTV-04, INTV-05)."""

import pytest
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.regimes import RegimeType
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.quality.model import QualityRiskModel
from process_guardian.intervention.schemas import ActionType, CandidateAction
from process_guardian.intervention.surrogate import InterventionSurrogateModel
from process_guardian.intervention.optimizer import InterventionOptimizer


@pytest.fixture
def optimizer_fixture():
    """Setup baseline fingerprint, trained quality risk model, surrogate, and drift cycle."""
    pipeline = TelemetryPipeline()
    sim_healthy = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    healthy_records = [pipeline.process(sim_healthy.step()) for _ in range(60)]

    builder = FingerprintBuilder()
    fp = builder.fit(healthy_records)

    risk_model = QualityRiskModel(fingerprint=fp)
    surrogate = InterventionSurrogateModel(quality_risk_model=risk_model)
    optimizer = InterventionOptimizer(surrogate_model=surrogate)

    # Injected thermal drift advanced to high-risk state (cycle 25)
    sim_drift = InjectionMoldingSimulator(seed=123, base_regime=RegimeType.THERMAL_DRIFT)
    drift_records = []
    for _ in range(25):
        r = pipeline.process(sim_drift.step())
        risk_model.predict(r)
        drift_records.append(r)
    drift_record = drift_records[-1]

    return {
        "fingerprint": fp,
        "risk_model": risk_model,
        "surrogate": surrogate,
        "optimizer": optimizer,
        "drift_record": drift_record,
    }


def test_surrogate_model_risk_prediction(optimizer_fixture):
    """Test surrogate forward physics and post-intervention risk computation (INTV-03)."""
    surrogate = optimizer_fixture["surrogate"]
    fp = optimizer_fixture["fingerprint"]
    drift_record = optimizer_fixture["drift_record"]
    risk_model = optimizer_fixture["risk_model"]

    # Baseline risk for current drifting record
    base_out = risk_model.predict(drift_record)
    assert base_out.risk_probability > 0.40

    # A1: Reduce Zone 3 temperature by -2.5°C
    cand_temp = CandidateAction(
        action_id="A1",
        action_type=ActionType.TEMP_ADJUST,
        name="Reduce Zone 3 Temp",
        target_signal="barrel_temp_z3",
        delta_value=-2.5,
        unit="°C",
    )

    # 1. Check physical forward state projection
    proj_record = surrogate.project_state(drift_record, cand_temp, fp)
    assert proj_record.barrel_temp_z3 < drift_record.barrel_temp_z3
    # Cavity peak pressure should increase as melt viscosity normalizes
    assert proj_record.peak_pressure >= drift_record.peak_pressure

    # 2. Check post-intervention risk drop (the calibrated model's own prediction on the
    # projected state, not a hand-tuned formula -- see test_post_intervention_risk_uses_model_not_formula)
    post_risk, _ = surrogate.estimate_post_intervention_risk(drift_record, cand_temp, fp)
    assert post_risk < base_out.risk_probability
    assert post_risk <= 0.35  # The model's own calibrated low-risk prediction for the corrected state


def test_post_intervention_risk_uses_model_not_formula(optimizer_fixture):
    """Regression (hostile-review HIGH finding #2): a compliant, non-defect candidate's
    post-intervention risk must come from quality_risk_model.predict() on the projected
    surrogate record, not a hand-tuned formula clamped to [0.08, 0.35]. Proven by spying on
    predict(): it must be called exactly once, with the surrogate (projected) record, and the
    returned risk must equal the model's own prediction for that exact record -- not a value
    only derivable from a closed-form formula over z-scores."""
    surrogate = optimizer_fixture["surrogate"]
    fp = optimizer_fixture["fingerprint"]
    drift_record = optimizer_fixture["drift_record"]
    risk_model = optimizer_fixture["risk_model"]

    cand_temp = CandidateAction(
        action_id="A1",
        action_type=ActionType.TEMP_ADJUST,
        name="Reduce Zone 3 Temp",
        target_signal="barrel_temp_z3",
        delta_value=-2.5,
        unit="°C",
    )

    expected_surrogate_record = surrogate.project_state(drift_record, cand_temp, fp)

    calls = []
    original_predict = risk_model.predict

    def spy_predict(*args, **kwargs):
        calls.append(kwargs.get("record", args[0] if args else None))
        return original_predict(*args, **kwargs)

    risk_model.predict = spy_predict
    try:
        post_risk, surrogate_record = surrogate.estimate_post_intervention_risk(drift_record, cand_temp, fp)
    finally:
        risk_model.predict = original_predict

    assert len(calls) == 1, "estimate_post_intervention_risk must call predict() exactly once"
    assert calls[0] == expected_surrogate_record, (
        "predict() must be called with the projected surrogate record, not a formula substitute"
    )

    # The returned risk must equal a fresh model prediction on the same projected record
    # (snapshot/restore means a second call on the identical record reproduces it exactly).
    confirmation = risk_model.predict(record=surrogate_record)
    assert post_risk == pytest.approx(confirmation.risk_probability)


def test_cost_risk_disruption_optimization(optimizer_fixture):
    """Test constrained multi-objective optimization J = P_risk + lambda*C + mu*D (INTV-04)."""
    optimizer = optimizer_fixture["optimizer"]
    fp = optimizer_fixture["fingerprint"]
    drift_record = optimizer_fixture["drift_record"]

    table = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)

    # INTV-04: System minimizes J subject to constraints
    assert table.recommended_action_id is not None
    # For thermal drift, A1 (temperature adjustment) should be selected as minimum-cost effective action
    assert table.recommended_action_id == "A1"

    selected_eval = next(e for e in table.evaluations if e.candidate.action_id == table.recommended_action_id)
    assert selected_eval.is_selected is True
    assert selected_eval.constraint_check.is_feasible is True

    # Compare A1 with A0 (Do nothing)
    a0_eval = next(e for e in table.evaluations if e.candidate.action_id == "A0")
    # Even though A0 has 0 cost and 0 disruption, its high risk probability makes its J score worse than A1
    assert a0_eval.post_intervention_risk > selected_eval.post_intervention_risk
    assert a0_eval.objective_score > selected_eval.objective_score


def test_candidate_comparison_table(optimizer_fixture):
    """Test comparison table structure, rankings, and formatted ASCII output (INTV-05)."""
    optimizer = optimizer_fixture["optimizer"]
    fp = optimizer_fixture["fingerprint"]
    drift_record = optimizer_fixture["drift_record"]

    table = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)

    # Table contains all 5 candidates
    assert len(table.evaluations) >= 5
    ids = [e.candidate.action_id for e in table.evaluations]
    assert set(ids) == {"A0", "A1", "A2", "A3", "A4"}

    # Evaluations are sorted with feasible ranked best
    ranks = [e.rank for e in table.evaluations]
    assert ranks == list(range(1, len(table.evaluations) + 1))

    # Formatted summary contains key elements
    summary = table.table_summary
    assert "Candidate Intervention Comparison" in summary
    assert "Post-Risk" in summary
    assert "J-Score" in summary
    assert "RECOMMENDED" in summary
    assert "FEASIBLE" in summary


def test_healthy_baseline_selects_a0_monitoring(optimizer_fixture):
    """Test that when baseline risk is low, A0 (continue monitoring) is selected to prevent unnecessary disruption."""
    optimizer = optimizer_fixture["optimizer"]
    fp = optimizer_fixture["fingerprint"]
    risk_model = optimizer_fixture["risk_model"]

    # Healthy cycle
    sim = InjectionMoldingSimulator(seed=777, base_regime=RegimeType.HEALTHY)
    pipe = TelemetryPipeline()
    for _ in range(20):
        h_rec = pipe.process(sim.step())
        risk_model.predict(h_rec)

    table = optimizer.evaluate_candidates(record=h_rec, fingerprint=fp)
    assert table.baseline_risk < 0.35
    assert table.recommended_action_id == "A0"
    a0_eval = next(e for e in table.evaluations if e.candidate.action_id == "A0")
    assert a0_eval.is_selected is True


def test_evaluate_candidates_does_not_pollute_live_feature_history(optimizer_fixture):
    """Regression (hostile-review HIGH finding #1): comparing candidates for a cycle must not
    leak into the live quality-risk model's rolling feature history. Both
    InterventionOptimizer.evaluate_candidates and InterventionSurrogateModel's internal
    baseline predict() call the shared model's predict(); each unguarded call pushes the
    record into extractor.signal_history and bumps extractor.cycle_count, so repeated
    candidate comparisons would corrupt later live risk predictions with duplicate history."""
    optimizer = optimizer_fixture["optimizer"]
    fp = optimizer_fixture["fingerprint"]
    drift_record = optimizer_fixture["drift_record"]
    risk_model = optimizer_fixture["risk_model"]
    extractor = risk_model.feature_extractor

    cycle_count_before = extractor.cycle_count
    history_before = {sig: list(extractor.signal_history[sig]) for sig in extractor.CORE_SIGNALS}

    # One comparison evaluates A0 + 4 candidates against the shared live model.
    optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)

    assert extractor.cycle_count == cycle_count_before, (
        "evaluate_candidates must not advance the live model's cycle_count"
    )
    history_after = {sig: list(extractor.signal_history[sig]) for sig in extractor.CORE_SIGNALS}
    assert history_after == history_before, (
        "evaluate_candidates must not mutate the live model's rolling signal history"
    )

