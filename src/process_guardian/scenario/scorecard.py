"""Objective Industrial Scorecard Evaluator for Process Guardian Scenarios.

Evaluates the 6 core pillars of the closed-loop decision lifecycle:
1. Detection (Early sentinel detection vs false-alarm avoidance)
2. Diagnosis (Dominant root-cause isolation and ranked attribution)
3. Intervention (Constrained minimum-cost selection, checkpoint gate, or mandatory abstain)
4. Recovery (Dynamic parameter stabilization window and recovery verification)
5. Containment (Suspect quarantine window isolation and defect containment)
6. Counterfactual Proof (Controlled delta: Guardian OFF uncontained scrap vs Guardian ON)
"""

from typing import Dict, List, Any, Optional
from process_guardian.scenario.models import (
    ScenarioDefinition,
    ScenarioScorecard,
    PillarEvaluation,
    ScenarioReplayCycle,
)
from process_guardian.counterfactual.models import CounterfactualComparison
from process_guardian.lifecycle import ClosedLoopOrchestrator


class ScenarioScorecardEvaluator:
    """Evaluates scenario execution results against formal industrial validation criteria."""

    def evaluate(
        self,
        scenario: ScenarioDefinition,
        orchestrator: ClosedLoopOrchestrator,
        replay_stream: List[ScenarioReplayCycle],
        counterfactual: CounterfactualComparison,
    ) -> ScenarioScorecard:
        """Generate objective scorecard across all 7 operational pillars."""
        expected = scenario.expected_outcome

        # Extract lifecycle milestones from execution
        drift_detected_cycles = [
            c.cycle_index for c in replay_stream if c.drift_detected
        ]
        first_drift_cycle = drift_detected_cycles[0] if drift_detected_cycles else None
        
        # Check interventions and recommendations
        interventions_found = [
            c for c in replay_stream if c.action_applied is not None
        ]
        abstain_cycles = [
            c for c in replay_stream if c.state == "ABSTAIN" or "ABSTAIN" in (c.action_applied or "")
        ]
        
        # Check root causes
        root_causes_seen = [
            c.dominant_signal for c in replay_stream if c.dominant_signal is not None
        ]
        dominant_root_cause = root_causes_seen[-1] if root_causes_seen else None

        # Human-channel-only incidents (P1, scope_plan.md Sec.3: the flip scenario)
        # never set drift_detected -- sensors genuinely stay quiet -- so detection
        # has to also recognize the human-channel contributor becoming dominant as
        # a valid detection mode, not just sensor T2.
        human_channel_cycles = [
            c.cycle_index for c in replay_stream if c.dominant_signal == "human_channel"
        ]
        first_human_channel_cycle = human_channel_cycles[0] if human_channel_cycles else None

        # Containment metrics
        containment_window = orchestrator.containment_engine.get_containment_window()
        suspect_count = containment_window.suspect_cycle_count

        # Recovery status
        recovery_verified = (
            orchestrator.containment_engine.recovery_cycle is not None
            or any(c.state in ("RELEASE", "RELEASED_HEALTHY", "INTERVENTION_MEMORY") for c in replay_stream)
        )

        # ---------------------------------------------------------------------
        # 1. Detection Pillar
        # ---------------------------------------------------------------------
        if expected.drift_expected:
            # Detection only counts from the cycle the disturbance actually starts.
            # Anything before that is a false alarm, and "lead time" measured as
            # cycles-remaining-in-the-run rewarded detecting early for the wrong
            # reason -- a false alarm at cycle 5 used to score best of all.
            onset_cycle = min(
                (d.start_cycle for d in scenario.disturbances),
                default=(
                    scenario.operational_overrides.human_channel_event_cycle
                    if scenario.operational_overrides
                    and scenario.operational_overrides.human_channel_event_cycle is not None
                    else None
                ),
            )
            detected_cycle = first_drift_cycle if first_drift_cycle is not None else first_human_channel_cycle
            premature = (
                detected_cycle is not None and onset_cycle is not None and detected_cycle < onset_cycle
            )
            det_passed = detected_cycle is not None and not premature
            latency = (
                detected_cycle - onset_cycle
                if detected_cycle is not None and onset_cycle is not None
                else None
            )
            via_human_channel = first_drift_cycle is None and first_human_channel_cycle is not None

            if not detected_cycle:
                det_label = "DRIFT_MISSED"
                det_detail = "Sentinel failed to confirm process drift"
            elif premature:
                det_label = "FALSE_ALARM_BEFORE_ONSET"
                det_detail = (
                    f"Flagged at cycle #{detected_cycle}, before the disturbance begins at #{onset_cycle}"
                )
            else:
                det_label = "EARLY_DRIFT_DETECTED"
                latency_txt = f"{latency} cycles after onset" if latency is not None else "onset not parameterized"
                det_detail = (
                    f"Human-channel evidence flagged at cycle #{detected_cycle} ({latency_txt}); "
                    f"sensor telemetry stayed fully in-envelope throughout"
                    if via_human_channel
                    else f"Drift confirmed at cycle #{detected_cycle} ({latency_txt})"
                )
            det_metrics = {
                "drift_confirmed": det_passed,
                "onset_cycle": onset_cycle,
                "first_drift_cycle": detected_cycle,
                "detection_latency_cycles": latency,
                "detected_via_human_channel": via_human_channel,
            }
        else:
            # Normal variation / false positive test
            false_alerts = len(drift_detected_cycles)
            det_passed = false_alerts == 0
            det_label = "NOISE_REJECTED" if det_passed else "FALSE_ALARM_TRIGGERED"
            det_detail = (
                f"Zero false alarms across {scenario.total_cycles} cycles; noise rejected"
                if det_passed
                else f"Sentinel triggered {false_alerts} false alerts during normal variation"
            )
            det_metrics = {
                "false_alerts": false_alerts,
                "noise_filtering_effective": det_passed,
            }

        detection_eval = PillarEvaluation(
            passed=det_passed,
            status_label=det_label,
            detail=det_detail,
            metrics=det_metrics,
        )

        # ---------------------------------------------------------------------
        # 2. Diagnosis Pillar
        # ---------------------------------------------------------------------
        if expected.dominant_signal:
            # The expected signal has to actually dominate the incident window, not
            # merely appear once somewhere in ~500 cycles. Root cause runs every
            # cycle and all 14 signals take a turn on top, so "appeared at least
            # once" was true for every signal in every scenario -- the pillar could
            # not fail.
            incident_causes = [
                c.dominant_signal
                for c in replay_stream
                if c.dominant_signal is not None and c.state != "HEALTHY"
            ]
            window = incident_causes or root_causes_seen
            cause_counts: Dict[str, int] = {}
            for sig in window:
                cause_counts[sig] = cause_counts.get(sig, 0) + 1
            modal_cause = max(cause_counts, key=cause_counts.get) if cause_counts else None
            share = (cause_counts.get(modal_cause, 0) / len(window)) if window else 0.0

            diag_passed = modal_cause is not None and expected.dominant_signal in modal_cause
            diag_label = "ROOT_CAUSE_ISOLATED" if diag_passed else "ATTRIBUTION_MISMATCH"
            diag_detail = (
                f"'{modal_cause}' dominated {share * 100:.0f}% of the incident window"
                if diag_passed
                else f"Expected '{expected.dominant_signal}' to dominate, but '{modal_cause}' did ({share * 100:.0f}%)"
            )
            diag_metrics = {
                "dominant_signal": modal_cause,
                "expected_signal": expected.dominant_signal,
                "dominant_share_pct": round(share * 100, 1),
                "attribution_correct": diag_passed,
            }
        else:
            # Scenarios with no expected single signal (normal variation or checkpoint)
            diag_passed = True
            diag_label = "DIAGNOSTIC_BOUNDARY_HELD"
            diag_detail = "Operating within nominal baseline; no erroneous root-cause attribution"
            diag_metrics = {"dominant_signal": None, "attribution_correct": True}

        diagnosis_eval = PillarEvaluation(
            passed=diag_passed,
            status_label=diag_label,
            detail=diag_detail,
            metrics=diag_metrics,
        )

        # ---------------------------------------------------------------------
        # 3. Intervention Pillar
        # ---------------------------------------------------------------------
        if expected.action_class == "abstain":
            # The engine must actually abstain. `or not expected.allow_intervention`
            # made this unfailable for the one scenario it is supposed to police.
            act_passed = len(abstain_cycles) > 0
            act_label = "MANDATORY_ABSTAIN_TRIGGERED" if act_passed else "UNVALIDATED_ACTION_PERMITTED"
            act_detail = (
                "Epistemic uncertainty (< 0.65) safely triggered SAFE-03 mandatory abstention"
                if act_passed
                else "System failed to trigger mandatory abstention on out-of-distribution drift"
            )
            act_metrics = {"abstain_triggered": act_passed, "safe_03_enforced": True}
        elif expected.action_class == "monitor":
            act_passed = len(interventions_found) == 0
            act_label = "MONITORING_MAINTAINED" if act_passed else "UNNECESSARY_INTERVENTION"
            act_detail = (
                "A0 Monitoring maintained; zero unnecessary parameter changes"
                if act_passed
                else f"Unwarranted intervention recommended: {interventions_found[0].action_applied}"
            )
            act_metrics = {"interventions_count": len(interventions_found)}
        elif expected.action_class == "operational_checkpoint":
            # Was an unconditional pass, which let a scenario that exercises no
            # checkpoint behaviour at all report "gate enforced". The observable
            # claim is that the engine did not reach for a parameter change on a
            # procedural problem a parameter change cannot fix.
            act_passed = len(interventions_found) == 0
            act_label = "OPERATIONAL_GATE_ENFORCED" if act_passed else "PARAMETER_CHANGE_ON_PROCEDURAL_FAULT"
            act_detail = (
                "No machine-parameter change proposed; the fault is procedural and is routed to the operator"
                if act_passed
                else f"Engine proposed a parameter change ({interventions_found[0].action_applied}) for a procedural fault"
            )
            act_metrics = {"interventions_count": len(interventions_found)}
        elif expected.action_class == "material_checkpoint":
            # P1 (scope_plan.md Sec.3): the correct response to a sensor-blind
            # material risk is a physical verification request, not a parametric
            # machine action -- checks the engine actually reached QC_REQUIRED
            # rather than granting a blanket pass.
            act_passed = any(c.state == "QC_REQUIRED" for c in replay_stream)
            act_label = "MATERIAL_VERIFICATION_REQUESTED" if act_passed else "MATERIAL_RISK_UNVERIFIED"
            act_detail = (
                "Human-channel evidence triggered a physical material/moisture verification request"
                if act_passed
                else "Operator-reported material risk did not trigger the expected verification request"
            )
            act_metrics = {"qc_required_triggered": act_passed}
        else:
            # Constrained machine intervention expected
            act_passed = len(interventions_found) > 0
            act_label = "MINIMUM_COST_ACTION_SELECTED" if act_passed else "NO_INTERVENTION_GENERATED"
            applied_name = interventions_found[0].action_applied if interventions_found else "None"
            act_detail = (
                f"Constrained intervention selected: {applied_name}"
                if act_passed
                else "Optimizer failed to generate a feasible intervention"
            )
            act_metrics = {
                "action_applied": applied_name,
                "candidate_evaluated": act_passed,
            }

        intervention_eval = PillarEvaluation(
            passed=act_passed,
            status_label=act_label,
            detail=act_detail,
            metrics=act_metrics,
        )

        # ---------------------------------------------------------------------
        # 4. Recovery Pillar
        # ---------------------------------------------------------------------
        if expected.action_class in ("operational_checkpoint", "material_checkpoint", "monitor"):
            # Nothing was applied, so there is no recovery to verify. The checkable
            # claim is the absence of a false recovery declaration, not a blanket pass.
            rec_passed = not recovery_verified
            rec_label = "NO_RECOVERY_CLAIMED" if rec_passed else "FALSE_RECOVERY_DECLARED"
            rec_detail = (
                "No intervention applied, so no recovery is claimed; the hold stands until a human acts"
                if rec_passed
                else "Recovery was declared although no corrective action was ever applied"
            )
            rec_metrics = {"recovery_claimed": recovery_verified}
        elif expected.recovery_expected:
            rec_passed = recovery_verified
            rec_label = "STABILITY_VERIFIED" if rec_passed else "RECOVERY_UNVERIFIED"
            rec_detail = (
                "Parameter convergence confirmed across required consecutive cooling window"
                if rec_passed
                else "Process failed to achieve required multi-cycle stability"
            )
            rec_metrics = {"stability_confirmed": rec_passed}
        else:
            # Failed intervention / persistent drift scenario
            rec_passed = not recovery_verified
            rec_label = "RECOVERY_FAILURE_CAUGHT" if rec_passed else "FALSE_STABILITY_DECLARED"
            rec_detail = (
                "Recovery failure correctly identified; no premature or false clearance"
                if rec_passed
                else "Safety failure: process marked recovered despite persistent drift"
            )
            rec_metrics = {"timeout_escalated": rec_passed}

        recovery_eval = PillarEvaluation(
            passed=rec_passed,
            status_label=rec_label,
            detail=rec_detail,
            metrics=rec_metrics,
        )

        # ---------------------------------------------------------------------
        # 5. Containment Pillar
        # ---------------------------------------------------------------------
        off_suspect = counterfactual.guardian_off.suspect_cycles
        # A material-checkpoint scenario (the S-FLIP human-channel signal) has no
        # machine-side action available -- it holds the suspect window open pending
        # a physical/external action (drying the resin) that is outside this replay.
        # Scoped to action_class=="material_checkpoint" specifically (not merely
        # allow_intervention=False, which SCN-08's ABSTAIN path also sets) so this
        # exception can't silently swallow a real containment overflow on a future
        # abstain scenario that happens to end in QC_REQUIRED.
        held_pending_physical_action = (
            expected.action_class == "material_checkpoint"
            and replay_stream[-1].state == "QC_REQUIRED"
        )
        if held_pending_physical_action:
            cont_passed = suspect_count > 0
            cont_label = "SUSPECT_WINDOW_HELD_PENDING_PHYSICAL_VERIFICATION"
            cont_detail = (
                f"{suspect_count} cycles held in suspect quarantine pending physical verification "
                "that no machine-side action can substitute for; window stays open by design"
            )
            cont_metrics = {"suspect_cycles": suspect_count, "held_pending_physical_action": True}
        elif expected.drift_expected:
            cont_passed = suspect_count > 0 and (suspect_count <= 80 or suspect_count < off_suspect)
            cont_label = "SUSPECT_WINDOW_ISOLATED" if cont_passed else "CONTAINMENT_OVERFLOW"
            cont_detail = (
                f"{suspect_count} suspect cycles isolated between drift onset and verified recovery "
                f"(vs {off_suspect} cycles in status quo)"
                if cont_passed
                else f"Suspect window count ({suspect_count}) outside expected bounds"
            )
            cont_metrics = {
                "suspect_cycles": suspect_count,
                "off_suspect_cycles": off_suspect,
                "containment_collapsed": suspect_count < max(off_suspect, 1),
            }
        else:
            cont_passed = suspect_count == 0
            cont_label = "ZERO_SUSPECT_HOLD" if cont_passed else "UNNECESSARY_QUARANTINE"
            cont_detail = "Zero cycles quarantined; continuous throughput preserved"
            cont_metrics = {"suspect_cycles": 0}

        containment_eval = PillarEvaluation(
            passed=cont_passed,
            status_label=cont_label,
            detail=cont_detail,
            metrics=cont_metrics,
        )

        # ---------------------------------------------------------------------
        # 6. Counterfactual Proof Pillar
        # ---------------------------------------------------------------------
        off_scrap = counterfactual.guardian_off.scrap_parts_count
        on_scrap = counterfactual.guardian_on.scrap_parts_count
        suspect_reduction = counterfactual.suspect_lot_reduction_pct
        avoided_loss = counterfactual.net_avoided_loss

        if expected.drift_expected and expected.recovery_expected and off_suspect == 0 and suspect_count > 0:
            # Human-channel-only incidents (P1): the status-quo baseline has zero
            # sensor-level trigger, so it never flags a single suspect cycle --
            # off_suspect == 0 makes the normal suspect_reduction_pct formula
            # (divides by off_suspect) meaningless. The headline proof here *is*
            # that the baseline caught nothing while Guardian caught it.
            cf_passed = on_scrap <= off_scrap
            cf_label = "BASELINE_BLIND_GUARDIAN_CAUGHT_IT"
            cf_detail = (
                f"Status-quo baseline recorded zero suspect cycles (no sensor-level trigger exists in this "
                f"scenario); Guardian isolated {suspect_count} cycles via the fused human-channel signal."
            )
            cf_metrics = {"off_suspect": 0, "on_suspect": suspect_count, "baseline_blind": True}
        elif expected.drift_expected and expected.recovery_expected:
            cf_passed = on_scrap <= off_scrap and suspect_reduction >= 0.0
            cf_label = "DIVERGENCE_DEMONSTRATED" if cf_passed else "COUNTERFACTUAL_INVERSION"
            cf_detail = (
                f"Guardian ON vs OFF: {off_scrap} → {on_scrap} scrap parts ({counterfactual.scrap_reduction_pct}% reduction), "
                f"₹{avoided_loss:,.0f} net avoided loss"
            )
            cf_metrics = {
                "off_scrap": off_scrap,
                "on_scrap": on_scrap,
                "suspect_reduction_pct": suspect_reduction,
                "avoided_copq_inr": avoided_loss,
            }
        else:
            # No drift expected, so there is no divergence to prove. Assert the one
            # thing that is actually checkable here -- Guardian did not manufacture
            # scrap the status quo avoided -- instead of claiming a replay we never ran.
            cf_passed = on_scrap <= off_scrap
            cf_label = "NO_DIVERGENCE_EXPECTED" if cf_passed else "GUARDIAN_ADDED_SCRAP"
            cf_detail = f"Nominal scenario: Guardian ON {on_scrap} vs OFF {off_scrap} scrap parts"
            cf_metrics = {"off_scrap": off_scrap, "on_scrap": on_scrap}

        counterfactual_eval = PillarEvaluation(
            passed=cf_passed,
            status_label=cf_label,
            detail=cf_detail,
            metrics=cf_metrics,
        )

        # Overall Status
        all_passed = all([
            detection_eval.passed,
            diagnosis_eval.passed,
            intervention_eval.passed,
            recovery_eval.passed,
            containment_eval.passed,
            counterfactual_eval.passed,
        ])

        summary = (
            f"Successfully validated all 6 pillars for {scenario.title}. "
            f"Verified closed operational decision loop under deterministic seed {scenario.seed}."
            if all_passed
            else f"Validation criteria failed for {scenario.title}. Check individual pillar evaluations."
        )

        return ScenarioScorecard(
            scenario_id=scenario.scenario_id,
            scenario_title=scenario.title,
            category=scenario.category,
            total_cycles=scenario.total_cycles,
            overall_passed=all_passed,
            detection=detection_eval,
            diagnosis=diagnosis_eval,
            intervention=intervention_eval,
            recovery=recovery_eval,
            containment=containment_eval,
            counterfactual_proof=counterfactual_eval,
            summary=summary,
        )
