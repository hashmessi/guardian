# Phase 7 Context: Industrial UI + Audit Trail

**Captured:** 2026-09-24
**Phase:** 7 — Industrial UI + Audit Trail
**Requirements:** UI-01, UI-02, UI-03, TRST-01, TRST-02, TRST-03
**Build window:** 29–30 Sep (Day 7 PM – Day 8)

---

## Design System — Locked Decisions

### Theme
**Light — Warm Parchment.**
Adapted from the Superhuman editorial system (DESIGN (4).md). No dark mode for this phase. Judge-facing demo under normal lighting — parchment reads clean and premium without looking clinical.

### Color Palette (from design reference, adapted for industrial)

| Token | Value | Industrial Role |
|---|---|---|
| Parchment Canvas | `#f2f0eb` | Page background — dominant surface |
| Midnight Wine | `#421d24` | PRIMARY action fill, HIGH severity indicators, `Apply Demo Intervention` button |
| Royal Violet | `#714cb6` | DRIFT state accent, evidence links, contributing factor callouts |
| Lilac Mist | `#d4c7ff` | Selected tab fill, secondary badge surfaces, warning-state tint |
| Deep Lagoon | `#0c4243` | HEALTHY/STABLE state indicator, recovery-confirmed band |
| Ink Charcoal | `#292827` | All data labels, values, headings — never pure black |
| Stone Gray | `#666666` | Secondary labels, helper text, muted descriptions |
| Soft Mist | `#e3e3e2` | Hairline grid lines, card borders, gauge track |
| Paper White | `#ffffff` | Elevated cards, floating data panels |

**Strict constraints (carried from design reference):**
- No blue, green, or red accents — palette is maroon + violet + lilac only
- No drop shadows on cards — depth from layering and border contrast
- No gradients on UI surfaces — gradients only as atmospheric decoration if used
- No weight 700+ for headlines — weight 460–540 is the voice
- Midnight Wine is the ONLY chromatic fill button — everything else is ghost or outlined

### Typography
**Font:** Inter Variable (Google Fonts)
Substitute for Super Sans VF. Full variable weight axis (100–900).

| Role | Weight | Size | Use |
|---|---|---|---|
| Display / Screen Title | 460 | 28px | Screen headings (Live Process, Incident Diagnosis, etc.) |
| Section Label | 540 | 16px | Panel headers, group labels |
| Data Value (large) | 600 | 32px | Stability %, Risk %, current cycle — hero numerics |
| Data Value (medium) | 540 | 20px | Signal readings, contributor percentages |
| Body / Description | 460 | 14px | Evidence text, descriptions |
| Caption / Metadata | 400 | 12px | Timestamps, unit labels, envelope values |
| Monospace Numerics | 540 | 14–16px | Cycle numbers, exact sensor readings — use `font-variant-numeric: tabular-nums` |

Letter spacing: tight on display sizes (-0.022em at 28px), zero below 16px.

### Spacing & Layout
- **Base unit:** 4px
- **Page max-width:** 1280px centered
- **Card padding:** 16px
- **Section gap:** 24–32px (tighter than editorial — this is a dashboard, not a landing page)
- **Element gap:** 8px
- **Border radius:** Cards 12px, buttons 12px, tabs 8px outer, pills 999px, gauges 4px

---

## Navigation — Locked

**Horizontal tab strip at top** (3 tabs, Suite Tab Strip pattern from design reference):

```
[Live Process]  [Incident Diagnosis]  [Intervention + Recovery]
```

- Active tab: `#d4c7ff` (Lilac Mist) fill, `#292827` text, no shadow
- Inactive tabs: `#ffffff` background, `#292827` text
- Status badge on tab: Midnight Wine pill when drift detected on Live Process; amber-tinted pill when risk HIGH on Diagnosis; checkmark when recovery verified on Intervention
- Tab strip sits below the scenario banner and machine context header

---

## Header Structure — Locked

**Three-zone header (top → bottom):**

```
┌─────────────────────────────────────────────────────────────────────┐
│  PROCESS GUARDIAN                         ● SIMULATION · 2s STREAM  │
│  Injection Process Intelligence                                     │
├─────────────────────────────────────────────────────────────────────┤
│  DEMO · THERMAL DRIFT                                               │
│  HTF-200 · GMB-48A · Automotive Bracket · R-12 · Cycle #437        │
├─────────────────────────────────────────────────────────────────────┤
│  TEMP        PRESSURE       MOISTURE      QUALITY RISK              │
│  238°C       84 MPa         0.18%         72%                       │
│  ▲ DRIFT     ▲ DRIFT        NORMAL        HIGH                      │
├─────────────────────────────────────────────────────────────────────┤
│  [Live Process 🔴]  [Incident Diagnosis ⚠]  [Interv. + Recovery]   │
└─────────────────────────────────────────────────────────────────────┘
```

**Zone 1 — Brand bar:** `#f2f0eb` parchment background. Left: "PROCESS GUARDIAN" wordmark (Ink Charcoal, weight 540, 16px) + "Injection Process Intelligence" subtitle (Stone Gray, 12px). Right: `● SIMULATION · 2s STREAM` pulse indicator — small animated dot + label in Stone Gray 12px. Honest labeling: never implies a real factory connection.

**Zone 2 — Scenario + Machine context:**
- `DEMO · THERMAL DRIFT` — ALL CAPS, Midnight Wine `#421d24`, weight 540, 13px. **Static** — this is the deliberate demo scenario narrative, not a live API value.
- `HTF-200 · GMB-48A · Automotive Bracket · R-12 · Cycle #437` — Stone Gray 12px, **dynamic**: cycle number pulled from `/api/process/current`, rest are static demo context strings. Architecturally: scenario is a known failure mode being demonstrated; machine telemetry underneath is live from the simulator.

**Zone 3 — PS02 Hero Stats (4 cards):**
Four equal-width stat cards in a horizontal row. This is the judge's 3-second read — they see the problem immediately.

| Card | Value | Status row |
|---|---|---|
| TEMP | `238°C` | `▲ DRIFT` (Midnight Wine pill) |
| PRESSURE | `84 MPa` | `▲ DRIFT` (Midnight Wine pill) |
| MOISTURE | `0.18%` | `NORMAL` (Deep Lagoon pill) |
| QUALITY RISK | `72%` | `HIGH` (Midnight Wine pill) |

- Card background: `#ffffff` Paper White (lifts off parchment)
- Value: 32px weight 600 Ink Charcoal, tabular-nums
- Label: 10px weight 540 Stone Gray ALL CAPS
- Status pill: Midnight Wine `#421d24` for DRIFT/HIGH, Deep Lagoon `#0c4243` for NORMAL/LOW
- All 4 values dynamic: Temperature, Pressure, Moisture from `/api/process/current`; Risk % from `/api/quality/risk`

**Data refresh:** Polling every 2 seconds via `setInterval`. No WebSocket.

---

## Screen 1 — Live Process (UI-01)

### Layout
Two-column grid on desktop (8/4 split).

**Left column (8/12):**
- Hero stats row: Stability % (32px/600), Risk % (32px/600), Current Cycle (32px/600), Drift Status pill
- Signal Gauges panel (4 gauges: Temperature, Pressure, Moisture, Cycle Time)
- Process Stability Sparkline (last 50 cycles, thin line, no axis clutter)

**Right column (4/12):**
- Quality Contract card (part targets vs current values, check/cross status)
- System State Machine badge (current state + last transition timestamp)
- Last 5 events feed (timestamped list, minimal)

### Signal Gauges — Locked
**Horizontal instrument-style gauge bars:**
- Track: `#e3e3e2` (Soft Mist) full width, 8px height, 4px radius
- Fingerprint envelope: shaded `#d4c7ff` region showing normal operating range
- Current value: vertical marker line (3px wide) in `#292827`
- Out-of-envelope deviation: marker shifts to `#421d24` (Midnight Wine) when drifting
- Value label: right-aligned numeric + unit in 16px/540
- No decorative animations — marker position IS the state

### Status Colors (RAG adapted to palette)

| State | Color | Usage |
|---|---|---|
| HEALTHY | `#0c4243` Deep Lagoon | Stability pill, state badge |
| DRIFT_SUSPECTED | `#714cb6` Royal Violet | Warning pill, signal deviation marker |
| DRIFT_CONFIRMED / QUALITY_RISK_HIGH | `#421d24` Midnight Wine | Severity pill, gauge deviation |
| RECOVERY_VERIFIED | `#0c4243` Deep Lagoon | Recovery banner |
| ABSTAIN | `#666666` Stone Gray | Greyed-out action button |

---

## Screen 2 — Incident Diagnosis (UI-02)

### Layout
Two-column grid (7/5 split).

**Left (7/12):**
- Risk Escalation card: shows 3% → 72% trajectory, lead time in cycles, confidence score
- Drift Evidence panel: which methods fired (EWMA, CUSUM, Mahalanobis) with severity scores
- Affected Cycle Window: horizontal range bar (last known good → detection → present → current)

**Right (5/12):**
- Root Cause Contributors: ranked horizontal bars
  - Lilac Mist fill for all bars, Midnight Wine for top contributor
  - Value labels (e.g., "Temperature 68%") in 540/16px
  - Evidence snippet below each: "Variance ↑ 3.2σ from fingerprint" in Stone Gray 12px
  - **Honest language enforced:** all labels use "likely contributor", "evidence", "modeled effect"
- Confidence Score: arc gauge (hairline stroke, no gradient ring)

### Critical Rule
No fabricated evidence text. Every string comes from the API. If API returns no evidence, show "Insufficient data for this signal" in Stone Gray — never invent.

---

## Screen 3 — Intervention + Recovery (UI-03)

### Layout
Three zones stacked vertically within the screen.

**Zone A — Candidate Comparison Table:**
- Columns: Action | Predicted Risk After | Cost | Disruption | Constraint Status
- One row per candidate (A0: Continue Monitoring, A1: Temperature Adjust, A2: Pressure Adjust, A3: Material Check)
- Recommended row: `#f2f0eb` background + `3px solid #421d24` left border
- ABSTAIN state: all rows `#e3e3e2` background + Stone Gray text, banner "ABSTAIN — confidence below threshold"

**Zone B — Recommendation Panel (7-field card):**
Fields: ACTION | WHY | EVIDENCE | EXPECTED EFFECT | CONFIDENCE | OPERATING LIMIT | RECOVERY CHECK
- Field label: 12px Stone Gray
- Field value: 16px Ink Charcoal, weight 460
- **Apply Demo Intervention** button:
  - Normal: `#421d24` fill, `#ffffff` text, 12px radius, 48px height, weight 540
  - Disabled (ABSTAIN): `#e3e3e2` fill, `#666666` text, cursor not-allowed
  - Loading: spinner + "Applying…" text
  - This is the ONLY Midnight Wine fill button in the entire UI

**Zone C — Recovery Verification:**
- Post-intervention display: Risk before → after, Stability before → after, Recovery status
- VERIFIED: `#0c4243` Deep Lagoon badge + "Production Released" label
- FAILED: `#421d24` Midnight Wine badge + "Reassessing…" label
- Scrap containment: "Cycles 432–444 quarantined (13 cycles, ~97.1% scrap reduction)"

---

## Audit Trail — Locked

**Collapsible drawer at bottom of Screen 3.**

- Trigger: "View Evidence Chain ↑" text link in Royal Violet `#714cb6` (no underline default, underline on hover, 0.2s ease transition)
- Expanded: slides up (~40vh) showing the full audit timeline
- Timeline layout: vertical hairline left, events right
- Full chain: Signal Change → Drift Evidence → Risk Estimate → Cause Evidence → Candidate Actions → Selected Action → Expected Outcome → Observed Outcome → Recovery Decision → Production Disposition
- Event type pills use palette: drift=violet, risk=wine, recovery=lagoon, containment=gray
- Data source: `/api/containment/window` + audit_log table
- "Export Audit Log" ghost button: `#292827` text, no fill, `1px #e3e3e2` border — downloads JSON

---

## API Integration Map

| Screen | Polled Endpoints (2s) |
|---|---|
| Header | `/api/process/current` |
| Screen 1 | `/api/process/current`, `/api/process/drift`, `/api/quality/risk` |
| Screen 2 | `/api/quality/risk`, `/api/process/drift`, `/api/interventions/recommendation` |
| Screen 3 | `/api/interventions/recommendation`, `/api/interventions/history`, `/api/recovery/status`, `/api/containment/window` |
| Audit Drawer | `/api/containment/window` + audit_log (new `/api/audit` endpoint or repurpose existing) |
| Apply Button | `POST /api/interventions/apply-demo` |

---

## Tech Stack — Locked

- **Framework:** React + Vite
- **Styling:** Vanilla CSS with CSS custom properties (all design tokens as CSS vars in `tokens.css`)
- **Charts:** Recharts for sparklines, native SVG/CSS for instrument gauge bars
- **HTTP:** native `fetch` + `setInterval` polling — no React Query
- **No:** Tailwind, CSS-in-JS, shadcn, or pre-built component libraries — custom only

---

## Anti-Patterns (Explicit Bans)

- No glowing orbs, pulsing halos, animated gradient rings around numbers
- No holographic dark glass panels — the design is LIGHT
- No AI-generated decorative wave/mesh backgrounds
- No drop shadows on cards — border contrast only
- No skeleton loaders — use "—" placeholder for loading states
- No pure `#000000` or pure `#ffffff` as page background
- No blue or green in the palette — RAG uses maroon + violet + lagoon only
- No fabricated evidence strings — API values or explicit "Insufficient data" fallback
- No weight 700+ headlines
- No second colored action button — Midnight Wine fill is exclusive to Apply Intervention

---

## Success Criteria (from Roadmap Phase 7)

1. Screen 1: machine context, stability %, risk %, current cycle, drift status, signal gauges ✓
2. Screen 2: risk escalation (3% → 72%), lead time, confidence, ranked contributors, affected window ✓
3. Screen 3: candidate comparison, 7-field recommendation, Apply button, recovery, containment ✓
4. Audit trail: full evidence chain per intervention, collapsible drawer ✓
5. A judge can understand the complete decision loop without explanation ✓

---

## Deferred (Out of Scope Phase 7)

- Dark mode toggle
- Mobile responsive layout (desktop-first for demo)
- Export to PDF (JSON export sufficient)
- Real-time WebSocket (polling covers demo)
- Animated cycle-by-cycle replay

---

*Context captured: 2026-09-24 — gsd-discuss-phase + impeccable*
*All decisions confirmed by user. Downstream planning and execution agents act without re-asking.*
