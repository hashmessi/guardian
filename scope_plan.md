# Scope Plan — FINAL / LOCKED (v1.2 · "Bridge the Industrial Gap")

**Date:** 2026-10-11
**Problem (PS02):** Bring injection-molding scrap at Ragam Polymolds from 6–7% to the automotive target ≤2%, using low-cost shop-floor sensors, moisture checks and standardized operational checkpoints.
**What this document locks:** the final feature scope, the noise we cut, and the single claim the product is allowed to make.

---

## 0. The one claim we make

> **Process Guardian catches the scrap the plant's own instruments cannot see — the moisture-delay, clerical-setup and mold-release failures behind the last points of the 6→2 gap — names the cause correctly, refuses to act when it isn't sure, and proves every number it shows.**

We do **not** claim a real-plant scrap reduction we have not measured. We claim a **trustworthy workflow that bridges the specific industrial gap**, grounded in one real anchor and honest about its one limit (not yet run on a press).

## 1. The gap most teams skip — and we fill

Ten teams will build a real-time gauge dashboard with threshold alarms and a defect-predictor on synthetic data. An industrial judge has seen it and the machine's own SCADA already does it. It plateaus **above** 2%, because:

**The last ~4 points of the gap are human, material-handling and procedural — invisible to any barrel-temperature sensor.**

| Cause | Sensor-visible | Real fix | Who misses it |
|---|---|---|---|
| Thermal / pressure drift | yes | trim in-envelope | nobody — table stakes |
| Raw-material **moisture** | partial, **delayed** (from the dryer, not the press) | **dry the resin** — cannot be dialed out with pressure | teams treat it as one more live threshold |
| **Clerical / setpoint drift** | **no** | reconcile active setpoint vs locked recipe | teams skip entirely |
| **Mold-release spray** | **no** | procedural cycle-count checkpoint | teams try to "sensor" it |

The expensive error is **mis-attributing the cause**, because a pressure-chasing system *worsens* a wet-resin defect. **Filling the sensor-blind channel with cause-correct attribution is the gap. That is the whole product.**

## 2. How we fill it — the engine, not a dashboard

A small, **local**, multilingual decision model (**Laya**, Apache-2.0, 322M, ~33ms, calibrated typed decisions, runs on the demo laptop so shop-floor data never leaves the plant) instruments the human/procedural channel and **feeds it as validated evidence into the deterministic engine we already have.** Laya **proposes in type-safe terms; the deterministic engine decides; nothing is shown as fact until the engine confirms it.**

- `root_cause/analyzer.py` → add a `human_channel` contributor into the existing ranked attribution.
- `quality/model.py` ABSTAIN (`OperatorMode.ABSTAIN_AND_MONITOR`) → also driven by Laya's calibrated probability. Low confidence → abstain, same `SAFE-03` gate.
- `quality/operational_checkpoints.py` (`evaluate_recipe`, `evaluate_moisture`, spray counter) → inputs become Laya-parsed multilingual text instead of hardcoded flags.
- **New:** `llm/human_channel.py` — thin local Laya client → pydantic schema, with a deterministic fallback so the loop never *depends* on the model.

One new module, one new evidence source, fused into what exists. **Not a parallel system, not a dashboard.**

## 3. Feature scope (locked)

### P0 — Operational checkpoint gates (maps 1:1 to the problem statement, no free-form typing)
Laya `noul` over bounded local-language answers: *spray done this interval? resin lot dried & signed? setpoint matches recipe R-12?* → drives existing checkpoint + abstain logic.

### P1 — Human-channel evidence fusion + the one demo that wins
Shift notes / operator observations (Hindi/Tamil/Kannada) → `choice{thermal|pressure|moisture|mold_release|recipe|material_lot|unknown}` + confidence → fused into root-cause attribution.
**The winning scenario:** sensors read in-spec / healthy — T² quiet, all params in envelope — and the fused human channel ("prev shift: new resin lot, dryer was down") **flips the verdict CONTINUE → CONTAIN + verify moisture.** No sensor-only solution in the room produces that moment. **If a feature does not contribute to this flip, it is cut.**

### Not in scope
Generative briefing/translation (Laya can't generate — optional separate small model, does not block anything). Audit-trail NL query. Fine-tuning Laya (base checkpoint + tight schema <20 options for the demo; fine-tune is the production path, not now).

## 4. Cut the noise (this is the optimization)

### Scenarios: 10 → 3 demo-worthy proofs
Each kept scenario is a distinct, memorable proof. Everything else leaves the live UI.

| Keep (live) | Proves |
|---|---|
| **S06 Compound drift** | the deterministic closed loop end-to-end (detect→diagnose→act→verify→contain→**printed tag**) **and** the SPC-says-fine / Guardian-acts contradiction |
| **S-FLIP (moisture/material via human channel)** | the sensor-blind gap filled — the differentiator no other team has |
| **S08 Out-of-distribution → ABSTAIN** | the refusal — the trust moment that wins industrial panels |

**Cut from the live demo:** S01, S02, S03, S04, S05, S07, S09, S10. The automated 10-scenario suite stays **only** as a one-line cited artifact ("10 scenarios pass deterministically"), never a screen.

### Features / surfaces cut or demoted
| Cut / demote | Why |
|---|---|
| 7-pillar scorecard **as a screen** → one evidence line on request | eats the demo clock; judges don't read pillars |
| 13-state machine visualization | internal mechanism, not a decision surface |
| 4-level epistemic framework **as a page** → footer line + table on request | already demoted in the honesty pass |
| Counterfactual "canvas" polish beyond the two-column divergence | chrome, not evidence |
| Generic telemetry gauges **as the product** → kept only as context for the contradiction moments | a gauge wall is what 10 teams ship |
| Any ₹ figure without its formula inputs on screen | self-referential economics is the attack surface |
| Live-running more than the 3 scenarios | breadth reads as shallow-but-wide |
| NL chatbot / "ask the data" panel | the generic feature we refuse to build |
| `xgboost` dependency | already removed — declared, never imported |

**Nothing in the demo claims a generic dashboard metric.** Every number on screen is either computed live and traceable, or labeled modeled.

## 5. The four industrial-judge ceiling-breakers (small, non-feature)

1. **One real anchor** — a real resin-moisture/defect reference with a citation, one retrofit-sensor/hopper-hygrometer trace, or a captured Ragam Polymolds operator quote. Labeled as the single real datapoint. Converts "modeled" → "grounded in one real instance." *(Must be sourced from outside the repo — the one thing code cannot manufacture.)*
2. **Signal-acquisition path on legacy presses** — one line: Euromap 63/77 where it exists; ~$20 clamp thermocouple + hopper hygrometer where it doesn't. Answers the first question an industrial judge asks.
3. **Headline metric = avoided customer PPM / escape**, not scrap % — a contained lot tied to an avoided OEM line-stop. The Tier-2 existential metric.
4. **Frozen 4-minute script**, 3 scenarios, contradiction as the opening shot.

## 6. Trust & honesty contract (non-negotiable)

1. Laya output is **evidence the engine validates** — never a verdict shown as fact.
2. Calibrated P below threshold → `ABSTAIN_AND_MONITOR` (`SAFE-03`), same gate as sensor uncertainty.
3. Every human-channel signal carries its source and confidence — no laundering a guess into a fact.
4. Local inference only; shop-floor text never leaves the plant (`SAFE-01`, read-only, no PLC write-back).
5. Laya down / low-confidence → deterministic path runs unchanged.
6. Exactly one stated limitation, said out loud: **not yet run on a production machine.** Everything else is proven, computed, or one real anchor.

## 7. Risks (honest)

- **Adoption, not accuracy, is the real failure mode** — P0 checkpoint gates need no free-form writing, which is why they lead.
- **Laya base-checkpoint accuracy on molding text is unproven** — tight schema, few options; fine-tune is the production path. Latency/benchmark/calibration figures are vendor-reported.
- **The real anchor (§5.1) must be sourced externally** — it is the one ceiling-breaker code cannot produce.
- **Honesty regression** — the moment a Laya guess is shown as a conclusion, the hallucination risk returns. The engine gates every signal.

## 8. Build order

**P0 checkpoint gates → P1 fusion + the flip scenario → §5 ceiling-breakers → cut the noise (§4) → freeze the 4-min script.** Stop there. The generative briefing is optional and blocks nothing.

**Frozen demo (4 min):**
1. S06 — machine SPC: ALL PASS. Guardian: drift, act, recover, **print the containment tag**. *(contradiction #1)*
2. S-FLIP — sensors healthy; operator note in local language; human channel flips to CONTAIN + verify moisture. *(contradiction #2 — the gap filled)*
3. S08 — out-of-distribution; Guardian **abstains** and calls for inspection. *(trust)*
4. Close on the one real anchor and the one honest limit.

---

*Scope only — no code in this document. On approval: lock P0 against `operational_checkpoints.py`, wire the Laya client with its deterministic fallback, build S-FLIP, then cut S01–S05/S07/S09/S10 from the live UI.*
