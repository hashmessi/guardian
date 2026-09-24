"""Recovery verification and scrap containment REST endpoints (API-05)."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime, timezone

from process_guardian.recovery.schemas import RecoveryStatus
from process_guardian.api.schemas import (
    RecoveryStatusResponse,
    ContainmentWindowResponse,
    ContainmentReleaseRequest,
    ContainmentReleaseResponse,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)
from process_guardian.storage.schemas import (
    StoredAuditLogRecord,
    StoredContainmentWindowRecord,
)

router = APIRouter(tags=["Recovery & Containment"])


@router.get("/recovery/status", response_model=RecoveryStatusResponse)
def get_recovery_status(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get post-intervention parameter movement confirmation and stability window progress.
    """
    orchestrator = container.orchestrator
    verifier = orchestrator.recovery_verifier
    stored_recov = container.repository.get_latest_recovery_event(machine_id)
    latest_cycle = container.repository.get_latest_cycle(machine_id)
    cycle_idx = latest_cycle.cycle_index if latest_cycle else 0

    if not verifier.is_active:
        if stored_recov:
            return RecoveryStatusResponse(
                machine_id=machine_id,
                cycle_index=stored_recov.cycle_index,
                is_monitoring=False,
                recovery_status=stored_recov.recovery_status,
                release_decision=stored_recov.release_decision,
                parameter_movement_confirmed=True,
                observed_shift=None,
                target_shift=None,
                risk_before=stored_recov.risk_before,
                risk_current=stored_recov.risk_after,
                stability_before=stored_recov.stability_before,
                stability_current=stored_recov.stability_after,
                consecutive_stable_cycles=stored_recov.consecutive_stable_cycles,
                required_stable_cycles=verifier.required_stable_cycles,
                summary_message=stored_recov.summary_message,
            )

        return RecoveryStatusResponse(
            machine_id=machine_id,
            cycle_index=cycle_idx,
            is_monitoring=False,
            recovery_status="IDLE",
            release_decision="NOT_APPLICABLE",
            parameter_movement_confirmed=False,
            observed_shift=None,
            target_shift=None,
            risk_before=0.03,
            risk_current=0.03,
            stability_before=0.96,
            stability_current=0.96,
            consecutive_stable_cycles=0,
            required_stable_cycles=verifier.required_stable_cycles,
            summary_message="No active intervention recovery check in progress.",
        )

    # Active or completed monitoring in live memory
    rel_dec = (
        "APPROVED"
        if verifier.current_status == RecoveryStatus.VERIFIED
        else "REJECTED_QUARANTINE"
        if verifier.current_status == RecoveryStatus.FAILED
        else (stored_recov.release_decision if stored_recov else "PENDING_VERIFICATION")
    )
    is_mon = (verifier.current_status == RecoveryStatus.IN_PROGRESS)

    return RecoveryStatusResponse(
        machine_id=machine_id,
        cycle_index=cycle_idx,
        is_monitoring=is_mon,
        recovery_status=verifier.current_status.value,
        release_decision=rel_dec,
        parameter_movement_confirmed=verifier.parameter_movement_verified,
        observed_shift=None,
        target_shift=verifier.applied_candidate.delta_value if verifier.applied_candidate else None,
        risk_before=verifier.risk_before,
        risk_current=orchestrator.risk_history.get(cycle_idx, 0.08),
        stability_before=verifier.stability_before,
        stability_current=round(1.0 - orchestrator.risk_history.get(cycle_idx, 0.08), 2),
        consecutive_stable_cycles=verifier.consecutive_stable_cycles,
        required_stable_cycles=verifier.required_stable_cycles,
        summary_message=stored_recov.summary_message if (stored_recov and verifier.current_status == RecoveryStatus.VERIFIED) else f"Cooling stability window: {verifier.consecutive_stable_cycles}/{verifier.required_stable_cycles} consecutive stable cycles confirmed.",
    )


@router.get("/containment/window", response_model=ContainmentWindowResponse)
def get_containment_window(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get suspect production window boundaries, quarantine list, and scrap reduction metrics.
    """
    win = container.orchestrator.get_containment_window()
    stored_win = container.repository.get_latest_containment_window(machine_id)

    total_cycles = len(container.orchestrator.cycle_records)
    suspect_count = win.suspect_cycle_count
    
    # Calculate quarantined cycle indices
    if win.suspect_start_cycle is not None:
        q_cycles = list(range(win.suspect_start_cycle, (win.suspect_end_cycle or total_cycles) + 1))
    elif stored_win and stored_win.quarantine_cycles_json:
        q_cycles = stored_win.quarantine_cycles_json
    else:
        q_cycles = []

    # Scrap savings compared to uncontained batch run
    scrap_saved = max(0, total_cycles - suspect_count) if total_cycles > 0 else 0

    return ContainmentWindowResponse(
        machine_id=machine_id,
        last_known_good_cycle=win.last_known_good_cycle or (stored_win.last_known_good_cycle if stored_win else None),
        suspect_start_cycle=win.suspect_start_cycle or (stored_win.suspect_start_cycle if stored_win else None),
        suspect_end_cycle=win.suspect_end_cycle or (stored_win.suspect_end_cycle if stored_win else None),
        suspect_cycle_count=suspect_count or (stored_win.suspect_cycle_count if stored_win else 0),
        intervention_cycle=win.intervention_cycle or (stored_win.intervention_cycle if stored_win else None),
        recovery_cycle=win.recovery_cycle or (stored_win.recovery_cycle if stored_win else None),
        release_cycle=win.release_cycle or (stored_win.release_cycle if stored_win else None),
        quarantine_cycles=q_cycles,
        estimated_scrap_saved_cycles=scrap_saved,
    )


@router.post("/containment/release", response_model=ContainmentReleaseResponse, status_code=status.HTTP_200_OK)
def authorize_production_release(
    req: ContainmentReleaseRequest,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Authorize release of suspect or post-recovery production lot.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    cycle_idx = len(container.orchestrator.cycle_records)

    # Log audit event
    container.repository.log_audit_event(
        StoredAuditLogRecord(
            event_id=f"rel_{cycle_idx}_{req.operator_id}",
            cycle_index=cycle_idx,
            machine_id=req.machine_id,
            timestamp=timestamp,
            event_type="CONTAINMENT_RELEASE_AUTHORIZED",
            severity="INFO",
            description=f"Operator {req.operator_id} authorized production release: {req.release_notes}",
            details_json={"notes": req.release_notes, "operator_id": req.operator_id},
        )
    )

    return ContainmentReleaseResponse(
        machine_id=req.machine_id,
        status="RELEASE_AUTHORIZED",
        released_at=timestamp,
        message=f"Production release successfully authorized by {req.operator_id}.",
    )
