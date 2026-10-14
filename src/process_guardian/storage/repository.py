"""High-level repository pattern for Process Guardian SQLite persistence."""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

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


class GuardianRepository:
    """Provides strongly typed CRUD and audit logging for all 17 tables."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # ---------------------------------------------------------
    # 1-5: Topology (Machines, Molds, Parts, Recipes, Materials)
    # ---------------------------------------------------------

    def upsert_machine(self, m: MachineRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO machines (id, machine_name, model, tonnage, plant_location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    machine_name=excluded.machine_name,
                    model=excluded.model,
                    tonnage=excluded.tonnage,
                    plant_location=excluded.plant_location,
                    status=excluded.status;
                """,
                (m.id, m.machine_name, m.model, m.tonnage, m.plant_location, m.status, m.created_at),
            )

    def get_machine(self, machine_id: str) -> Optional[MachineRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
            row = cur.fetchone()
            return MachineRecord(**dict(row)) if row else None

    def list_machines(self) -> List[MachineRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM machines ORDER BY id ASC")
            return [MachineRecord(**dict(r)) for r in cur.fetchall()]

    def upsert_mold(self, m: MoldRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO molds (id, mold_code, cavities, material_compatibility, clamp_tonnage_required, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    mold_code=excluded.mold_code,
                    cavities=excluded.cavities,
                    material_compatibility=excluded.material_compatibility,
                    clamp_tonnage_required=excluded.clamp_tonnage_required;
                """,
                (m.id, m.mold_code, m.cavities, m.material_compatibility, m.clamp_tonnage_required, m.created_at),
            )

    def get_mold(self, mold_id: str) -> Optional[MoldRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM molds WHERE id = ?", (mold_id,))
            row = cur.fetchone()
            return MoldRecord(**dict(row)) if row else None

    def upsert_part(self, p: PartRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO parts (id, part_number, name, description, target_weight_g, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    part_number=excluded.part_number,
                    name=excluded.name,
                    description=excluded.description,
                    target_weight_g=excluded.target_weight_g;
                """,
                (p.id, p.part_number, p.name, p.description, p.target_weight_g, p.created_at),
            )

    def get_part(self, part_id: str) -> Optional[PartRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM parts WHERE id = ?", (part_id,))
            row = cur.fetchone()
            return PartRecord(**dict(row)) if row else None

    def upsert_recipe(self, r: RecipeRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO recipes (id, recipe_code, part_id, mold_id, machine_id, target_temperature, target_pressure, target_cycle_time, parameters_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    recipe_code=excluded.recipe_code,
                    part_id=excluded.part_id,
                    mold_id=excluded.mold_id,
                    machine_id=excluded.machine_id,
                    target_temperature=excluded.target_temperature,
                    target_pressure=excluded.target_pressure,
                    target_cycle_time=excluded.target_cycle_time,
                    parameters_json=excluded.parameters_json;
                """,
                (
                    r.id,
                    r.recipe_code,
                    r.part_id,
                    r.mold_id,
                    r.machine_id,
                    r.target_temperature,
                    r.target_pressure,
                    r.target_cycle_time,
                    json.dumps(r.parameters_json),
                    r.created_at,
                ),
            )

    def get_recipe(self, recipe_id: str) -> Optional[RecipeRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["parameters_json"] = json.loads(d["parameters_json"])
            return RecipeRecord(**d)

    def upsert_material(self, m: MaterialRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO materials (id, material_code, name, polymer_type, target_moisture_pct, max_moisture_pct, density_g_cm3, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    material_code=excluded.material_code,
                    name=excluded.name,
                    polymer_type=excluded.polymer_type,
                    target_moisture_pct=excluded.target_moisture_pct,
                    max_moisture_pct=excluded.max_moisture_pct,
                    density_g_cm3=excluded.density_g_cm3;
                """,
                (m.id, m.material_code, m.name, m.polymer_type, m.target_moisture_pct, m.max_moisture_pct, m.density_g_cm3, m.created_at),
            )

    def get_material(self, material_id: str) -> Optional[MaterialRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
            row = cur.fetchone()
            return MaterialRecord(**dict(row)) if row else None

    # ---------------------------------------------------------
    # 6: Cycles Telemetry
    # ---------------------------------------------------------

    def insert_cycle(self, c: StoredCycleRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO cycles (
                    cycle_index, machine_id, mold_id, part_id, recipe_id, timestamp,
                    barrel_temp_z1, barrel_temp_z2, barrel_temp_z3, barrel_temp_z4,
                    nozzle_temp, mold_temp, injection_pressure, holding_pressure,
                    back_pressure, injection_speed, screw_rpm, cushion_position,
                    dosing_time, injection_time, cooling_time, cycle_time,
                    ambient_temp, ambient_humidity, material_moisture_pct,
                    part_weight_g, defect_flag, defect_type, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    c.cycle_index, c.machine_id, c.mold_id, c.part_id, c.recipe_id, c.timestamp,
                    c.barrel_temp_z1, c.barrel_temp_z2, c.barrel_temp_z3, c.barrel_temp_z4,
                    c.nozzle_temp, c.mold_temp, c.injection_pressure, c.holding_pressure,
                    c.back_pressure, c.injection_speed, c.screw_rpm, c.cushion_position,
                    c.dosing_time, c.injection_time, c.cooling_time, c.cycle_time,
                    c.ambient_temp, c.ambient_humidity, c.material_moisture_pct,
                    c.part_weight_g, int(c.defect_flag), c.defect_type, json.dumps(c.raw_json)
                ),
            )
            return cur.lastrowid

    def insert_cycles_batch(self, cycles: List[StoredCycleRecord]) -> int:
        if not cycles:
            return 0
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT INTO cycles (
                    cycle_index, machine_id, mold_id, part_id, recipe_id, timestamp,
                    barrel_temp_z1, barrel_temp_z2, barrel_temp_z3, barrel_temp_z4,
                    nozzle_temp, mold_temp, injection_pressure, holding_pressure,
                    back_pressure, injection_speed, screw_rpm, cushion_position,
                    dosing_time, injection_time, cooling_time, cycle_time,
                    ambient_temp, ambient_humidity, material_moisture_pct,
                    part_weight_g, defect_flag, defect_type, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.cycle_index, c.machine_id, c.mold_id, c.part_id, c.recipe_id, c.timestamp,
                        c.barrel_temp_z1, c.barrel_temp_z2, c.barrel_temp_z3, c.barrel_temp_z4,
                        c.nozzle_temp, c.mold_temp, c.injection_pressure, c.holding_pressure,
                        c.back_pressure, c.injection_speed, c.screw_rpm, c.cushion_position,
                        c.dosing_time, c.injection_time, c.cooling_time, c.cycle_time,
                        c.ambient_temp, c.ambient_humidity, c.material_moisture_pct,
                        c.part_weight_g, int(c.defect_flag), c.defect_type, json.dumps(c.raw_json)
                    )
                    for c in cycles
                ],
            )
            return len(cycles)

    def get_cycle(self, machine_id: str, cycle_index: int) -> Optional[StoredCycleRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cycles WHERE machine_id = ? AND cycle_index = ?", (machine_id, cycle_index))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["raw_json"] = json.loads(d["raw_json"]) if d.get("raw_json") else {}
            d["defect_flag"] = bool(d["defect_flag"])
            return StoredCycleRecord(**d)

    def get_cycles_range(self, machine_id: str, start_cycle: int, end_cycle: int) -> List[StoredCycleRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM cycles WHERE machine_id = ? AND cycle_index >= ? AND cycle_index <= ? ORDER BY cycle_index ASC",
                (machine_id, start_cycle, end_cycle),
            )
            results = []
            for row in cur.fetchall():
                d = dict(row)
                d["raw_json"] = json.loads(d["raw_json"]) if d.get("raw_json") else {}
                d["defect_flag"] = bool(d["defect_flag"])
                results.append(StoredCycleRecord(**d))
            return results

    def get_latest_cycle(self, machine_id: str) -> Optional[StoredCycleRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM cycles WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT 1", (machine_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["raw_json"] = json.loads(d["raw_json"]) if d.get("raw_json") else {}
            d["defect_flag"] = bool(d["defect_flag"])
            return StoredCycleRecord(**d)

    def get_cycle_count(self, machine_id: str) -> int:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM cycles WHERE machine_id = ?", (machine_id,))
            return cur.fetchone()[0]

    # ---------------------------------------------------------
    # 7-8: Fingerprints & Quality Contracts
    # ---------------------------------------------------------

    def upsert_fingerprint(self, f: StoredFingerprintRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO process_fingerprints (id, context_key, machine_id, mold_id, part_id, recipe_id, baseline_version, sample_count, stats_json, envelope_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    context_key=excluded.context_key,
                    baseline_version=excluded.baseline_version,
                    sample_count=excluded.sample_count,
                    stats_json=excluded.stats_json,
                    envelope_json=excluded.envelope_json;
                """,
                (
                    f.id, f.context_key, f.machine_id, f.mold_id, f.part_id, f.recipe_id,
                    f.baseline_version, f.sample_count, json.dumps(f.stats_json), json.dumps(f.envelope_json), f.created_at
                ),
            )

    def get_fingerprint(self, fingerprint_id: str) -> Optional[StoredFingerprintRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM process_fingerprints WHERE id = ?", (fingerprint_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["stats_json"] = json.loads(d["stats_json"])
            d["envelope_json"] = json.loads(d["envelope_json"])
            return StoredFingerprintRecord(**d)

    def get_fingerprint_by_machine(self, machine_id: str) -> Optional[StoredFingerprintRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM process_fingerprints WHERE machine_id = ? ORDER BY created_at DESC LIMIT 1", (machine_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["stats_json"] = json.loads(d["stats_json"])
            d["envelope_json"] = json.loads(d["envelope_json"])
            return StoredFingerprintRecord(**d)

    def upsert_quality_contract(self, qc: StoredQualityContractRecord) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO quality_contracts (id, contract_code, part_id, recipe_id, target_weight_g, weight_tolerance_g, max_sink_mark_mm, allow_flash, target_cycle_time_s, cycle_time_tolerance_s, specs_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    contract_code=excluded.contract_code,
                    target_weight_g=excluded.target_weight_g,
                    weight_tolerance_g=excluded.weight_tolerance_g,
                    max_sink_mark_mm=excluded.max_sink_mark_mm,
                    allow_flash=excluded.allow_flash,
                    target_cycle_time_s=excluded.target_cycle_time_s,
                    cycle_time_tolerance_s=excluded.cycle_time_tolerance_s,
                    specs_json=excluded.specs_json;
                """,
                (
                    qc.id, qc.contract_code, qc.part_id, qc.recipe_id, qc.target_weight_g,
                    qc.weight_tolerance_g, qc.max_sink_mark_mm, int(qc.allow_flash),
                    qc.target_cycle_time_s, qc.cycle_time_tolerance_s, json.dumps(qc.specs_json), qc.created_at
                ),
            )

    def get_quality_contract(self, contract_id: str) -> Optional[StoredQualityContractRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM quality_contracts WHERE id = ?", (contract_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["specs_json"] = json.loads(d["specs_json"])
            d["allow_flash"] = bool(d["allow_flash"])
            return StoredQualityContractRecord(**d)

    def get_quality_contract_by_part(self, part_id: str) -> Optional[StoredQualityContractRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM quality_contracts WHERE part_id = ? ORDER BY created_at DESC LIMIT 1", (part_id,))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["specs_json"] = json.loads(d["specs_json"])
            d["allow_flash"] = bool(d["allow_flash"])
            return StoredQualityContractRecord(**d)

    # ---------------------------------------------------------
    # 9-10: Drift Events & Quality Predictions
    # ---------------------------------------------------------

    def insert_drift_event(self, d: StoredDriftEventRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO drift_events (event_id, cycle_index, machine_id, timestamp, drift, severity, lead_cycles, signals_json, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    severity=excluded.severity,
                    lead_cycles=excluded.lead_cycles,
                    signals_json=excluded.signals_json,
                    details_json=excluded.details_json;
                """,
                (
                    d.event_id, d.cycle_index, d.machine_id, d.timestamp,
                    int(d.drift), d.severity, d.lead_cycles,
                    json.dumps(d.signals_json), json.dumps(d.details_json), d.created_at
                ),
            )
            return cur.lastrowid

    def list_drift_events(self, machine_id: str, limit: int = 100) -> List[StoredDriftEventRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM drift_events WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT ?",
                (machine_id, int(limit)),
            )
            records = []
            for r in cur.fetchall():
                d = dict(r)
                d["signals_json"] = json.loads(d["signals_json"]) if d.get("signals_json") else []
                d["details_json"] = json.loads(d["details_json"]) if d.get("details_json") else {}
                d["drift"] = bool(d["drift"])
                records.append(StoredDriftEventRecord(**d))
            return records

    def insert_quality_prediction(self, p: StoredQualityPredictionRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO quality_predictions (event_id, cycle_index, machine_id, risk_probability, confidence, risk_state, operator_mode, root_cause_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p.event_id, p.cycle_index, p.machine_id, p.risk_probability,
                    p.confidence, p.risk_state, p.operator_mode,
                    json.dumps(p.root_cause_json), p.created_at
                ),
            )
            return cur.lastrowid

    def list_quality_predictions(self, machine_id: str, limit: int = 100) -> List[StoredQualityPredictionRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM quality_predictions WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT ?",
                (machine_id, limit),
            )
            records = []
            for r in cur.fetchall():
                d = dict(r)
                d["root_cause_json"] = json.loads(d["root_cause_json"])
                records.append(StoredQualityPredictionRecord(**d))
            return records

    def get_latest_prediction(self, machine_id: str) -> Optional[StoredQualityPredictionRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM quality_predictions WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT 1",
                (machine_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["root_cause_json"] = json.loads(d["root_cause_json"])
            return StoredQualityPredictionRecord(**d)

    # ---------------------------------------------------------
    # 11-13: Interventions (Candidates, Recommendations, Applications)
    # ---------------------------------------------------------

    def insert_recommendation(
        self,
        rec: StoredRecommendationRecord,
        candidates: Optional[List[StoredInterventionCandidateRecord]] = None,
    ) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO intervention_recommendations (
                    recommendation_id, event_id, cycle_index, machine_id, action_id,
                    action_text, why_text, evidence_json, expected_effect, confidence,
                    operating_limit, recovery_check, is_abstain, abstain_reason,
                    operator_mode, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(recommendation_id) DO UPDATE SET
                    action_text=excluded.action_text,
                    why_text=excluded.why_text,
                    evidence_json=excluded.evidence_json,
                    expected_effect=excluded.expected_effect,
                    confidence=excluded.confidence;
                """,
                (
                    rec.recommendation_id, rec.event_id, rec.cycle_index, rec.machine_id, rec.action_id,
                    rec.action_text, rec.why_text, json.dumps(rec.evidence_json), rec.expected_effect, rec.confidence,
                    rec.operating_limit, rec.recovery_check, int(rec.is_abstain), rec.abstain_reason,
                    rec.operator_mode, rec.created_at
                ),
            )
            rec_id = cur.lastrowid

            if candidates:
                for c in candidates:
                    cur.execute(
                        """
                        INSERT INTO intervention_candidates (
                            recommendation_id, action_id, name, target_signal, delta_value,
                            unit, cost, disruption, estimated_risk, boundary_checked, is_selected, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            rec.recommendation_id, c.action_id, c.name, c.target_signal, c.delta_value,
                            c.unit, c.cost, c.disruption, c.estimated_risk, int(c.boundary_checked),
                            int(c.is_selected), json.dumps(c.metadata_json)
                        ),
                    )
            return rec_id

    def get_latest_recommendation(self, machine_id: str) -> Optional[StoredRecommendationRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention_recommendations WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT 1",
                (machine_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["evidence_json"] = json.loads(d["evidence_json"])
            d["is_abstain"] = bool(d["is_abstain"])
            return StoredRecommendationRecord(**d)

    def get_recommendation_candidates(self, recommendation_id: str) -> List[StoredInterventionCandidateRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention_candidates WHERE recommendation_id = ? ORDER BY action_id ASC",
                (recommendation_id,),
            )
            candidates = []
            for r in cur.fetchall():
                d = dict(r)
                d["metadata_json"] = json.loads(d["metadata_json"])
                d["boundary_checked"] = bool(d["boundary_checked"])
                d["is_selected"] = bool(d["is_selected"])
                candidates.append(StoredInterventionCandidateRecord(**d))
            return candidates

    def insert_intervention_application(self, app: StoredInterventionApplicationRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO intervention_applications (
                    cycle_index, machine_id, action_id, applied_by, timestamp,
                    pre_intervention_risk, target_delta, status, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    app.cycle_index, app.machine_id, app.action_id, app.applied_by, app.timestamp,
                    app.pre_intervention_risk, app.target_delta, app.status, json.dumps(app.details_json), app.created_at
                ),
            )
            return cur.lastrowid

    def list_intervention_applications(self, machine_id: str) -> List[StoredInterventionApplicationRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM intervention_applications WHERE machine_id = ? ORDER BY cycle_index DESC",
                (machine_id,),
            )
            records = []
            for r in cur.fetchall():
                d = dict(r)
                d["details_json"] = json.loads(d["details_json"])
                records.append(StoredInterventionApplicationRecord(**d))
            return records

    # ---------------------------------------------------------
    # 14-15: Recovery & Containment
    # ---------------------------------------------------------

    def insert_recovery_event(self, recov: StoredRecoveryEventRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO recovery_events (
                    cycle_index, machine_id, intervention_id, recovery_status, release_decision,
                    risk_before, risk_after, stability_before, stability_after,
                    consecutive_stable_cycles, summary_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recov.cycle_index, recov.machine_id, recov.intervention_id, recov.recovery_status,
                    recov.release_decision, recov.risk_before, recov.risk_after, recov.stability_before,
                    recov.stability_after, recov.consecutive_stable_cycles, recov.summary_message, recov.created_at
                ),
            )
            return cur.lastrowid

    def get_latest_recovery_event(self, machine_id: str) -> Optional[StoredRecoveryEventRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM recovery_events WHERE machine_id = ? ORDER BY cycle_index DESC LIMIT 1",
                (machine_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return StoredRecoveryEventRecord(**dict(row))

    def upsert_containment_window(self, win: StoredContainmentWindowRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO containment_windows (
                    machine_id, last_known_good_cycle, suspect_start_cycle, suspect_end_cycle,
                    suspect_cycle_count, intervention_cycle, recovery_cycle, release_cycle,
                    quarantine_cycles_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    win.machine_id, win.last_known_good_cycle, win.suspect_start_cycle, win.suspect_end_cycle,
                    win.suspect_cycle_count, win.intervention_cycle, win.recovery_cycle, win.release_cycle,
                    json.dumps(win.quarantine_cycles_json), win.created_at
                ),
            )
            return cur.lastrowid

    def get_latest_containment_window(self, machine_id: str) -> Optional[StoredContainmentWindowRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM containment_windows WHERE machine_id = ? ORDER BY id DESC LIMIT 1",
                (machine_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["quarantine_cycles_json"] = json.loads(d["quarantine_cycles_json"])
            return StoredContainmentWindowRecord(**d)

    # ---------------------------------------------------------
    # 16-17: Checkpoints & Audit Log
    # ---------------------------------------------------------

    def insert_checkpoint(self, chk: StoredCheckpointRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO checkpoints (checkpoint_name, cycle_index, machine_id, timestamp, state, data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chk.checkpoint_name, chk.cycle_index, chk.machine_id, chk.timestamp,
                    chk.state, json.dumps(chk.data_json), chk.created_at
                ),
            )
            return cur.lastrowid

    def get_checkpoint(self, checkpoint_name: str) -> Optional[StoredCheckpointRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_name = ? ORDER BY id DESC LIMIT 1",
                (checkpoint_name,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["data_json"] = json.loads(d["data_json"])
            return StoredCheckpointRecord(**d)

    def list_checkpoints(self, machine_id: str) -> List[StoredCheckpointRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM checkpoints WHERE machine_id = ? ORDER BY id DESC", (machine_id,))
            records = []
            for r in cur.fetchall():
                d = dict(r)
                d["data_json"] = json.loads(d["data_json"])
                records.append(StoredCheckpointRecord(**d))
            return records

    def log_audit_event(self, log: StoredAuditLogRecord) -> int:
        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO audit_log (event_id, cycle_index, machine_id, timestamp, event_type, severity, description, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.event_id, log.cycle_index, log.machine_id, log.timestamp,
                    log.event_type, log.severity, log.description,
                    json.dumps(log.details_json), log.created_at
                ),
            )
            return cur.lastrowid

    def list_audit_logs(self, machine_id: str, limit: int = 100) -> List[StoredAuditLogRecord]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM audit_log WHERE machine_id = ? ORDER BY id DESC LIMIT ?",
                (machine_id, limit),
            )
            records = []
            for r in cur.fetchall():
                d = dict(r)
                d["details_json"] = json.loads(d["details_json"])
                records.append(StoredAuditLogRecord(**d))
            return records

    # ---------------------------------------------------------
    # Unified Event Object (STOR-02)
    # ---------------------------------------------------------

    def record_unified_event(self, event: GuardianEvent) -> None:
        """
        Record a standardized GuardianEvent into audit_log and relevant typed event tables.
        """
        # 1. Always record in audit log
        audit = StoredAuditLogRecord(
            event_id=event.event_id,
            cycle_index=event.cycle_id,
            machine_id=event.machine_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            severity=event.severity,
            description=f"Event {event.event_type} at cycle {event.cycle_id}: severity {event.severity}, risk {event.quality_risk:.2f}",
            details_json={
                "signals": event.signals,
                "quality_risk": event.quality_risk,
                "confidence": event.confidence,
                "mold_id": event.mold_id,
                "part_id": event.part_id,
                "recipe_id": event.recipe_id,
                "details": event.details,
            },
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.log_audit_event(audit)

        # 2. If PROCESS_DRIFT event, also insert to drift_events
        if "DRIFT" in event.event_type:
            self.insert_drift_event(
                StoredDriftEventRecord(
                    event_id=event.event_id,
                    cycle_index=event.cycle_id,
                    machine_id=event.machine_id,
                    timestamp=event.timestamp,
                    drift=True,
                    severity=1.0 if event.severity == "HIGH" else 0.5,
                    lead_cycles=event.details.get("lead_cycles", 0),
                    signals_json=event.signals,
                    details_json=event.details,
                )
            )

    # ---------------------------------------------------------
    # Seed Initial Topology Data
    # ---------------------------------------------------------

    def seed_default_plant_data(self) -> None:
        """Populate initial topology records for primary automotive demo scenario."""
        self.upsert_machine(
            MachineRecord(
                id="IMM-01",
                machine_name="Engel Victory 120T",
                model="Victory 120",
                tonnage=120.0,
                plant_location="Bay-3 / Line-A",
                status="ACTIVE",
            )
        )
        self.upsert_mold(
            MoldRecord(
                id="MOLD-18",
                mold_code="MOLD-AUTO-H18",
                cavities=1,
                material_compatibility="PA66-GF30",
                clamp_tonnage_required=110.0,
            )
        )
        self.upsert_mold(
            MoldRecord(
                id="MOLD-HOUSING-04",
                mold_code="MOLD-HOUSING-04",
                cavities=1,
                material_compatibility="PP-HOMO",
                clamp_tonnage_required=100.0,
            )
        )
        self.upsert_part(
            PartRecord(
                id="AUTO-HOUSING-A",
                part_number="PN-AH-8820",
                name="Automotive Electronic Sensor Housing",
                description="High-precision glass-filled PA66 sensor housing for powertrain",
                target_weight_g=142.5,
            )
        )
        self.upsert_part(
            PartRecord(
                id="PART-AUTO-HOUSING-A",
                part_number="PART-AUTO-HOUSING-A",
                name="Automotive Electronic Sensor Housing",
                description="High-precision glass-filled PA66 sensor housing for powertrain",
                target_weight_g=142.5,
            )
        )
        self.upsert_material(
            MaterialRecord(
                id="PA66-GF30",
                material_code="MAT-PA66-GF30-BLK",
                name="Polyamide 66 30% Glass Fiber Reinforced",
                polymer_type="PA66",
                target_moisture_pct=0.12,
                max_moisture_pct=0.20,
                density_g_cm3=1.35,
            )
        )
        self.upsert_material(
            MaterialRecord(
                id="PP-HOMO",
                material_code="MAT-PP-HOMO-NAT",
                name="Polypropylene Homopolymer",
                polymer_type="PP",
                target_moisture_pct=0.08,
                max_moisture_pct=0.15,
                density_g_cm3=0.91,
            )
        )
        self.upsert_recipe(
            RecipeRecord(
                id="RCP-12",
                recipe_code="RCP-AH-PA66-STD",
                part_id="AUTO-HOUSING-A",
                mold_id="MOLD-18",
                machine_id="IMM-01",
                target_temperature=285.0,
                target_pressure=120.0,
                target_cycle_time=30.0,
                parameters_json={
                    "barrel_temp_z1": 275.0,
                    "barrel_temp_z2": 280.0,
                    "barrel_temp_z3": 285.0,
                    "barrel_temp_z4": 285.0,
                    "nozzle_temp": 285.0,
                    "mold_temp": 80.0,
                    "injection_pressure": 120.0,
                    "holding_pressure": 85.0,
                    "back_pressure": 10.0,
                    "injection_speed": 45.0,
                    "screw_rpm": 60.0,
                    "cooling_time": 12.0,
                    "cycle_time": 30.0,
                },
            )
        )
        self.upsert_recipe(
            RecipeRecord(
                id="RECIPE-PP-V2.1",
                recipe_code="RECIPE-PP-V2.1",
                part_id="PART-AUTO-HOUSING-A",
                mold_id="MOLD-HOUSING-04",
                machine_id="IMM-01",
                target_temperature=285.0,
                target_pressure=120.0,
                target_cycle_time=30.0,
                parameters_json={
                    "barrel_temp_z1": 275.0,
                    "barrel_temp_z2": 280.0,
                    "barrel_temp_z3": 285.0,
                    "barrel_temp_z4": 285.0,
                    "nozzle_temp": 285.0,
                    "mold_temp": 80.0,
                    "injection_pressure": 120.0,
                    "holding_pressure": 85.0,
                    "back_pressure": 10.0,
                    "injection_speed": 45.0,
                    "screw_rpm": 60.0,
                    "cooling_time": 12.0,
                    "cycle_time": 30.0,
                },
            )
        )
        self.upsert_quality_contract(
            StoredQualityContractRecord(
                id="QC-AUTO-01",
                contract_code="QC-AH-STANDARD",
                part_id="AUTO-HOUSING-A",
                recipe_id="RCP-12",
                target_weight_g=142.5,
                weight_tolerance_g=1.5,
                max_sink_mark_mm=0.08,
                allow_flash=False,
                target_cycle_time_s=30.0,
                cycle_time_tolerance_s=2.0,
                specs_json={
                    "critical_dimensions_mm": [24.5, 48.0, 12.2],
                    "surface_finish_ra_um": 0.8,
                },
            )
        )

    # ---------------------------------------------------------
    # Deterministic Demo Reset & Session Isolation (DEMO-02)
    # ---------------------------------------------------------

    def reset_demo_session(
        self,
        machine_id: str = "IMM-01",
        run_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[str, int]:
        """
        Create a new isolated demo run while strictly preserving historical audit records.
        
        Returns:
            Tuple of (new_run_id, count_of_preserved_audit_records)
        """
        import uuid
        from datetime import datetime, timezone
        from process_guardian.storage.schemas import StoredAuditLogRecord

        new_run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        with self.db.transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM audit_log WHERE machine_id = ?", (machine_id,))
            audit_count_prior = cur.fetchone()[0]

            reset_event = StoredAuditLogRecord(
                event_id=f"audit_reset_{uuid.uuid4().hex[:8]}",
                cycle_index=0,
                machine_id=machine_id,
                timestamp=now_ts,
                event_type="DEMO_SESSION_RESET",
                severity="INFO",
                description=f"Demo session reset. New isolated run initiated: {new_run_id}. Prior audit log entries strictly preserved.",
                details_json={
                    "run_id": new_run_id,
                    "notes": notes or "Deterministic demo replay reset",
                    "prior_audit_count": audit_count_prior,
                },
            )
            cur.execute(
                """
                INSERT INTO audit_log (event_id, cycle_index, machine_id, timestamp, event_type, severity, description, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reset_event.event_id,
                    reset_event.cycle_index,
                    reset_event.machine_id,
                    reset_event.timestamp,
                    reset_event.event_type,
                    reset_event.severity,
                    reset_event.description,
                    json.dumps(reset_event.details_json),
                    reset_event.created_at or now_ts,
                ),
            )

            # Clear active runtime execution tables for this machine (leaving audit_log intact!)
            cur.execute("DELETE FROM intervention_candidates")
            tables_to_clear = [
                "cycles",
                "drift_events",
                "quality_predictions",
                "intervention_recommendations",
                "intervention_applications",
                "recovery_events",
                "containment_windows",
            ]
            for tbl in tables_to_clear:
                cur.execute(f"DELETE FROM {tbl} WHERE machine_id = ?", (machine_id,))

            cur.execute("SELECT COUNT(*) FROM audit_log WHERE machine_id = ?", (machine_id,))
            total_audit_preserved = cur.fetchone()[0]

        # Re-seed default plant data
        self.seed_default_plant_data()

        return new_run_id, total_audit_preserved
