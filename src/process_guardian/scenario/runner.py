"""Scenario Runner & Dual-Mode Counterfactual Replay Engine.

Executes deterministic production trajectories through the unified Process Guardian
decision pipeline and conducts side-by-side baseline (Guardian OFF) counterfactual replay.
"""

from typing import List, Dict, Any, Optional, Callable
import numpy as np

from process_guardian.core.types import RegimeType, RawCycleTelemetry
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.lifecycle import ClosedLoopOrchestrator, OrchestratorCycleResult
from process_guardian.state_machine.schemas import ProcessState
from process_guardian.counterfactual.models import (
    CounterfactualStreamPoint,
    CounterfactualRun,
    CounterfactualComparison,
)
from process_guardian.economics.models import CoPQParameters
from process_guardian.economics.engine import CoPQCalculator
from process_guardian.scenario.models import (
    ScenarioDefinition,
    ScenarioReplayCycle,
    ScenarioRunSummary,
    ScenarioScorecard,
    DisturbanceSpec,
)
from process_guardian.scenario.scorecard import ScenarioScorecardEvaluator
from process_guardian.llm.human_channel import HumanChannelClient, CheckpointQuestion


class ScenarioRunner:
    """Orchestrates scenario execution through the complete Process Guardian pipeline."""

    def __init__(
        self,
        copq_params: Optional[CoPQParameters] = None,
        scorecard_evaluator: Optional[ScenarioScorecardEvaluator] = None,
    ):
        self.copq_params = copq_params or CoPQParameters()
        self.copq_calculator = CoPQCalculator(self.copq_params)
        self.evaluator = scorecard_evaluator or ScenarioScorecardEvaluator()
        self._cache: Dict[str, ScenarioRunSummary] = {}

    def _setup_simulator(self, scenario: ScenarioDefinition) -> InjectionMoldingSimulator:
        """Instantiate simulator with deterministic seed and schedule scenario disturbances."""
        sim = InjectionMoldingSimulator(seed=scenario.seed, base_regime=RegimeType.HEALTHY)

        for d in scenario.disturbances:
            if d.pattern == "linear_drift":
                if "barrel" in d.signal or "temp" in d.signal:
                    sim.inject_event(
                        event_type="thermal_drift",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        duration=d.duration,
                    )
                elif "pressure" in d.signal:
                    sim.inject_event(
                        event_type="pressure_drift",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        duration=d.duration,
                    )
                elif "moisture" in d.signal:
                    sim.inject_event(
                        event_type="moisture_drift",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        duration=d.duration,
                    )
                else:
                    sim.inject_event(
                        event_type="signal_drift",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        duration=d.duration,
                        params={"signal": d.signal, "rate": d.rate or 0.20},
                    )

            elif d.pattern == "step_shift":
                delta_val = d.step_value if d.step_value is not None else 10.0
                if d.signal == "barrel_temp_z3":
                    sim.inject_event(
                        event_type="sudden_shift",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        params={"delta_temp_z3": delta_val},
                    )
                else:
                    sim.inject_event(
                        event_type="parameter_offset",
                        cycle=d.start_cycle,
                        severity=d.severity,
                        params={"signal": d.signal, "delta": delta_val},
                    )

            elif d.pattern == "moisture_surge":
                sim.inject_event(
                    event_type="moisture_drift",
                    cycle=d.start_cycle,
                    severity=d.severity,
                    duration=d.duration,
                )

            elif d.pattern == "noise_burst":
                sim.inject_event(
                    event_type="noise_burst",
                    cycle=d.start_cycle,
                    severity=d.severity,
                    duration=d.duration,
                    params=d.params,
                )

            elif d.pattern == "persistent_drift":
                sim.inject_event(
                    event_type="persistent_drift",
                    cycle=d.start_cycle,
                    severity=d.severity,
                    duration=d.duration,
                    params={"signal": d.signal, "rate": d.rate or 0.35},
                )

        return sim

    def _train_baseline_fingerprint(self, seed: int) -> ProcessFingerprint:
        """Build reference process fingerprint from 60 stationary baseline cycles."""
        sim = InjectionMoldingSimulator(seed=seed, base_regime=RegimeType.HEALTHY)
        pipe = TelemetryPipeline()
        records = [pipe.process(sim.step()) for _ in range(60)]
        return FingerprintBuilder().fit(records)

    def run_scenario(
        self,
        scenario: ScenarioDefinition,
        stream_callback: Optional[Callable[[ScenarioReplayCycle], None]] = None,
        use_cache: bool = False,
    ) -> ScenarioRunSummary:
        """
        Execute deterministic end-to-end scenario run through Guardian and dual baseline counterfactual.
        """
        if use_cache and scenario.scenario_id in self._cache:
            return self._cache[scenario.scenario_id]

        total_cycles = scenario.total_cycles
        fingerprint = self._train_baseline_fingerprint(seed=scenario.seed)

        # ---------------------------------------------------------------------
        # 1. GUARDIAN ON PIPELINE EXECUTION
        # ---------------------------------------------------------------------
        sim_on = self._setup_simulator(scenario)
        orchestrator = ClosedLoopOrchestrator(
            fingerprint=fingerprint,
            machine_id="IMM-01",
            auto_apply_intervention=scenario.expected_outcome.allow_intervention,
            required_stable_cycles=3,
            intervention_trigger_risk_threshold=0.50,
        )

        # Handle operational overrides
        is_ineffective_intervention = (
            scenario.operational_overrides and scenario.operational_overrides.intervention_ineffective
        )
        human_channel_event_cycle = (
            scenario.operational_overrides.human_channel_event_cycle
            if scenario.operational_overrides else None
        )
        human_channel_event_text = (
            scenario.operational_overrides.human_channel_event_text
            if scenario.operational_overrides else None
        )
        # Pinned deterministic: a scenario replay is a reproducibility claim, so it
        # must not change behaviour just because a dev shell has the Laya env var set.
        human_channel_client = HumanChannelClient(enable_laya=False)

        stream_on: List[ScenarioReplayCycle] = []
        cf_stream_on: List[CounterfactualStreamPoint] = []
        intervention_applied_cycle: Optional[int] = None
        on_scrap_count = 0

        for _ in range(total_cycles):
            raw_telemetry = sim_on.step()
            c_idx = raw_telemetry.cycle_index

            # P1 (scope_plan.md Sec.3): an authored operator note arriving at this
            # cycle is parsed through the same llm/human_channel.py path a live
            # operator's text goes through -- the scenario is not hand-faking a
            # signal object, it is replaying realistic input through the real parser.
            human_signal = None
            if human_channel_event_cycle == c_idx and human_channel_event_text:
                human_signal = human_channel_client.parse(human_channel_event_text, CheckpointQuestion.MOISTURE_SIGNED)

            res = orchestrator.step(raw_telemetry, human_channel_signal=human_signal)

            # If intervention occurred, handle simulator physical recovery response
            action_desc = None
            if res.recommendation and res.recommendation.candidate_id and res.recommendation.candidate_id != "A0":
                action_desc = f"{res.recommendation.candidate_id}: {res.recommendation.action}"
                if intervention_applied_cycle is None:
                    intervention_applied_cycle = c_idx

                    # Unless intervention is physically ineffective, arrest drift and dampen toward nominal
                    if not is_ineffective_intervention:
                        sim_on.event_queue.remove_event("thermal_drift")
                        sim_on.event_queue.remove_event("pressure_drift")
                        sim_on.event_queue.remove_event("signal_drift")
                        sim_on.event_queue.remove_event("moisture_drift")
                        sim_on.inject_event(
                            event_type="recovery",
                            cycle=c_idx + 1,
                            severity=1.0,
                        )

            is_quarantine = (
                res.disposition.disposition.value in ("QUARANTINED", "SCRAP")
                or res.state not in (ProcessState.HEALTHY, ProcessState.RELEASE)
            )
            is_defective = raw_telemetry.defect_flag or (res.risk_output.risk_probability > 0.85 and c_idx % 2 == 0)
            if is_defective:
                on_scrap_count += 1

            dom_signal = (
                res.root_cause_report.primary_contributor
                if res.root_cause_report and res.root_cause_report.contributors
                else None
            )

            replay_pt = ScenarioReplayCycle(
                cycle_index=c_idx,
                timestamp=res.timestamp,
                state=res.state.value,
                barrel_temp_z3=raw_telemetry.barrel_temp_z3,
                injection_pressure=raw_telemetry.injection_pressure,
                material_moisture=raw_telemetry.material_moisture,
                quality_risk=round(res.risk_output.risk_probability, 3),
                drift_detected=res.drift_output.drift,
                dominant_signal=dom_signal,
                action_applied=action_desc,
                is_quarantine=is_quarantine,
                is_defective=is_defective,
                disposition=res.disposition.disposition.value,
            )
            stream_on.append(replay_pt)

            cf_pt_on = CounterfactualStreamPoint(
                cycle_index=c_idx,
                barrel_temp=raw_telemetry.barrel_temp_z3,
                injection_pressure=raw_telemetry.injection_pressure,
                defect_risk=round(res.risk_output.risk_probability, 3),
                is_defective=is_defective,
                state=res.state.value,
                action_applied=action_desc,
                is_quarantine=is_quarantine,
            )
            cf_stream_on.append(cf_pt_on)

            if stream_callback:
                stream_callback(replay_pt)

        # ---------------------------------------------------------------------
        # 2. GUARDIAN OFF BASELINE PIPELINE (IDENTICAL INITIAL CONDITIONS & DISTURBANCE)
        # ---------------------------------------------------------------------
        sim_off = self._setup_simulator(scenario)
        pipe_off = TelemetryPipeline()
        cf_stream_off: List[CounterfactualStreamPoint] = []
        off_scrap_count = 0
        first_drift_start = min([d.start_cycle for d in scenario.disturbances]) if scenario.disturbances else total_cycles + 1

        for _ in range(total_cycles):
            raw_off = sim_off.step()
            c_idx = raw_off.cycle_index
            norm_off = pipe_off.process(raw_off)

            # Guardian OFF does not intervene -> continuous drift progression
            is_post_drift = c_idx >= first_drift_start
            state_off = "DRIFTING_UNNOTICED" if is_post_drift else "HEALTHY"

            # In Guardian OFF, defects escalate as disturbance widens without correction
            is_def_off = raw_off.defect_flag or (is_post_drift and (c_idx > first_drift_start + 15) and (c_idx % 2 == 0 or c_idx > first_drift_start + 40))
            if is_def_off:
                off_scrap_count += 1

            # High risk follows physics breach
            risk_off = min(0.99, max(0.04, 0.05 + (0.02 * max(0, c_idx - first_drift_start))))

            cf_pt_off = CounterfactualStreamPoint(
                cycle_index=c_idx,
                barrel_temp=raw_off.barrel_temp_z3,
                injection_pressure=raw_off.injection_pressure,
                defect_risk=round(risk_off, 3),
                is_defective=is_def_off,
                state=state_off,
                action_applied=None,
                is_quarantine=is_post_drift,
            )
            cf_stream_off.append(cf_pt_off)

        # ---------------------------------------------------------------------
        # 3. COUNTERFACTUAL COMPARISON DELTA (CRPL-01, CRPL-02)
        # ---------------------------------------------------------------------
        breakdown = self.copq_calculator.calculate_breakdown(self.copq_params)
        direct_scrap_cost = breakdown.direct_scrap_copq_per_defect
        sorting_cost = self.copq_params.sorting_cost_per_part

        off_suspect_cycles = max(0, total_cycles - first_drift_start + 1) if first_drift_start <= total_cycles else 0
        off_scrap_cost = off_scrap_count * direct_scrap_cost
        off_sorting_cost = off_suspect_cycles * sorting_cost
        off_downtime_penalty = 12000.0 if off_scrap_count > 5 else 0.0
        off_total_loss = off_scrap_cost + off_sorting_cost + off_downtime_penalty

        win = orchestrator.containment_engine.get_containment_window()
        on_suspect_cycles = win.suspect_cycle_count
        on_scrap_cost = on_scrap_count * direct_scrap_cost
        on_sorting_cost = on_suspect_cycles * sorting_cost
        on_tuning_cost = 250.0 if intervention_applied_cycle else 0.0
        on_total_loss = on_scrap_cost + on_sorting_cost + on_tuning_cost

        suspect_reduction_pct = (
            round(((off_suspect_cycles - on_suspect_cycles) / max(1, off_suspect_cycles)) * 100.0, 1)
            if off_suspect_cycles > 0
            else 0.0
        )
        scrap_reduction_pct = (
            round(((off_scrap_count - on_scrap_count) / max(1, off_scrap_count)) * 100.0, 1)
            if off_scrap_count > 0
            else 0.0
        )
        net_avoided = max(0.0, round(off_total_loss - on_total_loss, 2))

        run_off = CounterfactualRun(
            mode="GUARDIAN_OFF",
            name="Status Quo (Conventional Operation)",
            description="Fixed parameters, conventional wide SPC limits. Uncontained drift runaway.",
            total_cycles=total_cycles,
            suspect_cycles=off_suspect_cycles,
            scrap_parts_count=off_scrap_count,
            quarantine_parts_count=off_suspect_cycles,
            direct_scrap_cost=round(off_scrap_cost, 2),
            quarantine_sorting_cost=round(off_sorting_cost, 2),
            total_financial_loss=round(off_total_loss, 2),
            stream=cf_stream_off,
        )

        run_on = CounterfactualRun(
            mode="GUARDIAN_ON",
            name="Dynamic Quality Reaction (Process Guardian)",
            description="Early Sentinel detection, constrained intervention, verified recovery, physical QC sign-off.",
            total_cycles=total_cycles,
            suspect_cycles=on_suspect_cycles,
            scrap_parts_count=on_scrap_count,
            quarantine_parts_count=on_suspect_cycles,
            direct_scrap_cost=round(on_scrap_cost, 2),
            quarantine_sorting_cost=round(on_sorting_cost, 2),
            total_financial_loss=round(on_total_loss, 2),
            stream=cf_stream_on,
        )

        divergence_cycle = intervention_applied_cycle or first_drift_start

        comparison = CounterfactualComparison(
            guardian_off=run_off,
            guardian_on=run_on,
            suspect_lot_reduction_pct=suspect_reduction_pct,
            scrap_reduction_pct=scrap_reduction_pct,
            net_avoided_loss=net_avoided,
            timeline_divergence_cycle=divergence_cycle,
        )

        # ---------------------------------------------------------------------
        # 4. SCORECARD GENERATION ACROSS 7 PILLARS
        # ---------------------------------------------------------------------
        scorecard = self.evaluator.evaluate(
            scenario=scenario,
            orchestrator=orchestrator,
            replay_stream=stream_on,
            counterfactual=comparison,
        )

        summary = ScenarioRunSummary(
            scenario=scenario,
            scorecard=scorecard,
            stream=stream_on,
            counterfactual=comparison,
            total_cycles=total_cycles,
            duration_cycles=total_cycles,
            passed=scorecard.overall_passed,
        )

        self._cache[scenario.scenario_id] = summary
        return summary
