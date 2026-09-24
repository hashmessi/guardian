"""Unified telemetry ingestion pipeline combining normalization, validation, and enrichment."""

from typing import Union, Dict, Any, List, Optional
from datetime import datetime

from process_guardian.core.types import MachineContext, RawCycleTelemetry
from process_guardian.core.constants import NOMINAL_PP_PARAMS
from process_guardian.adapter.schemas import (
    RawTelemetryPayload,
    NormalizedCycleRecord,
    EnrichedContext,
    QualityFlag,
)
from process_guardian.adapter.normalizer import TelemetryNormalizer, SequenceTracker
from process_guardian.adapter.validator import TelemetryValidator
from process_guardian.adapter.enricher import ContextEnricher


class TelemetryPipeline:
    """
    End-to-end telemetry adapter and normalization pipeline.
    
    Transforms raw incoming telemetry packets (dict, Pydantic model, or RawCycleTelemetry)
    into validated, standardized, and enriched NormalizedCycleRecord instances.
    """

    def __init__(self, context: Optional[MachineContext] = None):
        self.context = context or MachineContext()
        self.normalizer = TelemetryNormalizer()
        self.validator = TelemetryValidator()
        self.enricher = ContextEnricher(self.context)
        self.sequence_tracker = SequenceTracker()

    def process(self, raw_input: Union[Dict[str, Any], RawTelemetryPayload, RawCycleTelemetry]) -> NormalizedCycleRecord:
        """
        Process a single raw cycle into a validated NormalizedCycleRecord.
        """
        # 1. Coerce to dictionary
        if isinstance(raw_input, RawCycleTelemetry):
            data = {
                "cycle_index": raw_input.cycle_index,
                "barrel_temp_z1": raw_input.barrel_temp_z1,
                "barrel_temp_z2": raw_input.barrel_temp_z2,
                "barrel_temp_z3": raw_input.barrel_temp_z3,
                "barrel_temp_z4": raw_input.barrel_temp_z4,
                "barrel_temp_z5": raw_input.barrel_temp_z5,
                "nozzle_temp": raw_input.nozzle_temp,
                "injection_pressure": raw_input.injection_pressure,
                "peak_pressure": raw_input.peak_pressure,
                "hold_pressure": raw_input.hold_pressure,
                "injection_time": raw_input.injection_time,
                "hold_time": raw_input.hold_time,
                "cooling_time": raw_input.cooling_time,
                "cycle_time": raw_input.cycle_time,
                "part_weight": raw_input.part_weight,
                "material_moisture": raw_input.material_moisture,
                "ambient_temp": raw_input.ambient_temp,
                "ambient_humidity": raw_input.ambient_humidity,
                "sink_mark_depth": raw_input.sink_mark_depth,
                "flash_observed": raw_input.flash_observed,
                "defect_flag": raw_input.defect_flag,
                "pressure_unit": "bar",
                "temp_unit": "c",
            }
        elif isinstance(raw_input, RawTelemetryPayload):
            data = raw_input.model_dump()
        elif isinstance(raw_input, dict):
            data = dict(raw_input)
        else:
            raise TypeError(f"Unsupported telemetry input type: {type(raw_input)}")

        # 2. Sequence tracking & Timestamping
        cycle_idx = self.sequence_tracker.track(data.get("cycle_index"))
        iso_timestamp = self.normalizer.generate_timestamp(data.get("timestamp"), cycle_idx)

        # 3. Unit Normalization
        p_unit = data.get("pressure_unit", "bar")
        t_unit = data.get("temp_unit", "c")

        normalized_signals: Dict[str, Optional[float]] = {
            "barrel_temp_z1": self.normalizer.normalize_temperature(data.get("barrel_temp_z1"), t_unit),
            "barrel_temp_z2": self.normalizer.normalize_temperature(data.get("barrel_temp_z2"), t_unit),
            "barrel_temp_z3": self.normalizer.normalize_temperature(data.get("barrel_temp_z3"), t_unit),
            "barrel_temp_z4": self.normalizer.normalize_temperature(data.get("barrel_temp_z4"), t_unit),
            "barrel_temp_z5": self.normalizer.normalize_temperature(data.get("barrel_temp_z5"), t_unit),
            "nozzle_temp": self.normalizer.normalize_temperature(data.get("nozzle_temp"), t_unit),
            "injection_pressure": self.normalizer.normalize_pressure(data.get("injection_pressure"), p_unit),
            "peak_pressure": self.normalizer.normalize_pressure(data.get("peak_pressure"), p_unit),
            "hold_pressure": self.normalizer.normalize_pressure(data.get("hold_pressure"), p_unit),
            "injection_time": round(float(data["injection_time"]), 2) if data.get("injection_time") is not None else None,
            "hold_time": round(float(data["hold_time"]), 2) if data.get("hold_time") is not None else None,
            "cooling_time": round(float(data["cooling_time"]), 2) if data.get("cooling_time") is not None else None,
            "cycle_time": round(float(data["cycle_time"]), 2) if data.get("cycle_time") is not None else None,
            "part_weight": round(float(data["part_weight"]), 2) if data.get("part_weight") is not None else None,
            "material_moisture": round(float(data["material_moisture"]), 4) if data.get("material_moisture") is not None else None,
            "ambient_temp": round(float(data["ambient_temp"]), 2) if data.get("ambient_temp") is not None else None,
            "ambient_humidity": round(float(data["ambient_humidity"]), 2) if data.get("ambient_humidity") is not None else None,
        }

        # 4. Physical bounds & sensor quality validation
        quality_flags, is_valid = self.validator.validate(normalized_signals)

        # 5. Safe nominal fallbacks for missing signals to construct valid domain record
        final_signals: Dict[str, float] = {}
        for sig_name, val in normalized_signals.items():
            if val is not None:
                final_signals[sig_name] = val
            else:
                # Use nominal fallback value, flag remains MISSING_SIGNAL
                final_signals[sig_name] = NOMINAL_PP_PARAMS.get(sig_name, 0.0)

        # 6. Context enrichment
        enriched_ctx = self.enricher.enrich(data)

        # 7. Construct and return NormalizedCycleRecord
        return NormalizedCycleRecord(
            cycle_index=cycle_idx,
            timestamp=iso_timestamp,
            barrel_temp_z1=final_signals["barrel_temp_z1"],
            barrel_temp_z2=final_signals["barrel_temp_z2"],
            barrel_temp_z3=final_signals["barrel_temp_z3"],
            barrel_temp_z4=final_signals["barrel_temp_z4"],
            barrel_temp_z5=final_signals["barrel_temp_z5"],
            nozzle_temp=final_signals["nozzle_temp"],
            injection_pressure=final_signals["injection_pressure"],
            peak_pressure=final_signals["peak_pressure"],
            hold_pressure=final_signals["hold_pressure"],
            injection_time=final_signals["injection_time"],
            hold_time=final_signals["hold_time"],
            cooling_time=final_signals["cooling_time"],
            cycle_time=final_signals["cycle_time"],
            part_weight=final_signals["part_weight"],
            material_moisture=final_signals["material_moisture"],
            ambient_temp=final_signals["ambient_temp"],
            ambient_humidity=final_signals["ambient_humidity"],
            sink_mark_depth=float(data.get("sink_mark_depth", 0.0)),
            flash_observed=bool(data.get("flash_observed", False)),
            defect_flag=bool(data.get("defect_flag", False)),
            context=enriched_ctx,
            quality_flags=quality_flags,
            is_valid=is_valid,
        )

    def process_batch(self, raw_items: List[Any]) -> List[NormalizedCycleRecord]:
        """Process a list of raw cycles in sequence."""
        return [self.process(item) for item in raw_items]
