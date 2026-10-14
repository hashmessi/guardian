"""REST endpoints for Demo Replay, Session Isolation, and Economic Impact Evaluation (DEMO-01, DEMO-02)."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status

from process_guardian.api.schemas import (
    DemoResetRequest,
    DemoResetResponse,
    EconomicImpactResponse,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)

router = APIRouter(tags=["Demo & Hardening"])


@router.post("/demo/reset", response_model=DemoResetResponse, status_code=status.HTTP_200_OK)
def reset_demo_session(
    req: DemoResetRequest = DemoResetRequest(),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Execute a deterministic one-click demo reset (DEMO-02).
    
    Creates a new isolated demo run (run_id) while strictly preserving all previous
    audit trail records in SQLite for immutable compliance history.
    """
    # The container is single-machine (ServiceContainer.machine_id is fixed at
    # construction): a mismatched machine_id must be rejected, not silently echoed
    # back while the reset actually runs against a different machine (hostile-review
    # MEDIUM #6).
    if req.machine_id != container.machine_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown machine_id '{req.machine_id}'; this container serves '{container.machine_id}'.",
        )

    res = container.reset_demo_session(
        seed_baseline=req.seed_baseline,
        baseline_cycles=req.baseline_cycles,
    )
    now_ts = datetime.now(timezone.utc).isoformat()

    return DemoResetResponse(
        status=res["status"],
        run_id=res["run_id"],
        machine_id=req.machine_id,
        state=res["state"],
        seeded_cycles=res["seeded_cycles"],
        audit_records_preserved=res["audit_records_preserved"],
        timestamp=now_ts,
        message=f"Demo session successfully reset to baseline ({res['seeded_cycles']} cycles). {res['audit_records_preserved']} historical audit records preserved.",
    )


@router.get("/demo/economic-impact", response_model=EconomicImpactResponse, status_code=status.HTTP_200_OK)
def get_economic_impact(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    part_cost: float = Query(450.0, ge=0.0, description="Modeled scrap cost per part in INR (defaults to ₹450)"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Calculate the Modeled Avoided Scrap Value (Step 10 of Demo Story, DEMO-01).

    Calculates cost savings strictly from estimated avoided defective cycles,
    rather than every potentially exposed cycle, clearly labeling all assumptions.
    """
    win = container.orchestrator.get_containment_window()
    total_cycles = len(container.orchestrator.cycle_records)
    suspect_count = win.suspect_cycle_count

    # Avoided defective cycles: bounded by what Guardian actually caught and held
    # back from shipping -- the quarantined/suspect window -- not every other cycle
    # in the run, which has no relation to the drift event Guardian responded to
    # (scope_plan.md Sec.4: no INR figure without a traceable formula). Each
    # quarantined cycle is a potential customer escape Guardian withheld for
    # physical inspection instead of letting it ship silently.
    avoided_defective_cycles = suspect_count if win.suspect_start_cycle is not None else 0

    modeled_avoided_value = round(avoided_defective_cycles * part_cost, 2)
    assumptions_detail = (
        f"Assumes ₹{part_cost:.2f}/part defect cost · {avoided_defective_cycles} cycles quarantined and "
        f"withheld from shipping during the suspect window, instead of escaping undetected."
    )

    copq_data = None
    if hasattr(container, "copq_calculator") and container.copq_calculator:
        copq_data = container.copq_calculator.calculate_breakdown(container.copq_params).model_dump()

    return EconomicImpactResponse(
        machine_id=machine_id,
        modeled_avoided_scrap_value=modeled_avoided_value,
        avoided_defective_cycles=avoided_defective_cycles,
        total_lot_cycles=total_cycles,
        quarantined_suspect_cycles=suspect_count,
        part_cost=part_cost,
        currency="INR",
        currency_symbol="₹",
        assumptions_label="Modeled Avoided Scrap Value",
        assumptions_detail=assumptions_detail,
        disclaimer="SIMULATION · PROTOTYPE RESULTS ONLY",
        is_prototype=True,
        copq_breakdown=copq_data,
    )


@router.get("/demo/runs", status_code=status.HTTP_200_OK)
def get_demo_runs_history(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
) -> List[Dict[str, Any]]:
    """
    Fetch historical isolated demo run checkpoints recorded in the immutable audit trail.
    """
    records = container.repository.list_audit_logs(machine_id=machine_id, limit=100)
    reset_events = [
        {
            "event_id": r.event_id,
            "timestamp": r.timestamp,
            "description": r.description,
            "details": r.details_json,
        }
        for r in records
        if r.event_type == "DEMO_SESSION_RESET"
    ]
    return reset_events
