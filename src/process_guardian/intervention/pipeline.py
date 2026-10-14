"""Unified Intervention Engine orchestrating candidate generation, boundary checking, surrogate modeling, optimization, and recommendation formatting."""

from typing import Optional, Tuple
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.schemas import QualityRiskOutput
from process_guardian.root_cause.schemas import RootCauseReport
from process_guardian.intervention.schemas import (
    InterventionComparisonTable,
    InterventionRecommendation,
    StepLimits,
)
from process_guardian.intervention.candidates import CandidateGenerator, ConstraintChecker
from process_guardian.intervention.surrogate import InterventionSurrogateModel
from process_guardian.intervention.optimizer import InterventionOptimizer
from process_guardian.intervention.recommendation import RecommendationEngine


class InterventionEngine:
    """
    Unified end-to-end intervention decision and recommendation engine (Phase 4).
    
    Coordinates:
    1. Candidate generation (A0..A4) conditioned on drift and root cause (INTV-01)
    2. Multi-constraint boundary verification (safety, recipe, envelope, step, direction) (INTV-02)
    3. Coupled physics surrogate response surface modeling for post-action risk estimation (INTV-03)
    4. Multi-objective cost-disruption optimization minimizing J = P_risk + lambda*C + mu*D (INTV-04)
    5. Comprehensive candidate comparison table compilation (INTV-05)
    6. Seven-field structured recommendation generation (RCMD-01)
    7. Operator guidance mode routing and mandatory ABSTAIN safety gate (RCMD-02, RCMD-03)
    """

    def __init__(
        self,
        risk_model: QualityRiskModel,
        step_limits: Optional[StepLimits] = None,
        min_confidence_threshold: float = 0.65,
        cost_weight: float = 0.25,
        disruption_weight: float = 0.20,
    ):
        self.risk_model = risk_model
        self.candidate_generator = CandidateGenerator(step_limits=step_limits)
        self.constraint_checker = ConstraintChecker(step_limits=step_limits)
        self.surrogate_model = InterventionSurrogateModel(quality_risk_model=risk_model)
        self.optimizer = InterventionOptimizer(
            surrogate_model=self.surrogate_model,
            constraint_checker=self.constraint_checker,
            candidate_generator=self.candidate_generator,
            cost_weight=cost_weight,
            disruption_weight=disruption_weight,
        )
        self.recommender = RecommendationEngine(min_confidence_threshold=min_confidence_threshold)

    @property
    def min_confidence_threshold(self) -> float:
        return self.recommender.min_confidence_threshold

    @min_confidence_threshold.setter
    def min_confidence_threshold(self, value: float) -> None:
        self.recommender.min_confidence_threshold = value

    def evaluate(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        risk_output: QualityRiskOutput,
        drift_output: Optional[DriftOutput] = None,
        root_cause_report: Optional[RootCauseReport] = None,
        contract: Optional[QualityContract] = None,
    ) -> Tuple[InterventionRecommendation, InterventionComparisonTable]:
        """
        Evaluate an operational cycle end-to-end and generate recommendation and comparison table.
        
        Returns:
            Tuple of (InterventionRecommendation, InterventionComparisonTable)
        """
        # 1. Generate and evaluate candidate actions via multi-objective optimizer
        comparison_table = self.optimizer.evaluate_candidates(
            record=record,
            fingerprint=fingerprint,
            contract=contract,
            drift_output=drift_output,
            root_cause_report=root_cause_report,
        )

        # 2. Format 7-field recommendation enforcing operator modes and ABSTAIN safety gate
        recommendation = self.recommender.generate_recommendation(
            record=record,
            fingerprint=fingerprint,
            comparison_table=comparison_table,
            risk_output=risk_output,
            drift_output=drift_output,
            root_cause_report=root_cause_report,
        )

        return recommendation, comparison_table
