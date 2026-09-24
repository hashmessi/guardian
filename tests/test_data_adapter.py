"""Unit tests for Data Adapter layer, normalization, bounds validation, and context enrichment (DADP-01, DADP-02, DADP-03)."""

import pytest
from datetime import datetime, timezone
from process_guardian.core.types import MachineContext
from process_guardian.adapter.schemas import QualityFlag, NormalizedCycleRecord
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.adapter.normalizer import TelemetryNormalizer


def test_normalization_and_sequencing():
    """Verify engineering unit normalization, timestamp formatting, and monotonic indexing (DADP-01)."""
    pipeline = TelemetryPipeline()

    # 1. Test pressure normalization (psi -> bar, mpa -> bar)
    normalizer = TelemetryNormalizer()
    assert normalizer.normalize_pressure(145.038, "psi") == 10.0
    assert normalizer.normalize_pressure(12.0, "mpa") == 120.0
    assert normalizer.normalize_pressure(85.5, "bar") == 85.5

    # 2. Test temperature normalization (°F -> °C)
    assert normalizer.normalize_temperature(446.0, "f") == 230.0
    assert normalizer.normalize_temperature(230.0, "c") == 230.0

    # 3. Process payload with non-standard units through pipeline
    raw_payload = {
        "cycle_index": 1,
        "timestamp": "2026-09-24T08:00:00Z",
        "pressure_unit": "psi",
        "temp_unit": "f",
        "barrel_temp_z1": 410.0,    # ~210°C
        "barrel_temp_z2": 428.0,    # ~220°C
        "barrel_temp_z3": 446.0,    # 230°C
        "barrel_temp_z4": 455.0,    # ~235°C
        "barrel_temp_z5": 455.0,    # ~235°C
        "nozzle_temp": 464.0,       # 240°C
        "injection_pressure": 1595.4, # ~110 bar
        "peak_pressure": 1958.0,      # ~135 bar
        "hold_pressure": 942.7,       # ~65 bar
        "injection_time": 2.4,
        "hold_time": 6.5,
        "cooling_time": 14.0,
        "cycle_time": 28.5,
        "part_weight": 142.5,
        "material_moisture": 0.02,
    }

    record = pipeline.process(raw_payload)
    assert isinstance(record, NormalizedCycleRecord)
    assert record.cycle_index == 1
    assert record.timestamp == "2026-09-24T08:00:00Z"

    # Normalized temperatures should be in °C
    assert abs(record.barrel_temp_z3 - 230.0) < 0.5
    # Normalized pressures should be in bar
    assert abs(record.injection_pressure - 110.0) < 0.5
    assert abs(record.peak_pressure - 135.0) < 0.5


def test_bounds_validation_and_missing_signals():
    """Verify physical range checking and missing signal detection (DADP-02)."""
    pipeline = TelemetryPipeline()

    # 1. Payload with an out-of-bounds temperature (500°C)
    payload_oob = {
        "barrel_temp_z3": 500.0,   # Exceeds max 420°C limit
        "injection_pressure": 110.0,
    }

    record_oob = pipeline.process(payload_oob)
    assert record_oob.quality_flags["barrel_temp_z3"] == QualityFlag.OUT_OF_BOUNDS
    assert record_oob.is_valid is False

    # 2. Payload with missing required signals (omits injection_time, part_weight)
    payload_missing = {
        "barrel_temp_z1": 210.0,
        "barrel_temp_z2": 220.0,
        "barrel_temp_z3": 230.0,
        "barrel_temp_z4": 235.0,
        "barrel_temp_z5": 235.0,
        "nozzle_temp": 240.0,
        "injection_pressure": 110.0,
        "peak_pressure": 135.0,
        "hold_pressure": 65.0,
        # cooling_time, part_weight missing
    }

    record_missing = pipeline.process(payload_missing)
    assert record_missing.quality_flags["part_weight"] == QualityFlag.MISSING_SIGNAL
    assert record_missing.is_valid is False
    # Pipeline safely filled nominal fallback so record is complete
    assert record_missing.part_weight == 142.5


def test_context_enrichment():
    """Verify attachment of machine, mold, recipe, and material context (DADP-03)."""
    custom_context = MachineContext(
        machine_id="IMM-TEST-09",
        mold_id="MOLD-PANEL-B",
        part_id="PART-DOOR-TRIM",
        recipe_id="RECIPE-ABS-V1",
        recipe_version="1.0",
        material_batch="BATCH-999",
        operator_id="OP-404",
    )

    pipeline = TelemetryPipeline(context=custom_context)
    record = pipeline.process({"barrel_temp_z3": 230.0, "injection_pressure": 110.0})

    assert record.context.machine_id == "IMM-TEST-09"
    assert record.context.mold_id == "MOLD-PANEL-B"
    assert record.context.part_id == "PART-DOOR-TRIM"
    assert record.context.recipe_id == "RECIPE-ABS-V1"
    assert record.context.recipe_version == "1.0"
    assert record.context.material_batch == "BATCH-999"
    assert record.context.operator_id == "OP-404"
