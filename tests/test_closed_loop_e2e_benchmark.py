"""End-to-End Closed-Loop Operational Decision Loop Benchmark (Phases 1-5 Integration).

Tests the full closed loop:
1. Early Drift Detection (Phase 2 - EWMA/CUSUM/Multivariate)
2. Quality Risk Prediction & Root Cause Isolation (Phase 3 - Calibrated XGBoost/LightGBM)
3. Constrained Intervention Optimization (Phase 4 - Multi-candidate ranking, surrogate risk)
4. Minimum-Cost Action Recommendation (Phase 4 - 7-field contract, safety gate)
5. Post-Intervention Recovery Verification (Phase 5 - Parameter movement, 3-cycle cooling window)
6. Scrap Containment & Batch Disposition (Phase 5 - Suspect window quarantine, zero uncontained scrap)
7. Explicit Finite State Machine (Phase 5 - Strict graph transitions, full audit trail)
"""

import pytest
from process_guardian.core.types import RegimeType
from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.quality.pipeline import QualityEngine
from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode
from process_guardian.intervention.pipeline import InterventionEngine
from process_guardian.intervention.schemas import CandidateAction
from process_guardian.state_machine.schemas import ProcessState
from process_guardian.recovery.schemas import RecoveryStatus, ReleaseDecision
from process_guardian.recovery.verifier import RecoveryVerifier
from process_guardian.containment.schemas import DispositionType
from process_guardian.containment.engine import ScrapContainmentEngine
from process_guardian.lifecycle import ClosedLoopOrchestrator


def _create_trained_orchestrator(machine_id: str = "IMM-01", auto_apply: bool = True):
    """Helper to train baseline fingerprint and instantiate the complete closed-loop orchestrator."""
    sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=42)
    pipe_base = TelemetryPipeline()
    base_records = [pipe_base.process(sim_base.step()) for _ in range(60)]
    fingerprint = FingerprintBuilder().fit(base_records)

    orchestrator = ClosedLoopOrchestrator(
        fingerprint=fingerprint,
        machine_id=machine_id,
        auto_apply_intervention=auto_apply,
        required_stable_cycles=3,
        intervention_trigger_risk_threshold=0.50,
    )
    return orchestrator, fingerprint


def test_full_primary_demo_scenario_closed_loop():
    """
    Execute the entire 10-step primary demo scenario (cycles 1 to 450) and verify the closed decision loop:
    - Normal baseline operation (Cycles 1-419) -> HEALTHY
    - Injected thermal drift (Cycles 420-440) -> DRIFT_CONFIRMED
    - Quality contract risk elevation (Cycle 441) -> QUALITY_RISK_HIGH -> DIAGNOSING -> INTERVENTION_EVALUATION -> RECOMMEND -> APPLIED -> RECOVERY_CHECK
    - Simulated physical intervention executed (-3.0°C zone 3) -> observed delta verified
    - Sustained recovery across 3-cycle cooling window (Cycles 442-444) -> RELEASE -> INTERVENTION_MEMORY -> HEALTHY
    - Scrap containment report: pre-drift released, suspect window quarantined, post-recovery released.
    """
    orchestrator, _ = _create_trained_orchestrator(auto_apply=True)
    sim = build_demo_scenario(seed=42)

    states_visited = set()
    recommendation_generated = None
    table_generated = None
    release_cycle = None

    # Step through cycles 1 to 450
    for c in range(1, 451):
        raw = sim.step()
        result = orchestrator.step(raw)
        states_visited.add(result.state)

        if result.recommendation:
            recommendation_generated = result.recommendation
            table_generated = result.comparison_table

        if result.recovery_output and result.recovery_output.release_decision == ReleaseDecision.APPROVED:
            release_cycle = c

    # 1. State Machine Transitions Coverage
    assert ProcessState.HEALTHY in states_visited
    assert ProcessState.DRIFT_CONFIRMED in states_visited
    assert ProcessState.RECOVERY_CHECK in states_visited

    # At completion of demo scenario, machine must have safely returned to HEALTHY baseline
    assert orchestrator.current_state == ProcessState.HEALTHY

    # Verify audit history
    audit_history = orchestrator.get_state_transition_history()
    assert len(audit_history) >= 8

    # Verify chronological sequence in audit history
    expected_sequence = [
        ProcessState.HEALTHY,
        ProcessState.DRIFT_CONFIRMED,
        ProcessState.QUALITY_RISK_HIGH,
        ProcessState.DIAGNOSING,
        ProcessState.INTERVENTION_EVALUATION,
        ProcessState.RECOMMEND,
        ProcessState.APPLIED,
        ProcessState.RECOVERY_CHECK,
        ProcessState.RELEASE,
        ProcessState.INTERVENTION_MEMORY,
        ProcessState.HEALTHY,
    ]
    actual_states = [audit_history[0].from_state] + [t.to_state for t in audit_history]
    assert actual_states == expected_sequence

    # 2. Recommendation Contract & Constraint Validation (Phase 4 integration)
    assert recommendation_generated is not None
    assert recommendation_generated.operator_mode == "RECOMMEND_ACTION"
    assert "barrel_temp_z3" in recommendation_generated.action
    assert "-3.0°C" in recommendation_generated.action or "-2." in recommendation_generated.action
    assert len(recommendation_generated.why) > 10
    assert len(recommendation_generated.evidence) > 5
    assert len(recommendation_generated.expected_effect) > 10
    assert "within 3 cycles" in recommendation_generated.recovery_check

    assert table_generated is not None
    assert table_generated.recommended_action_id == "A1"
    a1_eval = next(ev for ev in table_generated.evaluations if ev.candidate.action_id == "A1")
    assert a1_eval.is_selected is True
    assert a1_eval.constraint_check.is_feasible is True
    assert a1_eval.risk_reduction > 0.30

    # 3. Post-Intervention Recovery Verification (Phase 5 RECV-01..05)
    assert release_cycle == 444
    assert orchestrator.recovery_verifier.current_status == RecoveryStatus.VERIFIED
    assert orchestrator.recovery_verifier.parameter_movement_verified is True
    assert orchestrator.recovery_verifier.consecutive_stable_cycles >= 3

    # 4. Scrap Containment & Batch Disposition (Phase 5 CNTN-01..04)
    containment_window = orchestrator.get_containment_window()
    assert containment_window.last_known_good_cycle == 431
    assert containment_window.suspect_start_cycle == 432
    assert containment_window.suspect_end_cycle == 444
    assert containment_window.suspect_cycle_count == 13

    report = orchestrator.get_containment_report()
    assert report.total_cycles_evaluated == 450
    assert report.released_pre_drift_count == 431
    assert report.quarantine_suspect_count == 13
    assert report.released_post_recovery_count == 6  # Cycles 445..450

    # Strict isolation: 0 pre-drift parts quarantined, only suspect window quarantined
    assert report.released_pre_drift_count + report.quarantine_suspect_count + report.released_post_recovery_count == 450
    scrap_reduction_percentage = ((report.total_cycles_evaluated - report.quarantine_suspect_count) / report.total_cycles_evaluated) * 100.0
    assert scrap_reduction_percentage > 95.0  # Saves ~97.1% of parts from blind scrapping
    assert "Release 431 pre-drift cycles" in report.disposition_summary or "quarantine" in report.disposition_summary.lower()


def test_closed_loop_low_confidence_abstention():
    """
    Verify epistemic abstention gate inside the closed-loop orchestrator:
    When model confidence is below safety threshold (0.65), system transitions to ABSTAIN
    rather than blindly executing an intervention.
    """
    orchestrator, _ = _create_trained_orchestrator(auto_apply=True)
    orchestrator.intervention_engine.min_confidence_threshold = 0.99  # Force abstention due to high bar

    sim = build_demo_scenario(seed=42)

    # Run until cycle 441 (when quality risk spikes)
    for c in range(1, 442):
        raw = sim.step()
        res = orchestrator.step(raw)

    # Machine must enter ABSTAIN state due to confidence gate
    assert orchestrator.current_state == ProcessState.ABSTAIN
    history = orchestrator.get_state_transition_history()
    to_states = [t.to_state for t in history]
    assert ProcessState.ABSTAIN in to_states
    assert ProcessState.RECOMMEND not in to_states
    assert ProcessState.APPLIED not in to_states


def test_closed_loop_recovery_failure_and_reassessment():
    """
    Verify that if recovery verification fails (e.g. parameter failed to stabilize or defect occurred),
    the state machine transitions back to DIAGNOSING to re-assess root cause or escalate.
    """
    orchestrator, _ = _create_trained_orchestrator(auto_apply=True)
    sim = build_demo_scenario(seed=42)

    # Step up to cycle 441 when intervention is applied and RECOVERY_CHECK is entered
    for c in range(1, 442):
        raw = sim.step()
        res = orchestrator.step(raw)

    assert orchestrator.current_state == ProcessState.RECOVERY_CHECK

    # Force recovery verifier timeout/failure by exceeding monitoring window
    orchestrator.recovery_verifier.cycles_monitored = orchestrator.recovery_verifier.max_monitoring_window

    # Step one more cycle to trigger verifier failure check
    raw_next = sim.step()
    res_next = orchestrator.step(raw_next)

    # Must transition from RECOVERY_CHECK back to DIAGNOSING upon recovery failure
    assert orchestrator.current_state == ProcessState.DIAGNOSING
    history = orchestrator.get_state_transition_history()
    reassess_transition = next((t for t in history if t.from_state == ProcessState.RECOVERY_CHECK), None)
    assert reassess_transition is not None
    assert reassess_transition.to_state == ProcessState.DIAGNOSING
    assert "Recovery verification failed" in reassess_transition.reason


def test_closed_loop_manual_operator_mode():
    """
    Verify that when auto_apply_intervention=False, orchestrator pauses at RECOMMEND
    requiring manual operator authorization before entering RECOVERY_CHECK.
    """
    orchestrator, _ = _create_trained_orchestrator(auto_apply=False)
    sim = build_demo_scenario(seed=42)

    recommendation_result = None

    # Step until recommendation is issued (cycle 441)
    for c in range(1, 442):
        raw = sim.step()
        res = orchestrator.step(raw)
        if res.recommendation and res.state == ProcessState.RECOMMEND:
            recommendation_result = res
            break

    assert orchestrator.current_state == ProcessState.RECOMMEND
    assert recommendation_result is not None
    assert recommendation_result.comparison_table.recommended_action_id == "A1"

    # Operator reviews recommendation and authorizes manual application
    rec = recommendation_result.recommendation
    table = recommendation_result.comparison_table
    selected_cand = next(ev.candidate for ev in table.evaluations if ev.is_selected)

    orchestrator.manual_apply_intervention(
        candidate=selected_cand,
        record=recommendation_result.record,
        risk_before=0.95,
    )

    assert orchestrator.current_state == ProcessState.RECOVERY_CHECK

    # Continue running through recovery
    for c in range(442, 450):
        raw = sim.step()
        res = orchestrator.step(raw)
        if res.state == ProcessState.HEALTHY:
            break

    assert orchestrator.current_state == ProcessState.HEALTHY
