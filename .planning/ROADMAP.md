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

---

### Phase 11: Physical QC Verification & Operational Poka-Yoke
**Goal:** Integrate `MANDATORY_QC_CHECKPOINT` into the state machine requiring recorded CTQ measurement before release, integrate PS02 shop-floor operational checkpoints, and generate physical scrap containment boundary tracing.

**Requirements:** QCHK-01, QCHK-02, CNTN-05  
**UI hint:** yes (QC checkpoint modal/panel & physical containment boundary card)

**Success Criteria:**
1. State machine refuses release until physical QC CTQ measurement (part weight / visual blemish) passes.
2. PS02 operational checkpoints evaluate recipe lock, moisture sign-off, and mold-release interval.
3. Physical scrap containment boundary card tracks exact cycle boundaries (Last Good → Drift Start → Suspect Lot → Action Applied → Stabilized → QC Passed → Release).

---

### Phase 12: Controlled Counterfactual Replay Canvas
**Goal:** Build the dual-mode counterfactual replay engine running identical event streams in Guardian OFF vs Guardian ON, and present side-by-side comparative evidence showing suspect lot collapse (>75%) and net avoided loss.

**Requirements:** CRPL-01, CRPL-02  
**UI hint:** yes (Side-by-side counterfactual replay view)

**Success Criteria:**
1. Dual-stream deterministic replay executes identical drift event with Guardian OFF vs Guardian ON.
2. Side-by-side comparative view shows divergence: Guardian OFF accumulates 80+ scrap cycles; Guardian ON recovers and releases in ~10 cycles.
3. Net economic benefit and avoided suspect lot containment explicitly rendered with honest simulation disclosures.

---

### Phase 13: Automotive Judge Hardening & Final Rehearsal
**Goal:** Harden against automotive quality director attacks, run automated regression tests (100% green), update demo freeze manifesto for v1.1, and verify complete judge walkthrough script.

**Success Criteria:**
1. Zero regressions across existing 97 tests + new v1.1 test suite.
2. Demo script directly answers judge questions ("Why intervene?", "Where is real proof?", "How is recovery verified?").
3. Final freeze certification documented and ready for Oct 2 competition day.

---

## Coverage Summary

| Phase | Requirements | Count | Status |
|---|---|---|---|
| Phases 1–8 | SIM-01..05, DADP-01..03, FPRN-01..03, DRFT-01..04, QRSK-01..04, ROOT-01..03, INTV-01..05, RCMD-01..03, RECV-01..05, CNTN-01..04, STMC-01..02, API-01..05, STOR-01..02, UI-01..03, TRST-01..03, DEMO-01..03, SAFE-01..04 | 61 | Complete ✓ |
| Phase 9 | EVID-01, EVID-02, EVID-03 | 3 | Scoped |
| Phase 10 | ECON-01, ECON-02 | 2 | Scoped |
| Phase 11 | QCHK-01, QCHK-02, CNTN-05 | 3 | Scoped |
| Phase 12 | CRPL-01, CRPL-02 | 2 | Scoped |
| Phase 13 | Final Hardening & Freeze | — | Scoped |
| **Total** | | **71** | **100% Mapped** ✓ |

---
*Roadmap updated: 2026-10-01 after initializing Milestone v1.1*
