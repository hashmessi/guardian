"""Grounding Benchmark Report Engine (EVID-02).

Every case in this report carries a `source_type` stating what kind of evidence
it is. Only one kind is an outside measurement; the rest are this system's own
modelled behaviour, and are labelled as such rather than dressed up as studies.

  PUBLISHED_DATASET  a real, citable third-party experiment (DOI below)
  COMPUTED_ON_REPLICA  computed by us on the replica of that experiment's design
  MODELLED_ASSUMPTION  a parameter we chose, calibrated to published practice
  OWN_SIMULATION       the result of our own deterministic replay

No case in this report is a measured result from a production plant. Process
Guardian has not been deployed on a machine, and this report must never imply
otherwise.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from process_guardian.evidence.benchmark_dataset import (
    BENCHMARK_CITATION,
    BENCHMARK_DOI,
    BENCHMARK_PROVENANCE_NOTE,
    ExternalBenchmarkAdapter,
)

# Resin moisture has two distinct thresholds; conflating them reads as sloppy.
# The gate is the conservative limit a plant signs off against; the knee is
# where our model's scrap penalty accelerates.
MOISTURE_PROCESS_GATE_PCT = 0.15
MOISTURE_MODELLED_KNEE_PCT = 0.18


@dataclass
class GroundingTestCaseResult:
    """Individual benchmark comparison result, with its evidence class."""

    case_id: str
    title: str
    empirical_reference: str
    conventional_spc_behavior: str
    conventional_defect_escape_rate_pct: float
    process_guardian_behavior: str
    process_guardian_lead_time_cycles: float
    scrap_reduction_pct: float
    is_conclusive: bool
    evidence_summary: str
    source_type: str = "OWN_SIMULATION"
    citation: Optional[str] = None


@dataclass
class GroundingReport:
    """Complete automated grounding benchmark report."""

    report_id: str
    timestamp: str
    overall_status: str
    benchmark_dataset: str
    key_findings: List[str]
    test_cases: List[GroundingTestCaseResult]
    non_linear_moisture_curve: Dict[str, float]
    conclusion_for_evaluators: str


class GroundingBenchmarkEngine:
    """Engine that generates empirical grounding comparison metrics."""

    @classmethod
    def generate_report(cls) -> GroundingReport:
        """Run empirical benchmark comparisons and assemble report."""
        # Case 1 is the only outside-anchored comparison, and even then the
        # numbers are computed on the replica, not read off the original parts.
        flaw = ExternalBenchmarkAdapter.evaluate_machine_limits_flaw()
        escape_pct = flaw["escaped_defects_percentage"]
        univariate_catch = flaw["conventional_spc_catch_rate"]
        multivariate_catch = flaw["guardian_multivariate_catch_rate"]
        uplift = flaw["catch_rate_uplift_at_equal_cost"]
        matched_fa = flaw["matched_false_alarm_rate_pct"]
        rescued = flaw["guardian_rescued_defects_count"]

        case_1 = GroundingTestCaseResult(
            case_id="EVID-REPLICA-01",
            title="Defects Inside Tolerance: Univariate Limits vs Multivariate Distance",
            empirical_reference=(
                f"Replica of the published SKZ/Fraunhofer ProBayes DoE "
                f"({flaw['total_evaluated_parts']} parts, {flaw['total_defective_parts']} defective)"
            ),
            source_type="COMPUTED_ON_REPLICA",
            citation=f"{BENCHMARK_CITATION} | DOI {BENCHMARK_DOI}",
            conventional_spc_behavior=(
                f"Accepted {flaw['escaped_defects_count']} of {flaw['total_defective_parts']} defective parts "
                f"({escape_pct}%) because every individual parameter stayed inside its tolerance band. "
                f"Catch rate {univariate_catch}%."
            ),
            conventional_defect_escape_rate_pct=escape_pct,
            process_guardian_behavior=(
                f"Hotelling T^2 distance from the good-part population, thresholded to stop the same share of "
                f"good parts ({matched_fa}%), catches {multivariate_catch}% of the same defects -- "
                f"{uplift}x more at identical operator cost, including {rescued} the machine limits accepted."
            ),
            process_guardian_lead_time_cycles=0.0,  # per-part dataset: no cycle sequence to lead
            scrap_reduction_pct=0.0,  # detection comparison only; no intervention applied here
            is_conclusive=True,
            evidence_summary=(
                "Univariate tolerance checking misses defects whose individual signals all sit inside their "
                "bands while the combination has moved. Both detectors were held to the same false-alarm rate "
                f"on good parts, so the {uplift}x gap is not bought by alarming more often. "
                f"{BENCHMARK_PROVENANCE_NOTE}"
            ),
        )

        case_2 = GroundingTestCaseResult(
            case_id="MODEL-MOISTURE-01",
            title="Non-Linear Hygroscopic Moisture Penalty (Model Assumption)",
            empirical_reference=(
                "No public per-lot moisture/scrap dataset was used. The accelerating penalty above the "
                f"{MOISTURE_MODELLED_KNEE_PCT}% knee is OUR MODEL'S assumption, shaped by the standard "
                "polymer-drying practice that hygroscopic resins (PA, PBT) hydrolyse when moulded wet."
            ),
            source_type="MODELLED_ASSUMPTION",
            citation=None,
            conventional_spc_behavior=(
                "Machine controllers do not read hopper moisture at all, so no parameter limit can trip on it."
            ),
            conventional_defect_escape_rate_pct=100.0,
            process_guardian_behavior=(
                f"Quality Risk applies a non-linear penalty above {MOISTURE_MODELLED_KNEE_PCT}% moisture and "
                f"the operational checkpoint blocks release above the {MOISTURE_PROCESS_GATE_PCT}% process gate, "
                "requiring a drying sign-off instead of a machine-parameter change."
            ),
            process_guardian_lead_time_cycles=0.0,
            scrap_reduction_pct=0.0,
            is_conclusive=False,  # an assumption is not a finding
            evidence_summary=(
                "Stated as a tunable model parameter, not a measured curve. Its value to a plant is the "
                "behaviour it drives: a moisture excursion is answered with drying and a sign-off, never by "
                "trimming machine settings to mask a raw-material problem."
            ),
        )

        case_3 = GroundingTestCaseResult(
            case_id="OWN-REPLAY-01",
            title="Constrained Intervention vs Doing Nothing (Our Own Replay)",
            empirical_reference=(
                "Process Guardian's deterministic dual-stream replay: the identical event stream run with "
                "Guardian OFF and Guardian ON. This is our own simulation, not an industry study."
            ),
            source_type="OWN_SIMULATION",
            citation=None,
            conventional_spc_behavior=(
                "Guardian OFF: the line keeps running until downstream sorting finds the defective bin."
            ),
            conventional_defect_escape_rate_pct=0.0,
            process_guardian_behavior=(
                "Guardian ON: minimum-effective adjustment inside the 5-layer envelope, then a consecutive "
                "stability window and a physical QC checkpoint before the lot is released."
            ),
            process_guardian_lead_time_cycles=0.0,
            scrap_reduction_pct=0.0,  # read the live counterfactual run; no frozen figure claimed
            is_conclusive=False,
            evidence_summary=(
                "Measures the decision policy, not the world: it shows the loop closes and the suspect window "
                "collapses on identical inputs. Per-scenario figures come from the counterfactual replay the "
                "judge can re-run, so none are frozen into this report."
            ),
        )

        # Shape of the modelled penalty, not a measured scrap curve.
        moisture_curve = {
            "0.05%": 1.8,
            "0.10%": 2.8,
            f"{MOISTURE_PROCESS_GATE_PCT}% (process gate)": 3.4,
            f"{MOISTURE_MODELLED_KNEE_PCT}% (modelled knee)": 8.5,
            "0.22%": 22.1,
            "0.25%": 26.4,
        }

        return GroundingReport(
            report_id="GBR-2026-V11",
            timestamp="2026-10-01T23:30:00Z",
            overall_status="PARTIALLY_GROUNDED",
            benchmark_dataset=(
                f"Replica of published SKZ/Fraunhofer ProBayes DoE (DOI {BENCHMARK_DOI}) "
                "+ own deterministic replay"
            ),
            key_findings=[
                f"On the replica dataset, {escape_pct}% of defective parts passed every individual machine "
                "parameter limit.",
                f"At the same false-alarm rate on good parts ({matched_fa}%), multivariate distance catches "
                f"{multivariate_catch}% of defects against {univariate_catch}% for univariate limits ({uplift}x).",
                f"Resin moisture is handled with a modelled non-linear penalty above {MOISTURE_MODELLED_KNEE_PCT}% "
                f"and a hard release gate at {MOISTURE_PROCESS_GATE_PCT}% -- an assumption, not a measurement.",
                "Suspect-lot reduction figures come from our own dual-stream replay and are modelled, "
                "not observed in a plant.",
            ],
            test_cases=[case_1, case_2, case_3],
            non_linear_moisture_curve=moisture_curve,
            conclusion_for_evaluators=(
                "One comparison here is anchored to a published experiment's design; the rest is this system's "
                "own modelled behaviour, and each case says which it is. What the evidence supports is narrow "
                "and specific: checking parameters one at a time misses defects that a multivariate distance "
                "catches at the same false-alarm cost, and a constrained reaction policy closes the loop from "
                "that detection through verified recovery to a contained lot. What it does not support is any "
                "claim about scrap reduction on a real machine -- that needs a plant trial we have not run."
            ),
        )

    @classmethod
    def write_report_to_disk(cls, target_path: Optional[Path] = None) -> Path:
        """Write JSON report artifact to .planning directory."""
        if target_path is None:
            target_path = Path(".planning") / "grounding_benchmark_report.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        report = cls.generate_report()
        report_dict = asdict(report)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        return target_path


def main() -> None:
    """CLI runner printing ASCII scorecard and writing artifact."""
    report = GroundingBenchmarkEngine.generate_report()
    path = GroundingBenchmarkEngine.write_report_to_disk()
    print("=" * 76)
    print(f" PROCESS GUARDIAN: AUTOMATED GROUNDING BENCHMARK REPORT ({report.report_id})")
    print("=" * 76)
    print(f"Status:             {report.overall_status}")
    print(f"Benchmark Dataset:  {report.benchmark_dataset}")
    print(f"Artifact Location:  {path}")
    print("-" * 76)
    print("KEY EMPIRICAL FINDINGS:")
    for finding in report.key_findings:
        print(f"  * {finding}")
    print("-" * 76)
    print("TEST CASE COMPARISONS:")
    for tc in report.test_cases:
        print(f"[{tc.case_id}] {tc.title}")
        print(f"  Reference:        {tc.empirical_reference}")
        print(f"  Conventional SPC: {tc.conventional_spc_behavior}")
        print(f"  Process Guardian: {tc.process_guardian_behavior}")
        print(f"  Lead Time:        +{tc.process_guardian_lead_time_cycles} cycles | Scrap Reduction: {tc.scrap_reduction_pct}%")
        print()
    print("-" * 76)
    print("NON-LINEAR MOISTURE RESPONSE CURVE (% Scrap vs Resin Moisture):")
    for moisture_val, scrap_pct in report.non_linear_moisture_curve.items():
        bar = "#" * int(scrap_pct)
        print(f"  Moisture {moisture_val:>20}: {scrap_pct:>5.1f}% | {bar}")
    print("=" * 76)


if __name__ == "__main__":
    main()
