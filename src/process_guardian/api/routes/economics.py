"""FastAPI Routes for Decision Economics and Parametric CoPQ (ECON-01, ECON-02)."""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from process_guardian.api.dependencies import ServiceContainer, get_service_container
from process_guardian.economics.models import (
    CoPQParameters,
    CoPQBreakdown,
    DecisionValueBreakdown,
    EconomicActionDecision,
)
from process_guardian.state_machine.schemas import ProcessState

router = APIRouter(prefix="/economics", tags=["economics"])


class ParametersUpdateResponse(BaseModel):
    """Response when CoPQ parameters are updated."""
    message: str
    parameters: CoPQParameters
    breakdown: CoPQBreakdown


@router.get("/parameters", response_model=CoPQParameters, status_code=status.HTTP_200_OK)
def get_copq_parameters(
    container: ServiceContainer = Depends(get_service_container),
) -> CoPQParameters:
    """Return active parametric Cost of Poor Quality (CoPQ) parameters."""
    if not hasattr(container, "copq_params") or container.copq_params is None:
        container.copq_params = CoPQParameters()
    return container.copq_params


@router.post("/parameters", response_model=ParametersUpdateResponse, status_code=status.HTTP_200_OK)
def update_copq_parameters(
    params: CoPQParameters,
    container: ServiceContainer = Depends(get_service_container),
) -> ParametersUpdateResponse:
    """
    Update parametric CoPQ inputs (resin price, burden rate, kWh tariff, sorting cost, etc.).
    Recalculates real-time baseline breakdown immediately.
    """
    container.copq_params = params
    if not hasattr(container, "copq_calculator") or container.copq_calculator is None:
        from process_guardian.economics.engine import CoPQCalculator
        container.copq_calculator = CoPQCalculator(container.copq_params)
    else:
        container.copq_calculator.default_params = params

    # scenario_runner holds its own copq_params/copq_calculator (constructed once with
    # the container's original CoPQParameters object) and caches scenario run results
    # keyed only by scenario_id. Reassigning container.copq_params above leaves the
    # runner pointing at the stale object, so scorecards and validation-suite INR
    # figures would keep using the old price after an update (hostile-review LOW #10).
    if hasattr(container, "scenario_runner") and container.scenario_runner:
        container.scenario_runner.copq_params = params
        container.scenario_runner.copq_calculator.default_params = params
        container.scenario_runner._cache.clear()

    breakdown = container.copq_calculator.calculate_breakdown(params)
    return ParametersUpdateResponse(
        message="CoPQ parameters successfully updated and verified.",
        parameters=params,
        breakdown=breakdown,
    )


@router.get("/copq", response_model=CoPQBreakdown, status_code=status.HTTP_200_OK)
def get_copq_breakdown(
    container: ServiceContainer = Depends(get_service_container),
) -> CoPQBreakdown:
    """
    Calculate and return current itemized Cost of Poor Quality (CoPQ) breakdown.
    Provides auditable costs across resin material, machine burden, kWh energy, and sorting.
    """
    if not hasattr(container, "copq_params") or container.copq_params is None:
        container.copq_params = CoPQParameters()
    if not hasattr(container, "copq_calculator") or container.copq_calculator is None:
        from process_guardian.economics.engine import CoPQCalculator
        container.copq_calculator = CoPQCalculator(container.copq_params)

    return container.copq_calculator.calculate_breakdown(container.copq_params)


@router.get("/decision-value", response_model=DecisionValueBreakdown, status_code=status.HTTP_200_OK)
def get_decision_value(
    cycle_index: Optional[int] = Query(None, description="Operational cycle index (defaults to latest)"),
    risk_probability: Optional[float] = Query(None, ge=0.0, le=1.0, description="Defect probability override"),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Model confidence score override"),
    horizon_cycles: int = Query(20, ge=1, le=100, description="Lookahead horizon in cycles"),
    stabilization_cycles: int = Query(3, ge=1, le=20, description="Cycles required for stabilization post-action"),
    economic_threshold: float = Query(0.0, ge=0.0, description="Decision Value economic threshold in INR"),
    is_drift_confirmed: Optional[bool] = Query(None, description="Drift confirmed status flag"),
    container: ServiceContainer = Depends(get_service_container),
) -> DecisionValueBreakdown:
    """
    Calculate real-time Cost of Waiting vs Cost of Acting decision economics (ECON-02).
    
    Formula:
        Decision Value = ExpectedLoss_wait - Cost_act
        
    Outputs signed Decision Value and operational recommendation:
    - INTERVENE_NOW if Decision Value > threshold
    - MONITOR_AND_WAIT if Decision Value <= threshold (prevents premature thermal disruption)
    - CRITICAL_QUALITY_LOCK if risk >= 75% or safety limit reached
    - ABSTAIN_UNCERTAINTY if confidence < 65%
    """
    if not hasattr(container, "copq_params") or container.copq_params is None:
        container.copq_params = CoPQParameters()
    if not hasattr(container, "decision_evaluator") or container.decision_evaluator is None:
        from process_guardian.economics.engine import CoPQCalculator, CostOfWaitingEvaluator
        container.copq_calculator = CoPQCalculator(container.copq_params)
        container.decision_evaluator = CostOfWaitingEvaluator(copq_calculator=container.copq_calculator)

    # Resolve the real cycle result to evaluate against -- never a fabricated
    # placeholder. An explicit cycle_index/risk_probability/confidence override
    # is honored outright (used by tests and scenario replay); otherwise this
    # must come from an actual processed cycle.
    orchestrator = container.orchestrator
    latest_result = None
    if orchestrator and orchestrator.results_history:
        if cycle_index is not None:
            latest_result = next(
                (r for r in orchestrator.results_history if r.cycle_index == cycle_index), None
            )
        else:
            latest_result = orchestrator.results_history[-1]

    current_cycle = cycle_index if cycle_index is not None else (
        latest_result.cycle_index if latest_result is not None else None
    )
    curr_risk = risk_probability
    curr_conf = confidence
    confirmed_drift = is_drift_confirmed

    if latest_result is not None:
        if curr_risk is None:
            curr_risk = latest_result.risk_output.risk_probability
        if curr_conf is None:
            curr_conf = latest_result.risk_output.confidence
        if confirmed_drift is None:
            state = orchestrator.current_state
            if state in (ProcessState.DRIFT_CONFIRMED, ProcessState.QUALITY_RISK_HIGH, ProcessState.RECOMMEND):
                confirmed_drift = True
            else:
                confirmed_drift = bool(latest_result.drift_output.drift)
    elif curr_risk is None or curr_conf is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No processed cycle telemetry found for decision economics. Ingest a cycle first, "
                "or pass risk_probability and confidence explicitly."
            ),
        )
    elif confirmed_drift is None:
        confirmed_drift = curr_risk >= 0.30

    if current_cycle is None:
        current_cycle = 0

    drift_rate = 0.03 if confirmed_drift else 0.0

    return container.decision_evaluator.evaluate(
        current_cycle=current_cycle,
        current_risk_probability=curr_risk,
        confidence=curr_conf,
        horizon_cycles=horizon_cycles,
        stabilization_cycles=stabilization_cycles,
        copq_params=container.copq_params,
        economic_threshold=economic_threshold,
        drift_growth_rate=drift_rate,
        is_drift_confirmed=bool(confirmed_drift),
    )
