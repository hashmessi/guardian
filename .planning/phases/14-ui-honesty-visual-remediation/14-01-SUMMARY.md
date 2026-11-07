---
plan: 14-01
status: complete
date: 2026-11-07
---

# Plan 14-01 Summary: Honesty, Interaction & Copy Fixes

## What Was Built

All 7 tasks executed (executed while the executor session hit a network error before returning — work was verified on-disk and via the 6 atomic commits listed below):

| Task | What shipped | Commit |
|---|---|---|
| 1 | Scorecard badge derived from the pillars array (`✓ ${passedCount}/${pillars.length} PILLARS PASSED`); literal `7/7` eliminated | (within 2657cdc) |
| 2 | CandidateTable fabricated fallback rows removed; honest empty state `.candidate-empty`; count derived from `items.length`; highlight only on engine's actual selection (no `|| 'A1'`) | 3b3a339 |
| 3 | Escape-to-close on ScenarioScorecardModal / CoPQModal / OperationalCheckpointsModal; mold-spray failure renders a visible inline error (no silent console-only failure) | 2657cdc |
| 4 | IncidentDiagnosis null-guard on `currentRisk.toFixed` → renders `—` | cbbf1de |
| 5 | LiveProcess Quality Contract cycle-duration spec sourced from the live fingerprint envelope; honest placeholder when absent (hardcoded `26.5 ± 2.5s` removed) | b5293c0 |
| 6 | Copy sweep: raw `err.message` and SCN ids out of user alerts, "judges" → "an evaluator", header dropdown ordered by demo order (`SCENARIO_DEMO_ORDER`) | 75ea7b9 |
| 7 | 13-SUMMARY.md correction note (ScenarioTimelineBar / ValidationSuiteModal never built, absent per DEMO_FREEZE §2) | 9a599d8 |

## Key Files Modified
- frontend/src/components/CandidateTable.jsx/.css
- frontend/src/components/ScenarioScorecardModal.jsx, CoPQModal.jsx, OperationalCheckpointsModal.jsx
- frontend/src/screens/IncidentDiagnosis.jsx, LiveProcess.jsx, FrontPage.jsx
- frontend/src/components/AppShell.jsx
- .planning/phases/13-scenario-engine-operational-validation/13-SUMMARY.md

## Verification (narrow checks)
- Every task's acceptance-criteria greps pass (no `7/7`, no fabricated rows/count/`|| 'A1'`, no `26.5`, no `${err.message}` template, no "judges will ask", ESC present in all 3 modals, demo-order array present, correction section present).
- `npm run build` → ✓ built in 277ms (60 modules, exit 0)
- `npm run lint` → no errors in touched files

## Deviations
- Task 1 landed inside commit 2657cdc (single frontend-batch commit) instead of its own commit — content identical to the plan.
- Wave-1 executor session failed to return (opencode.ai DNS failure) after writing all work; completion verified via on-disk state + git log spot-checks.

## Self-Check: PASSED
