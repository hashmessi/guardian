# Project State: Process Guardian

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-10-01 for Milestone v1.1)

**Core value:** The closed operational decision loop: detect drift → diagnose cause → evaluate cost of waiting vs cost of acting → recommend minimum-effective action → verify recovery via physical QC sample → contain affected suspect lot.
**Current focus:** Phase 10 — Cost-of-Waiting Decision Economics (ECON-01, ECON-02)

## Current Milestone

**v1.1 — Dynamic Quality Reaction & Counterfactual Evidence Engine**
- Build window: 2026-10-01 to 2026-10-02 (Final Evaluation Prep)
- Goal: Prove to automotive industry evaluators that Process Guardian's dynamic quality reaction policy reduces modeled scrap exposure and suspect containment using real-world measured molding benchmarks, cost-of-waiting economics, and controlled counterfactual replay.
- Status: Phase 9 Complete; Executing Phase 10

## Milestone v1.0 Shipped Summary

Completed 2026-10-01 (Demo Freeze Enacted, 97/97 tests green, 10/10 scenarios passed):
- Phase 1: Digital Factory + Data Foundation (SIM-01..05, DADP-01..03)
- Phase 2: Process Fingerprint + Drift Sentinel (FPRN-01..03, DRFT-01..04)
- Phase 3: Quality Risk + Root-Cause Evidence (QRSK-01..04, ROOT-01..03)
- Phase 4: Intervention Engine + Recommendation (INTV-01..05, RCMD-01..03)
- Phase 5: Recovery Verifier + Scrap Containment + State Machine (STMC-01..02, RECV-01..05, CNTN-01..04)
- Phase 6: API + Storage Integration (STOR-01..02, API-01..05)
- Phase 7: Industrial UI + Audit Trail (UI-01..03, TRST-01..03)
- Phase 8: Validation + Hardening + Demo Freeze (DEMO-01..03, SAFE-01..04)

## Milestone v1.1 Phase Plan

| Phase | Name | Focus | Status |
|---|---|---|---|
| 9 | Real-World Molding Evidence & Grounding | External dataset benchmark (SKZ/Fraunhofer 564-part PP/ABS, 2026 automotive study) & epistemic levels | Complete (108/108 tests green, EVID-01..03) |
| 10 | Cost-of-Waiting Decision Economics | Parametric CoPQ model & Decision Value ($ExpectedLoss_{wait} - Cost_{act}$) | Up Next |
| 11 | Physical QC Verification & Operational Poka-Yoke | State machine `MANDATORY_QC_CHECKPOINT`, CTQ sampling, PS02 operational checkpoints | Scoped |
| 12 | Controlled Counterfactual Replay Canvas | Dual-mode replay (Guardian OFF vs ON), suspect lot collapse, side-by-side comparative UI | Scoped |
| 13 | Automotive Judge Hardening & Final Rehearsal | Evaluation script, pitch defensibility, demo freeze certification | Scoped |

## Accumulated Invariants & Safety Guarantees

- `SAFE-01`: Read-Only Machine Integration / Zero Automatic PLC Write-Back.
- `SAFE-02`: Strict 5-Layer Operating Envelope Compliance (Safety, Recipe, Fingerprint, Step, Direction).
- `SAFE-03`: Mandatory ABSTAIN Policy on Model Uncertainty (< 0.65 epistemic confidence).
- `SAFE-04 & DEMO-03`: Simulation Disclosures & Honest Epistemic Labels (Modeled values declared, zero claims of unverified plant trials).

---
*Last updated: 2026-10-01 after Milestone v1.1 initialization*
