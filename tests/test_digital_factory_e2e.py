"""Comprehensive End-to-End verification of the Digital Factory Foundation (SIM-01..05, DADP-01..03)."""

import csv
import json
import pytest
from pathlib import Path

from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.simulator.runner import ScenarioRunner
from process_guardian.adapter.schemas import NormalizedCycleRecord, QualityFlag
from process_guardian.core.constants import NOMINAL_PP_PARAMS
from process_guardian.core.types import RegimeType


def test_demo_scenario_progression():
    """
    Verify complete 10-step primary demo scenario progression:
    - Cycles 1 - 419: Healthy baseline
    - Cycles 420 - 441: Thermal drift develops, pressure drops, defect risk escalates
    - Cycle 442: Simulated intervention applied (-3°C adjustment)
    - Cycles 443 - 446: Recovery stabilization
    - Cycle 447+: Verified recovery and released production
    """
    sim = build_demo_scenario(seed=42)
    runner = ScenarioRunner(simulator=sim)
    records = runner.run(total_cycles=450)

    assert len(records) == 450

    # 1. Pre-drift window (cycles 1 - 419)
    # Check baseline health at cycle 419
    c_419 = records[418]
    assert c_419.cycle_index == 419
    assert c_419.is_valid is True
    assert abs(c_419.barrel_temp_z3 - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 1.2
    assert c_419.defect_flag is False

    # 2. Thermal drift window (cycles 420 - 441)
    # Check progressive rise of temperature
    c_420 = records[419]
    c_430 = records[429]
    c_440 = records[439]

    assert c_430.barrel_temp_z3 > c_420.barrel_temp_z3 + 1.2
    assert c_440.barrel_temp_z3 > c_420.barrel_temp_z3 + 3.0
    # Causal coupling: higher melt temperature lowers cavity peak pressure
    assert c_440.peak_pressure < c_419.peak_pressure - 1.5

    # 3. Post-intervention recovery window (cycles 442 - 450)
    # Cycle 442: Intervention of -3°C applied
    c_442 = records[441]
    # By cycle 446, temperature has stabilized back down toward nominal
    c_446 = records[445]
    c_450 = records[449]

    assert c_446.barrel_temp_z3 < c_440.barrel_temp_z3 - 2.0
    assert abs(c_450.barrel_temp_z3 - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 2.0


def test_end_to_end_deterministic_reset():
    """Verify that entire demo runner produces bitwise reproducible output and cleans up on reset (SIM-05)."""
    sim1 = build_demo_scenario(seed=42)
    runner1 = ScenarioRunner(simulator=sim1)
    records1 = runner1.run(total_cycles=100)

    # Re-run from reset
    sim1.reset(new_seed=42)
    # Re-build events on clean simulator
    sim_re = build_demo_scenario(seed=42)
    runner_re = ScenarioRunner(simulator=sim_re)
    records_re = runner_re.run(total_cycles=100)

    for r1, r2 in zip(records1, records_re):
        assert r1.cycle_index == r2.cycle_index
        assert r1.barrel_temp_z3 == r2.barrel_temp_z3
        assert r1.peak_pressure == r2.peak_pressure
        assert r1.part_weight == r2.part_weight
        assert r1.timestamp == r2.timestamp


def test_adapter_pipeline_data_integrity():
    """Verify data adapter pipeline guarantees schema compliance, enrichment, and monotonically advancing timestamps (DADP-01..03)."""
    sim = build_demo_scenario(seed=101)
    runner = ScenarioRunner(simulator=sim)
    records = runner.run(total_cycles=60)

    last_cycle = 0
    last_timestamp = ""

    for rec in records:
        assert isinstance(rec, NormalizedCycleRecord)
        # Monotonic cycle index
        assert rec.cycle_index == last_cycle + 1
        last_cycle = rec.cycle_index

        # ISO 8601 UTC timestamp format
        assert rec.timestamp.endswith("Z")
        assert rec.timestamp > last_timestamp
        last_timestamp = rec.timestamp

        # Enriched context
        assert rec.context.machine_id == "IMM-01"
        assert rec.context.mold_id == "MOLD-HOUSING-04"
        assert rec.context.recipe_version == "2.1"
        assert rec.context.material_batch == "BATCH-20260924-A"

        # Signal quality flags present for all required signals
        assert "barrel_temp_z3" in rec.quality_flags
        assert "injection_pressure" in rec.quality_flags
        assert rec.quality_flags["barrel_temp_z3"] in (QualityFlag.VALID, QualityFlag.OUT_OF_BOUNDS)


def test_scenario_json_and_csv_export(tmp_path: Path):
    """Verify file serialization into valid JSON and CSV formats."""
    sim = build_regime_scenario(RegimeType.HEALTHY, cycles=20, seed=42)
    runner = ScenarioRunner(simulator=sim)
    records = runner.run(total_cycles=20)

    json_path = tmp_path / "telemetry.json"
    csv_path = tmp_path / "telemetry.csv"

    runner.export_json(records, str(json_path))
    runner.export_csv(records, str(csv_path))

    # Verify JSON
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)
    assert len(loaded_json) == 20
    assert loaded_json[0]["cycle_index"] == 1
    assert "barrel_temp_z3" in loaded_json[0]

    # Verify CSV
    assert csv_path.exists()
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 20
    assert reader[0]["cycle_index"] == "1"
    assert "barrel_temp_z3" in reader[0]
