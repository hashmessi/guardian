"""Seven-Field Recommendation Contract, Operator Modes, and Mandatory ABSTAIN Safety Gate (RCMD-01..03)."""

from typing import Optional, List
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.schemas import QualityRiskOutput, RiskState
from process_guardian.root_cause.schemas import RootCauseReport
from process_guardian.intervention.schemas import (
    ActionType,
    CandidateAction,
    InterventionComparisonTable,
    InterventionRecommendation,
    ActionEvaluation,
)

BANNED_DOGMATIC_WORDS = [
    "guarantee",
    "guaranteed",
    "proven causal",
    "will definitely cure",
    "certain cause",
    "foolproof",
    "100% fix",
    "absolute certainty",
]


class RecommendationEngine:
    """
    Produces honest, structured 7-field recommendations with explicit operator modes and ABSTAIN safety gate.
    
    Fields (RCMD-01):
    1. ACTION: Concrete operational action or ABSTAIN directive.
    2. WHY: Root cause diagnosis and risk justification.
    3. EVIDENCE: Empirical quantitative telemetry, z-scores, and slope metrics.
    4. EXPECTED_EFFECT: Estimated defect risk reduction from surrogate model.
    5. CONFIDENCE: Calibrated confidence score in [0.0, 1.0].
    6. OPERATING_LIMIT: Safety, recipe, and operating envelope boundary compliance.
    7. RECOVERY_CHECK: Concrete verification criteria for post-intervention stability (Phase 5).
    """

    def __init__(self, min_confidence_threshold: float = 0.65):
        self.min_confidence_threshold = min_confidence_threshold

    def generate_recommendation(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        comparison_table: InterventionComparisonTable,
        risk_output: QualityRiskOutput,
        drift_output: Optional[DriftOutput] = None,
        root_cause_report: Optional[RootCauseReport] = None,
    ) -> InterventionRecommendation:
        """
        Generate the 7-field recommendation enforcing operator modes and ABSTAIN safety gate (RCMD-01..03).
        """
        risk = risk_output.risk_probability
        confidence = risk_output.confidence
        rec_id = comparison_table.recommended_action_id
        selected_eval: Optional[ActionEvaluation] = None

        if rec_id:
            selected_eval = next((e for e in comparison_table.evaluations if e.candidate.action_id == rec_id), None)

        # ---------------------------------------------------------
        # Case 1: LOW RISK (P < 0.35) -> NORMAL_MONITORING
        # ---------------------------------------------------------
        if risk < 0.35:
            rec = InterventionRecommendation(
                action="CONTINUE_MONITORING",
                why="Process is operating stably within approved tolerances; defect probability is low.",
                evidence=self._build_evidence_summary(record, fingerprint, drift_output, root_cause_report),
                expected_effect=f"Process stability maintained at nominal modeled defect risk ({risk * 100:.1f}%).",
                confidence=confidence,
                operating_limit="All monitored parameters remain compliant with approved recipe limits and fingerprint envelopes.",
                recovery_check="Maintain standard cycle monitoring; no parameter intervention required.",
                operator_mode="NORMAL_MONITORING",
                is_abstain=False,
                abstain_reason=None,
                cycle_index=record.cycle_index,
                timestamp=record.timestamp,
                candidate_id="A0",
            )
            self._lint_epistemics(rec)
            return rec

        # ---------------------------------------------------------
        # Case 2: MEDIUM RISK (0.35 <= P <= 0.70) -> REQUEST_QC_SAMPLE
        # ---------------------------------------------------------
        if risk <= 0.70:
            rec = InterventionRecommendation(
                action="REQUEST_QC_SAMPLE",
                why="Process telemetry indicates emerging statistical drift with moderate quality contract risk. Physical sample verification required before parameter alteration.",
                evidence=self._build_evidence_summary(record, fingerprint, drift_output, root_cause_report),
                expected_effect="Physical inspection of next 3 part samples confirms weight, dimensions, and sink mark compliance before machine intervention.",
                confidence=confidence,
                operating_limit="Current parameters approaching warning boundaries but remain within recipe tolerances.",
                recovery_check="Verify part weight in [141.0, 144.0] g and sink mark depth <= 0.08 mm on sampled parts.",
                operator_mode="REQUEST_QC_SAMPLE",
                is_abstain=False,
                abstain_reason=None,
                cycle_index=record.cycle_index,
                timestamp=record.timestamp,
                candidate_id=None,
            )
            self._lint_epistemics(rec)
            return rec

        # ---------------------------------------------------------
        # Case 3: HIGH RISK (P > 0.70)
        # Check ABSTAIN gate: low confidence OR all actions infeasible (RCMD-03)
        # ---------------------------------------------------------
        all_infeasible = not any(e.constraint_check.is_feasible for e in comparison_table.evaluations if e.candidate.action_id != "A0")
        low_confidence = confidence < self.min_confidence_threshold

        if low_confidence or all_infeasible or selected_eval is None or not selected_eval.constraint_check.is_feasible:
            # Enforce Mandatory ABSTAIN Gate (RCMD-03)
            if low_confidence:
                abstain_reason = (
                    f"Low epistemic confidence ({confidence:.2f} < {self.min_confidence_threshold:.2f} threshold). "
                    "Automated parameter adjustment withheld to prevent unverified machine disturbance."
                )
            else:
                abstain_reason = (
                    "All evaluated candidate adjustments violate physical machine safety limits or recipe bounds. "
                    "Automated parameter intervention blocked."
                )

            rec = InterventionRecommendation(
                action="ABSTAIN_AND_MONITOR",
                why=f"High defect risk ({risk * 100:.1f}%) observed, but automated parameter intervention is withheld by safety gate. {abstain_reason}",
                evidence=self._build_evidence_summary(record, fingerprint, drift_output, root_cause_report),
                expected_effect="Withholding automated parameter shift prevents potential process oscillation; manual quality inspection requested.",
                confidence=confidence,
                operating_limit="Machine safety and recipe limit interlocks are active; candidate adjustments exceed envelope boundaries.",
                recovery_check="Immediate manual process review and root-cause inspection by senior technician required.",
                operator_mode="ABSTAIN_AND_MONITOR",
                is_abstain=True,
                abstain_reason=abstain_reason,
                cycle_index=record.cycle_index,
                timestamp=record.timestamp,
                candidate_id=None,
            )
            self._lint_epistemics(rec)
            return rec

        # ---------------------------------------------------------
        # Case 4: HIGH RISK & HIGH CONFIDENCE & FEASIBLE -> RECOMMEND_ACTION
        # ---------------------------------------------------------
        cand = selected_eval.candidate
        sig = cand.target_signal or "parameters"
        curr_val = getattr(record, sig, 0.0) if cand.target_signal else 0.0
        target_val = selected_eval.constraint_check.proposed_value or (curr_val + cand.delta_value)

        action_text = f"ADJUST {sig} BY {cand.delta_value:+.1f}{cand.unit} (from {curr_val:.1f}{cand.unit} to {target_val:.1f}{cand.unit})"

        why_text = self._build_why_justification(cand, root_cause_report, risk)
        evidence_text = self._build_evidence_summary(record, fingerprint, drift_output, root_cause_report)
        expected_effect_text = (
            f"Modeled effect: reduces predicted defect risk from {risk * 100:.1f}% to "
            f"{selected_eval.post_intervention_risk * 100:.1f}% (-{selected_eval.risk_reduction * 100:.1f}% estimated drop)."
        )

        operating_limit_text = (
            f"Target value {target_val:.1f}{cand.unit} satisfies machine safety bounds, approved recipe limits, "
            f"and operating envelope constraints."
        )

        recovery_check_text = self._build_recovery_check(cand, target_val)

        rec = InterventionRecommendation(
            action=action_text,
            why=why_text,
            evidence=evidence_text,
            expected_effect=expected_effect_text,
            confidence=confidence,
            operating_limit=operating_limit_text,
            recovery_check=recovery_check_text,
            operator_mode="RECOMMEND_ACTION",
            is_abstain=False,
            abstain_reason=None,
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            candidate_id=cand.action_id,
        )
        self._lint_epistemics(rec)
        return rec

    def _build_why_justification(
        self,
        candidate: CandidateAction,
        root_cause_report: Optional[RootCauseReport],
        risk: float,
    ) -> str:
        """Formulate honest root-cause why justification."""
        if root_cause_report and root_cause_report.contributors:
            top = root_cause_report.contributors[0]
            return (
                f"{top.display_name} is identified as the likely primary contributor ({top.contribution_pct:.1f}% attributed contribution) "
                f"driving elevated quality contract risk ({risk * 100:.1f}%). Adjusting {candidate.target_signal} directly opposes observed drift."
            )
        return (
            f"Observed telemetry drift drives elevated quality contract risk ({risk * 100:.1f}%). "
            f"Candidate {candidate.action_id} provides minimum effective intervention."
        )

    def _build_evidence_summary(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        drift_output: Optional[DriftOutput],
        root_cause_report: Optional[RootCauseReport],
    ) -> str:
        """Synthesize empirical evidence metrics (deviations, z-scores, slopes)."""
        ev_parts: List[str] = []
        if root_cause_report and root_cause_report.contributors:
            for item in root_cause_report.contributors[:2]:
                ev_parts.append(
                    f"{item.signal_name}: z-score={item.z_score:+.2f}, slope={item.slope_per_cycle:+.3f}/cycle"
                )
        elif drift_output and drift_output.signals:
            for sig in drift_output.signals[:2]:
                if sig in drift_output.details:
                    d = drift_output.details[sig]
                    ev_parts.append(f"{sig}: val={d.current_value:.2f}, z-score={d.z_score:+.2f}")

        if not ev_parts:
            z3 = getattr(record, "barrel_temp_z3", 230.0)
            p_peak = getattr(record, "peak_pressure", 135.0)
            ev_parts.append(f"barrel_temp_z3={z3:.1f}°C, peak_pressure={p_peak:.1f} bar")

        return "; ".join(ev_parts)

    def _build_recovery_check(self, candidate: CandidateAction, target_val: float) -> str:
        """Define concrete post-intervention verification criteria for Phase 5."""
        sig = candidate.target_signal
        unit = candidate.unit
        if candidate.action_type == ActionType.TEMP_ADJUST:
            return f"Verify {sig} stabilizes <= {target_val + 0.5:.1f}{unit} within 3 cycles and defect risk drops below 35%."
        elif candidate.action_type == ActionType.PRESSURE_ADJUST:
            return f"Verify {sig} reaches {target_val:.1f}{unit} within 1 cycle and cavity peak pressure returns to baseline envelope."
        elif candidate.action_type == ActionType.CYCLE_TIME_ADJUST:
            return f"Verify {sig} is maintained at {target_val:.1f}{unit} and part weight stabilizes in [141.0, 144.0] g."
        elif candidate.action_type == ActionType.MATERIAL_INSPECT_PURGE:
            return f"Verify material moisture drops below 0.10% on moisture analyzer within 2 cycles."
        return "Verify parameter stabilization and quality risk reduction below 35% within 3 cycles."

    def _lint_epistemics(self, recommendation: InterventionRecommendation) -> None:
        """Enforce strict epistemic honesty by rejecting banned certainty words."""
        combined_text = (
            f"{recommendation.action} {recommendation.why} {recommendation.evidence} "
            f"{recommendation.expected_effect} {recommendation.operating_limit} {recommendation.recovery_check}"
        ).lower()

        for banned in BANNED_DOGMATIC_WORDS:
            if banned in combined_text:
                raise ValueError(
                    f"Epistemic honesty violation: recommendation contains banned phrase '{banned}'"
                )
