# Phase 6: API + Storage Integration — Context

## Objective
Build the **FastAPI Service Layer** (`API-01..05`) and the **SQLite Storage Architecture** (`STOR-01..02`) that connects the core Process Guardian closed-loop engine into a robust, high-performance, vendor-neutral backend service.

## Target Requirements
- **API-01**: FastAPI ingestion endpoints: `POST /api/cycles`, `POST /api/events`, `POST /api/checkpoints`
- **API-02**: Process state endpoints: `GET /api/process/current`, `GET /api/process/fingerprint`, `GET /api/process/drift`
- **API-03**: Quality endpoints: `GET /api/quality/risk`, `GET /api/quality/contract`
- **API-04**: Intervention endpoints: `POST /api/interventions/simulate`, `GET /api/interventions/recommendation`, `POST /api/interventions/apply-demo`, `GET /api/interventions/history`
- **API-05**: Recovery/containment endpoints: `GET /api/recovery/status`, `GET /api/containment/window`, `POST /api/containment/release`
- **STOR-01**: SQLite database with 17 relational tables:
  `machines`, `molds`, `parts`, `recipes`, `materials`, `cycles`, `process_fingerprints`, `quality_contracts`, `drift_events`, `quality_predictions`, `intervention_candidates`, `intervention_recommendations`, `intervention_applications`, `recovery_events`, `containment_windows`, `checkpoints`, `audit_log`.
- **STOR-02**: Unified event model using consistent schema (`event_id`, `machine_id`, `mold_id`, `part_id`, `recipe_id`, `cycle_id`, `timestamp`, `event_type`, `severity`, `signals`, `quality_risk`, `confidence`).

## Architecture & Design

### 1. Storage Architecture (STOR-01, STOR-02)
- Local SQLite database (`process_guardian.db` or `:memory:` for testing).
- Complete DDL defining all 17 tables with appropriate indexes, foreign key constraints, and JSON serialization.
- Unified `GuardianEvent` schema matching the specification exactly.
- High-level Repository pattern providing typed data access methods for every table, atomic transactions, and automated audit logging.

### 2. Service & API Layer (API-01..API-05)
- FastAPI app instance with structured routers, lifecycle events for database schema migration and demo context initialization, and CORS middleware.
- Dependency injection pattern wiring the Database Session and `ClosedLoopOrchestrator`.
- Clean Pydantic request and response schemas for all 13 required REST endpoints.
- Deterministic demo execution support: one-click reset, scenario replay, and checkpointing.
