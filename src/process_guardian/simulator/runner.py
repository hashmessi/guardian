"""Scenario runner, cycle streamer, and dataset exporter."""

import argparse
import csv
import json
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.scenarios import build_demo_scenario, build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.adapter.schemas import NormalizedCycleRecord


class ScenarioRunner:
    """
    Executes simulation scenarios, pipes cycles through the Data Adapter pipeline,
    and supports exporting datasets.
    """

    def __init__(
        self,
        simulator: InjectionMoldingSimulator,
        pipeline: Optional[TelemetryPipeline] = None,
    ):
        self.simulator = simulator
        self.pipeline = pipeline or TelemetryPipeline(simulator.context)

    def run(
        self,
        total_cycles: int = 500,
        stream_callback: Optional[Callable[[NormalizedCycleRecord], None]] = None,
    ) -> List[NormalizedCycleRecord]:
        """
        Step simulator for total_cycles, adapt each cycle through pipeline, and return records.
        """
        records: List[NormalizedCycleRecord] = []

        for _ in range(total_cycles):
            raw_telemetry = self.simulator.step()
            normalized_record = self.pipeline.process(raw_telemetry)

            if stream_callback is not None:
                stream_callback(normalized_record)

            records.append(normalized_record)

        return records

    def export_json(self, records: List[NormalizedCycleRecord], output_path: str) -> None:
        """Serialize records to formatted JSON."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.model_dump() for r in records]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def export_csv(self, records: List[NormalizedCycleRecord], output_path: str) -> None:
        """Export flat tabular records to CSV."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not records:
            return

        # Flatten record dictionaries
        fieldnames = [
            "cycle_index",
            "timestamp",
            "barrel_temp_z1",
            "barrel_temp_z2",
            "barrel_temp_z3",
            "barrel_temp_z4",
            "barrel_temp_z5",
            "nozzle_temp",
            "injection_pressure",
            "peak_pressure",
            "hold_pressure",
            "injection_time",
            "hold_time",
            "cooling_time",
            "cycle_time",
            "part_weight",
            "material_moisture",
            "ambient_temp",
            "ambient_humidity",
            "defect_flag",
            "sink_mark_depth",
            "flash_observed",
            "machine_id",
            "mold_id",
            "recipe_version",
            "is_valid",
        ]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                row = {
                    "cycle_index": r.cycle_index,
                    "timestamp": r.timestamp,
                    "barrel_temp_z1": r.barrel_temp_z1,
                    "barrel_temp_z2": r.barrel_temp_z2,
                    "barrel_temp_z3": r.barrel_temp_z3,
                    "barrel_temp_z4": r.barrel_temp_z4,
                    "barrel_temp_z5": r.barrel_temp_z5,
                    "nozzle_temp": r.nozzle_temp,
                    "injection_pressure": r.injection_pressure,
                    "peak_pressure": r.peak_pressure,
                    "hold_pressure": r.hold_pressure,
                    "injection_time": r.injection_time,
                    "hold_time": r.hold_time,
                    "cooling_time": r.cooling_time,
                    "cycle_time": r.cycle_time,
                    "part_weight": r.part_weight,
                    "material_moisture": r.material_moisture,
                    "ambient_temp": r.ambient_temp,
                    "ambient_humidity": r.ambient_humidity,
                    "defect_flag": r.defect_flag,
                    "sink_mark_depth": r.sink_mark_depth,
                    "flash_observed": r.flash_observed,
                    "machine_id": r.context.machine_id,
                    "mold_id": r.context.mold_id,
                    "recipe_version": r.context.recipe_version,
                    "is_valid": r.is_valid,
                }
                writer.writerow(row)


def main():
    """CLI entry point for running scenarios and generating synthetic factory telemetry."""
    parser = argparse.ArgumentParser(description="Process Guardian Digital Factory Scenario Runner")
    parser.add_argument("--scenario", default="demo", choices=["demo", "healthy", "thermal", "pressure", "moisture", "instability", "noise", "unseen"], help="Scenario to run")
    parser.add_argument("--cycles", type=int, default=500, help="Total cycles to simulate")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--export-json", type=str, default=None, help="Filepath to export JSON")
    parser.add_argument("--export-csv", type=str, default=None, help="Filepath to export CSV")
    args = parser.parse_args()

    if args.scenario == "demo":
        sim = build_demo_scenario(seed=args.seed)
    elif args.scenario == "healthy":
        sim = build_regime_scenario(RegimeType.HEALTHY, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "thermal":
        sim = build_regime_scenario(RegimeType.THERMAL_DRIFT, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "pressure":
        sim = build_regime_scenario(RegimeType.PRESSURE_DRIFT, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "moisture":
        sim = build_regime_scenario(RegimeType.MOISTURE_DRIFT, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "instability":
        sim = build_regime_scenario(RegimeType.CYCLE_INSTABILITY, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "noise":
        sim = build_regime_scenario(RegimeType.SENSOR_NOISE, cycles=args.cycles, seed=args.seed)
    elif args.scenario == "unseen":
        sim = build_regime_scenario(RegimeType.UNSEEN_DRIFT, cycles=args.cycles, seed=args.seed)
    else:
        sim = build_demo_scenario(seed=args.seed)

    runner = ScenarioRunner(simulator=sim)
    print(f"[*] Executing scenario '{args.scenario}' for {args.cycles} cycles (seed={args.seed})...")
    records = runner.run(total_cycles=args.cycles)

    print("\n--- MILESTONE TELEMETRY SNAPSHOT ---")
    milestone_cycles = [1, 200, 419, 420, 435, 441, 442, 446, min(450, args.cycles)]
    milestone_cycles = [c for c in milestone_cycles if c <= args.cycles]

    header = f"{'Cycle':<8}{'Z3 Temp(°C)':<14}{'Peak P(bar)':<14}{'Weight(g)':<12}{'Defect':<10}{'Valid':<8}"
    print(header)
    print("-" * len(header))

    for c_idx in milestone_cycles:
        rec = records[c_idx - 1]
        print(f"{rec.cycle_index:<8}{rec.barrel_temp_z3:<14.2f}{rec.peak_pressure:<14.2f}{rec.part_weight:<12.2f}{str(rec.defect_flag):<10}{str(rec.is_valid):<8}")

    if args.export_json:
        runner.export_json(records, args.export_json)
        print(f"\n[+] Exported JSON to: {args.export_json}")

    if args.export_csv:
        runner.export_csv(records, args.export_csv)
        print(f"\n[+] Exported CSV to: {args.export_csv}")


if __name__ == "__main__":
    main()
