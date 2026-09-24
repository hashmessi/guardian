"""Schemas and data models for post-intervention recovery verification (RECV-01..05)."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RecoveryStatus(str, Enum):
    """Categorical recovery state following an intervention."""
    NOT_STARTED = "NOT_STARTED"         # No intervention active
    IN_PROGRESS = "IN_PROGRESS"         # Intervention applied, evaluating stability window
    VERIFIED = "VERIFIED"               # Sustained stability window confirmed, contract compliant
    FAILED = "FAILED"                   # Stability window not met, timeout, or parameter didn't move


class ReleaseDecision(str, Enum):
    """Production release authorization decision (RECV-04, RECV-05)."""
    PENDING_VERIFICATION = "PENDING_VERIFICATION"   # Production held while stability evaluated
    APPROVED = "APPROVED"                           # Recovery verified, release production
    REJECTED_QUARANTINE = "REJECTED_QUARANTINE"     # Recovery failed, quarantine production


class RecoveryEvaluationOutput(BaseModel):
    """
    Structured recovery status output fulfilling requirement RECV-05.
    
    Contains risk before/after, stability before/after, parameter movement,
    recovery status, and release decision.
    """
    cycle_index: int = Field(..., description="Current evaluated cycle index")
    timestamp: str = Field(..., description="Evaluation timestamp")
    
    recovery_status: RecoveryStatus = Field(..., description="Overall recovery verification status")
    release_decision: ReleaseDecision = Field(..., description="Formal production release disposition")
    
    risk_before: float = Field(..., ge=0.0, le=1.0, description="Quality defect risk prior to intervention")
    risk_after: float = Field(..., ge=0.0, le=1.0, description="Recomputed quality defect risk on current cycle")
    
    stability_before: float = Field(..., ge=0.0, le=1.0, description="Process stability index prior to intervention")
    stability_after: float = Field(..., ge=0.0, le=1.0, description="Recomputed process stability index on current cycle")
    
    parameter_movement_verified: bool = Field(..., description="True if target parameter moved in expected direction")
    target_parameter: Optional[str] = Field(default=None, description="Primary parameter adjusted")
    applied_delta: float = Field(default=0.0, description="Intended parameter adjustment")
    observed_delta: float = Field(default=0.0, description="Measured parameter shift from pre-intervention baseline")
    
    consecutive_stable_cycles: int = Field(default=0, description="Number of consecutive stable cycles observed")
    required_stable_cycles: int = Field(default=3, description="Required stability window length (N)")
    stability_window_met: bool = Field(default=False, description="True if consecutive_stable_cycles >= required_stable_cycles")
    
    contract_compliant: bool = Field(..., description="True if all Quality Contract conditions met on current cycle")
    contract_violations: List[str] = Field(default_factory=list, description="Specific tolerance violations if any")
    
    summary_message: str = Field(..., description="Human-readable operational summary of recovery state")
