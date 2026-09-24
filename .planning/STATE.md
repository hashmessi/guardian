# Project State: Process Guardian

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23)

**Core value:** Complete closed-loop intervention decision system — detect drift → diagnose → evaluate constrained actions → recommend minimum-cost intervention → verify recovery → contain affected production
**Current focus:** Phase 1 — Digital Factory + Data Foundation

## Current Milestone

**V1.0 — October 2 Prototype Demo**
- Total phases: 8
- Completed: 1
- Current: Phase 2 (Process Fingerprint + Drift Sentinel)
- Build window: 23 Sep - 2 Oct 2026

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Digital Factory + Data Foundation | Complete (13/13 tests green) |
| 2 | Process Fingerprint + Drift Sentinel | Ready to Plan |
| 3 | Quality Risk + Root-Cause Evidence | Not Started |
| 4 | Intervention Engine + Recommendation | Not Started |
| 5 | Recovery Verifier + Scrap Containment + State Machine | Not Started |
| 6 | API + Storage Integration | Not Started |
| 7 | Industrial UI + Audit Trail | Not Started |
| 8 | Validation + Hardening + Demo Freeze | Not Started |

## Key Decisions

- **Phase 1 Architecture**:
  - `01-01-PLAN.md` (Wave 1): Simulator Core & 9 Regimes (SIM-01, SIM-02, SIM-05)
  - `01-02-PLAN.md` (Wave 2): Causal Physics Dynamics & Event Injection API (SIM-03, SIM-04)
  - `01-03-PLAN.md` (Wave 2): Data Adapter, Normalization & Context Enrichment (DADP-01, DADP-02, DADP-03)
  - `01-04-PLAN.md` (Wave 3): Digital Factory Integration Harness, Scenario Runner & Verification (SIM-01..05, DADP-01..03)
  - Pure deterministic replay via NumPy seeded RNG (`default_rng(42)`)
  - Pydantic v2 schemas for tolerant data validation and quality flagging
  - Polymer pvT causal coupling (moisture -> viscosity -> pressure -> weight/shrinkage)

## Notes

- Build window is aggressive (10 days: 23 Sep - 2 Oct 2026)
- P0 features (Phases 1-5) must complete before P1 (Phases 6-8)
- Demo date: 2 Oct 2026, no feature additions after 1 Oct
- Software-first approach — no hardware dependencies
- Phase 1 plans generated with Nyquist validation contract (feedback latency < 5s)

---
*Last updated: 2026-09-24 after Phase 1 planning*
