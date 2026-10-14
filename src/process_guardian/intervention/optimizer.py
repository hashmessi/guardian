"""Constrained multi-objective cost-disruption optimizer and comparison table generator (INTV-04, INTV-05)."""

from copy import deepcopy
from typing import List, Optional, Tuple
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.root_cause.schemas import RootCauseReport
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.model import QualityRiskModel
from process_guardian.intervention.schemas import (
    CandidateAction,
    ActionEvaluation,
    InterventionComparisonTable,
)
from process_guardian.intervention.candidates import CandidateGenerator, ConstraintChecker
from process_guardian.intervention.surrogate import InterventionSurrogateModel


class InterventionOptimizer:
    """
    Evaluates candidate interventions against constraints and optimizes the multi-objective cost function (INTV-04, INTV-05):
    J(A_i) = P_risk(A_i) + lambda * Cost(A_i) + mu * Disruption(A_i)
    subject to Feasible(A_i) == True.
    """

    def __init__(
        self,
        surrogate_model: InterventionSurrogateModel,
        constraint_checker: Optional[ConstraintChecker] = None,
        candidate_generator: Optional[CandidateGenerator] = None,
        cost_weight: float = 0.25,
        disruption_weight: float = 0.20,
    ):
        self.surrogate_model = surrogate_model
        self.constraint_checker = constraint_checker or ConstraintChecker()
        self.candidate_generator = candidate_generator or CandidateGenerator()
        self.cost_weight = cost_weight
        self.disruption_weight = disruption_weight

    def evaluate_candidates(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        candidates: Optional[List[CandidateAction]] = None,
        contract: Optional[QualityContract] = None,
        drift_output: Optional[DriftOutput] = None,
        root_cause_report: Optional[RootCauseReport] = None,
    ) -> InterventionComparisonTable:
        """
        Evaluate all candidate operational actions, compute objective scores, and compile comparison table (INTV-04, INTV-05).
        """
        # Baseline pre-intervention risk (snapshot extractor state to avoid contaminating live model history)
        extractor = self.surrogate_model.quality_risk_model.feature_extractor
        saved_signal_history = deepcopy(extractor.signal_history)
        saved_cycle_count = extractor.cycle_count
        try:
            base_risk_out = self.surrogate_model.quality_risk_model.predict(record=record, contract=contract)
            baseline_risk = base_risk_out.risk_probability
        finally:
            extractor.signal_history = saved_signal_history
            extractor.cycle_count = saved_cycle_count

        if candidates is None:
            candidates = self.candidate_generator.generate_candidates(
                record=record,
                fingerprint=fingerprint,
                drift_output=drift_output,
                root_cause_report=root_cause_report,
            )

        evaluations: List[ActionEvaluation] = []

        for cand in candidates:
            # 1. Constraint check (INTV-02)
            c_check = self.constraint_checker.check_constraints(cand, record, fingerprint)

            # 2. Surrogate risk prediction (INTV-03)
            post_risk, _ = self.surrogate_model.estimate_post_intervention_risk(
                record=record,
                candidate=cand,
                fingerprint=fingerprint,
                contract=contract,
            )

            # If action is DO_NOTHING, post_risk is exactly baseline risk
            if cand.action_id == "A0":
                post_risk = baseline_risk

            risk_reduction = round(baseline_risk - post_risk, 3)

            # 3. Multi-objective cost score J = P_risk + lambda * Cost + mu * Disruption (INTV-04)
            obj_score = round(
                post_risk + (self.cost_weight * cand.cost_weight) + (self.disruption_weight * cand.disruption_weight),
                4,
            )

            evaluations.append(
                ActionEvaluation(
                    candidate=cand,
                    constraint_check=c_check,
                    pre_intervention_risk=baseline_risk,
                    post_intervention_risk=post_risk,
                    risk_reduction=risk_reduction,
                    cost=cand.cost_weight,
                    disruption=cand.disruption_weight,
                    objective_score=obj_score,
                    rank=1,
                    is_selected=False,
                )
            )

        # 4. Rank candidates
        # Feasible candidates ranked by objective_score ascending
        # Infeasible candidates sorted below feasible
        feasible_evals = [e for e in evaluations if e.constraint_check.is_feasible]
        infeasible_evals = [e for e in evaluations if not e.constraint_check.is_feasible]

        feasible_evals.sort(key=lambda e: e.objective_score)
        infeasible_evals.sort(key=lambda e: e.objective_score)

        ranked = feasible_evals + infeasible_evals
        for idx, e in enumerate(ranked):
            e.rank = idx + 1

        # Select recommended action among feasible
        recommended_id = None
        if feasible_evals:
            # If baseline risk is low (< 0.35), A0 is preferred if objective score is comparable
            if baseline_risk < 0.35:
                # Find A0
                a0_eval = next((e for e in feasible_evals if e.candidate.action_id == "A0"), None)
                if a0_eval:
                    a0_eval.is_selected = True
                    recommended_id = a0_eval.candidate.action_id
                else:
                    feasible_evals[0].is_selected = True
                    recommended_id = feasible_evals[0].candidate.action_id
            else:
                # High/Medium risk: select the candidate with the lowest objective score
                feasible_evals[0].is_selected = True
                recommended_id = feasible_evals[0].candidate.action_id

        # Format comparison table summary (INTV-05)
        table_summary = self._format_table_summary(ranked, recommended_id, baseline_risk)

        return InterventionComparisonTable(
            cycle_index=record.cycle_index,
            baseline_risk=baseline_risk,
            evaluations=ranked,
            recommended_action_id=recommended_id,
            table_summary=table_summary,
        )

    def _format_table_summary(
        self,
        evaluations: List[ActionEvaluation],
        recommended_id: Optional[str],
        baseline_risk: float,
    ) -> str:
        """Format an ASCII comparison table for operator displays (INTV-05)."""
        lines = [
            f"=== Candidate Intervention Comparison (Baseline Risk: {baseline_risk * 100:.1f}%) ===",
            f"{'ID':<4} {'Action Name':<32} {'Delta':<10} {'Post-Risk':<11} {'Cost':<6} {'Disrupt':<8} {'J-Score':<8} {'Status':<10} {'Selection'}",
            "-" * 105,
        ]

        for e in evaluations:
            cand = e.candidate
            delta_str = f"{cand.delta_value:+.1f}{cand.unit}" if cand.delta_value != 0.0 else "None"
            status_str = "FEASIBLE" if e.constraint_check.is_feasible else "REJECTED"
            selection_str = "<-- RECOMMENDED" if e.candidate.action_id == recommended_id else ""
            lines.append(
                f"{cand.action_id:<4} {cand.name:<32} {delta_str:<10} "
                f"{e.post_intervention_risk * 100:>5.1f}%     {e.cost:<6.2f} {e.disruption:<8.2f} "
                f"{e.objective_score:<8.3f} {status_str:<10} {selection_str}"
            )

        return "\n".join(lines)
