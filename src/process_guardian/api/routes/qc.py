"""FastAPI Routes for Operational Poka-Yoke checkpoints & Containment Boundary (QCHK-02, CNTN-05)."""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from process_guardian.api.dependencies import ServiceContainer, get_service_container
from process_guardian.quality.operational_checkpoints import (
    OperationalCheckpointsReport,
    MoldReleaseCheckpointStatus,
    MoistureCheckpointStatus,
)
from process_guardian.llm.human_channel import (
    CONFIDENCE_THRESHOLD,
    BoundedChoice,
    CheckpointQuestion,
    HumanChannelSignal,
)
from process_guardian.containment.schemas import (
    ContainmentWindow,
    PhysicalContainmentMilestones,
)
from process_guardian.state_machine.schemas import ProcessState

router = APIRouter(tags=["quality_checkpoints"])


class SprayRecordRequest(BaseModel):
    cycle_index: int = Field(..., ge=0, description="Cycle index when spray was applied")
    operator_id: str = Field(default="OP-104", description="Operator ID who applied mold spray")


class MoistureRecordRequest(BaseModel):
    moisture_pct: float = Field(..., ge=0.0, description="Measured resin moisture percentage")
    inspector_id: str = Field(..., description="QC inspector ID certifying moisture")
    batch_id: Optional[str] = Field(default="BATCH-PA66-202610", description="Resin lot batch number")


class HumanChannelTextRequest(BaseModel):
    question: CheckpointQuestion
    text: str = Field(..., min_length=1, description="Bounded shop-floor confirmation, any supported language")
    cycle_index: Optional[int] = Field(
        default=None, description="Required when question=spray_done; the cycle the confirmation applies to"
    )


class HumanChannelResponse(BaseModel):
    signal: HumanChannelSignal
    applied: bool
    mold_release_spray: Optional[MoldReleaseCheckpointStatus] = None


class ContainmentBoundaryResponse(BaseModel):
    machine_id: str
    milestones: PhysicalContainmentMilestones
    containment_window: ContainmentWindow
    is_quarantine_active: bool
    quarantine_summary: str


@router.get("/checkpoints/operational", response_model=OperationalCheckpointsReport, status_code=status.HTTP_200_OK)
def get_operational_checkpoints(
    container: ServiceContainer = Depends(get_service_container),
) -> OperationalCheckpointsReport:
    """
    Evaluate the 3 PS02 shop-floor operational checkpoints (QCHK-02):
    1. Recipe Verification Lock (R-12)
    2. Resin Moisture Batch Sign-Off (<= 0.15%)
    3. Mold-Release Spray Interval Tracking (scheduled 50 cycles, overdue 60)
    """
    orchestrator = container.orchestrator
    if not (orchestrator and orchestrator.cycle_records):
        raise HTTPException(
            status_code=404,
            detail=(
                "No processed cycle telemetry yet. Checkpoint status is only reported against "
                "real machine parameters, never against placeholder setpoints."
            ),
        )

    latest = orchestrator.cycle_records[-1]
    current_cycle = latest.cycle_index
    active_params: Dict[str, float] = {
        "zone_1_temp": latest.barrel_temp_z1,
        "zone_2_temp": latest.barrel_temp_z2,
        "zone_3_temp": latest.barrel_temp_z3,
        "zone_4_temp": latest.barrel_temp_z4,
        "holding_pressure": getattr(latest, "holding_pressure", getattr(latest, "hold_pressure", 75.0)),
        "injection_speed": getattr(latest, "injection_speed", 45.0),
        "cooling_time": latest.cooling_time,
    }

    return container.operational_checkpoints.evaluate_all(
        current_cycle=current_cycle,
        active_params=active_params,
    )


@router.post("/checkpoints/spray", response_model=MoldReleaseCheckpointStatus, status_code=status.HTTP_200_OK)
def record_mold_release_spray(
    payload: SprayRecordRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> MoldReleaseCheckpointStatus:
    """Record mold-release spray application and reset spray interval timer (QCHK-02)."""
    container.operational_checkpoints.record_spray(
        cycle_index=payload.cycle_index,
        operator_id=payload.operator_id,
    )
    return container.operational_checkpoints.evaluate_mold_spray(current_cycle=payload.cycle_index)


@router.post("/checkpoints/moisture", response_model=MoistureCheckpointStatus, status_code=status.HTTP_200_OK)
def update_resin_moisture(
    payload: MoistureRecordRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> MoistureCheckpointStatus:
    """Record resin moisture test and update batch sign-off status (QCHK-02)."""
    container.operational_checkpoints.update_moisture_signoff(
        moisture_pct=payload.moisture_pct,
        inspector_id=payload.inspector_id,
        batch_id=payload.batch_id,
    )
    return container.operational_checkpoints.evaluate_moisture()


@router.post("/checkpoints/human-channel", response_model=HumanChannelResponse, status_code=status.HTTP_200_OK)
def submit_human_channel_text(
    payload: HumanChannelTextRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> HumanChannelResponse:
    """
    Parse a bounded multilingual shop-floor attestation (P0, scope_plan.md Sec.3):
    spray done this interval? resin lot dried & signed? setpoint matches recipe R-12?
    Only the spray confirmation mutates state (it mirrors /checkpoints/spray); the
    moisture and recipe questions are corroborating evidence only -- the numeric
    sensor/parameter checks remain the deciding authority (scope_plan.md Sec.6 rule 1).
    """
    evaluator = container.operational_checkpoints

    if payload.question == CheckpointQuestion.SPRAY_DONE:
        if payload.cycle_index is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="cycle_index is required for the spray_done question.",
            )
        spray_status, signal = evaluator.record_spray_from_text(payload.text, cycle_index=payload.cycle_index)
        applied = signal.choice == BoundedChoice.YES and signal.confidence >= CONFIDENCE_THRESHOLD
        return HumanChannelResponse(signal=signal, applied=applied, mold_release_spray=spray_status)

    if payload.question == CheckpointQuestion.MOISTURE_SIGNED:
        signal = evaluator.attest_moisture_signoff_from_text(payload.text)
        return HumanChannelResponse(signal=signal, applied=False)

    signal = evaluator.attest_recipe_setpoint_from_text(payload.text)
    return HumanChannelResponse(signal=signal, applied=False)


@router.get("/containment/boundary", response_model=ContainmentBoundaryResponse, status_code=status.HTTP_200_OK)
def get_containment_boundary(
    container: ServiceContainer = Depends(get_service_container),
) -> ContainmentBoundaryResponse:
    """
    Return physical scrap containment boundary card data with 6 cycle milestones (CNTN-05):
    1. Last Verified Good
    2. Drift Start
    3. Suspect Lot Start
    4. Action Applied
    5. Stabilized
    6. Lot Release

    Every milestone is a cycle the engine observed. If no run is loaded there is no
    boundary to report -- this endpoint never serves a worked example as live data.
    """
    orchestrator = container.orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=404,
            detail="No active run. Containment boundaries are only reported for a real processed run.",
        )

    window = orchestrator.containment_engine.get_containment_window()
    milestones = window.milestones
    is_active = (
        window.suspect_start_cycle is not None and
        (window.release_cycle is None or window.suspect_end_cycle >= (window.release_cycle - 1))
    )
    if window.suspect_start_cycle is not None:
        summary = (
            f"Quarantine active for cycles {window.suspect_start_cycle} to {window.suspect_end_cycle} "
            f"({window.suspect_cycle_count} cycles, {window.quarantined_part_count} parts)."
        )
    else:
        summary = "No active scrap containment quarantine. Production operating within baseline envelope."

    return ContainmentBoundaryResponse(
        machine_id=container.machine_id,
        milestones=milestones,
        containment_window=window,
        is_quarantine_active=is_active,
        quarantine_summary=summary,
    )
