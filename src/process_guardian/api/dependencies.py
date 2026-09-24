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
from process_guardian.storage.schemas import StoredFingerprintRecord


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

        self.initialize()

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
