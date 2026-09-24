# Phase 6: API + Storage Integration — Research & Technical Decisions

## 1. Storage Architecture & 17-Table Schema

### Schema Breakdown
The SQLite database stores both static plant topology (machines, molds, parts, recipes, materials) and live operational telemetry/decisions.

1. `machines` (id TEXT PRIMARY KEY, machine_name TEXT, model TEXT, tonnage REAL, plant_location TEXT, status TEXT, created_at TEXT)
2. `molds` (id TEXT PRIMARY KEY, mold_code TEXT, cavities INTEGER, material_compatibility TEXT, clamp_tonnage_required REAL, created_at TEXT)
3. `parts` (id TEXT PRIMARY KEY, part_number TEXT, name TEXT, description TEXT, target_weight_g REAL, created_at TEXT)
4. `recipes` (id TEXT PRIMARY KEY, recipe_code TEXT, part_id TEXT, mold_id TEXT, machine_id TEXT, target_temperature REAL, target_pressure REAL, target_cycle_time REAL, parameters_json TEXT, created_at TEXT)
5. `materials` (id TEXT PRIMARY KEY, material_code TEXT, name TEXT, polymer_type TEXT, target_moisture_pct REAL, max_moisture_pct REAL, density_g_cm3 REAL, created_at TEXT)
6. `cycles` (id INTEGER PRIMARY KEY AUTOINCREMENT, cycle_index INTEGER, machine_id TEXT, mold_id TEXT, part_id TEXT, recipe_id TEXT, timestamp TEXT, barrel_temp_z1 REAL, barrel_temp_z2 REAL, barrel_temp_z3 REAL, barrel_temp_z4 REAL, nozzle_temp REAL, mold_temp REAL, injection_pressure REAL, holding_pressure REAL, back_pressure REAL, injection_speed REAL, screw_rpm REAL, cushion_position REAL, dosing_time REAL, injection_time REAL, cooling_time REAL, cycle_time REAL, ambient_temp REAL, ambient_humidity REAL, material_moisture_pct REAL, part_weight_g REAL, defect_flag INTEGER, defect_type TEXT, raw_json TEXT)
7. `process_fingerprints` (id TEXT PRIMARY KEY, context_key TEXT, machine_id TEXT, mold_id TEXT, part_id TEXT, recipe_id TEXT, baseline_version TEXT, sample_count INTEGER, stats_json TEXT, envelope_json TEXT, created_at TEXT)
8. `quality_contracts` (id TEXT PRIMARY KEY, contract_code TEXT, part_id TEXT, recipe_id TEXT, target_weight_g REAL, weight_tolerance_g REAL, max_sink_mark_mm REAL, allow_flash INTEGER, target_cycle_time_s REAL, cycle_time_tolerance_s REAL, specs_json TEXT, created_at TEXT)
9. `drift_events` (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE, cycle_index INTEGER, machine_id TEXT, timestamp TEXT, drift INTEGER, severity REAL, lead_cycles INTEGER, signals_json TEXT, details_json TEXT, created_at TEXT)
10. `quality_predictions` (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, cycle_index INTEGER, machine_id TEXT, risk_probability REAL, confidence REAL, risk_state TEXT, operator_mode TEXT, root_cause_json TEXT, created_at TEXT)
11. `intervention_candidates` (id INTEGER PRIMARY KEY AUTOINCREMENT, recommendation_id TEXT, action_id TEXT, name TEXT, target_signal TEXT, delta_value REAL, unit TEXT, cost REAL, disruption REAL, estimated_risk REAL, boundary_checked INTEGER, is_selected INTEGER, metadata_json TEXT)
12. `intervention_recommendations` (id INTEGER PRIMARY KEY AUTOINCREMENT, recommendation_id TEXT UNIQUE, event_id TEXT, cycle_index INTEGER, machine_id TEXT, action_id TEXT, action_text TEXT, why_text TEXT, evidence_json TEXT, expected_effect TEXT, confidence REAL, operating_limit TEXT, recovery_check TEXT, is_abstain INTEGER, abstain_reason TEXT, operator_mode TEXT, created_at TEXT)
13. `intervention_applications` (id INTEGER PRIMARY KEY AUTOINCREMENT, cycle_index INTEGER, machine_id TEXT, action_id TEXT, applied_by TEXT, timestamp TEXT, pre_intervention_risk REAL, target_delta REAL, status TEXT, created_at TEXT)
14. `recovery_events` (id INTEGER PRIMARY KEY AUTOINCREMENT, cycle_index INTEGER, machine_id TEXT, intervention_id TEXT, recovery_status TEXT, release_decision TEXT, risk_before REAL, risk_after REAL, stability_before REAL, stability_after REAL, consecutive_stable_cycles INTEGER, summary_message TEXT, created_at TEXT)
15. `containment_windows` (id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id TEXT, last_known_good_cycle INTEGER, suspect_start_cycle INTEGER, suspect_end_cycle INTEGER, suspect_cycle_count INTEGER, intervention_cycle INTEGER, recovery_cycle INTEGER, release_cycle INTEGER, quarantine_cycles_json TEXT, created_at TEXT)
16. `checkpoints` (id INTEGER PRIMARY KEY AUTOINCREMENT, checkpoint_name TEXT, cycle_index INTEGER, machine_id TEXT, timestamp TEXT, state TEXT, data_json TEXT, created_at TEXT)
17. `audit_log` (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, cycle_index INTEGER, machine_id TEXT, timestamp TEXT, event_type TEXT, severity TEXT, description TEXT, details_json TEXT, created_at TEXT)

### Unified Event Model (STOR-02)
Standardized schema matching Section 10 of Architecture:
```json
{
  "event_id": "evt_00421",
  "machine_id": "IMM_07",
  "mold_id": "MOLD_18",
  "part_id": "AUTO_HOUSING_A",
  "recipe_id": "RCP_12",
  "cycle_id": 429,
  "timestamp": "2026-09-29T10:21:14Z",
  "event_type": "PROCESS_DRIFT",
  "severity": "HIGH",
  "signals": ["barrel_temp_z3", "injection_pressure", "cycle_time"],
  "quality_risk": 0.72,
  "confidence": 0.93
}
```

## 2. API Design & FastAPI Implementation

### Ingestion Endpoints (API-01)
- `POST /api/cycles`: Ingests single telemetry record or batch of records. Normalizes, evaluates through ClosedLoopOrchestrator, records all decisions into SQLite, and returns cycle result.
- `POST /api/events`: Ingests injection event or custom operational alarm (e.g. `inject_event("thermal_drift", cycle=420)`).
- `POST /api/checkpoints`: Captures point-in-time state checkpoint or performs deterministic reset/restore.

### Process State Endpoints (API-02)
- `GET /api/process/current`: Current cycle index, stability score (0-100%), quality risk (0-100%), machine state, active telemetry values.
- `GET /api/process/fingerprint`: Baseline metrics, normal operating ranges, $\pm 3\sigma$ envelopes.
- `GET /api/process/drift`: Drift Sentinel status, severity score, lead cycles, multi-detector breakdown (EWMA, CUSUM, Mahalanobis, Student-t).

### Quality Risk Endpoints (API-03)
- `GET /api/quality/risk`: Calibrated defect risk probability, confidence, risk state, operator mode, and root cause evidence with percentage breakdown (summing to 100.0%).
- `GET /api/quality/contract`: Quality Contract thresholds, weight tolerances, sink mark tolerances, cycle time tolerances.

### Intervention Endpoints (API-04)
- `POST /api/interventions/simulate`: Evaluates candidate actions using surrogate response surface model.
- `GET /api/interventions/recommendation`: Active 7-field recommendation contract with confidence, boundary checks, and abstain logic.
- `POST /api/interventions/apply-demo`: Enacts recommended or selected intervention in demo mode, updating state to APPLIED/RECOVERY_CHECK.
- `GET /api/interventions/history`: Chronological log of generated recommendations and applications.

### Recovery & Containment Endpoints (API-05)
- `GET /api/recovery/status`: Recovery verifier state (parameter movement, stability window progress, release decision).
- `GET /api/containment/window`: Last-known-good cycle, suspect cycle count, quarantine list, release cycle.
- `POST /api/containment/release`: Authorize release of quarantined batch or confirm production release.
