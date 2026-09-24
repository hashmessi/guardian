"""Unit tests for the explicit Process Guardian State Machine (STMC-01, STMC-02)."""

import pytest
from process_guardian.state_machine.schemas import ProcessState, MachineContext, StateTransitionRecord
from process_guardian.state_machine.engine import ProcessStateMachine


def test_state_machine_transition_lifecycle():
    """Test standard complete intervention lifecycle from healthy through verified release (STMC-01)."""
    sm = ProcessStateMachine(machine_id="IMM-01")
    assert sm.current_state == ProcessState.HEALTHY

    # 1. Healthy -> Drift Suspected
    t1 = sm.transition_to(
        to_state=ProcessState.DRIFT_SUSPECTED,
        cycle_index=420,
        timestamp="2026-09-24T10:00:00Z",
        reason="EWMA statistical breach detected on barrel_temp_z3",
    )
    assert sm.current_state == ProcessState.DRIFT_SUSPECTED
    assert sm.context.drift_suspected_cycle == 420

    # 2. Drift Suspected -> Drift Confirmed
    t2 = sm.transition_to(
        to_state=ProcessState.DRIFT_CONFIRMED,
        cycle_index=422,
        timestamp="2026-09-24T10:01:00Z",
        reason="Persistence gate confirmed 2 consecutive drift alerts",
    )
    assert sm.current_state == ProcessState.DRIFT_CONFIRMED
    assert sm.context.drift_confirmed_cycle == 422

    # 3. Drift Confirmed -> Quality Risk High
    t3 = sm.transition_to(
        to_state=ProcessState.QUALITY_RISK_HIGH,
        cycle_index=435,
        timestamp="2026-09-24T10:07:00Z",
        reason="Defect probability escalated to 85.0% (> 70% threshold)",
    )
    assert sm.current_state == ProcessState.QUALITY_RISK_HIGH
    assert sm.context.quality_risk_high_cycle == 435

    # 4. Quality Risk High -> Diagnosing
    sm.transition_to(
        to_state=ProcessState.DIAGNOSING,
        cycle_index=436,
        timestamp="2026-09-24T10:07:30Z",
        reason="Automated root cause evidence attribution initialized",
    )
    assert sm.current_state == ProcessState.DIAGNOSING

    # 5. Diagnosing -> Intervention Evaluation
    sm.transition_to(
        to_state=ProcessState.INTERVENTION_EVALUATION,
        cycle_index=441,
        timestamp="2026-09-24T10:10:00Z",
        reason="Root cause points to Zone 3; screening candidate actions A0..A4",
    )
    assert sm.current_state == ProcessState.INTERVENTION_EVALUATION

    # 6. Intervention Evaluation -> Recommend
    sm.transition_to(
        to_state=ProcessState.RECOMMEND,
        cycle_index=441,
        timestamp="2026-09-24T10:10:05Z",
        reason="High confidence (0.88 >= 0.65); candidate A1 selected",
        metadata={"action": "ADJUST barrel_temp_z3 BY -3.0°C"},
    )
    assert sm.current_state == ProcessState.RECOMMEND
    assert sm.context.intervention_recommended_cycle == 441

    # 7. Recommend -> Applied
    sm.transition_to(
        to_state=ProcessState.APPLIED,
        cycle_index=442,
        timestamp="2026-09-24T10:10:30Z",
        reason="Operator applied -3.0°C temperature offset",
        metadata={"action": "ADJUST barrel_temp_z3 BY -3.0°C"},
    )
    assert sm.current_state == ProcessState.APPLIED
    assert sm.context.intervention_applied_cycle == 442

    # 8. Applied -> Recovery Check
    sm.transition_to(
        to_state=ProcessState.RECOVERY_CHECK,
        cycle_index=443,
        timestamp="2026-09-24T10:11:00Z",
        reason="Monitoring post-intervention parameter movement and 3-cycle stability window",
    )
    assert sm.current_state == ProcessState.RECOVERY_CHECK
    assert sm.context.recovery_start_cycle == 443

    # 9. Recovery Check -> Release
    sm.transition_to(
        to_state=ProcessState.RELEASE,
        cycle_index=446,
        timestamp="2026-09-24T10:12:30Z",
        reason="Recovery verified (stability window 3/3 compliant, defect risk 14.5%)",
    )
    assert sm.current_state == ProcessState.RELEASE
    assert sm.context.release_cycle == 446

    # 10. Release -> Intervention Memory
    sm.transition_to(
        to_state=ProcessState.INTERVENTION_MEMORY,
        cycle_index=447,
        timestamp="2026-09-24T10:13:00Z",
        reason="Episode archived to audit storage",
    )
    assert sm.current_state == ProcessState.INTERVENTION_MEMORY

    # 11. Memory -> Healthy
    sm.transition_to(
        to_state=ProcessState.HEALTHY,
        cycle_index=448,
        timestamp="2026-09-24T10:13:30Z",
        reason="Resuming stationary baseline observation",
    )
    assert sm.current_state == ProcessState.HEALTHY

    # Verify audit trail
    assert len(sm.context.history) == 11


def test_state_machine_explicit_code_architecture():
    """Test guard rules, illegal transition rejections, and alternative branching (STMC-02)."""
    sm = ProcessStateMachine()

    # 1. Illegal direct transitions from HEALTHY
    assert sm.can_transition(ProcessState.APPLIED) is False
    assert sm.can_transition(ProcessState.RELEASE) is False
    with pytest.raises(ValueError, match="Illegal state machine transition"):
        sm.transition_to(
            to_state=ProcessState.RELEASE,
            cycle_index=1,
            timestamp="2026-09-24T10:00:00Z",
            reason="Illegal jump",
        )

    # 2. Test ABSTAIN branch
    sm.transition_to(ProcessState.DRIFT_SUSPECTED, 10, "2026-09-24T10:00:00Z", "Warning")
    sm.transition_to(ProcessState.DRIFT_CONFIRMED, 12, "2026-09-24T10:01:00Z", "Confirmed")
    sm.transition_to(ProcessState.QUALITY_RISK_HIGH, 15, "2026-09-24T10:02:00Z", "High risk")
    sm.transition_to(ProcessState.DIAGNOSING, 16, "2026-09-24T10:02:30Z", "Diagnosing")
    sm.transition_to(ProcessState.INTERVENTION_EVALUATION, 17, "2026-09-24T10:03:00Z", "Eval")
    
    # Low confidence triggers ABSTAIN
    sm.transition_to(
        to_state=ProcessState.ABSTAIN,
        cycle_index=18,
        timestamp="2026-09-24T10:03:30Z",
        reason="Confidence 0.52 < 0.65 threshold; withholding recommendation",
    )
    assert sm.current_state == ProcessState.ABSTAIN

    # 3. Test Failed Recovery Loop
    sm_failed = ProcessStateMachine()
    sm_failed.transition_to(ProcessState.DRIFT_SUSPECTED, 10, "2026-09-24T10:00:00Z", "Warning")
    sm_failed.transition_to(ProcessState.DRIFT_CONFIRMED, 12, "2026-09-24T10:01:00Z", "Confirmed")
    sm_failed.transition_to(ProcessState.QUALITY_RISK_HIGH, 15, "2026-09-24T10:02:00Z", "High risk")
    sm_failed.transition_to(ProcessState.DIAGNOSING, 16, "2026-09-24T10:02:30Z", "Diagnosing")
    sm_failed.transition_to(ProcessState.INTERVENTION_EVALUATION, 17, "2026-09-24T10:03:00Z", "Eval")
    sm_failed.transition_to(ProcessState.RECOMMEND, 18, "2026-09-24T10:03:30Z", "Rec")
    sm_failed.transition_to(ProcessState.APPLIED, 19, "2026-09-24T10:04:00Z", "Applied")
    sm_failed.transition_to(ProcessState.RECOVERY_CHECK, 20, "2026-09-24T10:04:30Z", "Checking")

    # Recovery fails -> transitions back to DIAGNOSING for reassessment
    assert sm_failed.can_transition(ProcessState.DIAGNOSING) is True
    sm_failed.transition_to(
        to_state=ProcessState.DIAGNOSING,
        cycle_index=28,
        timestamp="2026-09-24T10:08:30Z",
        reason="Stability window timed out after 8 cycles without recovery; re-assessing",
    )
    assert sm_failed.current_state == ProcessState.DIAGNOSING
