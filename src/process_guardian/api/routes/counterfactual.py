"""FastAPI Routes for Controlled Counterfactual Replay Canvas (CRPL-01, CRPL-02)."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator

from process_guardian.api.dependencies import ServiceContainer, get_service_container
from process_guardian.counterfactual.models import CounterfactualComparison
from process_guardian.counterfactual.engine import CounterfactualReplayEngine

router = APIRouter(prefix="/counterfactual", tags=["counterfactual_replay"])


class ReplayRequest(BaseModel):
    total_cycles: int = Field(default=156, ge=90, le=250, description="Total replay horizon in cycles")
    drift_start_cycle: int = Field(default=72, ge=10, description="Cycle index of drift onset")
    intervention_cycle: int = Field(default=85, ge=75, description="Cycle index of corrective intervention")

    @model_validator(mode="after")
    def _validate_cycle_ordering(self) -> "ReplayRequest":
        if not (self.drift_start_cycle < self.intervention_cycle):
            raise ValueError("drift_start_cycle must be before intervention_cycle")
        # Recovery/QC/release milestones land at intervention_cycle + 5/7/8 (see
        # CounterfactualReplayEngine defaults) -- leave room for them plus a few
        # stable cycles so the suspect window actually closes within the replay.
        if not (self.total_cycles >= self.intervention_cycle + 15):
            raise ValueError("total_cycles must be at least intervention_cycle + 15")
        return self


@router.get("/compare", response_model=CounterfactualComparison, status_code=status.HTTP_200_OK)
def get_counterfactual_comparison(
    total_cycles: int = Query(156, ge=90, le=250, description="Replay horizon in cycles"),
    container: ServiceContainer = Depends(get_service_container),
) -> CounterfactualComparison:
    """
    Generate deterministic dual counterfactual comparison (CRPL-01, CRPL-02).
    Compares Guardian OFF (Status Quo uncontained scrap) vs Guardian ON (Dynamic Quality Reaction).

    Built fresh from the container's *current* CoPQ parameters on every call --
    never cached -- so a prior POST /economics/parameters update is reflected
    immediately instead of silently showing stale figures (replay below already
    did this correctly; compare did not).
    """
    engine = CounterfactualReplayEngine(copq_params=container.copq_params, total_cycles=total_cycles)
    return engine.generate_comparison(total_cycles=total_cycles)


@router.post("/replay", response_model=CounterfactualComparison, status_code=status.HTTP_200_OK)
def execute_counterfactual_replay(
    payload: ReplayRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> CounterfactualComparison:
    """
    Execute customized dual counterfactual replay with configurable parameters.
    """
    engine = CounterfactualReplayEngine(
        copq_params=container.copq_params,
        total_cycles=payload.total_cycles,
        drift_start_cycle=payload.drift_start_cycle,
        intervention_cycle=payload.intervention_cycle,
    )
    return engine.generate_comparison(total_cycles=payload.total_cycles)
