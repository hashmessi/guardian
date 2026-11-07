"""FastAPI endpoints for Leadership Incident Brief (Executive Briefing Layer)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from process_guardian.api.dependencies import ServiceContainer, get_service_container
from process_guardian.leadership.models import LeadershipReportContext
from process_guardian.leadership.engine import LeadershipReportBuilder

router = APIRouter(prefix="/leadership", tags=["Leadership Incident Brief"])

# Global builder instance
_builder = LeadershipReportBuilder()


@router.get("/brief", response_model=LeadershipReportContext, status_code=status.HTTP_200_OK)
def get_active_leadership_brief(
    container: ServiceContainer = Depends(get_service_container),
) -> LeadershipReportContext:
    """Retrieve the Leadership Incident Brief for the currently active scenario."""
    scenario_id = container.active_scenario_id
    summary = container.active_scenario_summary

    if not summary:
        scn = container.scenario_registry.get(scenario_id)
        if not scn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active scenario '{scenario_id}' not found.",
            )
        summary = container.scenario_runner.run_scenario(scn, use_cache=True)

    return _builder.build_report(summary)


@router.get("/brief/{scenario_id}", response_model=LeadershipReportContext, status_code=status.HTTP_200_OK)
def get_scenario_leadership_brief(
    scenario_id: str,
    container: ServiceContainer = Depends(get_service_container),
) -> LeadershipReportContext:
    """Retrieve the Leadership Incident Brief for a specific scenario ID."""
    scn = container.scenario_registry.get(scenario_id)
    if not scn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found in registry.",
        )

    summary = container.scenario_runner.run_scenario(scn, use_cache=True)
    return _builder.build_report(summary)


@router.post("/brief/{scenario_id}/generate", response_model=LeadershipReportContext, status_code=status.HTTP_200_OK)
def generate_leadership_brief(
    scenario_id: str,
    force_fresh: bool = Query(False, description="Bypass cache and generate fresh AI summary"),
    container: ServiceContainer = Depends(get_service_container),
) -> LeadershipReportContext:
    """Force generation of an AI-written Leadership Incident Brief for the given scenario."""
    scn = container.scenario_registry.get(scenario_id)
    if not scn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID '{scenario_id}' not found in registry.",
        )

    summary = container.scenario_runner.run_scenario(scn, use_cache=True)
    return _builder.build_report(summary, force_fresh_ai=force_fresh)

