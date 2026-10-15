# PROCESS GUARDIAN: DEMO FREEZE MANIFESTO (v1.2)

**Date**: 2026-10-15
**Project**: Process Guardian — Injection-Molding Operational Drift & Intervention Engine
**Competition Target**: Hack4Purpose PS02
**Target Audience**: Indian Automotive Tier-2 / Tier-3 Plastic Injection Molders
**System Status**: **FROZEN FOR DEMONSTRATION**
**Supersedes**: v1.0 (2026-10-01) — that version described the old 3-screen UI, the old 10-scenario live demo, and machine ID `HTF-200`/`GMB-48A`. None of that matches the current system (`IMM-01`, 3 locked scenarios, DETECT → DIAGNOSE → ACT & VERIFY). Read this version, not that one.

---

## 1. The one claim this demo makes

> Process Guardian catches the scrap the plant's own instruments cannot see — the moisture-delay, clerical-setup and mold-release failures behind the last points of the 6→2 gap — names the cause correctly, refuses to act when it isn't sure, and proves every number it shows.

Full reasoning: `scope_plan.md` §0–§1. This document is the frozen *delivery* of that plan — the exact script, in the exact order, for the exact three scenarios it locks.

---

## 2. Three scenarios, three distinct proofs (10 → 3, locked)

The automated validation suite still runs 10 scenarios (`python -m process_guardian.validation`, 100% pass) and is citable as one line of evidence — **it is never a screen in the live demo.** Only these three ever run on the shared display:

| Code | Title | Proves |
|---|---|---|
| **S06** | Compound Multi-Signal Drift | The deterministic closed loop end-to-end (detect → diagnose → act → verify → contain) **and** the "machine's own limits say fine, Guardian acts" contradiction. |
| **S-FLIP** | Human-Channel Material Risk | The sensor-blind gap filled — zero sensor disturbance the entire run; a shop-floor note in a local language is the only evidence, and it alone flips the verdict. The differentiator no sensor-only system in the room can produce. |
| **S08** | Out-of-Distribution Drift | The refusal. Model confidence drops below 0.65 → mandatory `ABSTAIN_AND_MONITOR` (`SAFE-03`). This is the trust moment, not a non-event — narrate it as one (see §4, Beat 3). |

---

## 3. The frozen 4-minute script

**Beat 0 — Opening line (before touching the keyboard):**
> "Two of the next three runs never trip a single sensor threshold. That's the gap we're here about — not another dashboard."

This sets up the contradiction before anyone sees a gauge, and immediately differentiates from the gauge-wall every other team will show.

**Beat 1 — S06 (contradiction #1, ~90s):**
1. Front page → select **Scenario 06 — Compound Multi-Signal Drift** → opens the live DETECT screen mid-drift.
2. Point at the banner: every individual signal is still inside its own tolerance band — a threshold-alarm system reads this as fine. Point at the quality-risk pill: it is not fine.
3. Switch to DIAGNOSE. Root-cause attribution ranks the real coupled driver (barrel Zone 3 thermal + hydraulic pressure) — say the percentages on screen, don't round them up.
4. Switch to ACT & VERIFY. Say: *"The engine is picking the smallest action that clears this risk, scored against doing nothing — not claiming a calibrated optimum. We show that distinction on purpose."* Click apply. Show the 3-cycle recovery window close and the containment tag print.

**Beat 2 — S-FLIP (contradiction #2, the one that wins, ~90s):**
1. Select **Scenario FLIP — Human-Channel Material Risk**.
2. Say out loud, before advancing: *"Every sensor on this machine will read in-spec for the entire run. Watch what still catches this."*
3. Show the DETECT screen: stable, no drift anywhere.
4. Trigger/show the operator shift note (local-language text: new resin lot, dryer was down, moisture not verified). Show the verdict flip to `QC_REQUIRED`.
5. Name the mechanism honestly: *"This runs on a bounded, deterministic multilingual parser — it's the thing that actually works reliably. A small local model, Laya, is wired in as an optional confidence layer behind it, but we benchmarked Laya's zero-shot accuracy ourselves, found it unreliable on real molding phrasing, and shipped the safe deterministic path instead of a demo that could fail live. That's in our own project notes, not hidden."*

**Beat 3 — S08 (trust, ~45s):**
1. Select **Scenario 08 — Out-of-Distribution Drift**.
2. Before the ABSTAIN fires, say: *"Watch what it does when it isn't sure."*
3. Show the mandatory ABSTAIN gate firing, production held, inspection requested — no speculative action taken. Narrate it as the win it is: *"This is the differentiator most teams can't show — a system that knows the limit of its own model and stops there."*

**Beat 4 — Close (~15s):**
1. State the one real anchor: `[PENDING — see scope_plan.md §5.1; must be sourced externally (a citation, a sensor trace, or a captured operator quote) before this line can be filled in; do not demo this closing beat with a fabricated anchor]`.
2. State the one honest limit, out loud, every time: *"This has not yet run on a production machine. Everything else here is proven, computed, or that one real anchor."*

---

## 4. Strict Safety Invariants (unchanged, still audited)

1. **SAFE-01: Read-Only Machine Integration / Zero Automatic PLC Write-Back.** No PLC write-back sockets, Modbus write registers, or OPC-UA write clients exist. All interventions are advisory; the operator is the sole authority over the physical machine.
2. **SAFE-02: Strict 5-Layer Operating Envelope Compliance.** Every candidate action is checked against machine safety limits, recipe limits, baseline fingerprint envelope, single-step rate limits, and drift-opposition direction.
3. **SAFE-03: Mandatory ABSTAIN Policy on Model Uncertainty.** Confidence below 0.65, or an unseen drift pattern outside validated surrogate coverage, triggers `ABSTAIN_AND_MONITOR` and a human inspection request — this is Beat 3 above.
4. **SAFE-04: Simulation Disclosures & Honest Epistemic Labels.** Every modeled number is labeled modeled; no "guaranteed" or "proven" language anywhere in system output; UI persistently shows `ADVISORY ONLY · ZERO PLC WRITE-BACK`.

---

## 5. Pre-demo checklist

- [ ] `demo.cmd` (or `uvicorn` + `npm run dev` manually) — both processes healthy, `GET /api/health` → 200.
- [ ] `bash scripts/verify.sh` green on the exact commit being demoed.
- [ ] One real anchor sourced and written into Beat 4 above (**blocking — see §3 Beat 4**).
- [ ] Script rehearsed with the actual click-path on the actual build at least once, out loud, with a timer.
- [ ] Reset Demo button tested — confirms a clean run before judges arrive.

**Freeze sign-off:** Engineering complete and gate-green. **Not yet certified for demo** — Beat 4's real anchor is the one open item, and it is intentionally left open rather than faked.
