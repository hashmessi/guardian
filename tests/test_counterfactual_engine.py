"""Unit tests for Controlled Counterfactual Replay Engine (CRPL-01)."""

import pytest
from process_guardian.counterfactual.engine import CounterfactualReplayEngine
from process_guardian.economics.models import CoPQParameters


def test_counterfactual_predrift_trajectory_identity():
    """Verify Guardian OFF and ON produce identical telemetry before drift onset (Cycles 1-71)."""
    engine = CounterfactualReplayEngine(total_cycles=140)
    comparison = engine.generate_comparison()

    off_stream = comparison.guardian_off.stream
    on_stream = comparison.guardian_on.stream

    assert len(off_stream) == 140
    assert len(on_stream) == 140

    # Test pre-drift cycles 1 to 71 are bit-for-bit identical
    for c in range(0, 71):
        pt_off = off_stream[c]
        pt_on = on_stream[c]
        assert pt_off.cycle_index == pt_on.cycle_index
        assert pt_off.barrel_temp == pt_on.barrel_temp
        assert pt_off.injection_pressure == pt_on.injection_pressure
        assert pt_off.defect_risk == pt_on.defect_risk
        assert pt_off.is_defective == pt_on.is_defective
        assert pt_off.state == "HEALTHY"
        assert pt_off.is_quarantine is False


def test_counterfactual_divergence_at_intervention():
    """Verify trajectory diverges at intervention cycle (85) and recovers in Guardian ON."""
    engine = CounterfactualReplayEngine(total_cycles=140)
    comparison = engine.generate_comparison()

    off_stream = comparison.guardian_off.stream
    on_stream = comparison.guardian_on.stream

    # At cycle 84 (index 83), both are at elevated drifting temperature
    assert off_stream[83].barrel_temp == on_stream[83].barrel_temp
    assert off_stream[83].barrel_temp > 240.0

    # At cycle 95 (index 94), Guardian OFF is hot and high risk; Guardian ON is recovered
    pt_off_95 = off_stream[94]
    pt_on_95 = on_stream[94]

    assert pt_off_95.barrel_temp > 250.0
    assert pt_off_95.defect_risk > 0.80
    assert pt_off_95.is_quarantine is True

    assert pt_on_95.barrel_temp < 237.0
    assert pt_on_95.defect_risk < 0.10
    assert pt_on_95.state == "RELEASED_HEALTHY"
    assert pt_on_95.is_quarantine is False


def test_counterfactual_suspect_lot_and_scrap_reduction():
    """Verify suspect lot quarantine collapses by >65% (and >=75% at full 155c run) and scrap is slashed."""
    engine = CounterfactualReplayEngine(total_cycles=156)
    comparison = engine.generate_comparison()

    # Suspect cycle counts
    off_suspect = comparison.guardian_off.suspect_cycles
    on_suspect = comparison.guardian_on.suspect_cycles
    assert on_suspect == 21
    assert off_suspect >= 84
    assert comparison.suspect_lot_reduction_pct >= 75.0

    # Scrap part counts. `on_scrap` is derived from a real per-cycle risk
    # comparison (not a hand-picked literal cycle list), so it isn't pinned to an
    # exact small number -- it has to still be dramatically lower than off_scrap.
    off_scrap = comparison.guardian_off.scrap_parts_count
    on_scrap = comparison.guardian_on.scrap_parts_count
    assert off_scrap > 25
    assert on_scrap < off_scrap * 0.2
    assert comparison.scrap_reduction_pct >= 85.0

    # Net avoided loss
    assert comparison.net_avoided_loss > 10000.0


def test_counterfactual_epistemic_disclaimer():
    """Verify Level 4 epistemic categorization and simulation disclosures."""
    engine = CounterfactualReplayEngine()
    comparison = engine.generate_comparison()

    assert comparison.epistemic_level == "LEVEL_4_CONTROLLED_COUNTERFACTUAL"
    assert "Level 4 Epistemic Model" in comparison.epistemic_disclaimer
    assert "identical disturbance seeds" in comparison.epistemic_disclaimer
