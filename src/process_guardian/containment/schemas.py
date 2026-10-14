"""Schemas and data models for scrap containment and production disposition (CNTN-01..04)."""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class DispositionType(str, Enum):
    """Production lot disposition classification."""
    RELEASED_PRE_DRIFT = "RELEASED_PRE_DRIFT"       # Pristine production before drift started
    QUARANTINE_INSPECT = "QUARANTINE_INSPECT"       # Suspect production between drift and recovery
    RELEASED_POST_RECOVERY = "RELEASED_POST_RECOVERY" # Production post-verified recovery


class CycleDisposition(BaseModel):
    """Disposition evaluation for an individual cycle."""
    cycle_index: int
    timestamp: str
    disposition: DispositionType
    defect_risk: float
    is_defective: bool = False
    notes: str = ""


class PhysicalContainmentMilestones(BaseModel):
    """Explicit 6-milestone physical scrap containment boundary track (CNTN-05).

    Every milestone here is a cycle index the engine actually observed. There is no
    physical-measurement milestone: the engine cannot witness a caliper reading, so
    it does not claim one.
    """
    last_verified_good: Optional[int] = Field(default=None, description="Milestone 1: Last confirmed healthy cycle")
    drift_start: Optional[int] = Field(default=None, description="Milestone 2: First cycle of statistical drift")
    suspect_lot_start: Optional[int] = Field(default=None, description="Milestone 3: Suspect lot quarantine start cycle")
    action_applied: Optional[int] = Field(default=None, description="Milestone 4: Corrective intervention applied cycle")
    stabilized: Optional[int] = Field(default=None, description="Milestone 5: Post-intervention parameter stabilization cycle")
    lot_release: Optional[int] = Field(default=None, description="Milestone 6: Production authorized for unrestricted release")


class ContainmentWindow(BaseModel):
    """
    Explicit milestone cycle boundaries and suspect containment window (CNTN-01..03, CNTN-05).
    """
    last_known_good_cycle: Optional[int] = Field(default=None, description="Last stable cycle before drift initiated (CNTN-01)")
    suspect_start_cycle: Optional[int] = Field(default=None, description="First cycle of suspected/confirmed drift (CNTN-02)")
    suspect_end_cycle: Optional[int] = Field(default=None, description="Last cycle before production release (CNTN-02)")
    
    intervention_cycle: Optional[int] = Field(default=None, description="Cycle corrective parameter shift was applied (CNTN-03)")
    recovery_cycle: Optional[int] = Field(default=None, description="Cycle stability window completed (CNTN-03)")
    stabilization_cycle: Optional[int] = Field(default=None, description="Cycle stabilization confirmed (CNTN-05)")
    release_cycle: Optional[int] = Field(default=None, description="First cycle authorized for production release (CNTN-03)")
    
    suspect_cycle_count: int = Field(default=0, description="Total number of cycles in the quarantine window")
    quarantined_part_count: int = Field(default=0, description="Total parts held for inspection (parts per cycle)")
    estimated_scrap_cycles: int = Field(default=0, description="Estimated number of cycles with high defect risk")

    @property
    def milestones(self) -> PhysicalContainmentMilestones:
        """Return the complete 6-milestone boundary model (CNTN-05)."""
        return PhysicalContainmentMilestones(
            last_verified_good=self.last_known_good_cycle,
            drift_start=self.suspect_start_cycle,
            suspect_lot_start=self.suspect_start_cycle,
            action_applied=self.intervention_cycle,
            stabilized=self.stabilization_cycle or self.recovery_cycle,
            lot_release=self.release_cycle,
        )


class BatchDispositionReport(BaseModel):
    """
    Comprehensive containment report answering: 'Which production should we inspect, quarantine, or release?' (CNTN-04).
    """
    machine_id: str = "IMM-01"
    report_timestamp: str
    total_cycles_evaluated: int
    
    released_pre_drift_count: int
    quarantine_suspect_count: int
    released_post_recovery_count: int
    
    containment_window: ContainmentWindow
    disposition_summary: str
    cycle_dispositions: List[CycleDisposition] = Field(default_factory=list)
