"""Schemas and data models for the explicit Process Guardian State Machine (STMC-01, STMC-02)."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ProcessState(str, Enum):
    """
    The 13 canonical operational states of the Process Guardian decision loop (STMC-01).
    """
    HEALTHY = "HEALTHY"
    DRIFT_SUSPECTED = "DRIFT_SUSPECTED"
    DRIFT_CONFIRMED = "DRIFT_CONFIRMED"
    QUALITY_RISK_HIGH = "QUALITY_RISK_HIGH"
    DIAGNOSING = "DIAGNOSING"
    INTERVENTION_EVALUATION = "INTERVENTION_EVALUATION"
    ABSTAIN = "ABSTAIN"
    QC_REQUIRED = "QC_REQUIRED"
    RECOMMEND = "RECOMMEND"
    APPLIED = "APPLIED"
    RECOVERY_CHECK = "RECOVERY_CHECK"
    RELEASE = "RELEASE"
    INTERVENTION_MEMORY = "INTERVENTION_MEMORY"


class StateTransitionRecord(BaseModel):
    """Immutable audit record of a state machine transition."""
    from_state: ProcessState
    to_state: ProcessState
    cycle_index: int
    timestamp: str
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MachineContext(BaseModel):
    """
    Operational lifecycle context tracking active machine milestones and state progression.
    """
    machine_id: str = "IMM-01"
    current_state: ProcessState = ProcessState.HEALTHY

    # Milestone cycle tracking (CNTN-01..03, STMC-01)
    drift_suspected_cycle: Optional[int] = None
    drift_confirmed_cycle: Optional[int] = None
    quality_risk_high_cycle: Optional[int] = None
    intervention_recommended_cycle: Optional[int] = None
    intervention_applied_cycle: Optional[int] = None
    recovery_start_cycle: Optional[int] = None
    recovery_verified_cycle: Optional[int] = None
    release_cycle: Optional[int] = None

    # Post-intervention monitoring
    consecutive_stable_cycles: int = 0
    active_intervention: Optional[Dict[str, Any]] = None

    # Audit history
    history: List[StateTransitionRecord] = Field(default_factory=list)
