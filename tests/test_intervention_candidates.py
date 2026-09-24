"""Unit tests for candidate action generation and multi-constraint boundary verification (INTV-01, INTV-02)."""

import pytest
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.regimes import RegimeType
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.intervention.schemas import ActionType, CandidateAction, ConstraintCheckResult
from process_guardian.intervention.candidates import CandidateGenerator, ConstraintChecker


@pytest.fixture
def baseline_fixture():
    """Build baseline fingerprint and sample cycle records."""
    pipeline = TelemetryPipeline()
    sim_healthy = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    healthy_records = [pipeline.process(sim_healthy.step()) for _ in range(60)]

    builder = FingerprintBuilder()
    fp = builder.fit(healthy_records)

    # Generate a cycle with early thermal drift (detected early before scrap)
    sim_drift = InjectionMoldingSimulator(seed=123, base_regime=RegimeType.THERMAL_DRIFT)
    drift_records = [pipeline.process(sim_drift.step()) for _ in range(15)]
    drift_record = drift_records[-1]

    return {
        "fingerprint": fp,
        "healthy_record": healthy_records[-1],
        "drift_record": drift_record,
    }


def test_candidate_action_generation(baseline_fixture):
    """Test candidate action generation outputs at least 5 structured operational candidates (INTV-01)."""
    fp = baseline_fixture["fingerprint"]
    drift_record = baseline_fixture["drift_record"]

    generator = CandidateGenerator()
    candidates = generator.generate_candidates(drift_record, fp)

    # INTV-01: System evaluates at least 4 candidate actions (A0..A4)
    assert len(candidates) >= 5
    action_ids = [c.action_id for c in candidates]
    assert "A0" in action_ids
    assert "A1" in action_ids
    assert "A2" in action_ids
    assert "A3" in action_ids
    assert "A4" in action_ids

    # A0 must be continue monitoring with 0 cost and disruption
    a0 = next(c for c in candidates if c.action_id == "A0")
    assert a0.action_type == ActionType.DO_NOTHING
    assert a0.target_signal is None
    assert a0.delta_value == 0.0
    assert a0.cost_weight == 0.0
    assert a0.disruption_weight == 0.0

    # A1 must target barrel_temp_z3 with negative delta when drifted high
    a1 = next(c for c in candidates if c.action_id == "A1")
    assert a1.action_type == ActionType.TEMP_ADJUST
    assert a1.target_signal == "barrel_temp_z3"
    assert a1.delta_value < 0.0
    assert abs(a1.delta_value) <= 3.0  # Max step limit

    # A2 must target hold_pressure with bounded delta
    a2 = next(c for c in candidates if c.action_id == "A2")
    assert a2.action_type == ActionType.PRESSURE_ADJUST
    assert a2.target_signal == "hold_pressure"
    assert abs(a2.delta_value) <= 6.0

    # A3 must target cooling_time
    a3 = next(c for c in candidates if c.action_id == "A3")
    assert a3.action_type == ActionType.CYCLE_TIME_ADJUST
    assert a3.target_signal == "cooling_time"
    assert abs(a3.delta_value) <= 2.0

    # A4 must target material_moisture
    a4 = next(c for c in candidates if c.action_id == "A4")
    assert a4.action_type == ActionType.MATERIAL_INSPECT_PURGE
    assert a4.cost_weight > 0.50
    assert a4.disruption_weight > 0.50


def test_multi_constraint_boundary_checks(baseline_fixture):
    """Test multi-constraint verification against safety, recipe, envelope, step, and direction bounds (INTV-02)."""
    fp = baseline_fixture["fingerprint"]
    drift_record = baseline_fixture["drift_record"]
    checker = ConstraintChecker()

    # 1. Normal valid candidate opposing drift
    valid_candidate = CandidateAction(
        action_id="A1",
        action_type=ActionType.TEMP_ADJUST,
        name="Valid Thermal Reduction",
        target_signal="barrel_temp_z3",
        delta_value=-2.5,
        unit="°C",
    )
    res = checker.check_constraints(valid_candidate, drift_record, fp)
    assert res.is_feasible is True
    assert res.safety_ok is True
    assert res.recipe_ok is True
    assert res.envelope_ok is True
    assert res.step_ok is True
    assert res.direction_ok is True
    assert len(res.violations) == 0

    # 2. Exceeding max permitted step delta (e.g. -5.0°C when limit is 3.0°C)
    excessive_step_candidate = CandidateAction(
        action_id="A1_BAD_STEP",
        action_type=ActionType.TEMP_ADJUST,
        name="Excessive Thermal Step",
        target_signal="barrel_temp_z3",
        delta_value=-5.0,
        unit="°C",
    )
    res_step = checker.check_constraints(excessive_step_candidate, drift_record, fp)
    assert res_step.is_feasible is False
    assert res_step.step_ok is False
    assert any("Max Step Delta" in v for v in res_step.violations)

    # 3. Violating recipe limits (e.g. lowering temp so far it breaches minimum recipe tolerance)
    out_of_recipe_candidate = CandidateAction(
        action_id="A1_BAD_RECIPE",
        action_type=ActionType.TEMP_ADJUST,
        name="Breaches Recipe Floor",
        target_signal="barrel_temp_z3",
        delta_value=-20.0,
        unit="°C",
    )
    res_recipe = checker.check_constraints(out_of_recipe_candidate, drift_record, fp)
    assert res_recipe.is_feasible is False
    assert res_recipe.recipe_ok is False

    # 4. Violating physical machine safety limits
    extreme_pressure_candidate = CandidateAction(
        action_id="A2_UNSAFE",
        action_type=ActionType.PRESSURE_ADJUST,
        name="Unsafe Extreme Pressure",
        target_signal="hold_pressure",
        delta_value=120.0,
        unit="bar",
    )
    res_safety = checker.check_constraints(extreme_pressure_candidate, drift_record, fp)
    assert res_safety.is_feasible is False
    assert res_safety.safety_ok is False
    assert any("Safety Limits" in v for v in res_safety.violations)

    # 5. Violating directional policy (adding heat when temperature is already drifted high)
    wrong_direction_candidate = CandidateAction(
        action_id="A1_WRONG_DIR",
        action_type=ActionType.TEMP_ADJUST,
        name="Exacerbate Thermal Drift",
        target_signal="barrel_temp_z3",
        delta_value=+2.5,
        unit="°C",
    )
    res_dir = checker.check_constraints(wrong_direction_candidate, drift_record, fp)
    assert res_dir.is_feasible is False
    assert res_dir.direction_ok is False
    assert any("Directional Policy" in v for v in res_dir.violations)


def test_candidate_checks_across_all_types_and_severe_drift(baseline_fixture):
    """Test constraint checking across all candidate types (A0..A4) and extreme drift breach."""
    fp = baseline_fixture["fingerprint"]
    drift_record = baseline_fixture["drift_record"]
    generator = CandidateGenerator()
    checker = ConstraintChecker()

    candidates = generator.generate_candidates(drift_record, fp)
    for cand in candidates:
        res = checker.check_constraints(cand, drift_record, fp)
        assert isinstance(res, ConstraintCheckResult)
        assert isinstance(res.is_feasible, bool)

    # Extreme out-of-envelope drift scenario
    sim_extreme = InjectionMoldingSimulator(seed=999, base_regime=RegimeType.THERMAL_DRIFT)
    pipe = TelemetryPipeline()
    extreme_records = [pipe.process(sim_extreme.step()) for _ in range(50)]
    extreme_record = extreme_records[-1]

    # Action proposing positive step when already drifted high (moves further away from envelope)
    step_candidate = CandidateAction(
        action_id="A1",
        action_type=ActionType.TEMP_ADJUST,
        name="Move Away From Envelope",
        target_signal="barrel_temp_z3",
        delta_value=+2.0,
        unit="°C",
    )
    res_extreme = checker.check_constraints(step_candidate, extreme_record, fp)
    assert res_extreme.envelope_ok is False
    assert res_extreme.is_feasible is False
    assert any("Fingerprint Envelope" in v for v in res_extreme.violations)
