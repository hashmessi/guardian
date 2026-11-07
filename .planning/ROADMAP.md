# Roadmap: Process Guardian

**Milestone:** v1.1 — Dynamic Quality Reaction & Counterfactual Evidence Engine  
**Status:** In Progress (Continuing from Milestone v1.0 Phases 1–8)  
**Phases:** 13 total (Phases 1–8 Complete; Phases 9–13 Scoped)  
**Requirements:** 71 total (61 Validated in v1.0, 10 Scoped in v1.1)

---

## Completed Milestone v1.0 (Phases 1–8)

- **Phase 1: Digital Factory + Data Foundation** (SIM-01..05, DADP-01..03) — 13/13 tests green
- **Phase 2: Process Fingerprint + Drift Sentinel** (FPRN-01..03, DRFT-01..04) — 21/21 tests green
- **Phase 3: Quality Risk + Root-Cause Evidence** (QRSK-01..04, ROOT-01..03) — 30/30 tests green
- **Phase 4: Intervention Engine + Recommendation** (INTV-01..05, RCMD-01..03) — 44/44 tests green
- **Phase 5: Recovery Verifier + Scrap Containment + State Machine** (RECV-01..05, CNTN-01..04, STMC-01..02) — 61/61 tests green
- **Phase 6: API + Storage Integration** (API-01..05, STOR-01..02) — 79/79 tests green
- **Phase 7: Industrial UI + Audit Trail** (UI-01..03, TRST-01..03) — Clean Vite build, 3 screens, E2E verified
- **Phase 8: Validation + Hardening + Demo Freeze** (DEMO-01..03, SAFE-01..04) — 97/97 tests green, 10/10 scenarios passed, DEMO_FREEZE.md enacted

---

## Milestone v1.1 Phases

### Phase 9: Real-World Molding Evidence & Grounding
**Goal:** Integrate external measured injection-molding production dataset adapter (public SKZ/Fraunhofer 564-part PP/ABS, 334 features, OK/NOK quality) and generate an automated grounding benchmark report comparing digital factory drift against published 2026 automotive study findings. Enforce strict 4-level epistemic evidence separation.

**Requirements:** EVID-01, EVID-02, EVID-03  
**UI hint:** yes (Evidence tags and Level 2 benchmark card)

**Success Criteria:**
1. Public measured injection-molding dataset parsed, normalized, and benchmarked against feature relationships.
2. Automated grounding benchmark verifies non-linear moisture threshold (3% vs 22% scrap) and within-limits defect detection.
3. Epistemic tags (Level 1 Challenge, Level 2 External Measured, Level 3 Software Invariant, Level 4 Controlled Counterfactual) assigned to all system indicators.

---

### Phase 10: Cost-of-Waiting Decision Economics
**Goal:** Build parametric Cost of Poor Quality (CoPQ) engine (resin weight, hourly machine burden, kWh tariff, secondary sorting) and the real-time Cost of Waiting vs Cost of Acting decision evaluator ($ExpectedLoss_{wait} - Cost_{act} = DecisionValue$).

**Requirements:** ECON-01, ECON-02  
**UI hint:** yes (Cost of Waiting vs Cost of Acting hero card)

**Success Criteria:**
1. Configurable CoPQ model replaces flat ₹450 with granular breakdown (resin weight, hourly rate, energy, sorting).
2. Real-time decision evaluator calculates Expected Loss vs Action Cost and outputs signed Decision Value.
3. Engine only advises intervention when Decision Value > 0, preventing premature line interruptions.
**Status:** Complete (122/122 tests green, ECON-01..02)

---

### Phase 11: Physical QC Verification & Operational Poka-Yoke
**Goal:** Integrate `MANDATORY_QC_CHECKPOINT` into the state machine requiring recorded CTQ measurement before release, integrate PS02 shop-floor operational checkpoints, and generate physical scrap containment boundary tracing.

**Requirements:** QCHK-01, QCHK-02, CNTN-05  
**UI hint:** yes (QC checkpoint modal/panel & physical containment boundary card)

**Success Criteria:**
1. State machine refuses release until physical QC CTQ measurement (part weight / visual blemish) passes.
2. PS02 operational checkpoints evaluate recipe lock, moisture sign-off, and mold-release interval.
3. Physical scrap containment boundary card tracks exact cycle boundaries (Last Good → Drift Start → Suspect Lot → Action Applied → Stabilized → QC Passed → Release).
**Status:** Complete (138/138 tests green, QCHK-01..02, CNTN-05)

---

### Phase 12: Controlled Counterfactual Replay Canvas
**Goal:** Build the dual-mode counterfactual replay engine running identical event streams in Guardian OFF vs Guardian ON, and present side-by-side comparative evidence showing suspect lot collapse (>75%) and net avoided loss.

**Requirements:** CRPL-01, CRPL-02  
**UI hint:** yes (Side-by-side counterfactual replay view)

**Success Criteria:**
1. Dual-stream deterministic replay executes identical drift event with Guardian OFF vs Guardian ON.
2. Side-by-side comparative view shows divergence: Guardian OFF accumulates 80+ scrap cycles; Guardian ON recovers and releases in ~10 cycles.
3. Net economic benefit and avoided suspect lot containment explicitly rendered with honest simulation disclosures.
**Status:** Complete (144/144 tests green, CRPL-01..02)

---

### Phase 13: Scenario Engine & Operational Validation Suite
**Goal:** Upgrade Process Guardian into a deterministic, scenario-driven industrial validation engine running 10 distinct automotive operating scenarios through the unified decision pipeline with counterfactual proof and the 7-pillar objective evidence scorecard.

**Success Criteria:**
1. Zero regressions across test suite: 156/156 tests green.
2. 10 data-driven scenarios covering thermal, pressure, moisture, recipe, mold spray, compound, normal variation, abstention, failed intervention, and release.
3. 7-pillar objective evidence scorecard and interactive validation suite modal in the UI.
4. Demo playbook directly answers judge questions ("Why intervene?", "Where is real proof?", "How is recovery verified?").
**Status:** Complete (156/156 tests green)

---

### Phase 14: UI Honesty & Visual System Remediation
**Goal:** Close every finding from the Phase 13 retroactive 6-pillar UI audit (13-UI-REVIEW.md, overall 13/24) to reach a clean 24/24: kill all fabricated-fallback and self-contradiction defects, unify the color/typography/spacing systems onto tokens.css, and remove dead style systems.

**Requirements:** UI-FIX-01..08 (derived from audit findings):
- UI-FIX-01 Scorecard pillar-count honesty (derive badge from array; 6 pillars everywhere)
- UI-FIX-02 CandidateTable honest empty state (no fabricated rows, real count, correct highlight)
- UI-FIX-03 Interaction integrity (ESC/focus handling on modals, visible failure feedback on spray record, null-safe risk rendering)
- UI-FIX-04 Copy discipline (no internal IDs/judge vocabulary/raw err.message in user-facing text; ordered dropdown)
- UI-FIX-05 Color token unification (58 off-token hex → tokens.css; one healthy-green regime; no box-shadows per token rule; dead styles removed)
- UI-FIX-06 Typography scale (type-size scale in tokens; sizes/weights map to tokens)
- UI-FIX-07 Spacing scale adoption (structural px → --sp steps)
- UI-FIX-08 Planning-record correction (13-SUMMARY.md false components claim noted per DEMO_FREEZE)

**Success Criteria:**
1. Zero fabricated values reachable on any screen (grep-verified: no hardcoded candidate rows/count, no 7/7 literal, no hardcoded envelope where live value exists).
2. No off-token hex color values in frontend CSS that duplicate token semantics; no box-shadow declarations remaining except none.
3. Typography uses only declared token sizes/weights; spacing uses --sp steps for all structural values (>10px).
4. `npm run build` + lint green; audit re-score shows no pillar below 4.

**Status:** Complete (2026-11-07). Both plans executed and verified: 14-01 (UAT 12/12, see 14-UAT.md) and 14-02 token sweep (`577a71c`, residual display-tier/spacing completion `d26c27c`). All 24 audit findings closed: derived scorecard badge, honest candidate table, ESC+failure feedback, copy discipline via `scenarioDisplayLabel`, single lagoon color regime, zero box-shadows, zero dead selectors, token-referenced typography and structural spacing. Success greps: 0 forbidden hexes/literals/selectors; `npm run build` ✓; `npm run lint` exit 0.

---

## Coverage Summary

| Phase | Requirements | Count | Status |
|---|---|---|---|
| Phases 1–8 | SIM-01..05, DADP-01..03, FPRN-01..03, DRFT-01..04, QRSK-01..04, ROOT-01..03, INTV-01..05, RCMD-01..03, RECV-01..05, CNTN-01..04, STMC-01..02, API-01..05, STOR-01..02, UI-01..03, TRST-01..03, DEMO-01..03, SAFE-01..04 | 61 | Complete ✓ |
| Phase 9 | EVID-01, EVID-02, EVID-03 | 3 | Complete ✓ |
| Phase 10 | ECON-01, ECON-02 | 2 | Complete ✓ |
| Phase 11 | QCHK-01, QCHK-02, CNTN-05 | 3 | Complete ✓ |
| Phase 12 | CRPL-01, CRPL-02 | 2 | Complete ✓ |
| Phase 13 | Final Hardening & 10-Scenario Validation Suite | — | Complete ✓ |
| Phase 14 | UI Honesty & Visual System Remediation | UI-FIX-01..08 | Complete |
| **Total** | | **71** | **100% Validated** ✓ |

---
*Roadmap updated: 2026-10-02 after Phase 13 completion*
