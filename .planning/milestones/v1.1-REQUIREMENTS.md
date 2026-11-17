# Requirements: Process Guardian

**Defined:** 2026-10-01  
**Milestone:** v1.1 — Dynamic Quality Reaction & Counterfactual Evidence Engine  
**Core Value:** The closed operational decision loop: detect drift → diagnose cause → evaluate cost of waiting vs cost of acting → recommend minimum-effective action → verify recovery via physical QC sample → contain affected suspect lot.

---

## v1.0 Validated Requirements (Completed)

All 61 requirements across Phases 1 through 8 are validated and frozen in `DEMO_FREEZE.md`:

- **Simulator Core (SIM-01..05)**: Cycle telemetry, deterministic baseline regimes, event injection API, causal physics dynamics, repeatable demo reset.
- **Data Adapter (DADP-01..03)**: Normalization, signal validation, context enrichment.
- **Process Fingerprint (FPRN-01..03)**: Multi-context envelope, dynamic baselines, storage.
- **Drift Sentinel (DRFT-01..04)**: EWMA/CUSUM/Hotelling $T^2$, structured drift payload, early warning lead-time, noise rejection.
- **Quality Risk (QRSK-01..04)**: Calibrated probabilities, 158-feature temporal pipeline, Quality Contract evaluation, operator risk modes.
- **Root Cause (ROOT-01..03)**: Ranked percentage attribution, empirical evidence chain, honest epistemic language.
- **Intervention (INTV-01..05)**: A0-A4 candidate evaluation, 5-layer envelope boundary checks, forward surrogate model, constrained cost-disruption optimization, candidate comparison.
- **Recommendation (RCMD-01..03)**: 7-field recommendation contract, 3 operator modes, mandatory ABSTAIN gate.
- **Recovery (RECV-01..05)**: Parameter shift confirmation, post-intervention telemetry recalculation, consecutive stability window, Quality Contract check, recovery status contract.
- **Containment (CNTN-01..04)**: Last-known-good cycle, suspect window quarantine, transition cycle tracking, disposition logic.
- **State Machine (STMC-01..02)**: Explicit 13-state FSM with legal transition validation and audit trail.
- **API & Storage (API-01..05, STOR-01..02)**: 17 SQLite schema tables, unified event bus, 14 operational FastAPI REST endpoints.
- **Industrial UI (UI-01..03, TRST-01..03)**: 3 primary screens, immutable audit trail, zero box-shadow industrial tokens.
- **Validation & Safety (DEMO-01..03, SAFE-01..04)**: 10-scenario validation suite (100% pass), deterministic reset, read-only invariants, synthetic disclosures.

---

## v1.1 Scoped Requirements: Dynamic Quality Reaction & Counterfactual Evidence

### Category 1: Real-World Molding Evidence & Grounding (EVID)

- [x] **EVID-01**: System integrates an external measured injection-molding benchmark dataset adapter (public SKZ/Fraunhofer 564-part PP/ABS production dataset) to benchmark real-world process-quality correlations.
- [x] **EVID-02**: System includes an automated grounding benchmark report comparing simulator drift dynamics against real industrial automotive study findings (non-linear moisture threshold 3% vs 22%, within-machine-limits visual scrap).
- [x] **EVID-03**: System enforces strict 4-level epistemic evidence labeling across all UI elements and API responses (Level 1: Challenge, Level 2: External Measured, Level 3: Software Invariant, Level 4: Controlled Counterfactual).

### Category 2: Decision Economics (ECON)

- [x] **ECON-01**: System implements a parametric Cost of Poor Quality (CoPQ) model calculating resin weight, machine hourly burden rate, energy kWh tariff, and secondary sorting costs.
- [x] **ECON-02**: System calculates real-time Cost of Waiting vs Cost of Acting ($ExpectedLoss_{wait} - Cost_{act} = DecisionValue$) with an explicit economic intervention threshold.

### Category 3: Quality Checkpoint & Operational Poka-Yoke (QCHK)

- [x] **QCHK-01**: State machine incorporates `MANDATORY_QC_CHECKPOINT` requiring recorded physical CTQ measurement (part weight / visual blemish pass-fail) post-parameter stabilization before `RELEASE`.
- [x] **QCHK-02**: System evaluates PS02 shop-floor operational checkpoints: recipe verification lock, resin moisture batch sign-off, and mold-release spray interval tracking.

### Category 4: Controlled Counterfactual Replay (CRPL)

- [x] **CRPL-01**: System provides a controlled counterfactual replay engine that runs identical drift event streams in dual mode: Guardian OFF (Status Quo) vs Guardian ON (Dynamic Quality Reaction).
- [x] **CRPL-02**: System renders a side-by-side counterfactual comparative evidence view displaying timeline divergence, suspect lot containment reduction (>75%), and avoided financial loss.

### Category 5: Physical Scrap Containment Boundary (CNTN)

- [x] **CNTN-05**: System renders a physical scrap containment boundary card explicitly displaying cycle milestones: Last Verified Good, Drift Start, Suspect Lot, Action Applied, Stabilized, QC Passed, and Lot Release.

---

## Out of Scope

| Excluded Item | Rationale |
|---|---|
| Hardware sensor rigs (DHT11, ESP32, breadboards) | Prototype is software decision layer; hardware is not needed for judge evidence and introduces physical failure modes. |
| Generic charts / dashboards | UI is an evidence canvas for decisions, not passive telemetry graphing. |
| LLMs / Chatbots | Deterministic epistemic contracts and math are required for automotive auditability. |
| Autonomous PLC write-back | Direct machine actuation violates safety protocols; operator-in-the-loop advisory is mandatory. |
| Cloud infrastructure / microservices | Local SQLite and deterministic in-memory replay guarantee 100% demo reliability. |

---

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| EVID-01 | Phase 9: Real-World Molding Evidence & Grounding | Complete |
| EVID-02 | Phase 9: Real-World Molding Evidence & Grounding | Complete |
| EVID-03 | Phase 9: Real-World Molding Evidence & Grounding | Complete |
| ECON-01 | Phase 10: Cost-of-Waiting Decision Economics | Complete |
| ECON-02 | Phase 10: Cost-of-Waiting Decision Economics | Complete |
| QCHK-01 | Phase 11: Physical QC Verification & Operational Poka-Yoke | Complete |
| QCHK-02 | Phase 11: Physical QC Verification & Operational Poka-Yoke | Complete |
| CNTN-05 | Phase 11: Physical QC Verification & Operational Poka-Yoke | Complete |
| CRPL-01 | Phase 12: Controlled Counterfactual Replay Canvas | Complete |
| CRPL-02 | Phase 12: Controlled Counterfactual Replay Canvas | Complete |

**Coverage:** 10 new scoped requirements mapped across 4 focused implementation phases (Phases 9–12) followed by Phase 13 (Automotive Judge Hardening & Final Rehearsal).
