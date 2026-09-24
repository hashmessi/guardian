"""Closed-loop operational lifecycle orchestrator executing the complete Process Guardian decision loop.

Closed Operational Loop:
1. Ingest telemetry cycle (TelemetryPipeline)
2. Detect drift early (DriftSentinel - EWMA/CUSUM/Multivariate)
3. Predict quality contract risk and isolate root cause (QualityEngine)
4. Evaluate constrained candidate interventions (InterventionEngine)
5. Propose minimum-cost action or safely abstain (RecommendationEngine)
6. Verify sustained recovery post-intervention (RecoveryVerifier)
7. Contain affected production and quarantine suspect window (ScrapContainmentEngine)
8. Maintain explicit state and audit history (ProcessStateMachine)
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from pydantic import BaseModel, Field

from process_guardian.core.types import RegimeType
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.adapter.schemas import NormalizedCycleRecord, RawTelemetryPayload
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.detector import DriftSentinel
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.pipeline import QualityEngine
from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode
from process_guardian.root_cause.schemas import RootCauseReport
from process_guardian.intervention.pipeline import InterventionEngine
from process_guardian.intervention.schemas import (
    CandidateAction,
    InterventionRecommendation,
    InterventionComparisonTable,
)
from process_guardian.state_machine.schemas import (
    ProcessState,
    StateTransitionRecord,
)
from process_guardian.state_machine.engine import ProcessStateMachine
from process_guardian.recovery.schemas import (
    RecoveryStatus,
    ReleaseDecision,
    RecoveryEvaluationOutput,
)
from process_guardian.recovery.verifier import RecoveryVerifier
from process_guardian.containment.schemas import (
    DispositionType,
    CycleDisposition,
    ContainmentWindow,
    BatchDispositionReport,
)
from process_guardian.containment.engine import ScrapContainmentEngine


class OrchestratorCycleResult(BaseModel):
    """Unified telemetry and decision result for a single processed cycle."""
    cycle_index: int
    timestamp: str
    state: ProcessState
    record: NormalizedCycleRecord
    drift_output: DriftOutput
    risk_output: QualityRiskOutput
    root_cause_report: Optional[RootCauseReport] = None
    recommendation: Optional[InterventionRecommendation] = None
    comparison_table: Optional[InterventionComparisonTable] = None
    recovery_output: Optional[RecoveryEvaluationOutput] = None
    disposition: CycleDisposition
    transitions: List[StateTransitionRecord] = Field(default_factory=list)


class ClosedLoopOrchestrator:
    """
    Vendor-neutral closed-loop intervention engine orchestrator.
    
    Coordinates detection, diagnosis, constrained intervention optimization,
    recovery verification, scrap containment, and state audit history.
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        pipeline: Optional[TelemetryPipeline] = None,
        sentinel: Optional[DriftSentinel] = None,
        quality_engine: Optional[QualityEngine] = None,
        intervention_engine: Optional[InterventionEngine] = None,
        recovery_verifier: Optional[RecoveryVerifier] = None,
        containment_engine: Optional[ScrapContainmentEngine] = None,
        state_machine: Optional[ProcessStateMachine] = None,
        machine_id: str = "IMM-01",
        auto_apply_intervention: bool = True,
        required_stable_cycles: int = 3,
        intervention_trigger_risk_threshold: float = 0.50,
    ):
        self.machine_id = machine_id
        self.fingerprint = fingerprint
        self.pipeline = pipeline or TelemetryPipeline()
        self.sentinel = sentinel or DriftSentinel(fingerprint=fingerprint, min_warmup_cycles=10, persistence_required=2)
        self.quality_engine = quality_engine or QualityEngine(fingerprint=fingerprint)
        self.intervention_engine = intervention_engine or InterventionEngine(risk_model=self.quality_engine.risk_model)
        self.recovery_verifier = recovery_verifier or RecoveryVerifier(
            fingerprint=fingerprint,
            risk_model=self.quality_engine.risk_model,
            required_stable_cycles=required_stable_cycles,
        )
        self.containment_engine = containment_engine or ScrapContainmentEngine(machine_id=machine_id)
        self.state_machine = state_machine or ProcessStateMachine(machine_id=machine_id)
        self.auto_apply_intervention = auto_apply_intervention
        self.intervention_trigger_risk_threshold = intervention_trigger_risk_threshold

        # Historical state tracking
        self.cycle_records: List[NormalizedCycleRecord] = []
        self.risk_history: Dict[int, float] = {}
        self.results_history: List[OrchestratorCycleResult] = []
        self.pending_recommendation: Optional[Tuple[InterventionRecommendation, InterventionComparisonTable]] = None
        self.applied_action: Optional[CandidateAction] = None

    @property
    def current_state(self) -> ProcessState:
        """Current operational state of the machine."""
        return self.state_machine.current_state

    def step(self, raw_or_record: Union[Dict[str, Any], RawTelemetryPayload, NormalizedCycleRecord]) -> OrchestratorCycleResult:
        """
        Execute one operational cycle step through the complete closed decision loop.
        """
        # 1. Normalize Telemetry
        if isinstance(raw_or_record, NormalizedCycleRecord):
            record = raw_or_record
        elif isinstance(raw_or_record, RawTelemetryPayload):
            record = self.pipeline.process(raw_or_record.model_dump())
        else:
            record = self.pipeline.process(raw_or_record)

        self.cycle_records.append(record)
        cycle_idx = record.cycle_index
        timestamp = record.timestamp
        step_transitions: List[StateTransitionRecord] = []

        # 2. Early Drift Detection
        drift_out = self.sentinel.evaluate(record)

        # 3. Quality Contract Risk Prediction & Root Cause Isolation
        risk_out, root_out = self.quality_engine.evaluate_cycle(record, drift_output=drift_out)
        self.risk_history[cycle_idx] = risk_out.risk_probability

        # Decision outputs for this cycle
        recommendation: Optional[InterventionRecommendation] = None
        comparison_table: Optional[InterventionComparisonTable] = None
        recovery_output: Optional[RecoveryEvaluationOutput] = None

        # 4. State Machine & Closed-Loop Decision Engine
        current = self.state_machine.current_state

        # Case A: Machine is in HEALTHY baseline monitoring
        if current == ProcessState.HEALTHY:
            if drift_out.drift:
                t = self.state_machine.transition_to(
                    to_state=ProcessState.DRIFT_CONFIRMED,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason=f"Persistent drift confirmed (severity {drift_out.severity:.2f})",
                    metadata={"signals": drift_out.signals},
                )
                step_transitions.append(t)
                self.containment_engine.record_drift_detection(cycle_idx)
            elif drift_out.severity > 0.30:
                t = self.state_machine.transition_to(
                    to_state=ProcessState.DRIFT_SUSPECTED,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason=f"Potential drift deviation detected (severity {drift_out.severity:.2f})",
                    metadata={"signals": drift_out.signals},
                )
                step_transitions.append(t)

        # Case B: Machine has suspected drift
        elif current == ProcessState.DRIFT_SUSPECTED:
            if drift_out.drift:
                t = self.state_machine.transition_to(
                    to_state=ProcessState.DRIFT_CONFIRMED,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Drift confirmed across persistent observations",
                    metadata={"signals": drift_out.signals},
                )
                step_transitions.append(t)
                self.containment_engine.record_drift_detection(cycle_idx)
            elif drift_out.severity < 0.20:
                t = self.state_machine.transition_to(
                    to_state=ProcessState.HEALTHY,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Transient deviation cleared; baseline returned to normal",
                )
                step_transitions.append(t)

        # Re-fetch state after possible transitions above
        current = self.state_machine.current_state

        # Case C: Drift is confirmed -> Check Quality Risk escalation
        if current == ProcessState.DRIFT_CONFIRMED:
            if (
                risk_out.risk_state == RiskState.HIGH
                or risk_out.risk_probability >= self.intervention_trigger_risk_threshold
            ):
                # 1. Escalate to Quality Risk High
                t1 = self.state_machine.transition_to(
                    to_state=ProcessState.QUALITY_RISK_HIGH,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason=f"Quality risk probability elevated to {risk_out.risk_probability * 100:.1f}%",
                    metadata={"risk_state": risk_out.risk_state.value},
                )
                step_transitions.append(t1)

                # 2. Enter Diagnosing
                t2 = self.state_machine.transition_to(
                    to_state=ProcessState.DIAGNOSING,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Isolating physical root cause and drift contributors",
                    metadata={"likely_contributors": [c.signal_name for c in root_out.contributors] if root_out else []},
                )
                step_transitions.append(t2)

                # 3. Enter Intervention Evaluation
                t3 = self.state_machine.transition_to(
                    to_state=ProcessState.INTERVENTION_EVALUATION,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Generating and evaluating candidate corrective interventions",
                )
                step_transitions.append(t3)

                # 4. Evaluate Interventions
                rec, table = self.intervention_engine.evaluate(
                    record=record,
                    fingerprint=self.fingerprint,
                    risk_output=risk_out,
                    drift_output=drift_out,
                    root_cause_report=root_out,
                )
                recommendation = rec
                comparison_table = table
                self.pending_recommendation = (rec, table)

                # Check outcome: Abstain, QC Sample, or Recommend Action
                if rec.is_abstain:
                    t4 = self.state_machine.transition_to(
                        to_state=ProcessState.ABSTAIN,
                        cycle_index=cycle_idx,
                        timestamp=timestamp,
                        reason=rec.abstain_reason or "Low epistemic confidence - abstaining from action",
                    )
                    step_transitions.append(t4)
                elif rec.operator_mode == "REQUEST_QC_SAMPLE":
                    t4 = self.state_machine.transition_to(
                        to_state=ProcessState.QC_REQUIRED,
                        cycle_index=cycle_idx,
                        timestamp=timestamp,
                        reason="Borderline risk confidence - physical QC sample requested",
                    )
                    step_transitions.append(t4)
                else:
                    t4 = self.state_machine.transition_to(
                        to_state=ProcessState.RECOMMEND,
                        cycle_index=cycle_idx,
                        timestamp=timestamp,
                        reason=f"Recommended minimum effective intervention {table.recommended_action_id}: {rec.action}",
                    )
                    step_transitions.append(t4)

                    # Auto-apply if configured
                    if self.auto_apply_intervention:
                        applied_transitions = self._apply_recommended_action(rec, table, record)
                        step_transitions.extend(applied_transitions)

        # Case D: In RECOVERY_CHECK -> Monitor post-intervention recovery
        elif current == ProcessState.RECOVERY_CHECK:
            recovery_output = self.recovery_verifier.evaluate_cycle(record, drift_output=drift_out)

            if recovery_output.release_decision == ReleaseDecision.APPROVED:
                # 1. Recovery Verified & Release
                t_rel = self.state_machine.transition_to(
                    to_state=ProcessState.RELEASE,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Post-intervention stability criteria satisfied. Production released.",
                    metadata={"consecutive_stable_cycles": recovery_output.consecutive_stable_cycles},
                )
                step_transitions.append(t_rel)

                # Record verified recovery in scrap containment
                self.containment_engine.record_recovery_verified(
                    recovery_cycle=cycle_idx,
                    release_cycle=cycle_idx + 1,
                )

                # 2. Transition to Intervention Memory
                t_mem = self.state_machine.transition_to(
                    to_state=ProcessState.INTERVENTION_MEMORY,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Logging verified intervention parameters to persistent memory",
                )
                step_transitions.append(t_mem)

                # 3. Reset drift sentinel history for new stable operating baseline
                self.sentinel.reset()

                # 4. Return to Healthy baseline
                t_health = self.state_machine.transition_to(
                    to_state=ProcessState.HEALTHY,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason="Machine restored to stationary healthy baseline monitoring",
                )
                step_transitions.append(t_health)

            elif (
                recovery_output.release_decision == ReleaseDecision.REJECTED_QUARANTINE
                or recovery_output.recovery_status == RecoveryStatus.FAILED
            ):
                # Recovery failed or timed out -> Re-assess root cause / escalate
                t_fail = self.state_machine.transition_to(
                    to_state=ProcessState.DIAGNOSING,
                    cycle_index=cycle_idx,
                    timestamp=timestamp,
                    reason=f"Recovery verification failed: {recovery_output.summary_message}. Re-assessing root cause.",
                )
                step_transitions.append(t_fail)

        # 5. Cycle Scrap Disposition
        disposition = self.containment_engine.disposition_cycle(
            cycle_index=cycle_idx,
            defect_risk=risk_out.risk_probability,
            defect_flag=record.defect_flag,
            timestamp=timestamp,
        )

        step_result = OrchestratorCycleResult(
            cycle_index=cycle_idx,
            timestamp=timestamp,
            state=self.state_machine.current_state,
            record=record,
            drift_output=drift_out,
            risk_output=risk_out,
            root_cause_report=root_out,
            recommendation=recommendation,
            comparison_table=comparison_table,
            recovery_output=recovery_output,
            disposition=disposition,
            transitions=step_transitions,
        )

        self.results_history.append(step_result)
        return step_result

    def _apply_recommended_action(
        self,
        recommendation: InterventionRecommendation,
        comparison_table: InterventionComparisonTable,
        record: NormalizedCycleRecord,
    ) -> List[StateTransitionRecord]:
        """Apply the selected candidate intervention and initialize recovery verification."""
        transitions: List[StateTransitionRecord] = []
        
        # Locate the selected candidate
        selected_eval = next(
            (ev for ev in comparison_table.evaluations if ev.is_selected),
            comparison_table.evaluations[0] if comparison_table.evaluations else None,
        )
        if not selected_eval:
            return transitions

        candidate = selected_eval.candidate
        self.applied_action = candidate

        # Transition RECOMMEND -> APPLIED
        t_app = self.state_machine.transition_to(
            to_state=ProcessState.APPLIED,
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            reason=f"Intervention {candidate.action_id} applied: {candidate.target_signal or candidate.name} {candidate.delta_value:+.1f}{candidate.unit}",
            metadata={"candidate": candidate.model_dump()},
        )
        transitions.append(t_app)

        # Record intervention cycle in containment engine
        self.containment_engine.record_intervention(record.cycle_index)

        # Initialize Recovery Verifier
        self.recovery_verifier.start_recovery_monitoring(
            intervention_record=record,
            candidate=candidate,
            risk_before=selected_eval.pre_intervention_risk,
            stability_before=round(1.0 - selected_eval.pre_intervention_risk, 2),
        )

        # Transition APPLIED -> RECOVERY_CHECK
        t_recov = self.state_machine.transition_to(
            to_state=ProcessState.RECOVERY_CHECK,
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            reason="Monitoring post-intervention parameter stabilization and cooling window",
        )
        transitions.append(t_recov)

        return transitions

    def manual_apply_intervention(
        self,
        candidate: CandidateAction,
        record: NormalizedCycleRecord,
        risk_before: float,
    ) -> List[StateTransitionRecord]:
        """Manually trigger application of an intervention by operator authorization."""
        if self.state_machine.current_state != ProcessState.RECOMMEND:
            raise ValueError(
                f"Cannot apply intervention in state {self.state_machine.current_state}. Must be in RECOMMEND."
            )

        self.applied_action = candidate
        transitions: List[StateTransitionRecord] = []

        t_app = self.state_machine.transition_to(
            to_state=ProcessState.APPLIED,
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            reason=f"Operator manually applied intervention {candidate.action_id}",
            metadata={"candidate": candidate.model_dump()},
        )
        transitions.append(t_app)
        self.containment_engine.record_intervention(record.cycle_index)

        self.recovery_verifier.start_recovery_monitoring(
            intervention_record=record,
            candidate=candidate,
            risk_before=risk_before,
        )

        t_recov = self.state_machine.transition_to(
            to_state=ProcessState.RECOVERY_CHECK,
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            reason="Monitoring recovery window after manual operator application",
        )
        transitions.append(t_recov)
        return transitions

    def get_containment_report(self) -> BatchDispositionReport:
        """Generate complete production batch disposition report."""
        return self.containment_engine.generate_disposition_report(
            cycles=self.cycle_records,
            risk_map=self.risk_history,
        )

    def get_containment_window(self) -> ContainmentWindow:
        """Get the current suspect production containment window boundaries."""
        return self.containment_engine.get_containment_window()

    def get_state_transition_history(self) -> List[StateTransitionRecord]:
        """Get complete sequential audit log of all state machine transitions."""
        return self.state_machine.context.history

    def get_summary(self) -> Dict[str, Any]:
        """Summarize current orchestrator execution status and metrics."""
        window = self.get_containment_window()
        return {
            "machine_id": self.machine_id,
            "current_state": self.state_machine.current_state.value,
            "total_cycles_processed": len(self.cycle_records),
            "drift_detected_cycle": window.suspect_start_cycle,
            "last_known_good_cycle": window.last_known_good_cycle,
            "intervention_cycle": window.intervention_cycle,
            "recovery_cycle": window.recovery_cycle,
            "release_cycle": window.release_cycle,
            "suspect_cycles": window.suspect_cycle_count,
            "total_transitions": len(self.state_machine.context.history),
        }
