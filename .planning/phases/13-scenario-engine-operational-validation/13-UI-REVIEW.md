# Phase 13 — UI Review

**Audited:** 2026-11-06 (full implemented UI audit — headers, pages, cards, modals; not just this phase's delta)
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md exists) + DEMO_FREEZE.md locked demo decisions + design tokens in `frontend/src/styles/tokens.css`
**Screenshots:** Captured. Live captures at 1440×900 (Chrome headless, dev server :5173): `.planning/ui-reviews/desktop-front.png`, `front-scrolled.png`, `screen-detect.png`, `screen-diagnose.png`, `screen-act.png`, `screen-act-2.png`, `modal-scorecard.png`. `tab-detect.png` and `13-20261106-222802/` are empty capture attempts (browser binary missing; the successful runs used `--channel chrome`). The orchestrator-referenced screenshot `frontend-front-page-1.png` no longer exists at the given path — all visual evidence here is freshly captured.
**Registry audit:** No `components.json` anywhere in the repo — shadcn not initialized, registry audit skinned/no-op (no third-party UI registry blocks).

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Renumber leak: header dropdown + scorecard modal render raw backend titles "Scenario 06/08 — ..." and "The One Demo That Wins", contradicting the renumbered FrontPage; internal IDs leak into status/error text |
| 2. Visuals | 3/4 | Strong focal hierarchy on all three stages, but the flagship evidence modal self-contradicts ("7/7" badge vs "all 6 pillars" body) and promised timeline bar is absent |
| 3. Color | 2/4 | 58 distinct off-token hex values; three competing "healthy green" systems fighting `--color-lagoon`; dead blue/indigo glow styles violate the token file's explicit no-shadow rule |
| 4. Typography | 2/4 | 25 distinct font sizes / 13 weight declarations vs a declared 5-weight system; six interleaved micro sizes between 10–12.5px |
| 5. Spacing | 2/4 | 80 `--sp-*` token usages vs 186 off-scale pixel literals; structural steps (14/18/22/28px) ignore the declared 4px scale |
| 6. Experience Design | 2/4 | Best-in-class offline refusal + honest empty states, undercut by a fabricated candidate-fallback table, a hardcoded "4 CANDIDATES EVALUATED", and an `|| 'A1'` highlight bug on the money screen |

**Overall: 13/24**

---

## Top 3 Priority Fixes

1. **Exclude the renumber leak — map backend titles to display numbers at the render boundary.**
   `AppShell.jsx:152–154` renders `s.title` (raw) and `ScenarioScorecardModal.jsx:23` renders `scorecard.scenario_title` (raw). Verified live: the persistent header dropdown on EVERY screen reads "Scenario 06 — Compound Multi-Signal Drift", "Scenario 08 — Low Confidence (Mandatory Abstain Safety Gate)", "Scenario FLIP — The One Demo That Wins (Human-Channel Material Risk)" — in the order 06→08→FLIP, contradicting FrontPage's locked "Scenario 1 / 2 / 3" numbering, and leaking internal sales copy ("The One Demo That Wins") into a control bar. Impact: the exact surviving inconsistency the renumber was supposed to remove; a judge reading the dropdown sees "Scenario 06" first. Fix: a `SCENARIO_DISPLAY_LABELS` map keyed by `scenario_id` (`SCN-06-COMPOUND → 'Scenario 1 — Compound Multi-Signal Drift'`, `SCN-FLIP-HUMAN-CHANNEL → 'Scenario 2 — Human-Channel Material Risk'`, `SCN-08-LOW-CONF-ABSTAIN → 'Scenario 3 — Out-of-Distribution Drift'`) used for `option` text and the scorecard `h2`. Also kill the raw-ID status messages (`AppShell.jsx:89` "Loading SCN-06-COMPOUND…", `:92` "✓ SCN-06-COMPOUND active") and raw `err.message` in user-visible alerts (`FrontPage.jsx:101`, `:249`).
2. **Fix the pillar-count contradiction in the scorecard modal.**
   `ScenarioScorecardModal.jsx:26–28` hardcodes `✓ 7/7 PILLARS PASSED`, but the `pillars` array has 6 entries (`:7–14`) and the engine evaluates 6 (`src/process_guardian/scenario/scorecard.py:411–425` — summary literally says "Successfully validated all 6 pillars"). Verified live in `modal-scorecard.png`: both contradictory counts visible on one screen. On a product whose one claim is "proves every number it shows", this is the single most credibility-damaging defect. Fix short-term: derive the badge from the array — `{pillars.filter(p => p.data?.passed).length}/{pillars.length} PILLARS PASSED`. Fix long-term: add the 7th (Physical QC Release Gate) pillar to the scorecard engine per 13-SUMMARY/DEMO_FREEZE §2, or restate the scorecard as 6 pillars everywhere (13-SUMMARY.md currently claims 7).
3. **Remove the fabricated-fallback population of the candidates table.**
   `CandidateTable.jsx:11–60` substitutes a hardcoded 4-row candidate set (predicted risks 0.08/0.18/0.12/0.05) "if no candidates from API", indistinguishable from engine output; `:73` hardcodes "4 CANDIDATES EVALUATED" regardless of actual count; `:98` highlights `cand.action_id === 'A1'` as recommended even when the engine selected another candidate (the exact silent-A1 bug `InterventionRecovery.jsx:32–37` documents fixing). Impact: on the flagship ACT screen, wrong risk numbers and a wrong MIN-COST highlight can render under data failure — violating the project's own no-fabrication stance that AppShell's offline refusal (`AppShell.jsx:59–64`) fights for at the shell level. Fix: render an honest "Awaiting engine candidate evaluation" empty state instead of surrogate rows, derive the count from `items.length`, and drop the `|| 'A1'` clause.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)

**Strengths (verified in code and on screen):** Copy is disciplined elsewhere — "Advisory recommendation · Non-invasive supervisory guidance · Operator enters setpoint on machine PLC" (RecommendationCard.jsx:89), the honest footnote "Not a guaranteed causal proof" (IncidentDiagnosis.jsx:294), "Modeled, not a plant trial" (InterventionRecovery.jsx:114). Empty-state copy is excellent: "No active drift to diagnose — Run a scenario from the front page…" (IncidentDiagnosis.jsx:68–72), "Gate status unavailable… Do not treat this as clearance" (OperationalCheckpointsModal.jsx:82–85). No generic OK/Cancel/Submit strings anywhere (grep confirmed; the only "Cancel"-family hits are onClose handlers, not labels).

**BLOCKER — surviving renumber inconsistency (the dashboard the user asked to verify):**
- `AppShell.jsx:153` renders `{s.title}` from `/api/scenarios?hero_only=true`. Verified live (playwright-read dropdown options): `"Scenario 06 — Compound Multi-Signal Drift"`, `"Scenario 08 — Low Confidence (Mandatory Abstain Safety Gate)"`, `"Scenario FLIP — The One Demo That Wins (Human-Channel Material Risk)"`. Backend registry titles intentionally unchanged (`src/process_guardian/scenario/registry.py:256,401,612`), but the UI is not shielding them. The FrontPage userInfo-facing renumber (FrontPage.jsx:191 "Scenario {num} — {title}" with lilac number, S1/S2/S3 badges, FLAGSHIP "SCENARIO 1" — confirmed in front-scrolled.png) is correct; the header dropdown is the leak.
- Dropdown ordering contradicts the locked numbering: 06 → 08 → FLIP, while FrontPage orders 1 → 2 → 3.
- `ScenarioScorecardModal.jsx:23` renders `scorecard.scenario_title` = backend title → modal title shows "Scenario 06 — Compound Multi-Signal Drift" (confirmed in modal-scorecard.png).
- Seed-number mismatch: FrontPage.jsx:73 shows "350 CYCLES · SEED #708" for Scenario 3, but the engine runs **400** total cycles for `SCN-08-LOW-CONF-ABSTAIN` (verified via `GET /api/scenarios/SCN-08-LOW-CONF-ABSTAIN` → `total_cycles: 400`). Scenarios 1 and 2 match (500/506, 300/913).

**WARNING — internal IDs rendered to users:**
- `AppShell.jsx:89` `Loading ${newScnId}...` and `:92` `✓ ${newScnId} active` → user sees "Loading SCN-08-LOW-CONF-ABSTAIN..." on every scenario switch.
- `FrontPage.jsx:101` `Could not start ${scenarioId}. The engine is not answering on its API port. (${err.message})` — internal code + raw error text in a user-facing alert.
- `FrontPage.jsx:249` `Could not load the scorecard. (${err.message})`.

**WARNING — audience leak:** FrontPage.jsx:169 "Optional replays for the material-risk and safety-gate questions **judges** will ask" — competition-internal vocabulary on a product UI targeting shop-floor molders.

**WARNING — offline fallback dropdown drift:** AppShell.jsx:159–163 claims to be "kept in sync with the locked hero set" but lists only 2 of the 3 locked scenarios (Scenario 2 / `SCN-FLIP-HUMAN-CHANNEL` missing), and its labels ("Scenario 1", "Scenario 3") don't match live API titles — three states of the same control with three different label sets.

### Pillar 2: Visuals (3/4)

**Strengths (verified in screenshots):** Clear focal point per screen — DETECT: full-width state banner + 4 gauge cards (screen-detect.png); ACT & VERIFY: dominant recommendation callout with border-accent,CONFIRM OPERATOR ACTION as the single dominant CTA (screen-act.png); front page: hero title + flagship card. Journey stepper (TabStrip) uses size/color/weight separation correctly with live state badges (screen-act.png: "DRIFT ACTIVE", "RISK HIGH" pills). Icon-only close buttons all carry `aria-label` (CoPQModal.jsx:97, ScenarioScorecardModal.jsx:29, OperationalCheckpointsModal.jsx:80,116). Token file's no-decorative-depth rule is respected on cards (all card CSS `box-shadow: none`).

**WARNING — flagship evidence surface self-contradicts:** `ScenarioScorecardModal.jsx:27` "✓ 7/7 PILLARS PASSED" vs `:72` engine summary "Successfully validated all 6 pillars" — both on screen simultaneously (modal-scorecard.png). The modal is THE decision-evidence artifact of Phase 13.

**WARNING — promised ScenarioTimelineBar absent:** Plan 13.3 promised "Scenario Timeline Bar rendered above the active screen showing cycle horizon, seed, active cycle, and narrative phase milestones". No `ScenarioTimelineBar.jsx`/`.css` exists (plan 13.3 Task 1); journey context (suspect window, milestones) only appears inside DIAGNOSE/ACT, not above every screen. Cycle-horizon/seed context is visible only in header machine context and scorecard modal.

**WARNING — dead/decoy visual system:** `.app-shell--dark` slate/navy theme (TabStrip.css:132–185, ~20 hardcoded slate values), `.scorecard-trigger-btn` (sky-blue glow), `.validation-suite-trigger-btn` (indigo glow) in AppShell.css:147–185 — zero JSX usage (grep confirmed). They are render-inert, but any accidental class reuse lands a foreign neon/glow style on the parchment UI. Same for the `Stage-badge--action` slate fill on the visible "DECISION & RECOVERY" badge (TabStrip.css:128) — the one badge in the visible UI not drawn from the 9-color token palette.

### Pillar 3: Color (2/4)

**Method:** token extraction over all 30 CSS files + screenshots.

**The declared system** (tokens.css:9–19) is 9 colors; the computed distribution shows wide divergence:

- **58 off-token hex keys** across 30 files. Worst offenders: three independent "healthy green" systems (@/emerald `#047857`/`#065f46`/`#d1fae5` in AppShell.css:50–57 and RecommendationCard.css; Tailwind green `#166534`/`#bbf7d0`/`#f0fdf4` in LiveProcess.css:64–68; plus IncidentDiagnosis/RecoveryPanel near-white surface variants `#fbfbf9`/`#faf9f6`/`#fbfaf7`/`#f7f6f2`/`#f9f8f5` — five different off-token near-whites for the same surface semantic while `--color-parchment` exists.
- **The token file's own hard rule is violated in two places:** tokens.css:61 "Elevation: Strictly NO box-shadows" — AppShell.css:164 `box-shadow: 0 0 8px rgba(2,132,199,.4)` (sky-blue glow, dead class), `:184` `0 0 8px rgba(79,70,229,.4)` (indigo glow, dead class), plus the live-glow `TabStrip.css:158` in the dead dark theme. Modal elevation shadows (OperationalCheckpointsModal.css:29, ScenarioScorecardModal.css:16) bolt a modal pretense — arguably acceptable deviation, but the rule is written absolute, and these precedents invite reuse.
- **Accent (wine/violet/lilac) discipline is good on-screen:** the fresh front-page screenshot and ACT screen show primary action (CONFIRM OPERATOR ACTION, Start the decision replay) consistently in wine; lilac only for selected/number highlight; violet for evidence links — 60/30/10 structure substantively holds in the rendered UI. The 30-layer (white cards) is fine; the 60-layer is parchment-warm.
- `.plant-target-badge` (AppShell.css:46–58) is emerald `#047857` — a semantic Healthy badge drawn outside the palette while `--color-lagoon` (defined exactly for "healthy") sits unused one file layer below.

**Score justification:** the on-screen 60/30/10 is genuinely admirable, but token compliance collapses with 58 raw values, three competing green regimes, and two contradictions of a written system rule. 2/4.

### Pillar 4: Typography (2/4)

**Declared:** 5 weights (`--fw-normal 400`, `--fw-editorial 460`, `--fw-label 540`, `--fw-data 600`, `--fw-bold 700`), Inter.

**Computed from 30 CSS files:**
- **25 distinct font-size values.** Standouts of drift: 10 / 10.5 / 11 / 11.5 / 12 / 12.5px are all in use (26+6+53+10+31+9 occurrences) — six interleaved micro sizes with no declared scale for heading/body steps (the token file defines weights and family but no type-size scale at all).
- **13 distinct weight declarations** including non-token literals `400`, `500`, `600`, `700`, `800`, `bold` duplicating the semantic names (e.g. front page badge `font-weight: 700/800` vs `--fw-label/--fw-bold`) — half the stylesheet uses tokens, half duplicates them numerically. `--fw-editorial` (460) is used only 8 times total despite being the system's signature weight; most body/UI text uses the 400/500/600 literals.
- Rendered output (screenshots) reads well — the problem is scale management, not composed pages: any new component picks among 3 near-identical label sizes with a coin flip.

### Pillar 5: Spacing (2/4)

**Declared scale:** 4px steps (`--sp-1`…`--sp-12`, tokens.css:35–44).

**Computed:** 80 `var(--sp-*)` usages vs **186 off-scale px literals** across padding/margin/gap declarations. Distribution: 10px(42×), 6px(35×), 2px(30×), 14px(23×), 3px(11×), 18px(9×), 7px(8×), 5px(7×), 28px(6×), 22px(6×), plus 9/11/1px one-offs. Micro-padding 2–7px inside pills/chips is arguably fine-grain typography spacing, but 14/18/22/28px are **structural** (section paddings, card gaps) and sit outside the declared steps; the scale is applied less than a third of the time. The screenshots show coherent rhythm (the spacing *values* were hand-tuned consistently), so this is a scale-adoption failure rather than a visual one.

### Pillar 6: Experience Design (2/4)

**State coverage is unusually strong** (grep + screenshots):
- Loading: DetectionComparison skeleton (`:26–33`), scenario-run button "Opening replay…"/"Starting…" with `aria-busy`/disabled (FrontPage.jsx:146, 263), apply-button "RECORDING ACTION…" (RecommendationCard.jsx:64).
- Error/live-data integrity: the shell-level offline refusal (`AppShell.jsx:59–64, 196–208, 212–224`) — three failed polls blank the screens rather than let a fabricated number be read; per-component equivalents ("showing nothing rather than a remembered number" DetectionComparison.jsx:40). Destructive/reset actions are guarded (disabled while `isResetting`, status feedback). No state invents a pass (`OperationalCheckpointsCard.jsx:23–24` — "No data is not a pass"; `GATE STATUS UNKNOWN`). This is the app's best pillar-quality asset.
- Empty: DIAGNOSE honest empty state (verified live, screen-diagnose.png).

**BLOCKER — fabricated-fallback candidates table:** detailed under Top 3 fix #3 (`CandidateTable.jsx:11–60,73,98`).

**WARNING — verification-count failure state:** `ScenarioScorecardModal.jsx:31` "⚠ VERIFICATION FAILED" is not regressed with the failed pillar list count; fine, but the modal provides no ESC key handling (only ContainmentTag.jsx:20 handles Escape; Scorecard/CoPQ/Checkpoints modals don't) and its backdrop-click-only dismissal plus a missing focus trap means keyboard users are trapped except via tabs reaching ✕ (which is reachable — aria-label present).

**WARNING — hardcode drift against the live envelope:** LiveProcess.jsx:218 renders "26.5 ± 2.5s" hardcoded in the Quality Contract table while the same screen's gauge envelope comes from the live fingerprint (`:55–58`), and those fingerprint values carry hardcoded fallbacks (228–236°C, 98–122 bar, …) that would silently present fabricated envelopes as real ones if the fingerprint endpoint died — in mild tension with the shell's own failure philosophy.

**WARNING — silent action failure:** OperationalCheckpointsModal.jsx:100–104 catches `recordMoldSpray` failure with `console.error` only — a shop-floor gate action fails with no user-visible feedback.

**Wide marginal case:** IncidentDiagnosis.jsx:140 `currentRisk.toFixed(1)` will throw on `null` if contributors exist without a risk probability (the `?? null` chain at `:13–14`).

**Plan-vs-implementation delta:** Plan 13.3 Tasks 1–2 promised `ScenarioTimelineBar` and `ValidationSuiteModal`; **neither exists** in the frontend (glob confirmed; only `.validation-suite-trigger-btn` dead CSS remains in AppShell.css:167–185). The absence is aligned with DEMO_FREEZE v1.2 §2 ("the suite is never a screen in the live demo — cited, not shown") and FrontPage.jsx:19–20, but **13-SUMMARY.md:41–43 falsely claims these components exist and are wired into AppShell/useApi**. Developers and the next auditor will chase ghosts off that summary; it needs a correction note. No Experience Design penalty applied beyond the surviving dead CSS since the removal restores demo-freeze compliance.

---

## Files Audited

**Screens:** `FrontPage.jsx/.css`, `LiveProcess.jsx/.css`, `IncidentDiagnosis.jsx/.css`, `InterventionRecovery.jsx/.css`
**Shell/navigation:** `App.jsx`, `main.jsx`, `AppShell.jsx/.css`, `TabStrip.jsx/.css`
**Components:** `ScenarioScorecardModal.jsx/.css`, `CandidateTable.jsx/.css`, `RecommendationCard.jsx/.css`, `DetectionComparison.jsx/.css`, `OperationalCheckpointsCard.jsx/.css`, `OperationalCheckpointsModal.jsx`, `CoPQModal.jsx` (state paths), `ProcessStateTimeline.jsx`, `SignalGauge.jsx/.css`, `ContainmentTag.jsx`, `ContainmentBoundaryCard.jsx/.css`, `AuditDrawer.css`, `RecoveryPanel.css`, `RootCauseBar.css`
**Styles:** `styles/tokens.css`, `styles/global.css`, `index.css`
**Data:** `hooks/useApi.js`, live API responses (`/api/scenarios`, `/api/scenarios/active`, `/api/scenarios/:id`, `/api/interventions/recommendation`)
**Process Guardian engine cross-refs:** `src/process_guardian/scenario/registry.py`, `scorecard.py`, `models.py`, `suite.py`
**Planning docs:** 13-SUMMARY.md, 13-01/02/03-PLAN.md, DEMO_FREEZE.md

**Screenshots:** `desktop-front.png`, `front-scrolled.png`, `screen-detect.png`, `screen-diagnose.png`, `screen-act.png`, `screen-act-2.png`, `modal-scorecard.png` (all `.planning/ui-reviews/`, gitignored)
