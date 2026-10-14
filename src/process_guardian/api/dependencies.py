"""Dependency injection container and state management for Process Guardian API."""

from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from process_guardian.core.types import RegimeType
from process_guardian.simulator.scenarios import build_regime_scenario
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.lifecycle import ClosedLoopOrchestrator
from process_guardian.storage.database import DatabaseManager
from process_guardian.storage.repository import GuardianRepository
from process_guardian.storage.schemas import (
    StoredFingerprintRecord,
    StoredCycleRecord,
    StoredDriftEventRecord,
    StoredRecommendationRecord,
    StoredInterventionCandidateRecord,
    StoredContainmentWindowRecord,
)
from process_guardian.economics.models import CoPQParameters
from process_guardian.economics.engine import CoPQCalculator, CostOfWaitingEvaluator


from process_guardian.quality.operational_checkpoints import OperationalCheckpointsEvaluator
from process_guardian.scenario.registry import get_scenario_registry, ScenarioRegistry
from process_guardian.scenario.runner import ScenarioRunner
from process_guardian.scenario.models import ScenarioRunSummary, ScenarioDefinition
from process_guardian.scenario.suite import OperationalValidationSuiteRunner


class ServiceContainer:
    """Stateful service container holding database manager, repository, and orchestrator instances."""

    def __init__(
        self,
        db_path: str = ":memory:",
        machine_id: str = "IMM-01",
        auto_apply_intervention: bool = False,
        seed: int = 42,
    ):
        self.db_path = db_path
        self.machine_id = machine_id
        self.auto_apply_intervention = auto_apply_intervention
        self.seed = seed

        self.db_manager: DatabaseManager = DatabaseManager(db_path=self.db_path)
        self.repository: GuardianRepository = GuardianRepository(self.db_manager)
        self.fingerprint: Optional[ProcessFingerprint] = None
        self.orchestrator: Optional[ClosedLoopOrchestrator] = None
        self.active_sim: Optional[Any] = None
        self.copq_params: CoPQParameters = CoPQParameters()
        self.copq_calculator: CoPQCalculator = CoPQCalculator(self.copq_params)
        self.decision_evaluator: CostOfWaitingEvaluator = CostOfWaitingEvaluator(copq_calculator=self.copq_calculator)
        self.operational_checkpoints: OperationalCheckpointsEvaluator = OperationalCheckpointsEvaluator()

        # Scenario Engine components
        self.scenario_registry: ScenarioRegistry = get_scenario_registry()
        self.scenario_runner: ScenarioRunner = ScenarioRunner(copq_params=self.copq_params)
        self.validation_suite_runner: OperationalValidationSuiteRunner = OperationalValidationSuiteRunner(
            registry=self.scenario_registry,
            runner=self.scenario_runner,
        )
        self.active_scenario_id: str = "SCN-01-THERMAL"
        self.active_scenario_summary: Optional[ScenarioRunSummary] = None

        self.initialize()

    def select_scenario(self, scenario_id: str) -> ScenarioRunSummary:
        """Select active scenario, run deterministic replay, and populate orchestrator state."""
        scn = self.scenario_registry.get(scenario_id)
        if scn is None:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        self.active_scenario_id = scn.scenario_id
        summary = self.scenario_runner.run_scenario(scn, use_cache=True)
        self.active_scenario_summary = summary

        # Update operational checkpoints: reset to defaults first, then apply whichever
        # overrides this scenario specifies. A scenario that overrides only one field
        # (e.g. moisture) must not inherit the other field's value (e.g. spray interval)
        # left behind by the previously selected scenario (hostile-review MEDIUM #7).
        self.operational_checkpoints.active_moisture_pct = 0.08
        self.operational_checkpoints.last_spray_cycle = 0
        if scn.operational_overrides:
            if scn.operational_overrides.initial_moisture_pct is not None:
                self.operational_checkpoints.active_moisture_pct = scn.operational_overrides.initial_moisture_pct
            if scn.operational_overrides.initial_spray_overdue_cycles is not None:
                self.operational_checkpoints.last_spray_cycle = max(0, scn.total_cycles - scn.operational_overrides.initial_spray_overdue_cycles)

        # Activate live state in repository and orchestrator
        self._activate_scenario_live_state(scn, summary)

        return summary

    def _activate_scenario_live_state(self, scn: ScenarioDefinition, summary: ScenarioRunSummary) -> None:
        """
        Activates the live process state, repository records, simulator, and orchestrator
        up to the incident/decision point of the selected scenario so all API endpoints
        and UI dashboards reflect genuine connected scenario telemetry.
        """
        # 1. Determine target incident cycle
        actions = [c.cycle_index for c in summary.stream if c.action_applied] if summary and summary.stream else []
        if actions:
            target_cycle = actions[0]
        elif summary and summary.scorecard and summary.scorecard.detection and summary.scorecard.detection.metrics.get("first_drift_cycle"):
            target_cycle = int(summary.scorecard.detection.metrics["first_drift_cycle"]) + 5
        else:
            target_cycle = min(scn.total_cycles, 60)

        # 2. Reset database demo session and QC verifier
        self.repository.reset_demo_session(self.machine_id)

        # 3. Train and set baseline fingerprint for this scenario seed
        fp = self.scenario_runner._train_baseline_fingerprint(seed=scn.seed)
        self.fingerprint = fp

        fp_rec = StoredFingerprintRecord(
            id=f"FP-{self.machine_id}-{scn.scenario_id}",
            context_key=f"{self.machine_id}:MOLD-18:AUTO-HOUSING-A:RCP-12",
            machine_id=self.machine_id,
            mold_id="MOLD-18",
            part_id="AUTO-HOUSING-A",
            recipe_id="RCP-12",
            baseline_version=f"v1.0.0-{scn.scenario_id}",
            sample_count=fp.sample_count,
            stats_json={
                sig: {"mean": stat.mean, "std": stat.std}
                for sig, stat in fp.signal_stats.items()
            },
            envelope_json={
                sig: {"lower": env.lower_limit, "upper": env.upper_limit}
                for sig, env in fp.operating_envelopes.items()
            },
        )
        self.repository.upsert_fingerprint(fp_rec)

        # 4. Instantiate simulator and orchestrator (auto_apply_intervention=False so it stays in INCIDENT/RECOMMENDING state)
        sim = self.scenario_runner._setup_simulator(scn)
        self.active_sim = sim

        self.orchestrator = ClosedLoopOrchestrator(
            fingerprint=self.fingerprint,
            machine_id=self.machine_id,
            auto_apply_intervention=False,
            required_stable_cycles=3,
            intervention_trigger_risk_threshold=0.50,
        )

        # 5. Advance simulator and orchestrator cycle by cycle up to target_cycle
        cycles_batch: List[StoredCycleRecord] = []
        for _ in range(target_cycle):
            raw = sim.step()
            c_idx = raw.cycle_index

            res = self.orchestrator.step(raw)
            rec = res.record

            cycle_db = StoredCycleRecord(
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
            cycles_batch.append(cycle_db)

            # Persist drift event if detected
            if res.drift_output and res.drift_output.drift:
                drift_db = StoredDriftEventRecord(
                    event_id=f"drift_{c_idx}",
                    cycle_index=c_idx,
                    machine_id=self.machine_id,
                    timestamp=rec.timestamp,
                    drift=True,
                    severity=res.drift_output.severity,
                    lead_cycles=res.drift_output.lead_cycles or 0,
                    signals_json=res.drift_output.signals,
                    details_json={
                        "multivariate_distance": res.drift_output.metrics.multivariate_distance,
                        "cusum_breached": res.drift_output.metrics.cusum_breached,
                        "ewma_breached": res.drift_output.metrics.ewma_breached,
                    },
                )
                self.repository.insert_drift_event(drift_db)

            # Persist recommendation if generated
            if res.recommendation and res.recommendation.candidate_id and res.recommendation.candidate_id != "A0":
                candidates_db = []
                if res.comparison_table:
                    for ev in res.comparison_table.evaluations:
                        candidates_db.append(
                            StoredInterventionCandidateRecord(
                                recommendation_id=f"rec_{c_idx}",
                                action_id=ev.candidate.action_id,
                                name=ev.candidate.name,
                                target_signal=ev.candidate.target_signal,
                                delta_value=ev.candidate.delta_value,
                                unit=ev.candidate.unit,
                                cost=ev.cost,
                                disruption=ev.disruption,
                                estimated_risk=ev.post_intervention_risk,
                                boundary_checked=ev.constraint_check.is_feasible,
                                is_selected=ev.is_selected,
                                metadata_json={"description": ev.candidate.description},
                            )
                        )
                rec_db = StoredRecommendationRecord(
                    recommendation_id=f"rec_{c_idx}",
                    event_id=f"evt_rec_{c_idx}",
                    cycle_index=c_idx,
                    machine_id=rec.context.machine_id,
                    action_id=res.comparison_table.recommended_action_id if res.comparison_table else "A0",
                    action_text=res.recommendation.action,
                    why_text=res.recommendation.why,
                    evidence_json={"evidence": res.recommendation.evidence},
                    expected_effect=res.recommendation.expected_effect,
                    confidence=res.recommendation.confidence,
                    operating_limit=res.recommendation.operating_limit,
                    recovery_check=res.recommendation.recovery_check,
                    is_abstain=res.recommendation.is_abstain,
                    abstain_reason=res.recommendation.abstain_reason,
                    operator_mode=res.recommendation.operator_mode,
                )
                self.repository.insert_recommendation(rec_db, candidates_db)

        self.repository.insert_cycles_batch(cycles_batch)

        # Update containment window in repository
        win = self.orchestrator.get_containment_window()
        if win and win.suspect_start_cycle is not None:
            q_list = list(range(win.suspect_start_cycle, (win.suspect_end_cycle or win.suspect_start_cycle) + 1))
            win_db = StoredContainmentWindowRecord(
                machine_id=self.machine_id,
                last_known_good_cycle=win.last_known_good_cycle,
                suspect_start_cycle=win.suspect_start_cycle,
                suspect_end_cycle=win.suspect_end_cycle,
                suspect_cycle_count=win.suspect_cycle_count,
                intervention_cycle=win.intervention_cycle,
                recovery_cycle=win.recovery_cycle,
                release_cycle=win.release_cycle,
                quarantine_cycles_json=q_list,
            )
            self.repository.upsert_containment_window(win_db)

    def initialize(self) -> None:
        """Initialize default plant topology, build baseline fingerprint, and instantiate orchestrator."""
        self.repository.seed_default_plant_data()

        # Build baseline fingerprint from 60 cycles of healthy simulation
        sim_base = build_regime_scenario(RegimeType.HEALTHY, cycles=60, seed=self.seed)
        pipe_base = TelemetryPipeline()
        base_records = [pipe_base.process(sim_base.step()) for _ in range(60)]
        self.fingerprint = FingerprintBuilder().fit(base_records)

        # Store baseline fingerprint in database
        fp_rec = StoredFingerprintRecord(
            id=f"FP-{self.machine_id}-BASE",
            context_key=f"{self.machine_id}:MOLD-18:AUTO-HOUSING-A:RCP-12",
            machine_id=self.machine_id,
            mold_id="MOLD-18",
            part_id="AUTO-HOUSING-A",
            recipe_id="RCP-12",
            baseline_version="v1.0.0-PROTOTYPE",
            sample_count=self.fingerprint.sample_count,
            stats_json={
                sig: {"mean": stat.mean, "std": stat.std}
                for sig, stat in self.fingerprint.signal_stats.items()
            },
            envelope_json={
                sig: {"lower": env.lower_limit, "upper": env.upper_limit}
                for sig, env in self.fingerprint.operating_envelopes.items()
            },
        )
        self.repository.upsert_fingerprint(fp_rec)

        # Instantiate closed loop orchestrator
        self.orchestrator = ClosedLoopOrchestrator(
            fingerprint=self.fingerprint,
            machine_id=self.machine_id,
            auto_apply_intervention=self.auto_apply_intervention,
            required_stable_cycles=3,
            intervention_trigger_risk_threshold=0.50,
        )

    def reset(self, auto_apply: Optional[bool] = None) -> None:
        """Deterministic reset of database and orchestrator for demo replay."""
        if auto_apply is not None:
            self.auto_apply_intervention = auto_apply
        self.db_manager.reset_database()
        self.initialize()

    def reset_demo_session(
        self,
        run_id: Optional[str] = None,
        seed_baseline: bool = True,
        baseline_cycles: int = 60,
    ) -> Dict[str, Any]:
        """
        Isolated demo reset: clears active telemetry while strictly preserving audit logs,
        reseeds pristine baseline cycles, and resets orchestrator memory to HEALTHY baseline.
        """
        new_run_id, preserved_count = self.repository.reset_demo_session(
            machine_id=self.machine_id,
            run_id=run_id,
        )

        # Clear stale scenario state. Without this, a scenario simulator selected before
        # the reset keeps stepping from its own cycle count on the next apply-demo call,
        # advancing the machine far past the freshly-seeded baseline cycles (hostile-review
        # MEDIUM #5), and a stale scorecard is still reported as the active scenario.
        self.active_sim = None
        self.active_scenario_summary = None
        self.operational_checkpoints.active_moisture_pct = 0.08
        self.operational_checkpoints.last_spray_cycle = 0

        # Reset orchestrator
        self.orchestrator = ClosedLoopOrchestrator(
            fingerprint=self.fingerprint,
            machine_id=self.machine_id,
            auto_apply_intervention=self.auto_apply_intervention,
            required_stable_cycles=3,
            intervention_trigger_risk_threshold=0.50,
        )

        # Reseed baseline cycles into both orchestrator and repository
        seeded_count = 0
        if seed_baseline:
            sim = build_regime_scenario(RegimeType.HEALTHY, cycles=baseline_cycles, seed=self.seed)
            pipe = TelemetryPipeline()
            for _ in range(baseline_cycles):
                raw = sim.step()
                rec = pipe.process(raw)
                cycle_db = StoredCycleRecord(
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
                self.repository.insert_cycle(cycle_db)
                self.orchestrator.step(rec)
                seeded_count += 1

        return {
            "status": "RESET_COMPLETE",
            "run_id": new_run_id,
            "machine_id": self.machine_id,
            "state": self.orchestrator.current_state.value,
            "seeded_cycles": seeded_count,
            "audit_records_preserved": preserved_count,
        }


# Global singleton instance for API dependency injection
_global_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """FastAPI dependency for accessing the active ServiceContainer."""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    return _global_container


def set_service_container(container: ServiceContainer) -> None:
    """Override the global container (useful for testing)."""
    global _global_container
    _global_container = container


def get_repository() -> GuardianRepository:
    """FastAPI dependency for repository access."""
    return get_service_container().repository


def get_orchestrator() -> ClosedLoopOrchestrator:
    """FastAPI dependency for orchestrator access."""
    return get_service_container().orchestrator
