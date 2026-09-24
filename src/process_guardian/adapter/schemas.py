"""Pydantic v2 schemas and models for raw ingestion and normalized cycle records."""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class QualityFlag(str, Enum):
    """Signal quality classification flags."""
    VALID = "VALID"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    MISSING_SIGNAL = "MISSING_SIGNAL"
    SENSOR_DROP = "SENSOR_DROP"
    STALE_VALUE = "STALE_VALUE"


class RawTelemetryPayload(BaseModel):
    """
    Tolerant schema for incoming raw sensor telemetry from PLCs, simulators, or edge gateways.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    cycle_index: Optional[int] = None
    timestamp: Optional[Union[datetime, str, float]] = None

    # Engineering units metadata
    pressure_unit: str = Field(default="bar", description="bar, psi, or mpa")
    temp_unit: str = Field(default="c", description="c or f")

    # Temperatures
    barrel_temp_z1: Optional[float] = None
    barrel_temp_z2: Optional[float] = None
    barrel_temp_z3: Optional[float] = None
    barrel_temp_z4: Optional[float] = None
    barrel_temp_z5: Optional[float] = None
    nozzle_temp: Optional[float] = None

    # Pressures
    injection_pressure: Optional[float] = None
    peak_pressure: Optional[float] = None
    hold_pressure: Optional[float] = None

    # Timings
    injection_time: Optional[float] = None
    hold_time: Optional[float] = None
    cooling_time: Optional[float] = None
    cycle_time: Optional[float] = None

    # Material & Environmental
    part_weight: Optional[float] = None
    material_moisture: Optional[float] = None
    ambient_temp: Optional[float] = None
    ambient_humidity: Optional[float] = None

    # Quality ground truth / visual checks if present
    sink_mark_depth: Optional[float] = None
    flash_observed: Optional[bool] = None
    defect_flag: Optional[bool] = None

    # Context overrides if present in packet
    machine_id: Optional[str] = None
    mold_id: Optional[str] = None
    part_id: Optional[str] = None
    recipe_id: Optional[str] = None
    recipe_version: Optional[str] = None
    material_batch: Optional[str] = None
    operator_id: Optional[str] = None


class EnrichedContext(BaseModel):
    """Complete machine, mold, recipe, and material context attached to cycle records."""
    machine_id: str = "IMM-01"
    mold_id: str = "MOLD-HOUSING-04"
    part_id: str = "PART-AUTO-HOUSING-A"
    recipe_id: str = "RECIPE-PP-V2.1"
    recipe_version: str = "2.1"
    material_batch: str = "BATCH-20260924-A"
    operator_id: str = "OP-102"


class NormalizedCycleRecord(BaseModel):
    """
    Vendor-neutral normalized cycle record.
    
    All engineering units are standardized:
    - Temperatures: Celsius (°C)
    - Pressures: bar
    - Timings: seconds (s)
    - Weight: grams (g)
    - Moisture: percentage (%)
    - Timestamp: ISO 8601 UTC string
    """
    cycle_index: int
    timestamp: str  # ISO 8601 UTC

    # Normalized temperatures (°C)
    barrel_temp_z1: float
    barrel_temp_z2: float
    barrel_temp_z3: float
    barrel_temp_z4: float
    barrel_temp_z5: float
    nozzle_temp: float

    # Normalized pressures (bar)
    injection_pressure: float
    peak_pressure: float
    hold_pressure: float

    # Normalized timings (s)
    injection_time: float
    hold_time: float
    cooling_time: float
    cycle_time: float

    # Normalized material & environment
    part_weight: float
    material_moisture: float
    ambient_temp: float
    ambient_humidity: float

    # Ground truth flags
    sink_mark_depth: float = 0.0
    flash_observed: bool = False
    defect_flag: bool = False

    # Metadata & Quality Audit
    context: EnrichedContext
    quality_flags: Dict[str, QualityFlag]
    is_valid: bool = True
