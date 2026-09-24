"""Unit tests for the post-intervention recovery verifier (RECV-01..05)."""

import pytest
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.regimes import RegimeType
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.contract import QualityContract
from process_guardian.intervention.schemas import CandidateAction, ActionType
from process_guardian.recovery.schemas import RecoveryStatus, ReleaseDecision, RecoveryEvaluationOutput
from process_guardian.recovery.verifier import RecoveryVerifier


@pytest.fixture
def recovery_fixture():
    """Setup fingerprint, trained risk model, and verifier."""
    pipeline = TelemetryPipeline()
    sim_healthy = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    healthy_records = [pipeline.process(sim_healthy.step()) for _ in range(60)]

    builder = FingerprintBuilder()
    fp = builder.fit(healthy_records)

    risk_model = QualityRiskModel(fingerprint=fp)
    verifier = RecoveryVerifier(fingerprint=fp, risk_model=risk_model, required_stable_cycles=3, max_monitoring_window=8)

    # Drifting cycle at intervention point
    sim_drift = InjectionMoldingSimulator(seed=123, base_regime=RegimeType.THERMAL_DRIFT)
    drift_records = []
    for _ in range(25):
        r = pipeline.process(sim_drift.step())
        risk_model.predict(r)
        drift_records.append(r)
    intervention_record = drift_records[-1]

    # Candidate A1 applied
    candidate_a1 = CandidateAction(
        action_id="A1",
        action_type=ActionType.TEMP_ADJUST,
        name="Reduce Zone 3 Temp",
        target_signal="barrel_temp_z3",
        delta_value=-3.0,
        unit="°C",
    )

    return {
        "fingerprint": fp,
        "risk_model": risk_model,
        "verifier": verifier,
        "pipeline": pipeline,
        "intervention_record": intervention_record,
        "candidate_a1": candidate_a1,
        "healthy_records": healthy_records,
    }


def test_parameter_movement_confirmation(recovery_fixture):
    """Verify that parameter movement in expected direction is verified (RECV-01)."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]

    # Start recovery monitoring (pre-intervention risk ~95%)
    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.95, stability_before=0.44)

    # 1. Post-intervention cycle where temperature did NOT move
    unmoved_rec = int_rec.model_copy(update={"barrel_temp_z3": int_rec.barrel_temp_z3 + 0.2})
    out1 = verifier.evaluate_cycle(unmoved_rec)
    assert out1.parameter_movement_verified is False
    assert out1.recovery_status == RecoveryStatus.IN_PROGRESS

    # 2. Post-intervention cycle where temperature dropped by 2.6°C (>= 40% of -3.0°C)
    moved_rec = int_rec.model_copy(update={
        "barrel_temp_z3": int_rec.barrel_temp_z3 - 2.6,
        "peak_pressure": 133.0,
        "part_weight": 142.4,
        "defect_flag": False,
        "sink_mark_depth": 0.0,
        "flash_observed": False,
    })
    out2 = verifier.evaluate_cycle(moved_rec)
    assert out2.parameter_movement_verified is True
    assert out2.observed_delta <= -2.5


def test_dynamic_telemetry_and_risk_recomputation(recovery_fixture):
    """Verify dynamic recomputation of quality risk and stability from post-intervention data (RECV-02)."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]
    healthy_rec = recovery_fixture["healthy_records"][-1]

    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.95)

    # Process stabilized back to healthy baseline
    stabilized_rec = healthy_rec.model_copy(update={
        "cycle_index": int_rec.cycle_index + 1,
        "timestamp": "2026-09-24T12:00:00Z",
    })
    out = verifier.evaluate_cycle(stabilized_rec)

    # RECV-02: Quality risk is dynamically recomputed and drops
    assert out.risk_after < 0.35
    assert out.risk_after < out.risk_before
    assert out.stability_after >= 0.85


def test_stability_window_enforcement(recovery_fixture):
    """Verify that recovery requires an N=3 consecutive stable cycle window, not an immediate claim (RECV-03)."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]
    healthy_rec = recovery_fixture["healthy_records"][-1]

    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.95)

    good_rec = healthy_rec.model_copy(update={
        "barrel_temp_z3": 230.2,
        "peak_pressure": 134.5,
        "part_weight": 142.5,
        "defect_flag": False,
    })

    # Cycle 1: First stable cycle -> NOT yet verified
    out1 = verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 1}))
    assert out1.consecutive_stable_cycles == 1
    assert out1.stability_window_met is False
    assert out1.recovery_status == RecoveryStatus.IN_PROGRESS
    assert out1.release_decision == ReleaseDecision.PENDING_VERIFICATION

    # Cycle 2: Second stable cycle -> Still in progress
    out2 = verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 2}))
    assert out2.consecutive_stable_cycles == 2
    assert out2.recovery_status == RecoveryStatus.IN_PROGRESS

    # Cycle 3: Transient instability spike -> Resets window to 0!
    bad_spike_rec = int_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 3, "defect_flag": True})
    out3 = verifier.evaluate_cycle(bad_spike_rec)
    assert out3.consecutive_stable_cycles == 0
    assert out3.recovery_status == RecoveryStatus.IN_PROGRESS

    # Subsequent 3 clean cycles complete the window
    verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 4}))
    verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 5}))
    out_final = verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 6}))

    # RECV-03: VERIFIED only after N=3 sustained cycles
    assert out_final.consecutive_stable_cycles == 3
    assert out_final.stability_window_met is True
    assert out_final.recovery_status == RecoveryStatus.VERIFIED
    assert out_final.release_decision == ReleaseDecision.APPROVED


def test_quality_contract_release_verification(recovery_fixture):
    """Verify Quality Contract compliance is strictly required for release approval (RECV-04)."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]
    healthy_rec = recovery_fixture["healthy_records"][-1]

    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.95)

    # 3 cycles with low risk but part weight exceeds Quality Contract tolerance (e.g. 145.2 g > 144.0 g)
    overweight_rec = healthy_rec.model_copy(update={
        "barrel_temp_z3": 230.2,
        "peak_pressure": 134.0,
        "part_weight": 145.2,  # Contract violation
        "defect_flag": True,
    })

    out = None
    for i in range(3):
        out = verifier.evaluate_cycle(overweight_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 1 + i}))

    assert out.contract_compliant is False
    assert out.recovery_status != RecoveryStatus.VERIFIED
    assert out.release_decision != ReleaseDecision.APPROVED


def test_structured_recovery_status_output(recovery_fixture):
    """Test structured output fields: risk before/after, stability before/after, recovery status, release decision (RECV-05)."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]
    healthy_rec = recovery_fixture["healthy_records"][-1]

    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.92, stability_before=0.40)

    # Run to verified recovery
    good_rec = healthy_rec.model_copy(update={
        "barrel_temp_z3": 230.0,
        "peak_pressure": 135.0,
        "part_weight": 142.5,
        "defect_flag": False,
        "sink_mark_depth": 0.0,
        "flash_observed": False,
    })

    out = None
    for i in range(3):
        out = verifier.evaluate_cycle(good_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 1 + i}))

    # RECV-05: All required fields present
    assert out.risk_before == 0.92
    assert out.risk_after < 0.35
    assert out.stability_before == 0.40
    assert out.stability_after >= 0.90
    assert out.recovery_status == RecoveryStatus.VERIFIED
    assert out.release_decision == ReleaseDecision.APPROVED
    assert "Recovery verified" in out.summary_message


def test_recovery_timeout_failure(recovery_fixture):
    """Verify that when recovery cannot be established within timeout (8 cycles), status transitions to FAILED."""
    verifier = recovery_fixture["verifier"]
    int_rec = recovery_fixture["intervention_record"]
    cand = recovery_fixture["candidate_a1"]

    verifier.start_recovery_monitoring(intervention_record=int_rec, candidate=cand, risk_before=0.95)

    # Process remains persistently bad
    stuck_bad_rec = int_rec.model_copy(update={"defect_flag": True})

    out = None
    for i in range(8):
        out = verifier.evaluate_cycle(stuck_bad_rec.model_copy(update={"cycle_index": int_rec.cycle_index + 1 + i}))

    assert out.recovery_status == RecoveryStatus.FAILED
    assert out.release_decision == ReleaseDecision.REJECTED_QUARANTINE
    assert "Recovery failed" in out.summary_message
