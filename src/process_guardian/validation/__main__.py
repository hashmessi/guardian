"""CLI entry point for running the 10-Scenario Validation Suite.

Usage:
    python -m process_guardian.validation
    python -m process_guardian.validation --scenario 2
    python -m process_guardian.validation --output .planning/validation_report.json
"""

import sys
import os
import argparse
from process_guardian.validation.runner import ScenarioValidationRunner
from process_guardian.validation.scenarios import SCENARIO_CATALOG


def main() -> int:
    parser = argparse.ArgumentParser(description="Process Guardian 10-Scenario Validation Suite")
    parser.add_argument("--scenario", default=None, help="Run specific scenario by ID (1-10) or name")
    parser.add_argument("--output", default=".planning/validation_report.json", help="Path to write JSON validation artifact")
    parser.add_argument("--quiet", action="store_true", help="Suppress terminal banners")
    args = parser.parse_args()

    runner = ScenarioValidationRunner()

    if not args.quiet:
        print("\n" + "=" * 80)
        print("  PROCESS GUARDIAN -- 10-SCENARIO VALIDATION SCORECARD (DEMO-01)")
        print("  Evaluating Closed-Loop Invariants & Statistical Robustness")
        print("=" * 80)

    if args.scenario is not None:
        # Run single scenario
        try:
            sid = int(args.scenario)
        except ValueError:
            sid = args.scenario

        print(f"[*] Executing target scenario: {sid}...")
        res = runner.run_scenario(sid)
        status_symbol = "[ PASS ]" if res.passed else "[ FAIL ]"
        print(f"\n{status_symbol} {res.title}")
        print(f"    Feature Tested: {res.feature_tested}")
        print(f"    Summary:        {res.summary}")
        if not res.passed:
            print(f"    Failures:       {', '.join(res.failure_reasons)}")
        return 0 if res.passed else 1

    # Run full suite
    def on_start(s):
        print(f"  -> [{s.scenario_id:02d}/10] Running {s.title} ({s.cycles_count} cycles)...", end="\r", flush=True)

    report = runner.run_all(on_scenario_start=on_start)

    print("\n" + "-" * 80)
    print(f"{'#':<3} {'Scenario Title':<42} {'Cycles':<8} {'Status':<10} {'Feature Tested'}")
    print("-" * 80)

    for r in report.results:
        status_str = "PASS" if r["passed"] else "FAIL"
        print(f"{r['scenario_id']:<3} {r['title'][:40]:<42} {r['cycles_evaluated']:<8} {status_str:<10} {r['feature_tested']}")

    print("-" * 80)
    print(f"  Result: {report.passed_count}/{report.total_scenarios} Passed ({report.pass_rate}%) in {report.total_duration_sec}s")
    print("=" * 80)

    # Save JSON report
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    report.save_json(args.output)
    print(f"[*] Machine-readable report saved to: {args.output}\n")

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
