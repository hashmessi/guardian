"""Quality REST endpoints for calibrated defect risk and Quality Contracts (API-03)."""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query

from process_guardian.api.schemas import (
    QualityRiskResponse,
    QualityContractResponse,
    RootCauseContributorItem,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)

router = APIRouter(prefix="/quality", tags=["Quality"])


@router.get("/risk", response_model=QualityRiskResponse)
def get_quality_risk(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get real-time calibrated quality risk prediction, confidence, operator mode,
    and ranked root cause physical contributors (Screen 2 support).
    """
    latest_pred = container.repository.get_latest_prediction(machine_id)
    latest_cycle = container.repository.get_latest_cycle(machine_id)
    cycle_idx = latest_cycle.cycle_index if latest_cycle else 0

    if not latest_pred:
        return QualityRiskResponse(
            machine_id=machine_id,
            cycle_index=cycle_idx,
            risk_probability=0.03,
            risk_percentage=3.0,
            confidence=0.95,
            risk_state="LOW",
            operator_mode="DIRECT_RECOMMENDATION",
            root_cause_isolated=False,
            contributors=[],
        )

    root_cause_data = latest_pred.root_cause_json or {}
    contributors_raw = root_cause_data.get("contributors", [])

    items: List[RootCauseContributorItem] = []
    for c in contributors_raw:
        items.append(
            RootCauseContributorItem(
                signal_name=c.get("signal_name", "unknown"),
                percentage=round(c.get("contribution_pct", c.get("percentage", 0.0)), 1),
                subsystem=c.get("category", c.get("subsystem", "OTHER")),
                direction="POSITIVE" if c.get("z_score", 0.0) > 0 else "NEGATIVE",
                evidence_text=c.get("evidence", c.get("evidence_text", "")),
            )
        )

    return QualityRiskResponse(
        machine_id=machine_id,
        cycle_index=latest_pred.cycle_index,
        risk_probability=latest_pred.risk_probability,
        risk_percentage=round(latest_pred.risk_probability * 100, 1),
        confidence=latest_pred.confidence,
        risk_state=latest_pred.risk_state,
        operator_mode=latest_pred.operator_mode,
        root_cause_isolated=len(items) > 0,
        contributors=items,
    )


@router.get("/contract", response_model=QualityContractResponse)
def get_quality_contract(
    part_id: str = Query("AUTO-HOUSING-A", description="Part identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get active Quality Contract tolerances and physical requirements.
    """
    qc = container.repository.get_quality_contract_by_part(part_id)
    if not qc:
        raise HTTPException(status_code=404, detail=f"No Quality Contract found for part {part_id}")

    return QualityContractResponse(
        contract_code=qc.contract_code,
        part_id=qc.part_id,
        recipe_id=qc.recipe_id,
        target_weight_g=qc.target_weight_g,
        weight_tolerance_g=qc.weight_tolerance_g,
        weight_min_g=round(qc.target_weight_g - qc.weight_tolerance_g, 2),
        weight_max_g=round(qc.target_weight_g + qc.weight_tolerance_g, 2),
        max_sink_mark_mm=qc.max_sink_mark_mm,
        allow_flash=qc.allow_flash,
        target_cycle_time_s=qc.target_cycle_time_s,
        cycle_time_tolerance_s=qc.cycle_time_tolerance_s,
        specifications=qc.specs_json,
    )
