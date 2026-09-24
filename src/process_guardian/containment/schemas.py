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


class ContainmentWindow(BaseModel):
    """
    Explicit milestone cycle boundaries and suspect containment window (CNTN-01..03).
    """
    last_known_good_cycle: Optional[int] = Field(default=None, description="Last stable cycle before drift initiated (CNTN-01)")
    suspect_start_cycle: Optional[int] = Field(default=None, description="First cycle of suspected/confirmed drift (CNTN-02)")
    suspect_end_cycle: Optional[int] = Field(default=None, description="Last cycle before production release (CNTN-02)")
    
    intervention_cycle: Optional[int] = Field(default=None, description="Cycle corrective parameter shift was applied (CNTN-03)")
    recovery_cycle: Optional[int] = Field(default=None, description="Cycle stability window completed (CNTN-03)")
    release_cycle: Optional[int] = Field(default=None, description="First cycle authorized for production release (CNTN-03)")
    
    suspect_cycle_count: int = Field(default=0, description="Total number of cycles in the quarantine window")
    quarantined_part_count: int = Field(default=0, description="Total parts held for inspection (parts per cycle)")
    estimated_scrap_cycles: int = Field(default=0, description="Estimated number of cycles with high defect risk")


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
