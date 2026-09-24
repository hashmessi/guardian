"""Unit and integration tests for SQLite Storage and 17-Table Schema Layer."""

import pytest
from datetime import datetime

from process_guardian.storage.database import DatabaseManager
from process_guardian.storage.schemas import (
    GuardianEvent,
    MachineRecord,
    MoldRecord,
    PartRecord,
    RecipeRecord,
    MaterialRecord,
    StoredCycleRecord,
    StoredFingerprintRecord,
    StoredQualityContractRecord,
    StoredDriftEventRecord,
    StoredQualityPredictionRecord,
    StoredInterventionCandidateRecord,
    StoredRecommendationRecord,
    StoredInterventionApplicationRecord,
    StoredRecoveryEventRecord,
    StoredContainmentWindowRecord,
    StoredCheckpointRecord,
    StoredAuditLogRecord,
)
from process_guardian.storage.repository import GuardianRepository


@pytest.fixture
def db_repo():
    db = DatabaseManager(":memory:")
    repo = GuardianRepository(db)
    repo.seed_default_plant_data()
    return repo


def test_schema_creates_all_seventeen_tables(db_repo):
    """Verify all 17 tables required by STOR-01 exist in SQLite."""
    tables = db_repo.db.get_table_names()
    expected_tables = {
        "machines", "molds", "parts", "recipes", "materials",
        "cycles", "process_fingerprints", "quality_contracts",
        "drift_events", "quality_predictions", "intervention_candidates",
        "intervention_recommendations", "intervention_applications",
        "recovery_events", "containment_windows", "checkpoints", "audit_log"
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"
    assert len(tables) >= 17


def test_topology_seed_and_retrieval(db_repo):
    """Verify seed topology data is properly loaded and queryable."""
    machine = db_repo.get_machine("IMM-01")
    assert machine is not None
    assert machine.machine_name == "Engel Victory 120T"

    mold = db_repo.get_mold("MOLD-18")
    assert mold is not None
    assert mold.material_compatibility == "PA66-GF30"

    part = db_repo.get_part("AUTO-HOUSING-A")
    assert part is not None
    assert part.target_weight_g == 142.5

    recipe = db_repo.get_recipe("RCP-12")
    assert recipe is not None
    assert recipe.target_temperature == 285.0
    assert "barrel_temp_z3" in recipe.parameters_json

    material = db_repo.get_material("PA66-GF30")
    assert material is not None
    assert material.density_g_cm3 == 1.35


def test_cycle_telemetry_crud_and_range_queries(db_repo):
    """Verify inserting cycles and querying single/batch/range records."""
    cycles = [
        StoredCycleRecord(
            cycle_index=i,
            machine_id="IMM-01",
            mold_id="MOLD-18",
            part_id="AUTO-HOUSING-A",
            recipe_id="RCP-12",
            timestamp=f"2026-09-24T10:{i:02d}:00Z",
            barrel_temp_z1=275.0,
            barrel_temp_z2=280.0,
            barrel_temp_z3=285.0 + i * 0.1,
            barrel_temp_z4=285.0,
            nozzle_temp=285.0,
            mold_temp=80.0,
            injection_pressure=120.0,
            holding_pressure=85.0,
            back_pressure=10.0,
            injection_speed=45.0,
            screw_rpm=60.0,
            cushion_position=5.0,
            dosing_time=3.5,
            injection_time=2.1,
            cooling_time=12.0,
            cycle_time=30.0,
            ambient_temp=25.0,
            ambient_humidity=45.0,
            material_moisture_pct=0.12,
            part_weight_g=142.5,
            defect_flag=False,
            defect_type=None,
            raw_json={"source": "unit_test", "cycle": i},
        )
        for i in range(1, 11)
    ]

    inserted_count = db_repo.insert_cycles_batch(cycles)
    assert inserted_count == 10
    assert db_repo.get_cycle_count("IMM-01") == 10

    single = db_repo.get_cycle("IMM-01", 5)
    assert single is not None
    assert single.cycle_index == 5
    assert pytest.approx(single.barrel_temp_z3, rel=1e-3) == 285.5

    range_cycles = db_repo.get_cycles_range("IMM-01", 3, 7)
    assert len(range_cycles) == 5
    assert range_cycles[0].cycle_index == 3
    assert range_cycles[-1].cycle_index == 7

    latest = db_repo.get_latest_cycle("IMM-01")
    assert latest.cycle_index == 10


def test_unified_event_logging(db_repo):
    """Verify unified GuardianEvent schema logging (STOR-02) into audit and typed tables."""
    event = GuardianEvent(
        event_id="evt_00421",
        machine_id="IMM-01",
        mold_id="MOLD-18",
        part_id="AUTO-HOUSING-A",
        recipe_id="RCP-12",
        cycle_id=429,
        timestamp="2026-09-29T10:21:14Z",
        event_type="PROCESS_DRIFT",
        severity="HIGH",
        signals=["barrel_temp_z3", "injection_pressure", "cycle_time"],
        quality_risk=0.72,
        confidence=0.93,
        details={"lead_cycles": 11, "root_cause": "thermal_drift"},
    )

    db_repo.record_unified_event(event)

    # Check audit log
    logs = db_repo.list_audit_logs("IMM-01")
    assert len(logs) >= 1
    assert logs[0].event_id == "evt_00421"
    assert logs[0].event_type == "PROCESS_DRIFT"
    assert logs[0].severity == "HIGH"
    assert logs[0].details_json["quality_risk"] == 0.72

    # Check drift events table
    drifts = db_repo.list_drift_events("IMM-01")
    assert len(drifts) >= 1
    assert drifts[0].event_id == "evt_00421"
    assert "barrel_temp_z3" in drifts[0].signals_json


def test_recommendation_and_candidates_persistence(db_repo):
    """Verify storing and querying recommendations and candidate evaluations."""
    rec = StoredRecommendationRecord(
        recommendation_id="rec_001",
        event_id="evt_00421",
        cycle_index=431,
        machine_id="IMM-01",
        action_id="A1",
        action_text="Decrease barrel temperature zone 3 by -4.0 deg C",
        why_text="Barrel temperature zone 3 elevated by +4.8 deg C above fingerprint baseline.",
        evidence_json={"primary_signal": "barrel_temp_z3", "shift_z": 3.4},
        expected_effect="Reduces melt temperature, lowers flash risk from 72% to 26%.",
        confidence=0.93,
        operating_limit="Within safe limits [260.0, 300.0] deg C.",
        recovery_check="Confirm zone 3 temp <= 286.0 deg C within 3 cycles.",
        is_abstain=False,
        operator_mode="DIRECT_RECOMMENDATION",
    )

    candidates = [
        StoredInterventionCandidateRecord(
            recommendation_id="rec_001",
            action_id="A0",
            name="Continue monitoring",
            cost=0.0,
            disruption=0.0,
            estimated_risk=0.81,
            is_selected=False,
        ),
        StoredInterventionCandidateRecord(
            recommendation_id="rec_001",
            action_id="A1",
            name="Decrease barrel temp zone 3",
            target_signal="barrel_temp_z3",
            delta_value=-4.0,
            unit="deg C",
            cost=1.0,
            disruption=1.0,
            estimated_risk=0.26,
            is_selected=True,
        ),
    ]

    db_repo.insert_recommendation(rec, candidates)

    latest_rec = db_repo.get_latest_recommendation("IMM-01")
    assert latest_rec is not None
    assert latest_rec.recommendation_id == "rec_001"
    assert latest_rec.confidence == 0.93

    cands = db_repo.get_recommendation_candidates("rec_001")
    assert len(cands) == 2
    assert cands[1].is_selected is True
    assert cands[1].action_id == "A1"


def test_recovery_containment_and_checkpoints(db_repo):
    """Verify recovery events, containment windows, and checkpoint persistence."""
    # Recovery Event
    recov = StoredRecoveryEventRecord(
        cycle_index=444,
        machine_id="IMM-01",
        intervention_id="rec_001",
        recovery_status="VERIFIED",
        release_decision="APPROVED",
        risk_before=0.72,
        risk_after=0.08,
        stability_before=0.28,
        stability_after=0.96,
        consecutive_stable_cycles=3,
        summary_message="Sustained recovery verified across 3 consecutive cycles.",
    )
    db_repo.insert_recovery_event(recov)
    stored_recov = db_repo.get_latest_recovery_event("IMM-01")
    assert stored_recov.recovery_status == "VERIFIED"
    assert stored_recov.release_decision == "APPROVED"

    # Containment Window
    win = StoredContainmentWindowRecord(
        machine_id="IMM-01",
        last_known_good_cycle=429,
        suspect_start_cycle=430,
        suspect_end_cycle=444,
        suspect_cycle_count=15,
        intervention_cycle=431,
        recovery_cycle=444,
        release_cycle=445,
        quarantine_cycles_json=list(range(430, 445)),
    )
    db_repo.upsert_containment_window(win)
    stored_win = db_repo.get_latest_containment_window("IMM-01")
    assert stored_win.last_known_good_cycle == 429
    assert stored_win.suspect_cycle_count == 15
    assert len(stored_win.quarantine_cycles_json) == 15

    # Checkpoint
    chk = StoredCheckpointRecord(
        checkpoint_name="pre_drift_baseline",
        cycle_index=419,
        machine_id="IMM-01",
        timestamp="2026-09-24T10:00:00Z",
        state="HEALTHY",
        data_json={"risk": 0.03, "stability": 0.96},
    )
    db_repo.insert_checkpoint(chk)
    retrieved_chk = db_repo.get_checkpoint("pre_drift_baseline")
    assert retrieved_chk.cycle_index == 419
    assert retrieved_chk.state == "HEALTHY"
