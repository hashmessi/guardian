# Process Guardian

**Closed-loop decision engine for injection-molding drift.** It detects process drift early, weighs the cost of waiting against the cost of acting, recommends the smallest corrective action, verifies recovery with a physical quality check, and contains the suspect production lot.

Built for **Hack4Purpose, PS02**, for Indian automotive Tier-2/Tier-3 plastic injection molders.

---

## 1. Product overview

Process Guardian is a decision layer that sits beside an injection-molding machine. It reads cycle telemetry (temperature, pressure, moisture, operational signals), identifies when the process is drifting, and tells the operator what to do and what it costs. It does **not** write to the machine. All adjustments remain operator-advised.

## 2. Problem

Drift in temperature, pressure, or resin moisture often goes unnoticed until parts fail inspection. By then, a whole lot is suspect. Operators have to decide, under time pressure, whether to stop the line, adjust, or keep running, and they rarely have a quantified basis for that choice.

## 3. Solution

Process Guardian runs a single decision loop:

1. **Detect** drift with statistical monitors (EWMA, CUSUM, Hotelling T²).
2. **Diagnose** the likely cause with a root-cause evidence ranking.
3. **Evaluate** cost of waiting vs. cost of acting (CoPQ model).
4. **Recommend** the minimum-effective action, or **ABSTAIN** when evidence is insufficient.
5. **Verify** recovery through a mandatory physical QC checkpoint.
6. **Contain** the suspect lot from the last verified-good cycle to the QC release.

## 4. Key features

- **Drift detection:** multi-method detector (EWMA, CUSUM, multivariate Hotelling T², trend) with lead-cycle verification.
- **Quality risk:** calibrated per-cycle probability of Quality Contract violation (gradient-boosted classifier + probability calibration).
- **Constrained interventions:** candidate actions (A0–A4) scored by risk × cost × disruption under machine and operating-envelope constraints, with a surrogate model.
- **Recommendation contract:** every recommendation carries a fixed set of fields and passes an explicit ABSTAIN safety gate.
- **Recovery verification:** checks parameter shift and a stability window before release.
- **Scrap containment:** last-known-good, suspect window, quarantine and release logic, plus a containment boundary card.
- **Explicit state machine:** 13 states with validated transitions (`HEALTHY` → … → `RELEASE`).
- **Economics:** CoPQ parameters (resin, machine rate, energy, sorting), cost-of-waiting evaluator, and decision value.
- **Operational checkpoints:** recipe lock, resin moisture batch check, mold-release spray interval, and an operator human-channel confirmation.
- **Counterfactual replay:** the same event stream run with Guardian OFF vs. Guardian ON, with a side-by-side comparison.
- **Evidence levels:** every result is tagged as Level 1 (challenge), Level 2 (external measured data), Level 3 (software invariant), or Level 4 (controlled counterfactual).
- **Scenario engine and validation:** 10 scripted operational scenarios with a CLI runner and a JSON report.
- **Three-screen UI:** Live Process, Incident Diagnosis, and Intervention & Recovery, with a front page and an audit drawer.

## 5. Architecture

```
  Simulator / telemetry input
            │
            ▼
  Adapter (normalize, validate, enrich)
            │
            ▼
  Fingerprint ─► Sentinel (drift) ─► Quality risk ─► Root cause
                                          │
                                          ▼
               Economics (cost of waiting vs. acting)
                                          │
                                          ▼
          Intervention (candidates, optimizer, recommendation)
                                          │
                                          ▼
   Operator checkpoints ─► Recovery verifier ─► Containment
                                          │
                                          ▼
                 State machine  ·  SQLite storage + audit trail
                                          │
                                          ▼
                     FastAPI (`/api/*`)  ◄── React UI (polls every 2–30 s)
```

Code layout (`src/process_guardian/`):

| Package | Responsibility |
|---|---|
| `simulator/` | Deterministic cycle simulator with regimes and event injection |
| `adapter/` | Telemetry normalization, validation, context enrichment |
| `fingerprint/` | Process fingerprint (machine + mold + part + recipe + material baseline) |
| `sentinel/` | EWMA, CUSUM, multivariate and trend drift detectors |
| `quality/` | Quality risk model, features, Quality Contract, operational checkpoints |
| `root_cause/` | Feature contribution ranking and evidence generator |
| `intervention/` | Candidate generation, optimizer, surrogate model, recommendation |
| `recovery/` | Recovery verifier |
| `containment/` | Scrap containment engine |
| `state_machine/` | 13-state transition engine |
| `economics/` | CoPQ calculator and cost-of-waiting evaluator |
| `counterfactual/` | Dual-mode replay engine |
| `evidence/` | Replica external benchmark and grounding report |
| `scenario/`, `validation/` | Scenario registry, runner, scorecard, validation suite |
| `llm/` | Deterministic human-channel parser (optional Laya model) |
| `storage/` | SQLite schema, database manager, repository |
| `api/` | FastAPI app, routers, schemas, dependency container |

## 6. Tech stack

- **Backend:** Python 3.12, FastAPI, Uvicorn, Pydantic 2
- **ML and math:** NumPy, scikit-learn (gradient boosting, probability calibration)
- **Storage:** SQLite (standard library `sqlite3`)
- **Frontend:** React 19, Vite 8, Recharts
- **Tests:** pytest, httpx (FastAPI TestClient), oxlint

## 7. AI architecture

Process Guardian is mostly deterministic. The only learned components are:

- **Quality risk model:** `GradientBoostingClassifier` wrapped in `CalibratedClassifierCV`. It is trained at startup on synthetic multi-regime factory data, so its probabilities are calibrated to the simulator, not to a real plant.
- **Intervention surrogate:** a forward model used to predict the effect of candidate actions. It is evaluated inside the optimizer.
- **Human-channel parser:** a deterministic matcher maps short operator replies (English, plus common Hindi, Tamil and Kannada phrasing) to a typed yes/no signal. It always runs first, and its result is final for confident matches.
- **Laya (optional):** a local multilingual model consulted **only** when the parser returns UNKNOWN. Its reads are capped below an exact rule match and tagged `source="laya"`. It can never override a rule verdict. If it is disabled or fails, the deterministic path decides alone.

Laya is off by default and is not required for the decision loop.

## 8. Database

- SQLite, 17 tables, created on startup by `DatabaseManager`.
- Tables cover cycles, events, fingerprints, drift events, recommendations, intervention candidates, containment windows, and the audit trail.
- The default container uses `:memory:`, so **state resets when the server restarts**. Pass a file path to `ServiceContainer(db_path=...)` to persist it.

## 9. API and integrations

Base URL: `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

| Group | Endpoints |
|---|---|
| System | `GET /api/health` |
| Ingestion | `POST /api/cycles`, `POST /api/events`, `POST /api/checkpoints` |
| Process | `GET /api/process/current`, `/fingerprint`, `/drift`, `/audit-trail` |
| Quality | `GET /api/quality/risk`, `/contract` |
| Interventions | `POST /api/interventions/simulate`, `POST /api/interventions/apply-demo`, `GET /api/interventions/recommendation`, `/history` |
| Recovery and containment | `GET /api/recovery/status`, `GET /api/containment/window`, `POST /api/containment/release` |
| Checkpoints | `GET /api/checkpoints/operational`, `POST /api/checkpoints/spray`, `/moisture`, `/human-channel`, `GET /api/containment/boundary` |
| Economics | `GET/POST /api/economics/parameters`, `GET /api/economics/copq`, `/decision-value` |
| Evidence | `GET /api/evidence/levels`, `/external-benchmark`, `/grounding-report` |
| Counterfactual | `GET /api/counterfactual/compare`, `POST /api/counterfactual/replay` |
| Scenarios | `GET /api/scenarios`, `/active`, `/validation-suite`, `/{id}`, `POST /api/scenarios/{id}/run`, `/select` |
| Demo | `POST /api/demo/reset`, `GET /api/demo/economic-impact`, `/api/demo/runs` |

**External integrations:** none at runtime. The "external benchmark" is a deterministic **replica** of the published SKZ / Fraunhofer IPA ProBayes injection-molding DoE (564 parts, 47 DoE points, PP and ABS). It is generated in code (`evidence/benchmark_dataset.py`). It is not the raw published data file. The module links to the original DOI for reference.

## 10. Local setup

**Requirements:** Python 3.12+, Node.js 20.19+ or 22.12+ with npm (Vite 8 requirement).

**Windows, one command:**

```bat
demo.cmd
```

This installs Python dependencies if they are missing, starts the engine on port 8000, installs UI dependencies on the first run, and starts the UI on port 5173. Then open http://localhost:5173.

**Manual setup:**

```bash
# Backend (from the repo root)
python -m pip install -e .
# optional: local Laya model (about 644 MB download on first use)
python -m pip install -e ".[laya]"
set PYTHONPATH=src            # PowerShell: $env:PYTHONPATH="src"
python -m uvicorn process_guardian.api.app:app --port 8000

# Frontend (in a second terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Check the engine: `curl http://localhost:8000/api/health` should return `"status": "HEALTHY"`.

## 11. Environment variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `PROCESS_GUARDIAN_LAYA_ENABLED` | Backend | `0` | Set to `1` to enable the optional Laya fallback for human-channel parsing. Requires the `laya` extra. |
| `VITE_API_URL` | Frontend (`frontend/.env.local`) | `http://localhost:8000` | Backend base URL. The Vite dev proxy also forwards `/api` to `127.0.0.1:8000`. |
| `PYTHONPATH` | Backend run | — | Must include `src` when running uvicorn from the repo root. |

No secrets are required.

## 12. Deployment

**Not deployed.** The project is a local, offline-capable demo. There is no Dockerfile, no hosted service, and no CI deployment. The engine runs on a single machine with SQLite, and the UI talks to it over localhost. For a hosted demo, the backend would need a persistent `db_path`, a configured CORS origin list (currently `*`), and an authentication layer (see limitations).

## 13. Testing

```bash
python -m pytest -q          # backend unit, API, and invariant tests (pythonpath=src is set in pyproject.toml)
python -m process_guardian.validation --output .planning/validation_report.json   # 10-scenario suite
cd frontend && npm run build && npm run lint                                    # UI build and lint
```

Last recorded run on this working tree:

- `pytest`: **233 passed, 2 skipped** (about 65 s)
- Validation suite: **10 / 10 passed** (`.planning/validation_report.json`)
- `npm run build`: passes
- `npm run lint`: 4 warnings, no errors

Safety invariants (`SAFE-01` to `SAFE-04`) are checked in `tests/test_safety_invariants.py`, with related guards in the operational-checkpoint and economics tests.

`scripts/verify.sh` is the harness gate. It is not part of the demo workflow, and the `scripts/verify.d/` project checks are currently empty.

## 14. Known limitations

- **No authentication or authorization.** CORS allows every origin, and endpoints such as `POST /api/containment/release` are open. This is a local demo, not a secured service.
- **Simulated data only.** The quality model and the drift scenarios run on the built-in simulator. There is no live plant feed, and no measured plant data is ingested.
- **The external benchmark is a replica**, not the raw SKZ / Fraunhofer dataset. Results are labeled Level 2 for that reason. They are not plant-trial evidence.
- **In-memory database by default.** Restarting the backend clears state unless a file path is configured.
- **The Laya model is not validated for typed decisions.** The deterministic parser carries the correctness claims. Laya is a fallback only.
- **Read-only by design.** There is no PLC write-back, so every adjustment is operator-applied.
- **Four frontend lint warnings** (unused variables and one hook dependency). No errors.

## 15. Future improvements

- Ingest real machine telemetry through a documented adapter, and validate the risk model against plant data.
- Make persistence the default, with a documented backup and reset path.
- Add authentication and a tighter CORS policy before any hosted deployment.
- Fine-tune the Laya checkpoint on shop-floor phrasing and measure it before enabling it on the decision path.
- Clean up the four frontend lint warnings.

---

*Hack4Purpose PS02. Process Guardian is a decision-support prototype. Its outputs are advisory and must be verified by operators and quality staff before any action on the line.*
