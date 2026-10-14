"""Explicit System State Machine Engine for Process Guardian (STMC-01, STMC-02)."""

from typing import Dict, List, Optional, Set, Any
from process_guardian.state_machine.schemas import (
    ProcessState,
    StateTransitionRecord,
    MachineContext,
)


class ProcessStateMachine:
    """
    Explicit finite state machine governing the complete intervention decision loop (STMC-01, STMC-02).
    
    HEALTHY -> DRIFT_SUSPECTED -> DRIFT_CONFIRMED -> QUALITY_RISK_HIGH -> DIAGNOSING ->
    INTERVENTION_EVALUATION -> (ABSTAIN | QC_REQUIRED | RECOMMEND) -> APPLIED ->
    RECOVERY_CHECK -> (FAILED/DIAGNOSING | VERIFIED/RELEASE) -> INTERVENTION_MEMORY -> HEALTHY
    """

    # Permitted state transition directed graph
    VALID_TRANSITIONS: Dict[ProcessState, Set[ProcessState]] = {
        ProcessState.HEALTHY: {
            ProcessState.DRIFT_SUSPECTED,
            ProcessState.DRIFT_CONFIRMED,
        },
        ProcessState.DRIFT_SUSPECTED: {
            ProcessState.DRIFT_CONFIRMED,
            ProcessState.HEALTHY,  # Transient false alarm cleared
        },
        ProcessState.DRIFT_CONFIRMED: {
            ProcessState.QUALITY_RISK_HIGH,
            ProcessState.QC_REQUIRED,
            ProcessState.HEALTHY,
        },
        ProcessState.QUALITY_RISK_HIGH: {
            ProcessState.DIAGNOSING,
        },
        ProcessState.DIAGNOSING: {
            ProcessState.INTERVENTION_EVALUATION,
            ProcessState.ABSTAIN,
        },
        ProcessState.INTERVENTION_EVALUATION: {
            ProcessState.RECOMMEND,
            ProcessState.QC_REQUIRED,
            ProcessState.ABSTAIN,
        },
        ProcessState.ABSTAIN: {
            ProcessState.HEALTHY,
            ProcessState.DIAGNOSING,  # Re-evaluating on subsequent cycles
            ProcessState.QC_REQUIRED,
        },
        ProcessState.QC_REQUIRED: {
            ProcessState.HEALTHY,  # Physical QC sample passed
            ProcessState.RECOMMEND,  # Physical QC sample failed, recommend intervention
            ProcessState.ABSTAIN,
        },
        ProcessState.RECOMMEND: {
            ProcessState.APPLIED,
            ProcessState.ABSTAIN,  # Overridden or conditions degraded
        },
        ProcessState.APPLIED: {
            ProcessState.RECOVERY_CHECK,
        },
        ProcessState.RECOVERY_CHECK: {
            ProcessState.RELEASE,  # Sustained stability verified across the required window
            ProcessState.DIAGNOSING,  # Failed recovery -> re-assess root cause
        },
        ProcessState.RELEASE: {
            ProcessState.INTERVENTION_MEMORY,
        },
        ProcessState.INTERVENTION_MEMORY: {
            ProcessState.HEALTHY,
        },
    }

    def __init__(self, machine_id: str = "IMM-01"):
        self.context = MachineContext(machine_id=machine_id)

    @property
    def current_state(self) -> ProcessState:
        return self.context.current_state

    def can_transition(self, to_state: ProcessState) -> bool:
        """Check if transition from current state to target state is legally permitted."""
        valid_targets = self.VALID_TRANSITIONS.get(self.context.current_state, set())
        return to_state in valid_targets

    def transition_to(
        self,
        to_state: ProcessState,
        cycle_index: int,
        timestamp: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateTransitionRecord:
        """
        Execute an explicit state transition with guard checks and milestone tracking (STMC-01, STMC-02).
        """
        if not self.can_transition(to_state):
            raise ValueError(
                f"Illegal state machine transition: cannot transition from "
                f"'{self.context.current_state}' to '{to_state}'"
            )

        from_state = self.context.current_state
        metadata = metadata or {}

        # Milestone cycle tracking
        if to_state == ProcessState.DRIFT_SUSPECTED and self.context.drift_suspected_cycle is None:
            self.context.drift_suspected_cycle = cycle_index
        elif to_state == ProcessState.DRIFT_CONFIRMED and self.context.drift_confirmed_cycle is None:
            self.context.drift_confirmed_cycle = cycle_index
        elif to_state == ProcessState.QUALITY_RISK_HIGH and self.context.quality_risk_high_cycle is None:
            self.context.quality_risk_high_cycle = cycle_index
        elif to_state == ProcessState.RECOMMEND and self.context.intervention_recommended_cycle is None:
            self.context.intervention_recommended_cycle = cycle_index
        elif to_state == ProcessState.APPLIED and self.context.intervention_applied_cycle is None:
            self.context.intervention_applied_cycle = cycle_index
            if "action" in metadata:
                self.context.active_intervention = metadata["action"]
        elif to_state == ProcessState.RECOVERY_CHECK and self.context.recovery_start_cycle is None:
            self.context.recovery_start_cycle = cycle_index
        elif to_state == ProcessState.RELEASE and self.context.release_cycle is None:
            self.context.release_cycle = cycle_index

        record = StateTransitionRecord(
            from_state=from_state,
            to_state=to_state,
            cycle_index=cycle_index,
            timestamp=timestamp,
            reason=reason,
            metadata=metadata,
        )

        self.context.current_state = to_state
        self.context.history.append(record)
        return record

    def reset(self, cycle_index: int = 0, timestamp: str = "") -> None:
        """Reset machine context to clean HEALTHY state."""
        machine_id = self.context.machine_id
        self.context = MachineContext(machine_id=machine_id)
