"""FastAPI endpoints for Scenario Engine and Operational Validation Suite."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status

from process_guardian.api.dependencies import ServiceContainer, get_service_container
from process_guardian.scenario.models import (
    ScenarioDefinition,
    ScenarioRunSummary,
    ScenarioScorecard,
)
from process_guardian.scenario.suite import OperationalValidationSuiteReport

router = APIRouter(prefix="/scenarios", tags=["Scenario Engine"])


@router.get("", response_model=List[ScenarioDefinition], status_code=status.HTTP_200_OK)
def list_scenarios(
    hero_only: bool = Query(False, description="Filter for the locked demo-worthy scenarios (scope_plan.md Sec.4)"),
    container: ServiceContainer = Depends(get_service_container),
) -> List[ScenarioDefinition]:
    """
    List all deterministic operational scenarios available in the Scenario Registry.
    """
    if hero_only:
        return container.scenario_registry.list_hero_scenarios()
    return container.scenario_registry.list_all()


@router.get("/active", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_active_scenario(
    container: ServiceContainer = Depends(get_service_container),
) -> Dict[str, Any]:
    """
    Return currently active scenario ID and cached run status.
    """
    scn = container.scenario_registry.get(container.active_scenario_id)
    return {
        "active_scenario_id": container.active_scenario_id,
        "scenario": scn.model_dump() if scn else None,
        "has_cached_summary": container.active_scenario_summary is not None,
        "scorecard": (
            container.active_scenario_summary.scorecard.model_dump()
            if container.active_scenario_summary
            else None
        ),
    }


@router.get("/validation-suite", response_model=OperationalValidationSuiteReport, status_code=status.HTTP_200_OK)
def get_operational_validation_suite(
    run_fresh: bool = Query(False, description="Re-run all scenarios from scratch without cache"),
    container: ServiceContainer = Depends(get_service_container),
) -> OperationalValidationSuiteReport:
    """
    Execute or retrieve the 11-scenario Operational Validation Suite scorecard and aggregate metrics.
    """
    return container.validation_suite_runner.run_all(use_cache=not run_fresh)


@router.get("/{scenario_id}", response_model=ScenarioDefinition, status_code=status.HTTP_200_OK)
def get_scenario(
    scenario_id: str,
    container: ServiceContainer = Depends(get_service_container),
) -> ScenarioDefinition:
    """
    Retrieve single scenario definition with narrative milestones and expected outcome.
    """
    scn = container.scenario_registry.get(scenario_id)
    if not scn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found in registry.",
        )
    return scn


class ScenarioSelectRequest(BaseModel):
    scenario_id: str


def _select_failure(container: ServiceContainer, scenario_id: str, exc: ValueError) -> HTTPException:
    """Tell "no such scenario" apart from "the replay blew up".

    `select_scenario` raises ValueError for an unknown id, but the replay and
    live-state activation it runs afterwards can raise ValueError for entirely
    unrelated reasons. Reporting both as 404 "not found in registry" sends
    whoever is debugging it hunting for a missing scenario that is in fact
    sitting right there in the registry.
    """
    if container.scenario_registry.get(scenario_id) is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found in registry.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Scenario '{scenario_id}' exists but failed during replay: {exc}",
    )


@router.post("/select", response_model=ScenarioRunSummary, status_code=status.HTTP_200_OK)
def select_scenario_body(
    req: ScenarioSelectRequest,
    container: ServiceContainer = Depends(get_service_container),
) -> ScenarioRunSummary:
    """Select active scenario in the plant system via JSON body."""
    try:
        return container.select_scenario(req.scenario_id)
    except ValueError as e:
        raise _select_failure(container, req.scenario_id, e)


@router.post("/{scenario_id}/select", response_model=ScenarioRunSummary, status_code=status.HTTP_200_OK)
def select_scenario(
    scenario_id: str,
    container: ServiceContainer = Depends(get_service_container),
) -> ScenarioRunSummary:
    """
    Select active scenario in the plant system and return replay trajectory with scorecard.
    """
    try:
        summary = container.select_scenario(scenario_id)
        return summary
    except ValueError as e:
        raise _select_failure(container, scenario_id, e)


@router.post("/{scenario_id}/run", response_model=ScenarioRunSummary, status_code=status.HTTP_200_OK)
def run_scenario(
    scenario_id: str,
    use_cache: bool = Query(False, description="Use in-memory cached run if available"),
    container: ServiceContainer = Depends(get_service_container),
) -> ScenarioRunSummary:
    """
    Execute full scenario run through Guardian decision pipeline and dual counterfactual comparator.
    """
    scn = container.scenario_registry.get(scenario_id)
    if not scn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found in registry.",
        )
    return container.scenario_runner.run_scenario(scn, use_cache=use_cache)
