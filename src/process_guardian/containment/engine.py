"""Production Scrap Containment Engine determining suspect windows and batch dispositions (CNTN-01..04)."""

from typing import Dict, List, Optional
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.containment.schemas import (
    DispositionType,
    CycleDisposition,
    ContainmentWindow,
    BatchDispositionReport,
)


class ScrapContainmentEngine:
    """
    Identifies production exposure windows and manages batch dispositions (CNTN-01..04).
    
    Answers:
    1. What is the last-known-good cycle? (CNTN-01)
    2. What is the suspect production window between drift and recovery? (CNTN-02)
    3. What are the intervention, recovery, and release milestone cycles? (CNTN-03)
    4. Which production should we inspect, quarantine, or release? (CNTN-04)
    """

    def __init__(self, machine_id: str = "IMM-01", parts_per_cycle: int = 1):
        self.machine_id = machine_id
        self.parts_per_cycle = parts_per_cycle

        # Milestone cycles (CNTN-01..03)
        self.drift_start_cycle: Optional[int] = None
        self.last_known_good_cycle: Optional[int] = None
        self.intervention_cycle: Optional[int] = None
        self.recovery_cycle: Optional[int] = None
        self.release_cycle: Optional[int] = None
        self.latest_evaluated_cycle: int = 0

    def record_drift_detection(self, cycle_index: int) -> None:
        """
        Record when statistical drift was first detected and mark the last-known-good cycle (CNTN-01).
        """
        if self.drift_start_cycle is None:
            self.drift_start_cycle = cycle_index
            self.last_known_good_cycle = max(1, cycle_index - 1)

    def record_intervention(self, cycle_index: int) -> None:
        """
        Record the cycle on which corrective parameter intervention was applied (CNTN-03).
        """
        self.intervention_cycle = cycle_index

    def record_recovery_verified(self, recovery_cycle: int, release_cycle: Optional[int] = None) -> None:
        """
        Record verified recovery cycle and authorization of production release (CNTN-03).
        """
        self.recovery_cycle = recovery_cycle
        self.release_cycle = release_cycle if release_cycle is not None else (recovery_cycle + 1)

    def get_containment_window(self) -> ContainmentWindow:
        """
        Compute the bounded suspect containment window and part counts (CNTN-01..03).
        """
        if self.drift_start_cycle is None:
            return ContainmentWindow(
                last_known_good_cycle=self.latest_evaluated_cycle if self.latest_evaluated_cycle > 0 else None,
                suspect_start_cycle=None,
                suspect_end_cycle=None,
                intervention_cycle=None,
                recovery_cycle=None,
                release_cycle=None,
                suspect_cycle_count=0,
                quarantined_part_count=0,
                estimated_scrap_cycles=0,
            )

        suspect_start = self.drift_start_cycle
        suspect_end = self.recovery_cycle if self.recovery_cycle is not None else self.latest_evaluated_cycle
        suspect_count = max(0, suspect_end - suspect_start + 1)

        return ContainmentWindow(
            last_known_good_cycle=self.last_known_good_cycle,
            suspect_start_cycle=suspect_start,
            suspect_end_cycle=suspect_end,
            intervention_cycle=self.intervention_cycle,
            recovery_cycle=self.recovery_cycle,
            release_cycle=self.release_cycle,
            suspect_cycle_count=suspect_count,
            quarantined_part_count=suspect_count * self.parts_per_cycle,
            estimated_scrap_cycles=0,
        )

    def disposition_cycle(
        self,
        cycle_index: int,
        defect_risk: float = 0.0,
        defect_flag: bool = False,
        timestamp: str = "",
    ) -> CycleDisposition:
        """
        Assign an operational disposition to an individual cycle (CNTN-04).
        """
        self.latest_evaluated_cycle = max(self.latest_evaluated_cycle, cycle_index)

        if self.drift_start_cycle is None:
            # No drift event occurred
            return CycleDisposition(
                cycle_index=cycle_index,
                timestamp=timestamp,
                disposition=DispositionType.RELEASED_PRE_DRIFT,
                defect_risk=defect_risk,
                is_defective=defect_flag,
                notes="Normal production prior to any drift event.",
            )

        if cycle_index < self.drift_start_cycle:
            return CycleDisposition(
                cycle_index=cycle_index,
                timestamp=timestamp,
                disposition=DispositionType.RELEASED_PRE_DRIFT,
                defect_risk=defect_risk,
                is_defective=defect_flag,
                notes="Pristine production before drift onset. Authorized for release.",
            )

        if self.release_cycle is not None and cycle_index >= self.release_cycle:
            return CycleDisposition(
                cycle_index=cycle_index,
                timestamp=timestamp,
                disposition=DispositionType.RELEASED_POST_RECOVERY,
                defect_risk=defect_risk,
                is_defective=defect_flag,
                notes="Verified post-recovery production. Authorized for release.",
            )

        # Cycles within the suspect window [drift_start, release - 1]
        return CycleDisposition(
            cycle_index=cycle_index,
            timestamp=timestamp,
            disposition=DispositionType.QUARANTINE_INSPECT,
            defect_risk=defect_risk,
            is_defective=defect_flag,
            notes="Suspect production produced during process drift/recovery window. Mandatory 100% QC inspection required.",
        )

    def generate_disposition_report(
        self,
        cycles: List[NormalizedCycleRecord],
        risk_map: Optional[Dict[int, float]] = None,
    ) -> BatchDispositionReport:
        """
        Generate comprehensive batch disposition report answering:
        'Which production should we inspect, quarantine, or release?' (CNTN-04).
        """
        risk_map = risk_map or {}
        cycle_dispositions: List[CycleDisposition] = []

        pre_drift_count = 0
        quarantine_count = 0
        post_recovery_count = 0
        scrap_cycle_count = 0

        for r in cycles:
            risk = risk_map.get(r.cycle_index, 0.0)
            disp = self.disposition_cycle(
                cycle_index=r.cycle_index,
                defect_risk=risk,
                defect_flag=r.defect_flag,
                timestamp=r.timestamp,
            )
            cycle_dispositions.append(disp)

            if disp.disposition == DispositionType.RELEASED_PRE_DRIFT:
                pre_drift_count += 1
            elif disp.disposition == DispositionType.QUARANTINE_INSPECT:
                quarantine_count += 1
                if r.defect_flag or risk > 0.70:
                    scrap_cycle_count += 1
            elif disp.disposition == DispositionType.RELEASED_POST_RECOVERY:
                post_recovery_count += 1

        window = self.get_containment_window()
        window.estimated_scrap_cycles = scrap_cycle_count

        # Construct clear operational summary (CNTN-04)
        if self.drift_start_cycle is not None:
            summary = (
                f"Production Disposition Summary: "
                f"Release {pre_drift_count} pre-drift cycles (Cycles 1 to {window.last_known_good_cycle}). "
                f"QUARANTINE {quarantine_count} suspect cycles (Cycles {window.suspect_start_cycle} to {window.suspect_end_cycle}) "
                f"for 100% QC inspection (estimated scrap: {scrap_cycle_count} cycles). "
                f"Release {post_recovery_count} post-recovery cycles (Cycles {window.release_cycle} onwards)."
            )
        else:
            summary = f"All {len(cycles)} evaluated cycles released. No process drift detected."

        timestamp = cycles[-1].timestamp if cycles else "2026-09-24T12:00:00Z"

        return BatchDispositionReport(
            machine_id=self.machine_id,
            report_timestamp=timestamp,
            total_cycles_evaluated=len(cycles),
            released_pre_drift_count=pre_drift_count,
            quarantine_suspect_count=quarantine_count,
            released_post_recovery_count=post_recovery_count,
            containment_window=window,
            disposition_summary=summary,
            cycle_dispositions=cycle_dispositions,
        )
