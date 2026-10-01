# Phase 9: Real-World Molding Evidence & Grounding — Context

## Objective
Ground Process Guardian in real-world empirical injection-molding production evidence. Ingest external measured datasets (the public SKZ/Fraunhofer 564-part PP/ABS injection molding study with 334 features and OK/NOK classifications), validate process-quality relationships against published 2026 industrial automotive cases (within-limits defects and non-linear moisture scrap thresholds), and establish an explicit 4-level epistemic evidence architecture across API and UI.

## Target Requirements
- **EVID-01**: External measured injection-molding benchmark dataset adapter (public SKZ/Fraunhofer 564-part PP/ABS production dataset) mapping real machine/quality features.
- **EVID-02**: Grounding benchmark report comparing simulator drift dynamics against real industrial automotive study findings (non-linear moisture threshold 3% vs 22%, within-machine-limits visual scrap).
- **EVID-03**: Strict 4-level epistemic evidence labeling across all UI elements and API responses (Level 1: Challenge, Level 2: External Measured, Level 3: Software Invariant, Level 4: Controlled Counterfactual).

## Core Architectural Decisions

1. **Empirical Dataset Grounding (EVID-01)**:
   - Source: Public SKZ / Fraunhofer injection-molding benchmark production dataset (564 parts molded across Polypropylene [PP] and Acrylonitrile Butadiene Styrene [ABS]).
   - Features: Melt temperature, mold temperature, injection velocity, holding pressure, switchover pressure, cushion, cycle time, part weight, and OK/NOK quality label.
   - Purpose: Prove that Process Guardian's temporal and multivariate drift logic reflects empirical injection molding physics, not synthetic hand-waving.

2. **Grounding Benchmark Engine & Report (EVID-02)**:
   - Formally reproduce two critical shop-floor phenomena documented in 2026 automotive component studies:
     1. **The In-Limits Defect Failure of Conventional SPC**: Conventional machine envelope limits accept 100% of cycles (254/254), yet downstream visual camera inspection uncovers significant scrap due to switchover and cavity pressure variance. Process Guardian's Drift Sentinel catches this drift with > 8-cycle lead time.
     2. **Non-Linear Moisture Scrap Threshold**: Scrap rates remain low (~3%) in the optimal 0.08%–0.15% moisture window, but spike non-linearly to 22%–26% when moisture exceeds 0.22%.
   - Automated CLI report generator: `python -m process_guardian.evidence.grounding_report` outputting structured benchmark JSON.

3. **4-Level Epistemic Evidence Framework (EVID-03)**:
   - **Level 1 — Challenge Evidence**: PS02's documented industry baseline (6–7% rejection, target $\le$ 2%, barrel thermal/pressure/moisture sensitivity).
   - **Level 2 — External Industrial Evidence**: Real measured injection molding datasets (SKZ/Fraunhofer 564-part benchmark & 2026 published automotive supplier validation).
   - **Level 3 — Software System Invariants**: 97/97 tests green, 10/10 operational scenarios, 4 strict safety invariants (zero PLC write-back, 5-layer envelope, mandatory ABSTAIN).
   - **Level 4 — Controlled Counterfactual Intervention**: Deterministic dual-stream replay demonstrating suspect lot containment reduction.
   - REST API endpoints:
     - `GET /api/evidence/levels`: The 4-level taxonomy and verified claims.
     - `GET /api/evidence/external-benchmark`: Public dataset summary, correlation matrix, and OK/NOK separation metrics.
     - `GET /api/evidence/grounding-report`: In-limits failure audit and moisture non-linearity validation.

4. **UI Integration**:
   - Header badge / trigger for an **Evidence & Grounding Modal** (`EvidenceModal.jsx`) allowing automotive judges to inspect external datasets and the 4-level evidence chain directly.
   - High-trust epistemic badges on key metrics across all screens.

## Plans Breakdown
- **09-01-PLAN.md**: External Measured Dataset Adapter & Feature Sensitivity Engine (`EVID-01`)
- **09-02-PLAN.md**: Automated Grounding Benchmark Report & Conventional SPC Failure Proof (`EVID-02`)
- **09-03-PLAN.md**: 4-Level Epistemic Evidence API, UI Evidence Modal & End-to-End Verification (`EVID-03`)
