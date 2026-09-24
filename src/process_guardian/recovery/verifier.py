"""Post-intervention recovery verifier tracking parameter movement, stability windows, and quality contract compliance (RECV-01..05)."""

from typing import Optional, List
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.model import QualityRiskModel
from process_guardian.intervention.schemas import CandidateAction
from process_guardian.recovery.schemas import (
    RecoveryStatus,
    ReleaseDecision,
    RecoveryEvaluationOutput,
)


class RecoveryVerifier:
    """
    Verifies sustained process recovery following an intervention (RECV-01..05).
    
    Ensures:
    1. Parameter moved in expected direction (RECV-01)
    2. Real-time recalculation of drift and defect risk from actual telemetry (RECV-02)
    3. Mandatory stability window: requires N consecutive stable cycles within envelope (RECV-03)
    4. Quality contract compliance verification before release (RECV-04)
    5. Structured recovery status reporting (RECV-05)
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        risk_model: QualityRiskModel,
        contract: Optional[QualityContract] = None,
        required_stable_cycles: int = 3,
        max_monitoring_window: int = 8,
    ):
        self.fingerprint = fingerprint
        self.risk_model = risk_model
        self.contract = contract or QualityContract()
        self.required_stable_cycles = required_stable_cycles
        self.max_monitoring_window = max_monitoring_window

        # Active verification state
        self.is_active: bool = False
        self.intervention_record: Optional[NormalizedCycleRecord] = None
        self.applied_candidate: Optional[CandidateAction] = None
        self.risk_before: float = 0.0
        self.stability_before: float = 0.0
        self.consecutive_stable_cycles: int = 0
        self.cycles_monitored: int = 0
        self.parameter_movement_verified: bool = False
        self.current_status: RecoveryStatus = RecoveryStatus.NOT_STARTED

    def start_recovery_monitoring(
        self,
        intervention_record: NormalizedCycleRecord,
        candidate: CandidateAction,
        risk_before: float,
        stability_before: Optional[float] = None,
    ) -> None:
        """
        Initialize the post-intervention recovery verification monitoring window.
        """
        self.is_active = True
        self.intervention_record = intervention_record
        self.applied_candidate = candidate
        self.risk_before = risk_before
        self.stability_before = stability_before if stability_before is not None else 0.44
        self.consecutive_stable_cycles = 0
        self.cycles_monitored = 0
        self.parameter_movement_verified = False
        self.current_status = RecoveryStatus.IN_PROGRESS

    def evaluate_cycle(
        self,
        record: NormalizedCycleRecord,
        drift_output: Optional[DriftOutput] = None,
    ) -> RecoveryEvaluationOutput:
        """
        Evaluate an incoming post-intervention cycle against recovery criteria (RECV-01..05).
        """
        if not self.is_active or self.applied_candidate is None or self.intervention_record is None:
            return RecoveryEvaluationOutput(
                cycle_index=record.cycle_index,
                timestamp=record.timestamp,
                recovery_status=RecoveryStatus.NOT_STARTED,
                release_decision=ReleaseDecision.PENDING_VERIFICATION,
                risk_before=0.0,
                risk_after=0.0,
                stability_before=1.0,
                stability_after=1.0,
                parameter_movement_verified=False,
                target_parameter=None,
                applied_delta=0.0,
                observed_delta=0.0,
                consecutive_stable_cycles=0,
                required_stable_cycles=self.required_stable_cycles,
                stability_window_met=False,
                contract_compliant=True,
                contract_violations=[],
                summary_message="No intervention active. Standard production monitoring.",
            )

        self.cycles_monitored += 1
        cand = self.applied_candidate
        sig = cand.target_signal

        # 1. Parameter Movement Verification (RECV-01)
        applied_delta = cand.delta_value
        observed_delta = 0.0

        if sig is not None:
            curr_val = float(getattr(record, sig, 0.0))
            orig_val = float(getattr(self.intervention_record, sig, 0.0))
            observed_delta = round(curr_val - orig_val, 2)

            if applied_delta < 0:
                # Expected negative shift
                if observed_delta <= 0.40 * applied_delta:
                    self.parameter_movement_verified = True
            elif applied_delta > 0:
                # Expected positive shift
                if observed_delta >= 0.40 * applied_delta:
                    self.parameter_movement_verified = True
            else:
                self.parameter_movement_verified = True
        else:
            self.parameter_movement_verified = True

        # 2. Dynamic Telemetry & Risk Re-Evaluation (RECV-02)
        risk_out = self.risk_model.predict(record=record, contract=self.contract)
        risk_after = risk_out.risk_probability

        # Recomputed process stability index
        if drift_output:
            severity = drift_output.severity
            stability_after = round(max(0.10, min(0.98, 1.0 - severity)), 2)
        else:
            stability_after = round(max(0.10, min(0.98, 1.0 - risk_after)), 2)

        # 3. Quality Contract Compliance Check (RECV-04)
        contract_res = self.contract.evaluate(record)

        # 4. Check Operating Envelope
        in_envelope = True
        if sig and sig in self.fingerprint.operating_envelopes:
            env = self.fingerprint.operating_envelopes[sig]
            curr_val = float(getattr(record, sig, 0.0))
            in_envelope = (env.lower_limit <= curr_val <= env.upper_limit)

        # 5. Stability Window Evaluation (RECV-03)
        # Non-high risk (<= 0.45), parameter moved, inside envelope, zero defects, and contract compliant
        is_cycle_stable = (
            risk_after <= 0.45
            and self.parameter_movement_verified
            and in_envelope
            and contract_res.is_compliant
            and not record.defect_flag
        )

        if is_cycle_stable:
            self.consecutive_stable_cycles += 1
            stability_after = max(0.90, stability_after)
        else:
            # Sustained stability required: non-compliant cycle resets consecutive count
            self.consecutive_stable_cycles = 0

        stability_window_met = self.consecutive_stable_cycles >= self.required_stable_cycles

        # 6. Status & Release Decision (RECV-04, RECV-05)
        if stability_window_met and contract_res.is_compliant and risk_after < 0.35:
            self.current_status = RecoveryStatus.VERIFIED
            release_decision = ReleaseDecision.APPROVED
            summary = (
                f"Recovery verified: parameter movement confirmed ({observed_delta:+.1f}{cand.unit}), "
                f"stability sustained for {self.consecutive_stable_cycles}/{self.required_stable_cycles} cycles, "
                f"defect risk reduced from {self.risk_before * 100:.1f}% to {risk_after * 100:.1f}%. "
                f"Production release approved."
            )
        elif self.cycles_monitored >= self.max_monitoring_window:
            self.current_status = RecoveryStatus.FAILED
            release_decision = ReleaseDecision.REJECTED_QUARANTINE
            summary = (
                f"Recovery failed: stability window timeout after {self.cycles_monitored} cycles. "
                f"Parameter movement: {self.parameter_movement_verified}. "
                f"Quality contract compliant: {contract_res.is_compliant}. Quarantine production."
            )
        else:
            self.current_status = RecoveryStatus.IN_PROGRESS
            release_decision = ReleaseDecision.PENDING_VERIFICATION
            summary = (
                f"Post-intervention verification in progress: {self.consecutive_stable_cycles}/{self.required_stable_cycles} "
                f"stable cycles completed. Production held."
            )

        return RecoveryEvaluationOutput(
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            recovery_status=self.current_status,
            release_decision=release_decision,
            risk_before=self.risk_before,
            risk_after=risk_after,
            stability_before=self.stability_before,
            stability_after=stability_after,
            parameter_movement_verified=self.parameter_movement_verified,
            target_parameter=sig,
            applied_delta=applied_delta,
            observed_delta=observed_delta,
            consecutive_stable_cycles=self.consecutive_stable_cycles,
            required_stable_cycles=self.required_stable_cycles,
            stability_window_met=stability_window_met,
            contract_compliant=contract_res.is_compliant,
            contract_violations=contract_res.violations,
            summary_message=summary,
        )
