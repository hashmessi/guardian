"""Ingestion REST endpoints for cycle telemetry, events, and checkpoints (API-01)."""

import uuid
from typing import Dict, List, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from process_guardian.api.schemas import (
    CycleIngestRequest,
    BatchCycleIngestRequest,
    CycleIngestResponse,
    BatchCycleIngestResponse,
    EventIngestRequest,
    EventIngestResponse,
    CheckpointCreateRequest,
    CheckpointResponse,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)
from process_guardian.storage.schemas import (
    StoredCycleRecord,
    StoredCheckpointRecord,
    StoredAuditLogRecord,
    StoredDriftEventRecord,
    StoredQualityPredictionRecord,
    StoredRecommendationRecord,
    StoredInterventionCandidateRecord,
    StoredContainmentWindowRecord,
    StoredRecoveryEventRecord,
    GuardianEvent,
)
from process_guardian.state_machine.schemas import ProcessState
from process_guardian.containment.schemas import DispositionType

router = APIRouter(tags=["Ingestion"])


def _persist_cycle_step(container: ServiceContainer, res: Any) -> None:
    """Helper to persist all decisions and telemetry records from an orchestrator step to SQLite."""
    repo = container.repository
    rec = res.record

    # 1. Store Cycle Record
    cycle_db = StoredCycleRecord(
        cycle_index=rec.cycle_index,
        machine_id=rec.context.machine_id,
        mold_id=rec.context.mold_id,
        part_id=rec.context.part_id,
        recipe_id=rec.context.recipe_id,
        timestamp=rec.timestamp,
        barrel_temp_z1=rec.barrel_temp_z1,
        barrel_temp_z2=rec.barrel_temp_z2,
        barrel_temp_z3=rec.barrel_temp_z3,
        barrel_temp_z4=rec.barrel_temp_z4,
        nozzle_temp=rec.nozzle_temp,
        mold_temp=getattr(rec, "mold_temp", 80.0),
        injection_pressure=rec.injection_pressure,
        holding_pressure=getattr(rec, "hold_pressure", rec.injection_pressure * 0.7),
        back_pressure=getattr(rec, "back_pressure", 10.0),
        injection_speed=getattr(rec, "injection_speed", 45.0),
        screw_rpm=getattr(rec, "screw_rpm", 60.0),
        cushion_position=getattr(rec, "cushion_position", 5.0),
        dosing_time=getattr(rec, "dosing_time", 3.5),
        injection_time=rec.injection_time,
        cooling_time=rec.cooling_time,
        cycle_time=rec.cycle_time,
        ambient_temp=rec.ambient_temp,
        ambient_humidity=rec.ambient_humidity,
        material_moisture_pct=rec.material_moisture,
        part_weight_g=rec.part_weight,
        defect_flag=rec.defect_flag,
        defect_type="SINK_MARK" if getattr(rec, "sink_mark_depth", 0.0) > 0.08 else ("FLASH" if getattr(rec, "flash_observed", False) else None),
        raw_json=rec.model_dump(),
    )
    repo.insert_cycle(cycle_db)

    # 2. Store Drift Event if drift detected
    if res.drift_output.drift:
        drift_db = StoredDriftEventRecord(
            event_id=f"drf_{rec.cycle_index}_{uuid.uuid4().hex[:6]}",
            cycle_index=rec.cycle_index,
            machine_id=rec.context.machine_id,
            timestamp=rec.timestamp,
            drift=True,
            severity=res.drift_output.severity,
            lead_cycles=res.drift_output.lead_cycles or 0,
            signals_json=res.drift_output.signals,
            details_json={
                "metrics": res.drift_output.metrics.model_dump() if hasattr(res.drift_output, "metrics") and res.drift_output.metrics else {},
                "details": {k: v.model_dump() if hasattr(v, "model_dump") else v for k, v in res.drift_output.details.items()} if hasattr(res.drift_output, "details") else {},
            },
        )
        repo.insert_drift_event(drift_db)

    # 3. Store Quality Prediction
    pred_db = StoredQualityPredictionRecord(
        event_id=f"prd_{rec.cycle_index}_{uuid.uuid4().hex[:6]}",
        cycle_index=rec.cycle_index,
        machine_id=rec.context.machine_id,
        risk_probability=res.risk_output.risk_probability,
        confidence=res.risk_output.confidence,
        risk_state=res.risk_output.risk_state.value,
        operator_mode=res.risk_output.operator_mode.value,
        root_cause_json=res.root_cause_report.model_dump() if res.root_cause_report else {},
    )
    repo.insert_quality_prediction(pred_db)

    # 4. Store Recommendation if generated
    if res.recommendation:
        rec_model = res.recommendation
        candidates_db = []
        if res.comparison_table:
            for ev in res.comparison_table.evaluations:
                cand = ev.candidate
                candidates_db.append(
                    StoredInterventionCandidateRecord(
                        recommendation_id=f"rec_{rec.cycle_index}",
                        action_id=cand.action_id,
                        name=cand.name,
                        target_signal=cand.target_signal,
                        delta_value=cand.delta_value,
                        unit=cand.unit,
                        cost=ev.cost,
                        disruption=ev.disruption,
                        estimated_risk=ev.post_intervention_risk,
                        boundary_checked=ev.constraint_check.is_feasible,
                        is_selected=ev.is_selected,
                        metadata_json={"description": cand.description},
                    )
                )

        rec_db = StoredRecommendationRecord(
            recommendation_id=f"rec_{rec.cycle_index}",
            event_id=f"evt_rec_{rec.cycle_index}",
            cycle_index=rec.cycle_index,
            machine_id=rec.context.machine_id,
            action_id=res.comparison_table.recommended_action_id if res.comparison_table else "A0",
            action_text=rec_model.action,
            why_text=rec_model.why,
            evidence_json={"evidence": rec_model.evidence},
            expected_effect=rec_model.expected_effect,
            confidence=rec_model.confidence,
            operating_limit=rec_model.operating_limit,
            recovery_check=rec_model.recovery_check,
            is_abstain=rec_model.is_abstain,
            abstain_reason=rec_model.abstain_reason,
            operator_mode=rec_model.operator_mode,
        )
        repo.insert_recommendation(rec_db, candidates_db)

    # 5. Store Recovery Event if evaluated
    if res.recovery_output:
        recov = res.recovery_output
        recov_db = StoredRecoveryEventRecord(
            cycle_index=rec.cycle_index,
            machine_id=rec.context.machine_id,
            intervention_id=f"rec_{container.orchestrator.applied_action.action_id}" if container.orchestrator.applied_action else None,
            recovery_status=recov.recovery_status.value,
            release_decision=recov.release_decision.value,
            risk_before=recov.risk_before,
            risk_after=recov.risk_after,
            stability_before=recov.stability_before,
            stability_after=recov.stability_after,
            consecutive_stable_cycles=recov.consecutive_stable_cycles,
            summary_message=recov.summary_message,
        )
        repo.insert_recovery_event(recov_db)

    # 6. Store Containment Window
    win = container.orchestrator.get_containment_window()
    q_list = (
        list(range(win.suspect_start_cycle, (win.suspect_end_cycle or win.suspect_start_cycle) + 1))
        if win.suspect_start_cycle is not None
        else []
    )
    win_db = StoredContainmentWindowRecord(
        machine_id=rec.context.machine_id,
        last_known_good_cycle=win.last_known_good_cycle,
        suspect_start_cycle=win.suspect_start_cycle,
        suspect_end_cycle=win.suspect_end_cycle,
        suspect_cycle_count=win.suspect_cycle_count,
        intervention_cycle=win.intervention_cycle,
        recovery_cycle=win.recovery_cycle,
        release_cycle=win.release_cycle,
        quarantine_cycles_json=q_list,
    )
    repo.upsert_containment_window(win_db)

    # 7. Audit log state transitions
    for t in res.transitions:
        repo.log_audit_event(
            StoredAuditLogRecord(
                event_id=f"trans_{rec.cycle_index}_{t.to_state.value}",
                cycle_index=rec.cycle_index,
                machine_id=rec.context.machine_id,
                timestamp=rec.timestamp,
                event_type="STATE_TRANSITION",
                severity="INFO" if t.to_state == ProcessState.HEALTHY else "HIGH",
                description=f"State transitioned from {t.from_state.value} to {t.to_state.value}: {t.reason}",
                details_json=t.metadata,
            )
        )


@router.post("/cycles", response_model=Union[CycleIngestResponse, BatchCycleIngestResponse], status_code=status.HTTP_201_CREATED)
def ingest_cycles(
    payload: Union[CycleIngestRequest, BatchCycleIngestRequest, Dict[str, Any], List[Dict[str, Any]]],
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Ingest single or batch cycle telemetry.
    Normalizes inputs, runs through the closed decision loop, and persists to SQLite.
    """
    orchestrator = container.orchestrator

    # Case A: Batch Ingestion
    if isinstance(payload, BatchCycleIngestRequest) or (isinstance(payload, dict) and "cycles" in payload) or isinstance(payload, list):
        cycles_list = payload.cycles if isinstance(payload, BatchCycleIngestRequest) else (payload.get("cycles", []) if isinstance(payload, dict) else payload)
        if not cycles_list:
            raise HTTPException(status_code=400, detail="Empty cycles list in batch ingestion")
        
        start_c = None
        end_c = None
        for item in cycles_list:
            res = orchestrator.step(item)
            _persist_cycle_step(container, res)
            if start_c is None:
                start_c = res.cycle_index
            end_c = res.cycle_index

        win = orchestrator.get_containment_window()
        return BatchCycleIngestResponse(
            total_processed=len(cycles_list),
            start_cycle=start_c or 0,
            end_cycle=end_c or 0,
            current_state=orchestrator.current_state.value,
            suspect_cycle_count=win.suspect_cycle_count,
        )

    # Case B: Single Cycle Ingestion
    if isinstance(payload, CycleIngestRequest):
        cycle_dict = {
            "cycle_index": payload.cycle_index or (len(orchestrator.cycle_records) + 1),
            "machine_id": payload.machine_id,
            "mold_id": payload.mold_id,
            "part_id": payload.part_id,
            "recipe_id": payload.recipe_id,
            "timestamp": payload.timestamp or datetime.now(timezone.utc).isoformat(),
            **payload.telemetry,
        }
    elif isinstance(payload, dict):
        cycle_dict = payload
    else:
        raise HTTPException(status_code=400, detail="Invalid cycle payload format")

    res = orchestrator.step(cycle_dict)
    _persist_cycle_step(container, res)

    return CycleIngestResponse(
        cycle_index=res.cycle_index,
        machine_id=res.record.context.machine_id,
        state=res.state.value,
        drift_detected=res.drift_output.drift,
        drift_severity=res.drift_output.severity,
        quality_risk_pct=round(res.risk_output.risk_probability * 100, 1),
        process_stability_pct=round((1.0 - min(1.0, res.drift_output.severity)) * 100, 1),
        disposition=res.disposition.disposition.value,
        is_suspect=(res.disposition.disposition == DispositionType.QUARANTINE_INSPECT),
        recommendation_available=res.recommendation is not None,
        transitions=[t.model_dump() for t in res.transitions],
    )


@router.post("/events", response_model=EventIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_event(
    req: EventIngestRequest,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Ingest external or operator event (e.g. drift injection trigger, material lot change).
    Logs to unified event log and audit trail.
    """
    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    cycle_idx = req.cycle_index if req.cycle_index is not None else (len(container.orchestrator.cycle_records) + 1)
    timestamp = datetime.now(timezone.utc).isoformat()

    event = GuardianEvent(
        event_id=event_id,
        machine_id=req.machine_id,
        mold_id="MOLD-18",
        part_id="AUTO-HOUSING-A",
        recipe_id="RCP-12",
        cycle_id=cycle_idx,
        timestamp=timestamp,
        event_type=req.event_type,
        severity=req.severity,
        signals=req.signals,
        quality_risk=0.0,
        confidence=1.0,
        details=req.details,
    )

    container.repository.record_unified_event(event)

    return EventIngestResponse(
        event_id=event_id,
        status="RECORDED",
        cycle_index=cycle_idx,
        recorded_at=timestamp,
    )


@router.post("/checkpoints", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
def create_checkpoint(
    req: CheckpointCreateRequest,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Create a named checkpoint of the active orchestrator state in SQLite.
    """
    orchestrator = container.orchestrator
    cycle_idx = len(orchestrator.cycle_records)
    timestamp = datetime.now(timezone.utc).isoformat()
    state = orchestrator.current_state.value

    snapshot = {
        "summary": orchestrator.get_summary(),
        "containment_window": orchestrator.get_containment_window().model_dump(),
        "transitions_count": len(orchestrator.get_state_transition_history()),
        "custom_metadata": req.metadata,
    }

    chk = StoredCheckpointRecord(
        checkpoint_name=req.checkpoint_name,
        cycle_index=cycle_idx,
        machine_id=req.machine_id,
        timestamp=timestamp,
        state=state,
        data_json=snapshot,
    )
    container.repository.insert_checkpoint(chk)

    return CheckpointResponse(
        checkpoint_name=req.checkpoint_name,
        machine_id=req.machine_id,
        cycle_index=cycle_idx,
        state=state,
        timestamp=timestamp,
    )
