"""Process state REST endpoints for current stability, baseline fingerprint, and drift sentinel (API-02)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone

from process_guardian.api.schemas import (
    ProcessCurrentResponse,
    ProcessFingerprintResponse,
    ProcessDriftResponse,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)

router = APIRouter(prefix="/process", tags=["Process State"])


@router.get("/current", response_model=ProcessCurrentResponse)
def get_current_process_state(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get real-time operational status, stability %, quality risk %, and sensor values for Screen 1.
    """
    orchestrator = container.orchestrator
    latest_rec = container.repository.get_latest_cycle(machine_id)
    latest_pred = container.repository.get_latest_prediction(machine_id)

    # Defaults if no cycles processed yet
    if not latest_rec:
        return ProcessCurrentResponse(
            machine_id=machine_id,
            mold_id="MOLD-18",
            part_id="AUTO-HOUSING-A",
            recipe_id="RCP-12",
            current_cycle=0,
            state=orchestrator.current_state.value,
            process_stability_pct=100.0,
            quality_risk_pct=0.0,
            drift_status="NONE",
            signals={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Calculate real-time metrics
    raw = latest_rec.raw_json
    telemetry = raw.get("telemetry", {})
    risk_prob = latest_pred.risk_probability if latest_pred else 0.03
    drift_events = container.repository.list_drift_events(machine_id, limit=1)
    latest_drift = drift_events[0] if drift_events else None
    
    stability_pct = round((1.0 - min(1.0, latest_drift.severity if latest_drift and latest_drift.drift else 0.04)) * 100, 1)

    return ProcessCurrentResponse(
        machine_id=machine_id,
        mold_id=latest_rec.mold_id,
        part_id=latest_rec.part_id,
        recipe_id=latest_rec.recipe_id,
        current_cycle=latest_rec.cycle_index,
        state=orchestrator.current_state.value,
        process_stability_pct=stability_pct,
        quality_risk_pct=round(risk_prob * 100, 1),
        drift_status="DRIFT_DETECTED" if (latest_drift and latest_drift.drift) else "NONE",
        signals={
            "barrel_temp_z1": latest_rec.barrel_temp_z1,
            "barrel_temp_z2": latest_rec.barrel_temp_z2,
            "barrel_temp_z3": latest_rec.barrel_temp_z3,
            "barrel_temp_z4": latest_rec.barrel_temp_z4,
            "nozzle_temp": latest_rec.nozzle_temp,
            "mold_temp": latest_rec.mold_temp,
            "injection_pressure": latest_rec.injection_pressure,
            "holding_pressure": latest_rec.holding_pressure,
            "back_pressure": latest_rec.back_pressure,
            "injection_speed": latest_rec.injection_speed,
            "screw_rpm": latest_rec.screw_rpm,
            "cushion_position": latest_rec.cushion_position,
            "cycle_time": latest_rec.cycle_time,
            "material_moisture_pct": latest_rec.material_moisture_pct,
            "part_weight_g": latest_rec.part_weight_g,
        },
        timestamp=latest_rec.timestamp,
    )


@router.get("/fingerprint", response_model=ProcessFingerprintResponse)
def get_process_fingerprint(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get baseline distributions, means, stds, and envelope bounds for active production context.
    """
    fp_record = container.repository.get_fingerprint_by_machine(machine_id)
    if not fp_record:
        raise HTTPException(status_code=404, detail=f"No baseline fingerprint found for machine {machine_id}")

    stats = fp_record.stats_json
    envelopes = fp_record.envelope_json

    means = {sig: data["mean"] for sig, data in stats.items() if "mean" in data}
    stds = {sig: data["std"] for sig, data in stats.items() if "std" in data}

    return ProcessFingerprintResponse(
        context_key=fp_record.context_key,
        machine_id=fp_record.machine_id,
        mold_id=fp_record.mold_id,
        part_id=fp_record.part_id,
        recipe_id=fp_record.recipe_id,
        sample_count=fp_record.sample_count,
        signal_means=means,
        signal_stds=stds,
        signal_envelopes=envelopes,
    )


@router.get("/drift", response_model=ProcessDriftResponse)
def get_process_drift(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get Drift Sentinel multi-detector diagnostics, severity score, and lead-cycle calculation.
    """
    orchestrator = container.orchestrator
    drift_events = container.repository.list_drift_events(machine_id, limit=1)
    latest_cycle = container.repository.get_latest_cycle(machine_id)
    cycle_idx = latest_cycle.cycle_index if latest_cycle else 0

    if not drift_events:
        return ProcessDriftResponse(
            machine_id=machine_id,
            current_cycle=cycle_idx,
            drift=False,
            severity=0.0,
            lead_cycles=0,
            contributing_signals=[],
            detectors={},
        )

    latest_drift = drift_events[0]
    return ProcessDriftResponse(
        machine_id=machine_id,
        current_cycle=latest_drift.cycle_index,
        drift=latest_drift.drift,
        severity=latest_drift.severity,
        lead_cycles=latest_drift.lead_cycles,
        contributing_signals=latest_drift.signals_json,
        detectors=latest_drift.details_json,
    )
