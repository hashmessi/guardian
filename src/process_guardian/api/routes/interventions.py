"""Intervention REST endpoints for candidate simulation, recommendations, and demo application (API-04)."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime, timezone

from process_guardian.api.schemas import (
    InterventionSimulateRequest,
    InterventionSimulateResponse,
    RecommendationResponse,
    InterventionApplyRequest,
    InterventionApplyResponse,
    InterventionHistoryResponse,
    InterventionHistoryItem,
    CandidateSimulationItem,
)
from process_guardian.api.dependencies import (
    ServiceContainer,
    get_service_container,
)
from process_guardian.storage.schemas import (
    StoredInterventionApplicationRecord,
    StoredAuditLogRecord,
)
from process_guardian.state_machine.schemas import ProcessState
from process_guardian.intervention.schemas import CandidateAction, ActionType

router = APIRouter(prefix="/interventions", tags=["Interventions"])


@router.post("/simulate", response_model=InterventionSimulateResponse)
def simulate_interventions(
    req: InterventionSimulateRequest,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Run what-if surrogate response surface optimization over candidate corrective actions.
    """
    orchestrator = container.orchestrator
    if not orchestrator.cycle_records:
        raise HTTPException(status_code=400, detail="No cycles available to simulate intervention against.")

    latest_record = orchestrator.cycle_records[-1]
    latest_drift = container.repository.list_drift_events(req.machine_id, limit=1)
    drift_output = orchestrator.results_history[-1].drift_output if orchestrator.results_history else None
    root_cause = orchestrator.results_history[-1].root_cause_report if orchestrator.results_history else None
    risk_output = orchestrator.results_history[-1].risk_output if orchestrator.results_history else None

    if not risk_output or not drift_output:
        raise HTTPException(status_code=400, detail="Insufficient pipeline state to simulate intervention.")

    # Evaluate using intervention engine
    rec, table = orchestrator.intervention_engine.evaluate(
        record=latest_record,
        fingerprint=orchestrator.fingerprint,
        risk_output=risk_output,
        drift_output=drift_output,
        root_cause_report=root_cause,
    )

    items: List[CandidateSimulationItem] = []
    for ev in table.evaluations:
        cand = ev.candidate
        items.append(
            CandidateSimulationItem(
                action_id=cand.action_id,
                name=cand.name,
                target_signal=cand.target_signal,
                delta_value=cand.delta_value,
                unit=cand.unit,
                cost=ev.cost,
                disruption=ev.disruption,
                predicted_risk=ev.post_intervention_risk,
                is_feasible=ev.constraint_check.is_feasible,
                is_selected=ev.is_selected,
            )
        )

    return InterventionSimulateResponse(
        machine_id=req.machine_id,
        cycle_index=latest_record.cycle_index,
        pre_intervention_risk=risk_output.risk_probability,
        candidates=items,
        recommended_action_id=table.recommended_action_id,
    )


@router.get("/recommendation", response_model=RecommendationResponse)
def get_recommendation(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get active 7-field recommendation contract and candidate comparison table (Screen 3 support).
    """
    orchestrator = container.orchestrator
    stored_rec = container.repository.get_latest_recommendation(machine_id)

    # If pending recommendation exists in live orchestrator
    if orchestrator.pending_recommendation:
        rec_model, table = orchestrator.pending_recommendation
        comparison = [
            CandidateSimulationItem(
                action_id=ev.candidate.action_id,
                name=ev.candidate.name,
                target_signal=ev.candidate.target_signal,
                delta_value=ev.candidate.delta_value,
                unit=ev.candidate.unit,
                cost=ev.cost,
                disruption=ev.disruption,
                predicted_risk=ev.post_intervention_risk,
                is_feasible=ev.constraint_check.is_feasible,
                is_selected=ev.is_selected,
            )
            for ev in table.evaluations
        ]

        return RecommendationResponse(
            recommendation_id=f"rec_{orchestrator.cycle_records[-1].cycle_index if orchestrator.cycle_records else 0}",
            machine_id=machine_id,
            cycle_index=orchestrator.cycle_records[-1].cycle_index if orchestrator.cycle_records else 0,
            action=rec_model.action,
            why=rec_model.why,
            evidence=rec_model.evidence,
            expected_effect=rec_model.expected_effect,
            confidence=rec_model.confidence,
            operating_limit=rec_model.operating_limit,
            recovery_check=rec_model.recovery_check,
            is_abstain=rec_model.is_abstain,
            abstain_reason=rec_model.abstain_reason,
            operator_mode=rec_model.operator_mode,
            candidate_comparison=comparison,
        )

    if stored_rec:
        candidates_db = container.repository.get_recommendation_candidates(stored_rec.recommendation_id)
        comparison = [
            CandidateSimulationItem(
                action_id=c.action_id,
                name=c.name,
                target_signal=c.target_signal,
                delta_value=c.delta_value,
                unit=c.unit,
                cost=c.cost,
                disruption=c.disruption,
                predicted_risk=c.estimated_risk,
                is_feasible=c.boundary_checked,
                is_selected=c.is_selected,
            )
            for c in candidates_db
        ]

        return RecommendationResponse(
            recommendation_id=stored_rec.recommendation_id,
            machine_id=stored_rec.machine_id,
            cycle_index=stored_rec.cycle_index,
            action=stored_rec.action_text,
            why=stored_rec.why_text,
            evidence=stored_rec.evidence_json,
            expected_effect=stored_rec.expected_effect,
            confidence=stored_rec.confidence,
            operating_limit=stored_rec.operating_limit,
            recovery_check=stored_rec.recovery_check,
            is_abstain=stored_rec.is_abstain,
            abstain_reason=stored_rec.abstain_reason,
            operator_mode=stored_rec.operator_mode,
            candidate_comparison=comparison,
        )

    # Baseline default if no recommendation generated yet
    return RecommendationResponse(
        recommendation_id="rec_none",
        machine_id=machine_id,
        cycle_index=len(orchestrator.cycle_records),
        action="Continue standard production monitoring (A0)",
        why="Process is operating within validated fingerprint envelopes.",
        evidence={"drift_status": "NONE", "risk": 0.03},
        expected_effect="Maintain continuous stable output with zero defect risk.",
        confidence=0.98,
        operating_limit="All signals within nominal recipe bounds.",
        recovery_check="Ongoing statistical sentinel checks every cycle.",
        is_abstain=False,
        abstain_reason=None,
        operator_mode="DIRECT_RECOMMENDATION",
        candidate_comparison=[],
    )


@router.post("/apply-demo", response_model=InterventionApplyResponse, status_code=status.HTTP_200_OK)
def apply_demo_intervention(
    req: InterventionApplyRequest,
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Apply recommended corrective action in demo mode.
    Transitions state from RECOMMEND to APPLIED and initializes recovery verification.
    """
    orchestrator = container.orchestrator
    if not orchestrator.cycle_records:
        raise HTTPException(status_code=400, detail="No telemetry available to apply intervention against.")

    latest_record = orchestrator.cycle_records[-1]

    # Check if there is a pending recommendation
    if not orchestrator.pending_recommendation:
        # If in healthy state, simulate application of candidate A1 or specified action
        candidate = CandidateAction(
            action_id=req.action_id or "A1",
            action_type=ActionType.TEMP_ADJUST,
            name="Decrease barrel temp zone 3",
            target_signal="barrel_temp_z3",
            delta_value=-3.0,
            unit="deg C",
            cost_weight=0.2,
            disruption_weight=0.1,
            description="Decrease barrel temp zone 3 by -3.0 deg C",
        )
        pre_risk = 0.72
    else:
        rec_model, table = orchestrator.pending_recommendation
        selected_eval = None
        if req.action_id:
            selected_eval = next((ev for ev in table.evaluations if ev.candidate.action_id == req.action_id), None)
        if not selected_eval:
            selected_eval = next((ev for ev in table.evaluations if ev.is_selected), table.evaluations[0])
        candidate = selected_eval.candidate
        pre_risk = selected_eval.pre_intervention_risk

    # Enact manual application on orchestrator
    if orchestrator.current_state != ProcessState.RECOMMEND:
        # Force transition to RECOMMEND if needed for demo elasticity
        orchestrator.state_machine.context.current_state = ProcessState.RECOMMEND

    transitions = orchestrator.manual_apply_intervention(
        candidate=candidate,
        record=latest_record,
        risk_before=pre_risk,
    )

    # Persist application to SQLite
    app_db = StoredInterventionApplicationRecord(
        cycle_index=latest_record.cycle_index,
        machine_id=req.machine_id,
        action_id=candidate.action_id,
        applied_by=req.applied_by,
        timestamp=latest_record.timestamp,
        pre_intervention_risk=pre_risk,
        target_delta=candidate.delta_value,
        status="APPLIED",
        details_json={"candidate": candidate.model_dump(), "transitions_count": len(transitions)},
    )
    container.repository.insert_intervention_application(app_db)

    # Log audit event
    container.repository.log_audit_event(
        StoredAuditLogRecord(
            event_id=f"app_{latest_record.cycle_index}_{candidate.action_id}",
            cycle_index=latest_record.cycle_index,
            machine_id=req.machine_id,
            timestamp=latest_record.timestamp,
            event_type="INTERVENTION_APPLIED",
            severity="HIGH",
            description=f"Operator {req.applied_by} applied intervention {candidate.action_id}: {candidate.target_signal or candidate.name} {candidate.delta_value:+.1f}{candidate.unit}",
            details_json=candidate.model_dump(),
        )
    )

    return InterventionApplyResponse(
        machine_id=req.machine_id,
        cycle_index=latest_record.cycle_index,
        action_id=candidate.action_id,
        status="APPLIED",
        new_state=orchestrator.current_state.value,
        message=f"Intervention {candidate.action_id} successfully applied. System entered RECOVERY_CHECK stability window.",
    )


@router.get("/history", response_model=InterventionHistoryResponse)
def get_intervention_history(
    machine_id: str = Query("IMM-01", description="Machine identifier"),
    container: ServiceContainer = Depends(get_service_container),
):
    """
    Get historical log of enacted interventions and operator applications.
    """
    apps = container.repository.list_intervention_applications(machine_id)
    items = [
        InterventionHistoryItem(
            cycle_index=a.cycle_index,
            action_id=a.action_id,
            applied_by=a.applied_by,
            timestamp=a.timestamp,
            pre_intervention_risk=a.pre_intervention_risk,
            status=a.status,
        )
        for a in apps
    ]
    return InterventionHistoryResponse(
        machine_id=machine_id,
        applications=items,
    )
