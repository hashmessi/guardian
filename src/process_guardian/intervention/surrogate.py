"""Coupled-physics surrogate response surface model for post-intervention quality risk prediction (INTV-03)."""

import math
from typing import Tuple, Optional, Dict, Any
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.model import QualityRiskModel
from process_guardian.intervention.schemas import ActionType, CandidateAction


class InterventionSurrogateModel:
    """
    Response surface surrogate model estimating post-intervention telemetry and defect risk (INTV-03).
    
    Couples forward polymer rheology and pvT dynamics:
    - Zone 3 cooling increases melt viscosity, raises peak cavity pressure, suppresses flash, and shortens required cooling.
    - Hold pressure adjustments directly impact packing density and part weight.
    - Timing adjustments affect solidification and overall cycle duration.
    - Material purges remove moisture voids and normalize hydrolysis-driven viscosity drops.
    """

    def __init__(self, quality_risk_model: QualityRiskModel):
        self.quality_risk_model = quality_risk_model

    def project_state(
        self,
        record: NormalizedCycleRecord,
        candidate: CandidateAction,
        fingerprint: ProcessFingerprint,
    ) -> NormalizedCycleRecord:
        """
        Project post-intervention machine telemetry using coupled physics transfer functions.
        """
        # Shallow copy of record dictionary
        data: Dict[str, Any] = record.model_dump()

        if candidate.action_type == ActionType.DO_NOTHING or candidate.target_signal is None:
            return NormalizedCycleRecord(**data)

        delta = candidate.delta_value
        target_sig = candidate.target_signal

        # Extract baseline nominals from fingerprint
        nom_peak = fingerprint.signal_stats.get("peak_pressure").mean if "peak_pressure" in fingerprint.signal_stats else 135.0
        nom_inj = fingerprint.signal_stats.get("injection_pressure").mean if "injection_pressure" in fingerprint.signal_stats else 125.0
        nom_weight = fingerprint.signal_stats.get("part_weight").mean if "part_weight" in fingerprint.signal_stats else 142.5

        if candidate.action_type == ActionType.TEMP_ADJUST:
            # 1. Direct temperature adjustment
            data[target_sig] = float(data[target_sig]) + delta

            # 2. Coupled polymer physics dynamics
            delta_t_eff = 0.50 * delta  # effective melt temp shift
            # Viscosity shift (lower temp -> higher viscosity)
            delta_eta_rel = -0.012 * delta_t_eff
            # Peak cavity pressure increases as viscosity rises back towards baseline
            causal_p_peak_delta = nom_peak * delta_eta_rel
            data["peak_pressure"] = float(data["peak_pressure"]) + causal_p_peak_delta
            data["injection_pressure"] = float(data["injection_pressure"]) + (nom_inj * 0.65 * delta_eta_rel)

            # Part weight responds positively to cavity pressure recovery and thermal normalization
            weight_shift = (0.0007 * delta_t_eff) + (0.0006 * causal_p_peak_delta)
            data["part_weight"] = max(80.0, float(data["part_weight"]) + nom_weight * weight_shift)

            # Cooling time demand shifts slightly with melt temp
            data["cooling_time"] = max(5.0, float(data["cooling_time"]) + (14.0 * 0.005 * delta_t_eff))

        elif candidate.action_type == ActionType.PRESSURE_ADJUST:
            # Direct hold pressure adjustment
            data[target_sig] = float(data[target_sig]) + delta
            # Part weight responds directly to packing pressure (approx 0.0012 per bar)
            data["part_weight"] = float(data["part_weight"]) + (nom_weight * 0.0012 * delta)
            # Slight cavity pressure coupling
            data["peak_pressure"] = float(data["peak_pressure"]) + (0.35 * delta)

        elif candidate.action_type == ActionType.CYCLE_TIME_ADJUST:
            # Direct cooling time adjustment
            data[target_sig] = float(data[target_sig]) + delta
            data["cycle_time"] = float(data["cycle_time"]) + delta

        elif candidate.action_type == ActionType.MATERIAL_INSPECT_PURGE:
            # Material purge restores moisture to dry baseline
            moist_mean = fingerprint.signal_stats.get("material_moisture").mean if "material_moisture" in fingerprint.signal_stats else 0.08
            curr_moist = float(data["material_moisture"])
            delta_moist = moist_mean - curr_moist
            data["material_moisture"] = moist_mean
            # Restores viscosity and part density
            data["part_weight"] = float(data["part_weight"]) - (nom_weight * 1.5 * delta_moist)

        # Ground truth defect heuristic update on projected state
        p_peak = float(data["peak_pressure"])
        p_weight = float(data["part_weight"])
        z3_temp = float(data["barrel_temp_z3"])
        z3_mean = fingerprint.signal_stats.get("barrel_temp_z3").mean if "barrel_temp_z3" in fingerprint.signal_stats else 231.0

        if p_peak < 120.0 or p_weight < 140.8:
            data["defect_flag"] = True
            data["sink_mark_depth"] = round(max(0.0, (142.5 - p_weight) * 0.05), 3)
            data["flash_observed"] = False
        elif (z3_temp - z3_mean) > 3.8 or p_weight > 144.3:
            data["defect_flag"] = True
            data["flash_observed"] = True
            data["sink_mark_depth"] = 0.0
        else:
            data["defect_flag"] = False
            data["flash_observed"] = False
            data["sink_mark_depth"] = 0.0

        return NormalizedCycleRecord(**data)

    def estimate_post_intervention_risk(
        self,
        record: NormalizedCycleRecord,
        candidate: CandidateAction,
        fingerprint: ProcessFingerprint,
        contract: Optional[QualityContract] = None,
    ) -> Tuple[float, NormalizedCycleRecord]:
        """
        Estimate post-intervention quality risk using the surrogate response surface and calibrated risk model (INTV-03).
        
        Preserves the internal history of the quality risk model to avoid polluting live telemetry state.
        
        Returns:
            Tuple of (predicted_quality_risk: float, projected_record: NormalizedCycleRecord)
        """
        surrogate_record = self.project_state(record, candidate, fingerprint)

        # Snapshot feature extractor state
        extractor = self.quality_risk_model.feature_extractor
        saved_history = {
            sig: list(extractor.signal_history[sig])
            for sig in extractor.CORE_SIGNALS
        }
        saved_cycle_count = extractor.cycle_count

        try:
            risk_output = self.quality_risk_model.predict(record=surrogate_record, contract=contract)
            return risk_output.risk_probability, surrogate_record
        finally:
            # Restore feature extractor state
            extractor.cycle_count = saved_cycle_count
            for sig in extractor.CORE_SIGNALS:
                extractor.signal_history[sig].clear()
                extractor.signal_history[sig].extend(saved_history[sig])
