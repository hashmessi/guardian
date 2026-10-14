# Project State: Process Guardian

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-10-01 for Milestone v1.1)

**Core value:** The closed operational decision loop: detect drift → diagnose cause → evaluate cost of waiting vs cost of acting → recommend minimum-effective action → verify recovery via physical QC sample → contain affected suspect lot.
**Current focus:** Phase 13 — Automotive Judge Hardening & Final Rehearsal

## Current Milestone

**v1.1 — Dynamic Quality Reaction & Counterfactual Evidence Engine**
- Build window: 2026-10-01 to 2026-10-02 (Final Evaluation Prep)
- Goal: Prove to automotive industry evaluators that Process Guardian's dynamic quality reaction policy reduces modeled scrap exposure and suspect containment using real-world measured molding benchmarks, cost-of-waiting economics, and controlled counterfactual replay.
- Status: Phases 9, 10, 11, 12, & 13 Complete (156/156 tests green); Milestone v1.1 Complete & Ready for Final Demonstration

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
| 10 | Cost-of-Waiting Decision Economics | Parametric CoPQ model & Decision Value ($ExpectedLoss_{wait} - Cost_{act}$) | Complete (122/122 tests green, ECON-01..02) |
| 11 | Physical QC Verification & Operational Poka-Yoke | State machine `MANDATORY_QC_CHECKPOINT`, CTQ sampling, PS02 operational checkpoints | Complete (138/138 tests green, QCHK-01..02, CNTN-05) |
| 12 | Controlled Counterfactual Replay Canvas | Dual-mode replay (Guardian OFF vs ON), suspect lot collapse, side-by-side comparative UI | Complete (144/144 tests green, CRPL-01..02) |
| 13 | Scenario Engine & Operational Validation Suite | 10 data-driven scenarios, 7-pillar objective evidence scorecard, judge defensibility | Complete (156/156 tests green) |

## Accumulated Invariants & Safety Guarantees

- `SAFE-01`: Read-Only Machine Integration / Zero Automatic PLC Write-Back.
- `SAFE-02`: Strict 5-Layer Operating Envelope Compliance (Safety, Recipe, Fingerprint, Step, Direction).
- `SAFE-03`: Mandatory ABSTAIN Policy on Model Uncertainty (< 0.65 epistemic confidence).
- `SAFE-04 & DEMO-03`: Simulation Disclosures & Honest Epistemic Labels (Modeled values declared, zero claims of unverified plant trials).

## Phase 15 — Hostile-review remediation, QC removal, Laya repositioning, UI honesty pass (2026-10-14)

Five parallel hostile reviews over the whole uncommitted diff found that several
"Complete" claims were not true in the running system. Remediation, in order of
what mattered:

**Removed outright (was unenforced, so the claim was false):** the physical CTQ QC
subsystem — `quality/qc_checkpoint.py`, `/qc/submit`, `/qc/status`, the
`MANDATORY_QC_CHECKPOINT` state and its transitions, `QCCheckpointModal`, the
"QC passed" containment milestone (7 → 6) and the QC scorecard pillar (7 → 6).
`RECOVERY_CHECK → RELEASE` was always reachable, so the gate never gated; the demo
route then faked the state with a direct `context.current_state =` assignment that
bypassed the transition guard and left no audit record. Removing it also kills the
NaN-part-weight release bug. **`QC_REQUIRED` is a different state and is untouched**
— it is the S-FLIP human-channel hold, the differentiator.

**Human channel (the winning feature) — critical parser bug fixed.** `"haven't done
it"` parsed as YES at 0.9 and reset the spray interval counter: the negative list
only knew the literal bigram `"not done"`, so any other negation let the affirmative
token win. Now normalizes (`n't`, hyphens, whitespace), knows negated forms of its
own state-words, deferrals ("done tomorrow"), interrogatives ("shall I check later")
and affirmative idioms ("no problem, done"); governed negations ("never done") read
NO while genuinely conflicted text abstains. 20 regression tests.

**Laya repositioned from decorative to load-bearing-where-it-helps.** It used to
*replace* the deterministic parser whenever enabled. Now the rules always run first
and a confident verdict is final; Laya is consulted only when the rules return
UNKNOWN (an unseen, usually local-language phrasing) — their only real failure mode
and its only real strength. Model reads are capped at `LAYA_CONFIDENCE_CEILING`
(0.75, below an exact rule match) and labelled `source="laya"`. Zero added latency
on the common path; a wrong model read can at worst request an unneeded physical
check, never clear a gate the rules would have failed. Malformed model output now
degrades instead of raising. Scenario replay pins `enable_laya=False`.

**Scorecard made falsifiable; registry made truthful.** Diagnosis passed if the
expected signal appeared on any one of ~500 cycles (always true) → now must be the
modal cause of the incident window. Detection counted pre-onset false alarms as
successes and reported cycles-remaining as "lead time" → now requires detection at
or after onset and reports real latency. Abstain pillar had `or not
expected.allow_intervention`, making SAFE-03 unfailable → removed. Two
unconditional `True` pillars (operational-checkpoint intervention, checkpoint
recovery) now assert something. SCN-04/SCN-05 removed: the runner never read
`recipe_deviations` / spray overrides, so they were healthy runs reported as
checkpoint proofs. SCN-02/SCN-03 expectations corrected (symptom vs actuator;
moisture correctly abstains since it cannot be dialed out with machine parameters).
**9 scenarios, 9/9 genuinely passing.** Suite metrics no longer carry optimistic
defaults — `false_intervention_rate` and `mean_decision_latency` are computed.

**UI honesty + minimalism pass.** Removed every fabricated fallback that could be
read as live data: the `decision_value ≤ 500 → +₹2,198.92` floor (which inverted a
negative/MONITOR verdict), the checkpoint modal's full set of passing gate values
shown while loading/offline, `IncidentDiagnosis`'s invented 85% contributor and
always-"FIRED" detector table (it read `detectors.ewma.fired`; the backend sends
`ewma_breached`), `LiveProcess`'s placeholder readings under a "PRODUCTION SAFE"
banner, and `RecoveryPanel`'s 72.4/8.2/78/96.5 metrics defaulting to VERIFIED.
**The audit drawer was the worst case** — a hand-written ten-step narrative with
invented readings that credited an XGBoost classifier the project removed. There
was no endpoint serving the real trail, so one was added
(`GET /api/process/audit-trail`) and the drawer now renders actual recorded state
transitions. Also: hold-pressure drift no longer routes to an injection-pressure
correction (substring `"pressure"` matched both), `demo.cmd` no longer checks for
`xgboost`, keyboard access to the stage tabs restored, spray POST goes through the
API helper with `BASE_URL` + `res.ok`.

**Still open:** the legacy `src/process_guardian/validation/` package duplicates
`scenario/suite.py`, is wired to no route or screen, and carries its own hardcoded
metrics — safe to delete, not done. The `intervention/surrogate.py` post-action risk
is still a heuristic rather than the calibrated model, so any candidate beats A0 by
construction. §5 ceiling-breakers 1 and 3 (real anchor, PPM reframe) still need user
input.

---

## Phase 14 — scope_plan.md lock, noise cutdown, P0/P1 human-channel + Laya (P0+P1 COMPLETE & VERIFIED, session 2026-10-13)

`scope_plan.md` (repo root) is the locked source of truth for all remaining scope — read it first.

**Done, verified (gate passed at each step):**
- Noise cutdown (scope_plan Sec.4): live scenarios trimmed, dead components removed, unjustified ₹ card cut.
- P0 operational checkpoint gates: `src/process_guardian/llm/human_channel.py` (bounded multilingual yes/no parser, deterministic + optional real Laya), wired into `quality/operational_checkpoints.py`, `api/routes/qc.py` (`POST /api/checkpoints/human-channel`), and the frontend (`OperationalCheckpointsCard.jsx` trigger bar + `OperationalCheckpointsModal.jsx`).
- **Laya wired for real** (not a stub): `pip install laya`, real multilingual checkpoint downloaded and cached locally, real inference confirmed working via `RUN_LAYA_INTEGRATION_TESTS=1 python -m pytest tests/test_human_channel_laya_integration.py`. **Important finding, keep this documented**: measured zero-shot accuracy is poor — `noul` question type returned "False" on every one of 13 trivial inputs including the bare word "yes" (documented vendor bug, laya GitHub #156); the vendor's documented `choice` workaround (now what's implemented) only reached 5/8 (62.5%), still missing "yes" alone. Laya stays `enable_laya=False` by default — deterministic parser is what this product's correctness rests on. Full writeup in `human_channel.py`'s module docstring.

**P1 (human-channel fusion + S-FLIP scenario) — COMPLETE, hostile-reviewed, 203/203 tests green:**
- Persistence bug fixed (`lifecycle.py`): `ClosedLoopOrchestrator.active_human_channel_signal` now carries the triggering signal forward every cycle the QC_REQUIRED hold stays active, clearing on return to HEALTHY. Before this, root-cause attribution flickered to noise-driven sensor z-scores from cycle 151 onward.
- Dominance strengthened past the fix's first pass (fresh-context hostile review caught this): once a signal is *confirmed* (already drove the flip on a prior cycle, not the triggering cycle itself), `root_cause/analyzer.py` guarantees its score exceeds the max sensor score that cycle (`human_channel_confirmed` flag threaded through `quality/pipeline.py` → `lifecycle.py`). Verified: `human_channel` is the dominant signal for **151/151** hold cycles (was ~91% before this pass — rare multi-signal noise spikes across 14 signals × 150 cycles occasionally out-scored the uncapped base weight).
- Scorecard containment exception (`scenario/scorecard.py`): a material-checkpoint scenario with no machine-side action holds the suspect window open by design; gated specifically on `expected.action_class == "material_checkpoint"` (not the broader `not expected.allow_intervention`, which the review found would also silently swallow a real containment overflow on SCN-08's ABSTAIN path if a future change routed it to QC_REQUIRED).
- 5 stale-count tests fixed (registry 10→11 scenarios, hero set 2→3) + new regression test `test_scenario_flip_human_channel_persists_through_hold` (asserts `all()`, not a loose ratio).
- **Frontend gap found and fixed**: `FrontPage.jsx` never listed `SCN-FLIP-HUMAN-CHANNEL` as a selectable scenario card — the backend/registry had it marked `is_hero=True` but the live demo UI had no way to run it. This was the single most important missing piece (scope_plan: "if a feature does not contribute to this flip, it is cut" — it was unreachable, not cut deliberately). Added the card (reusing existing `cat-badge--material` / `status-material` CSS already present but unused) between S06 and S08, matching the frozen script's order. Confirmed present in the production build and reachable via `GET /api/scenarios?hero_only=true`.
- `demo.cmd` dependency check referenced `xgboost`, which scope_plan Sec.4 already locked as removed (`pyproject.toml` confirms: declared, never imported) — would have forced an unnecessary install or false failure on a clean demo machine. Fixed.
- Added the signal-acquisition-path one-liner (scope_plan Sec.5.2) to `AppShell.jsx`'s footer: Euromap 63/77 where it exists, ~$20 clamp thermocouple + hopper hygrometer retrofit where it doesn't.

**Remaining scope_plan.md §5 ceiling-breakers — NOT started, two need a decision/input only the user can give:**
1. **One real anchor** — a real citation, sensor trace, or captured Ragam Polymolds operator quote. **Blocked on the user**; cannot be fabricated (would violate the project's own honesty contract, scope_plan Sec.6).
2. Signal-acquisition path line — **done** (see above).
3. **Headline metric reframe to avoided customer PPM/escape** (vs scrap %) — a real feature change touching the economics/CoPQ hero card; a product-framing decision close to demo time, not started pending confirmation this is still wanted.
4. Frozen 4-minute script — **not written yet**; scope_plan Sec.8 already has the exact beat sheet (S06 → S-FLIP → S08 → close on anchor + honest limit), just needs transcribing into an operator-facing doc with the actual UI click-path.

---
*Last updated: 2026-10-13 — P0+P1 complete, hostile-reviewed, gate green (203/203 tests); §5 items 1 and 3 need user input/decision before proceeding, items 2 and 4 are the next small, unblocked tasks.*
