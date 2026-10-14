"""Intervention REST endpoints for candidate simulation, recommendations, and demo application (API-04)."""

import logging
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
    StoredCycleRecord,
    StoredContainmentWindowRecord,
)
from process_guardian.state_machine.schemas import ProcessState
from process_guardian.intervention.schemas import CandidateAction, ActionType

router = APIRouter(prefix="/interventions", tags=["Interventions"])
logger = logging.getLogger(__name__)


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

        # Only compute a decision-value breakdown from the real current cycle and its
        # actual recorded risk -- never an invented cycle/risk substitute (hostile-review
        # MEDIUM #8). No cycles or no risk_history entry means no real data to compute from.
        econ_eval = None
        if hasattr(container, "decision_evaluator") and container.decision_evaluator and orchestrator.cycle_records:
            curr_cycle = orchestrator.cycle_records[-1].cycle_index
            curr_risk = orchestrator.risk_history.get(curr_cycle)
            if curr_risk is not None:
                try:
                    econ_eval = container.decision_evaluator.evaluate(
                        current_cycle=curr_cycle,
                        current_risk_probability=curr_risk,
                        confidence=rec_model.confidence,
                        is_drift_confirmed=not rec_model.is_abstain,
                    ).model_dump()
                except Exception:
                    logger.warning("decision_value evaluation failed for cycle %s", curr_cycle, exc_info=True)
                    econ_eval = None

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
            decision_value_breakdown=econ_eval,
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

        # StoredRecommendationRecord does not persist the risk value that produced it, so
        # there is no real risk to compute a decision-value breakdown from here -- this
        # used to hardcode current_risk_probability=0.48 regardless of the actual risk
        # (hostile-review MEDIUM #8). Report no breakdown rather than a fabricated one.
        econ_eval = None

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
            decision_value_breakdown=econ_eval,
        )

    # Baseline default if no recommendation generated yet
    fallback_econ = None
    if hasattr(container, "decision_evaluator") and container.decision_evaluator:
        try:
            fallback_econ = container.decision_evaluator.evaluate(
                current_cycle=len(orchestrator.cycle_records) if orchestrator else 100,
                current_risk_probability=0.03,
                confidence=0.98,
                is_drift_confirmed=False,
            ).model_dump()
        except Exception:
            logger.warning("decision_value evaluation failed for no-recommendation baseline", exc_info=True)
            fallback_econ = None

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
        decision_value_breakdown=fallback_econ,
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

    # If an active simulator exists (demo scenario run), step the recovery cycles through
    recovery_cycles_stepped = hasattr(container, "active_sim") and bool(container.active_sim)
    if recovery_cycles_stepped:
        sim = container.active_sim
        sim.event_queue.remove_event("thermal_drift")
        sim.event_queue.remove_event("pressure_drift")
        sim.event_queue.remove_event("signal_drift")
        sim.event_queue.remove_event("moisture_drift")
        curr_c = latest_record.cycle_index
        sim.inject_event(
            event_type="recovery",
            cycle=curr_c + 1,
            severity=1.0,
            duration=None,
        )

        recovery_cycles = []
        for _ in range(3):
            raw = sim.step()
            res = orchestrator.step(raw)
            rec = res.record
            c_db = StoredCycleRecord(
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
                defect_type=None,
                raw_json=rec.model_dump(),
            )
            recovery_cycles.append(c_db)

        container.repository.insert_cycles_batch(recovery_cycles)

        # Update containment window
        win = orchestrator.get_containment_window()
        if win and win.suspect_start_cycle is not None:
            q_list = list(range(win.suspect_start_cycle, (win.suspect_end_cycle or win.suspect_start_cycle) + 1))
            win_db = StoredContainmentWindowRecord(
                machine_id=req.machine_id,
                last_known_good_cycle=win.last_known_good_cycle,
                suspect_start_cycle=win.suspect_start_cycle,
                suspect_end_cycle=win.suspect_end_cycle,
                suspect_cycle_count=win.suspect_cycle_count,
                intervention_cycle=win.intervention_cycle,
                recovery_cycle=orchestrator.cycle_records[-1].cycle_index,
                release_cycle=None,
                quarantine_cycles_json=q_list,
            )
            container.repository.upsert_containment_window(win_db)

    # The message must reflect what actually happened: whether recovery cycles ran at all,
    # and the orchestrator's real post-cycle state, not an unconditional success claim
    # (hostile-review MEDIUM #4 -- previously this text was emitted even when active_sim
    # was unset and zero recovery cycles were stepped).
    if not recovery_cycles_stepped:
        message = (
            f"Intervention {candidate.action_id} applied. No active scenario simulator -- "
            f"recovery cycles were not stepped. Mandatory physical QC checkpoint required."
        )
    elif orchestrator.current_state == ProcessState.HEALTHY:
        message = (
            f"Intervention {candidate.action_id} applied and 3 recovery cycles replayed; "
            f"process returned to HEALTHY. Mandatory physical QC checkpoint required."
        )
    else:
        message = (
            f"Intervention {candidate.action_id} applied and 3 recovery cycles replayed; "
            f"process is in {orchestrator.current_state.value}, recovery not yet confirmed. "
            f"Mandatory physical QC checkpoint required."
        )

    return InterventionApplyResponse(
        machine_id=req.machine_id,
        cycle_index=orchestrator.cycle_records[-1].cycle_index if orchestrator.cycle_records else latest_record.cycle_index,
        action_id=candidate.action_id,
        status="APPLIED",
        new_state=orchestrator.current_state.value,
        message=message,
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
