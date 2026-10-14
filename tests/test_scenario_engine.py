"""Tests for the Process Guardian Scenario Engine & Operational Validation Suite."""

import pytest
from process_guardian.scenario.registry import get_scenario_registry
from process_guardian.scenario.runner import ScenarioRunner
from process_guardian.scenario.suite import OperationalValidationSuiteRunner


def test_scenario_registry_contains_ten_scenarios():
    """Registry keeps 9 scenarios (for the validation suite); hero set is locked to 3.

    Per scope_plan.md Sec.4 the live UI shows only S06, SCN-FLIP-HUMAN-CHANNEL and
    S08. The rest back the cited "every scenario passes deterministically" claim, so
    a scenario only belongs here if it genuinely exercises what it says it does:
    SCN-04 (recipe) and SCN-05 (mold spray) were removed because the runner never
    read their override fields, making them healthy runs reported as checkpoint proofs.
    """
    registry = get_scenario_registry()
    all_scenarios = registry.list_all()
    assert len(all_scenarios) == 9

    hero_scenarios = registry.list_hero_scenarios()
    assert len(hero_scenarios) == 3
    assert {s.scenario_id for s in hero_scenarios} == {
        "SCN-06-COMPOUND", "SCN-FLIP-HUMAN-CHANNEL", "SCN-08-LOW-CONF-ABSTAIN"
    }

    ids = [s.scenario_id for s in all_scenarios]
    assert "SCN-01-THERMAL" in ids
    assert "SCN-02-PRESSURE" in ids
    assert "SCN-03-MOISTURE" in ids
    assert "SCN-06-COMPOUND" in ids
    assert "SCN-07-NORMAL-VAR" in ids
    assert "SCN-08-LOW-CONF-ABSTAIN" in ids
    assert "SCN-09-FAILED-INTERVENTION" in ids
    assert "SCN-10-RECOVERY-RELEASE" in ids
    assert "SCN-FLIP-HUMAN-CHANNEL" in ids


def test_scenario_01_thermal_drift_execution():
    """Verify Scenario 1 thermal drift closed loop and scorecard."""
    registry = get_scenario_registry()
    scn = registry.get("SCN-01-THERMAL")
    assert scn is not None

    runner = ScenarioRunner()
    # Test with shortened total_cycles for fast test execution
    test_scn = scn.model_copy(update={"total_cycles": 380, "disturbances": [
        scn.disturbances[0].model_copy(update={"start_cycle": 70})
    ]})
    summary = runner.run_scenario(test_scn)

    assert summary.total_cycles == 380
    assert len(summary.stream) == 380
    assert summary.scorecard.detection.passed is True
    assert summary.scorecard.diagnosis.passed is True
    assert summary.counterfactual.guardian_on.scrap_parts_count <= summary.counterfactual.guardian_off.scrap_parts_count
    assert summary.counterfactual.suspect_lot_reduction_pct >= 0.0


def test_scenario_02_pressure_drift_execution():
    """Verify Scenario 2 pressure drift detection and attribution."""
    registry = get_scenario_registry()
    scn = registry.get("SCN-02-PRESSURE")
    assert scn is not None

    runner = ScenarioRunner()
    test_scn = scn.model_copy(update={"total_cycles": 360, "disturbances": [
        scn.disturbances[0].model_copy(update={"start_cycle": 70})
    ]})
    summary = runner.run_scenario(test_scn)

    assert summary.scorecard.detection.passed is True
    assert summary.scorecard.diagnosis.passed is True
    assert "pressure" in summary.scorecard.diagnosis.metrics["expected_signal"]


def test_scenario_07_normal_variation_no_false_alarm():
    """Verify Scenario 7 normal variation refrains from false alarm and interventions."""
    registry = get_scenario_registry()
    scn = registry.get("SCN-07-NORMAL-VAR")
    assert scn is not None

    runner = ScenarioRunner()
    test_scn = scn.model_copy(update={"total_cycles": 150})
    summary = runner.run_scenario(test_scn)

    assert summary.scorecard.detection.passed is True
    assert summary.scorecard.intervention.passed is True
    assert summary.scorecard.detection.metrics["false_alerts"] == 0


def test_counterfactual_dual_run_identical_initial_conditions():
    """Verify Guardian OFF vs ON starts with identical seeds and disturbance profiles."""
    registry = get_scenario_registry()
    scn = registry.get("SCN-01-THERMAL")
    runner = ScenarioRunner()
    test_scn = scn.model_copy(update={"total_cycles": 100, "disturbances": [
        scn.disturbances[0].model_copy(update={"start_cycle": 50})
    ]})
    summary = runner.run_scenario(test_scn)

    stream_off = summary.counterfactual.guardian_off.stream
    stream_on = summary.counterfactual.guardian_on.stream

    # Prior to drift start cycle 50, both streams must be identical
    for c in range(45):
        assert stream_off[c].barrel_temp == stream_on[c].barrel_temp
        assert stream_off[c].injection_pressure == stream_on[c].injection_pressure


def test_scenario_flip_human_channel_persists_through_hold():
    """SCN-FLIP: the human-channel signal must dominate root-cause attribution for
    the whole QC_REQUIRED hold (cycles 150-300), not just the triggering cycle.

    Regression for the persistence bug documented in .planning/STATE.md Phase 14:
    before ClosedLoopOrchestrator remembered the active human-channel signal across
    cycles, root-cause attribution reverted to flickering between noise-driven
    sensor z-scores from cycle 151 onward, silently dropping the real cause.
    """
    registry = get_scenario_registry()
    scn = registry.get("SCN-FLIP-HUMAN-CHANNEL")
    assert scn is not None

    runner = ScenarioRunner()
    summary = runner.run_scenario(scn)

    hold_cycles = [c for c in summary.stream if c.cycle_index >= 150]
    assert all(c.dominant_signal == "human_channel" for c in hold_cycles)

    # Belt-and-suspenders: the scorecard's diagnosis pillar only reads the last
    # cycle's attribution (`root_causes_seen[-1]` in scorecard.py) and would
    # already pass via its any-cycle fallback even with a flickering hold, so the
    # strict all() check above -- not this line -- is what actually regression-
    # tests the fix.
    assert summary.stream[-1].dominant_signal == "human_channel"
    assert summary.stream[-1].state == "QC_REQUIRED"

    assert summary.scorecard.diagnosis.passed is True
    assert summary.scorecard.intervention.passed is True
    assert summary.scorecard.containment.passed is True
    assert summary.scorecard.containment.status_label == "SUSPECT_WINDOW_HELD_PENDING_PHYSICAL_VERIFICATION"


def test_operational_validation_suite_runner():
    """Verify batch runner compiles complete 10-scenario report."""
    suite_runner = OperationalValidationSuiteRunner()
    # Fast test with first 3 scenarios in registry
    report = suite_runner.run_all(use_cache=False)
    assert report.metrics.total_scenarios_evaluated == 9
    assert len(report.scorecards) == 9
    # Every registered scenario must pass: the suite backs a public claim.
    assert report.metrics.completion_rate_pct == 100.0
    assert all(sc.overall_passed for sc in report.scorecards)
