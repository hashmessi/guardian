# Phase 14: UI Honesty & Visual System Remediation - Context

**Gathered:** 2026-11-06
**Status:** Ready for planning
**Source:** `13-UI-REVIEW.md` (retroactive 6-pillar audit of the full implemented UI) + explicit user decision: "apply all fixes, target 24/24"

<domain>
## Phase Boundary

Frontend only (`frontend/src/**`). The Phase 13 engine/codebase stays untouched — with one exception: a correction note to `13-SUMMARY.md` (docs). Backend scenario registry titles/internals remain unchanged; the display boundary already exists (`frontend/src/scenarioDisplay.js`).

**Locked demo decisions that constrain every fix (DEMO_FREEZE):**
- 3 hero scenarios shown, numbered 1/2/3 in demo order; everything else "cited, not shown".
- No fabricated values on screen — missing data means honest empty/unknown states.
- Parchment/wine/violet/lilac/lagoon token palette, strictly NO box-shadows, no dark theme.

</domain>

<decisions>
## Implementation Decisions

### Honesty (from audit BLOCKERs — must ship)
1. `ScenarioScorecardModal.jsx`: derive the pass badge from the actual pillars array — `{passedCount}/{pillars.length} PILLARS PASSED`; the body already shows 6 pillars. Never render a hardcoded total.
2. `CandidateTable.jsx`: remove the hardcoded 4-row fallback dataset entirely; when no candidates render the honest empty state "Awaiting engine candidate evaluation…"; derive the count label from `items.length`; never highlight a candidate as recommended unless it is the engine's selected `action_id` (no `|| 'A1'`).

### Interaction integrity (from audit WARNINGs)
3. All three modals (`ScenarioScorecardModal`, `CoPQModal`, `OperationalCheckpointsModal`) close on Escape (follow the existing `ContainmentTag.jsx:20` keydown pattern) and keep the ✕ button working.
4. `OperationalCheckpointsModal.jsx`: a failed `recordMoldSpray` call must show visible user feedback (inline error line), not only `console.error`.
5. `IncidentDiagnosis.jsx:140`: guard `currentRisk` against `null` before `.toFixed(1)` (render "—" when absent).
6. `LiveProcess.jsx` Quality Contract row "26.5 ± 2.5s" must come from the live fingerprint spec, not a hardcoded literal.

### Copy discipline (from audit pillar 1)
7. No internal scenario IDs (`SCN-*`), no audit-vocabulary ("judges"), no raw `err.message` in user-facing text. Error alerts state what failed and what to do, in operator language. The header dropdown lists scenarios in demo order 1 → 2 → 3.

### Color system (pillar 3)
8. Every CSS color used maps to a token in `styles/tokens.css`. One healthy-green regime: `--color-lagoon` family; emerald/Tailwind-green duplicates collapse to lagoon. Off-token near-whites (`#fbfbf9`, `#faf9f6`, `#fbfaf7`, `#f7f6f2`, `#f9f8f5`) collapse to `--color-parchment` or `--color-white` per semantic.
9. Zero `box-shadow` declarations in any stylesheet (incl. modals — the dimmed backdrop provides separation).
10. Dead style systems are deleted: `.app-shell--dark` slate theme (TabStrip.css), `.scorecard-trigger-btn` / `.validation-suite-trigger-btn` glow CSS (AppShell.css), any unused stage-badge slate fill. The visible UI palette is exactly the 9 token colors.

### Typography (pillar 4)
11. Declare a type-size scale in tokens.css and use only those steps: `--fs-2xl 20px` (hero), `--fs-xl 16px` (card titles), `--fs-lg 13px` (body), `--fs-md 11px` (labels/meta), `--fs-sm 10px` (badges/tags). All `font-size` declarations use one of these tokens; 10.5/11.5/12.5-style micro variants collapse to the nearest step.
12. All `font-weight` literals use the semantic tokens (`--fw-normal/editorial/label/data/bold`). No new numeric literals.

### Spacing (pillar 5)
13. Structural spacing values (>10px: paddings, gaps, margins, radii) snap to the declared `--sp-*` steps. Values ≤10px (chip micro-padding, hairline details) may stay literal but map where a step exists.

### Planning record
14. `13-SUMMARY.md`: append a correction note — `ScenarioTimelineBar` and `ValidationSuiteModal` were NOT built; their absence intentionally restores DEMO_FREEZE §2 ("cited, not shown"); the dead trigger CSS is removed in this phase.

### Explicitly not changing
- Backend registry titles, scorecard engine, scenario ids, seeds (except the already-corrected cycles display), demo scripts.
- Screenshots/composition that the audit scored well — visual character (editorial parchment look) is preserved; scale adoption must not redesign, only normalize stray values.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit source (the work list)
- `.planning/phases/13-scenario-engine-operational-validation/13-UI-REVIEW.md` — every finding, `file:line`

### Locked decisions & system rules
- `.planning/DEMO_FREEZE.md` — demo scope, honesty contract, "cited, not shown"
- `frontend/src/styles/tokens.css` — the ONLY source of colors/weights/spacing; token rules are binding

### Prior work this phase extends
- `frontend/src/scenarioDisplay.js` — display-label boundary created in the pre-phase fix
- `frontend/src/hooks/useApi.js` — API layer; error rendering contracts

---
*Phase: 14-ui-honesty-visual-remediation*
*Context gathered: 2026-11-06 from 13-UI-REVIEW.md*
