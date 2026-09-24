"""Unit tests for the production scrap containment engine and batch disposition (CNTN-01..04)."""

import pytest
from process_guardian.containment.schemas import DispositionType, ContainmentWindow, BatchDispositionReport
from process_guardian.containment.engine import ScrapContainmentEngine
from process_guardian.simulator.scenarios import build_demo_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline


def test_last_known_good_identification():
    """Verify last-known-good cycle is identified immediately before drift start (CNTN-01)."""
    engine = ScrapContainmentEngine(machine_id="IMM-01")
    assert engine.last_known_good_cycle is None

    # Drift confirmed at cycle 420
    engine.record_drift_detection(cycle_index=420)

    # CNTN-01: last-known-good cycle = 419
    assert engine.last_known_good_cycle == 419
    assert engine.drift_start_cycle == 420


def test_suspect_window_boundary_calculation():
    """Verify suspect window boundaries and part counts between drift and recovery (CNTN-02)."""
    # 2 cavities per mold
    engine = ScrapContainmentEngine(machine_id="IMM-01", parts_per_cycle=2)

    engine.record_drift_detection(cycle_index=420)
    engine.record_intervention(cycle_index=442)
    engine.record_recovery_verified(recovery_cycle=446, release_cycle=447)

    window = engine.get_containment_window()

    # CNTN-02: suspect window is [420, 446]
    assert window.suspect_start_cycle == 420
    assert window.suspect_end_cycle == 446
    # 446 - 420 + 1 = 27 cycles
    assert window.suspect_cycle_count == 27
    # 27 cycles * 2 parts/cycle = 54 parts quarantined
    assert window.quarantined_part_count == 54


def test_milestone_cycles_tracking():
    """Verify explicit tracking of drift start, intervention, recovery, and release cycles (CNTN-03)."""
    engine = ScrapContainmentEngine(machine_id="IMM-01")

    engine.record_drift_detection(420)
    engine.record_intervention(442)
    engine.record_recovery_verified(446, 447)

    window = engine.get_containment_window()

    # CNTN-03: All milestone cycles tracked explicitly
    assert window.last_known_good_cycle == 419
    assert window.suspect_start_cycle == 420
    assert window.intervention_cycle == 442
    assert window.recovery_cycle == 446
    assert window.release_cycle == 447


def test_production_disposition_partitioning():
    """Verify batch partitioning into pre-drift release, quarantine suspect, and post-recovery release (CNTN-04)."""
    engine = ScrapContainmentEngine(machine_id="IMM-01")
    engine.record_drift_detection(420)
    engine.record_intervention(442)
    engine.record_recovery_verified(446, 447)

    # Test individual cycle dispositions
    # Cycle 418 (pre-drift)
    d_pre = engine.disposition_cycle(cycle_index=418)
    assert d_pre.disposition == DispositionType.RELEASED_PRE_DRIFT

    # Cycle 419 (last known good)
    d_lkg = engine.disposition_cycle(cycle_index=419)
    assert d_lkg.disposition == DispositionType.RELEASED_PRE_DRIFT

    # Cycle 420 (drift start) -> QUARANTINE
    d_drift = engine.disposition_cycle(cycle_index=420, defect_risk=0.45)
    assert d_drift.disposition == DispositionType.QUARANTINE_INSPECT

    # Cycle 442 (intervention) -> QUARANTINE
    d_int = engine.disposition_cycle(cycle_index=442, defect_risk=0.92)
    assert d_int.disposition == DispositionType.QUARANTINE_INSPECT

    # Cycle 446 (recovery end) -> QUARANTINE
    d_rec = engine.disposition_cycle(cycle_index=446, defect_risk=0.14)
    assert d_rec.disposition == DispositionType.QUARANTINE_INSPECT

    # Cycle 447 (release) -> RELEASED_POST_RECOVERY
    d_rel = engine.disposition_cycle(cycle_index=447, defect_risk=0.12)
    assert d_rel.disposition == DispositionType.RELEASED_POST_RECOVERY

    # Cycle 450 (ongoing stable) -> RELEASED_POST_RECOVERY
    d_post = engine.disposition_cycle(cycle_index=450, defect_risk=0.08)
    assert d_post.disposition == DispositionType.RELEASED_POST_RECOVERY


def test_batch_disposition_report_generation():
    """Verify generated batch report answering 'Which production should we inspect, quarantine, or release?' (CNTN-04)."""
    pipe = TelemetryPipeline()
    sim = build_demo_scenario(seed=42)
    records = [pipe.process(sim.step()) for _ in range(450)]

    engine = ScrapContainmentEngine(machine_id="IMM-01")
    engine.record_drift_detection(420)
    engine.record_intervention(442)
    engine.record_recovery_verified(446, 447)

    risk_map = {r.cycle_index: (0.90 if 430 <= r.cycle_index <= 442 else 0.15) for r in records}
    report = engine.generate_disposition_report(cycles=records, risk_map=risk_map)

    # CNTN-04: Answers which production to inspect, quarantine, release
    assert report.total_cycles_evaluated == 450
    assert report.released_pre_drift_count == 419  # Cycles 1 to 419
    assert report.quarantine_suspect_count == 27   # Cycles 420 to 446
    assert report.released_post_recovery_count == 4 # Cycles 447 to 450

    # Summary string contains clear directions
    summary = report.disposition_summary
    assert "Release 419 pre-drift cycles" in summary
    assert "QUARANTINE 27 suspect cycles" in summary
    assert "Release 4 post-recovery cycles" in summary
