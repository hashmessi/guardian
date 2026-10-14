"""Root Cause Analyzer computing percentage-normalized signal attribution (ROOT-01..03)."""

from typing import Dict, List, Optional
import numpy as np

from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.schemas import QualityRiskOutput
from process_guardian.root_cause.schemas import (
    ContributorItem,
    SubsystemAttribution,
    RootCauseReport,
)
from process_guardian.root_cause.evidence import EvidenceGenerator
from process_guardian.llm.human_channel import HumanChannelSignal, BoundedChoice


class RootCauseAnalyzer:
    """
    Multivariate root-cause contributor attribution engine.
    
    Transforms physical sensor deviations, tree model feature importances, and drift slopes
    into a ranked list of likely contributors summing strictly to 100.0% (ROOT-01),
    supported by verifiable empirical evidence (ROOT-02) and honest epistemics (ROOT-03).
    """

    SIGNALS = [
        "barrel_temp_z1", "barrel_temp_z2", "barrel_temp_z3", "barrel_temp_z4", "barrel_temp_z5",
        "nozzle_temp", "injection_pressure", "peak_pressure", "hold_pressure",
        "injection_time", "hold_time", "cooling_time", "cycle_time",
        "material_moisture",
    ]

    SUBSYSTEM_MAP = {
        "barrel_temp_z1": "Thermal",
        "barrel_temp_z2": "Thermal",
        "barrel_temp_z3": "Thermal",
        "barrel_temp_z4": "Thermal",
        "barrel_temp_z5": "Thermal",
        "nozzle_temp": "Thermal",
        "injection_pressure": "Pressure",
        "peak_pressure": "Pressure",
        "hold_pressure": "Pressure",
        "injection_time": "Timing",
        "hold_time": "Timing",
        "cooling_time": "Timing",
        "cycle_time": "Timing",
        "material_moisture": "Material",
        "human_channel": "Material",
    }

    def __init__(self, evidence_gen: Optional[EvidenceGenerator] = None):
        self.evidence_gen = evidence_gen or EvidenceGenerator()

    def analyze(
        self,
        record: NormalizedCycleRecord,
        fingerprint: ProcessFingerprint,
        drift_output: Optional[DriftOutput] = None,
        risk_output: Optional[QualityRiskOutput] = None,
        human_channel_signal: Optional[HumanChannelSignal] = None,
        human_channel_confirmed: bool = False,
    ) -> RootCauseReport:
        """
        Analyze a cycle and produce a percentage-normalized RootCauseReport.

        human_channel_signal (P1, scope_plan.md Sec.2/3): a confident, non-UNKNOWN
        operator attestation folds into the same normalized attribution pool as a
        named contributor. In a scenario where sensors stay fully healthy (the
        S-FLIP proof), the physical signals' scores are all noise-floor, so a
        confident human-channel signal naturally dominates -- never a silent
        override, always ranked and labeled with its own evidence (Sec.6 rule 3).

        human_channel_confirmed: True once this signal has already driven a state
        transition (the machine is being held pending verification *because* of
        it, not merely being offered it as one candidate cause among others). A
        single noisy sensor can still spike past the base human-channel score in
        a 150+ cycle healthy-noise hold purely by chance (multiple-testing across
        14 signals every cycle); once the hold is already adjudicated, attribution
        must not flicker below that noise -- still ranked and labeled with its own
        evidence, just guaranteed to stay on top while it is the reason for the hold.
        """
        raw_scores: Dict[str, float] = {}
        z_scores: Dict[str, float] = {}
        slopes: Dict[str, float] = {}

        # 1. Compute divergence and attribution scores per signal
        for sig in self.SIGNALS:
            val = float(getattr(record, sig, 0.0))
            stat = fingerprint.signal_stats.get(sig)
            mu = stat.mean if stat else val
            sigma = stat.std if stat and stat.std > 1e-4 else 1.0

            z = (val - mu) / sigma
            z_scores[sig] = z

            # Extract slope from drift_output details if available
            slope = 0.0
            if drift_output and sig in drift_output.details:
                slope = drift_output.details[sig].slope_per_cycle
            slopes[sig] = slope

            # Tree model weight if present
            tree_weight = 0.0
            if risk_output and risk_output.feature_contributions:
                tree_weight = sum(
                    v for k, v in risk_output.feature_contributions.items() if sig in k
                )

            # Mathematical attribution formulation:
            # Combines standardized distance (|z|), rate of change (|slope|/sigma), and tree weight
            z_term = max(0.05, abs(z) ** 1.6)
            slope_term = 2.0 * (abs(slope) / sigma)
            model_mult = 1.0 + 3.0 * tree_weight

            score = (z_term + slope_term) * model_mult
            raw_scores[sig] = score

        # Human-channel contributor: weight of 9.0 at full confidence sits well
        # above the noise floor of a fully-healthy regime (14 signals x ~0.05 each
        # = ~0.7) so it can dominate there, but well below a genuine confirmed
        # sensor drift (z_term alone exceeds 9.0 past roughly z=3.3), so it does
        # not drown out real drift in other scenarios.
        if human_channel_signal is not None and human_channel_signal.choice != BoundedChoice.UNKNOWN:
            base_score = 9.0 * human_channel_signal.confidence
            if human_channel_confirmed:
                sensor_max = max(raw_scores.values(), default=0.0)
                base_score = max(base_score, sensor_max * 1.1)
            raw_scores["human_channel"] = base_score

        # 2. Normalize raw scores so percentage sum is strictly 100.0%
        total_score = sum(raw_scores.values())
        if total_score < 1e-6:
            total_score = 1.0

        percentages: Dict[str, float] = {
            sig: round((raw_scores[sig] / total_score) * 100.0, 1)
            for sig in raw_scores
        }

        # Enforce exact 100.0% sum by adjusting highest score
        diff = round(100.0 - sum(percentages.values()), 1)
        top_sig = max(percentages, key=percentages.get)
        percentages[top_sig] = round(percentages[top_sig] + diff, 1)

        # 3. Subsystem category rollups
        subsystem_sums: Dict[str, float] = {"Thermal": 0.0, "Pressure": 0.0, "Timing": 0.0, "Material": 0.0}
        for sig, pct in percentages.items():
            cat = self.SUBSYSTEM_MAP.get(sig, "Thermal")
            subsystem_sums[cat] += pct

        sub_diff = round(100.0 - sum(subsystem_sums.values()), 1)
        top_cat = max(subsystem_sums, key=subsystem_sums.get)
        subsystem_sums[top_cat] = round(subsystem_sums[top_cat] + sub_diff, 1)

        subsystem_breakdown = SubsystemAttribution(
            thermal_pct=round(subsystem_sums["Thermal"], 1),
            pressure_pct=round(subsystem_sums["Pressure"], 1),
            timing_pct=round(subsystem_sums["Timing"], 1),
            material_pct=round(subsystem_sums["Material"], 1),
        )

        # 4. Generate structured contributor items
        contributors: List[ContributorItem] = []
        for sig in sorted(percentages, key=percentages.get, reverse=True):
            pct = percentages[sig]

            if sig == "human_channel":
                disp_name, cat = self.evidence_gen.FRIENDLY_NAMES["human_channel"]
                contributors.append(
                    ContributorItem(
                        signal_name="human_channel",
                        display_name=disp_name,
                        category=cat,
                        contribution_pct=pct,
                        evidence=(
                            f'Operator note ({human_channel_signal.source}, '
                            f'{human_channel_signal.confidence * 100:.0f}% parser confidence): '
                            f'"{human_channel_signal.raw_text}" -- parsed as {human_channel_signal.choice.value.upper()}. '
                            f"Sensor-blind channel: not yet reflected in instrument readings."
                        ),
                        z_score=0.0,
                        slope_per_cycle=0.0,
                    )
                )
                continue

            disp_name, cat = self.evidence_gen.FRIENDLY_NAMES.get(sig, (sig, "Process"))
            val = float(getattr(record, sig, 0.0))
            stat = fingerprint.signal_stats.get(sig)
            mu = stat.mean if stat else val
            sigma = stat.std if stat else 1.0

            evidence_text = self.evidence_gen.generate_signal_evidence(
                signal_name=sig,
                current_val=val,
                baseline_mean=mu,
                baseline_std=sigma,
                z_score=z_scores[sig],
                slope_per_cycle=slopes[sig],
            )

            contributors.append(
                ContributorItem(
                    signal_name=sig,
                    display_name=disp_name,
                    category=cat,
                    contribution_pct=pct,
                    evidence=evidence_text,
                    z_score=round(z_scores[sig], 2),
                    slope_per_cycle=round(slopes[sig], 4),
                )
            )

        # 5. Summary and honesty verification
        if top_sig == "human_channel":
            # z_scores has no entry for human_channel (it isn't a sensor reading);
            # generate_summary() would wrongly report "+0.00sigma deviation" if
            # reused here, so this case gets its own honest phrasing.
            summary = (
                f"Operator evidence identifies the primary likely contributor "
                f"({percentages[top_sig]:.1f}% attribution, "
                f"{human_channel_signal.confidence * 100:.0f}% parser confidence): "
                f'"{human_channel_signal.raw_text}". Sensor telemetry has not yet confirmed this; '
                f"material dynamics are flagged ahead of instrument confirmation."
            )
            assert self.evidence_gen.verify_honest_language(summary), "Summary failed honesty check"
        else:
            summary = self.evidence_gen.generate_summary(
                primary_signal=top_sig,
                primary_pct=percentages[top_sig],
                primary_z=z_scores[top_sig],
                top_category=top_cat,
            )

        all_evidence_clean = all(
            self.evidence_gen.verify_honest_language(c.evidence) for c in contributors
        ) and self.evidence_gen.verify_honest_language(summary)

        return RootCauseReport(
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            primary_contributor=top_sig,
            subsystem_breakdown=subsystem_breakdown,
            contributors=contributors,
            honest_language_compliant=all_evidence_clean,
            summary_statement=summary,
        )
