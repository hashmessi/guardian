# Process Guardian: Sensor Integration Spec (Moisture-First)

2026-11-25 · Supersedes the dryer-probe part of EDGE-04 and the BOM in the ₹6,950 thesis.

## 1. What changed and why

The industrial mentor gave us two facts:

1. **The presses already have pressure and temperature sensors built in** (injection/hydraulic pressure, barrel-zone thermocouples, often nozzle and oil temperature).
2. **The main cause of lost production is moisture in the resin**, and the plant wants to predict it from the drying setup and other process parameters.

That leads to three decisions:

- **We do not add pressure or barrel temperature sensors.** Duplicating sensors the press already has adds cost and wiring and tells us nothing new. Where the controller lets us, we **read** its values, read-only. We never write to it (SAFE-01).
- **We add sensors only where the press is blind: the dryer, the hopper, and the room air.** Moisture is decided before the resin reaches the barrel, and no press sensor looks there.
- **We fix a flaw in the old plan.** An SHT30 humidity probe at the dryer outlet cannot measure dew point (see §4). It moves to ambient air, where it works, and the dryer gets temperature probes and current clamps.

**Plant name check:** our planning docs say *Ragam Polymoulds* (Ponneri, PP/PA6 furniture parts). The request says *Rangan Polymods*. Confirm the correct name before this goes to the mentor.

## 2. The honest constraint on "measuring moisture accurately"

No low-cost sensor measures the water inside resin pellets inline. Inline NIR or microwave moisture analyzers do exist, but they cost lakhs per hopper, which is out of range for an MSME plant.

So the system works in two parts:

| Part | What it does | Accuracy |
| --- | --- | --- |
| **Predict** (per press, live) | Watches the causes of wet resin (dryer heater, airflow, air temperatures, time in the hopper, room humidity) and estimates moisture risk every cycle | Early warning. It is a risk score, not a percentage, until it is calibrated |
| **Verify** (one per plant, at the QC gate) | A halogen moisture analyzer measures a real moisture % on a pellet sample when the prediction raises a flag, and on a schedule | The ground truth. Each reading also calibrates the predictor for that material |

Prediction without verification is a guess. Verification without prediction catches problems too late or costs too much in sampling. We need both.

## 3. The exact sensor list

### 3a. Per press: the Guardian edge kit (new hardware)

| # | Sensor (exact part) | Where it goes | What it measures | Why it matters for moisture / scrap | Qty | ₹ each (retail) |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | **SCT-013-030** split-core CT | Dryer heater supply, in the dryer's panel | Heater on-state current and on-time | A heater trip or weak element is the #1 cause of wet resin. It is visible **at once**, minutes before outlet air cools | 1 | ~450 |
| S2 | **SCT-013-030** split-core CT | Dryer blower motor supply | Blower RMS current | Clogged filter or failed blower means low airflow, so resin under-dries even with the heater on | 1 | ~450 |
| S3 | **DS18B20** stainless waterproof probe, 3 m cable (silicone/PTFE cable variant, rated ≥ 100 °C) | Process-air line **into** the hopper | Drying air temperature | Must hold the datasheet setpoint (PA6: 80 °C). Confirms the heater fault S1 found and catches setpoint errors | 1 | 64–305 |
| S4 | **DS18B20** (same) | Return-air outlet at the **top** of the hopper | Return air temperature | Low return temperature means the pellets are not reaching drying temperature: throughput too high or residence too short | 1 | 64–305 |
| S5 | **SHT30 IP67** temperature/humidity probe | Room air beside the hopper and material store (not inside the dryer) | Ambient temperature and RH | Coastal plant at 70–85% RH. Drives moisture pickup on open bags and the output of hot-air dryers | 1 | ~899 |
| S6 | **SCT-013-100** split-core CT | Hydraulic pump motor feed | Pump current pattern | Counts cycles, which gives throughput and therefore resin residence time in the hopper. Also sizes the quarantine | 1 | ~450 |
| S7 | **SCT-013-030** split-core CT ×3–5 | Barrel heater-zone feeds | Zone on-state current and on-time | Heater-band failure, the second scrap cause. **Optional add-on**: the press thermocouples already cover temperature, our CT only adds earlier detection | 0, 3 or 5 | ~450 |

Electronics (unchanged from the thesis BOM): ESP32 dev board, ADS1115 16-bit ADC (1 board for the moisture kit, 2 if S7 is added: 8 CT channels in total), PCB and burden resistors, IP65 enclosure, 24 V supply, 3-colour andon on its own isolated relay.

Everything is clamp-on or strap-on. Nothing is drilled into the barrel or mold, and nothing is wired into the press controller.

### 3b. Per plant: shared verification instrument (new hardware)

| # | Instrument | Where | Spec to buy against | ₹ (Indian listings, 2026-11-25) |
| --- | --- | --- | --- | --- |
| V1 | **Halogen moisture analyzer** | QC desk near the presses | Readability **0.01% MC**, sample ≥ 10 g, 50–160 °C program, data output (USB/RS-232) so readings reach the tablet without retyping | ₹25,000 (low-end listing, polymer suitability unconfirmed) up to ₹1,68,800 (Mettler Toledo HE53). Get 2–3 quotes; ask the vendor to demo on PA6 pellets |

Why 0.01%: the PA6 limit is about 0.2% (§6), so we need to tell 0.15% from 0.25% reliably. A 0.1% instrument cannot.

### 3c. Already on the press: read, never add

| Signal from the press controller | What it adds | How we read it |
| --- | --- | --- |
| Screw recovery (plasticizing) time | Wet PA6 degrades and its viscosity drops, which shortens recovery. **This is a hypothesis to test in the pilot** | Euromap 77 (OPC UA, read-only user), or Euromap 63 (file-based), depending on controller |
| Peak injection pressure / pressure at switchover | Same viscosity effect. Also catches non-moisture drift | Same |
| Cushion | Unstable cushion follows viscosity and check-ring problems | Same |
| Barrel zone and nozzle temperatures | Confirms or contradicts a heater-CT alarm (cross-check) | Same |
| Shot counter | Cross-checks our cycle count from S6 | Same |

If a controller has neither Euromap interface (older presses), we use none of this: the kit still works on S1–S6 alone. We do not tap analog signals inside the press, because that risks the machine and its warranty.

**Whether each press supports Euromap 63 or 77 is unknown and must be checked on site** (look for the interface option in the controller menu, or ask the press vendor).

### 3d. Data from the operator tablet, no sensor needed

- Material grade and lot (QR/barcode scan): selects the drying limits.
- Time the bag or octabin was opened: how long resin sat in humid air.
- Regrind %: regrind picks up moisture faster.
- Shot weight from the recipe: turns the cycle count into kg/h through the hopper.

## 4. Why the SHT30 cannot stay at the dryer outlet

A humidity sensor measures relative humidity. Dew point is calculated from RH and temperature. In hot, very dry air the RH is too small to resolve:

| Dryer outlet dew point | RH the sensor sees at 80 °C | Healthy? |
| --- | --- | --- |
| −40 °C | 0.03% | Excellent desiccant dryer |
| −18 °C | 0.26% | PA6 limit (DuPont Zytel guide) |
| 0 °C | 1.27% | Failing |
| +10 °C | 2.56% | Failed |

The SHT30 is accurate to about ±2% RH. It reads every row of this table as "0–2%", so it cannot tell a healthy dryer from a failed one. (Values from the Magnus formula, computed 2026-11-25.)

So:

- **Hot-air dryers** (common in MSME plants): outlet dew point just follows the room air. The useful signals are heater current (S1), airflow (S2), air temperatures (S3, S4) and room RH (S5). This kit covers them fully.
- **Desiccant dryers**: dew point is the key signal. Most desiccant dryers show their own dew point on the panel. We **read that** (photo/manual entry on the tablet, or its 4–20 mA output if it has one). Only if a desiccant dryer has no dew-point meter do we add a proper dew-point transmitter for that dryer, and only after a quote, since these cost far more than the rest of the kit.

## 5. How the moisture risk is predicted

Inputs each cycle: S1–S6, the tablet data, and press signals when available.

1. **Hard faults (no model needed):** dryer heater current zero or on-time pinned at 100%; blower current outside its band; process-air temperature below setpoint − 5 °C for longer than a set time. Any of these raises Signature B (soft lock and QC gate) before suspect resin reaches the barrel, timed by hopper residence.
2. **Drying sufficiency:** effective drying time = hopper capacity ÷ throughput (from S6 + shot weight), adjusted when S3/S4 show the air below setpoint. Compared with the datasheet time for the material (PA6: 2–4 h at 80 °C).
3. **Exposure:** bag open time × room RH (S5), used to raise the predicted starting moisture.
4. **Process confirmation:** a shift in recovery time or peak pressure from the press, if readable.
5. **Calibration:** every halogen reading (V1) is stored with the predictor's inputs at that moment. After enough readings per material, the risk score maps to an estimated moisture % with a stated error. Until then the screen says "risk", not "%".

## 6. Limits per material

From supplier processing guides. The grade's own datasheet overrides these.

| Material | Max moisture at molding | Drying | Dryer dew point |
| --- | --- | --- | --- |
| PA6 | < 0.2% (ARBURG guide: < 0.15%) | 2–4 h at 80 °C for resin at 0.1–0.2%; 4–8 h at 0.2–0.5% | ≤ −18 °C (DuPont) |
| PP (virgin) | Barely absorbs water; drying usually not needed | Only if filled, recycled, or surface-wet | n/a |

Note: PA6 is often shipped at up to 0.25% moisture, so even a fresh bag can need drying. This is why the moisture story leads with PA6, not PP.

## 7. Cost per press

Retail single-unit prices, from the thesis BOM sources and new searches. Supplier quotes are still needed (EDGE-08).

| Kit | Contents | ₹ per press |
| --- | --- | --- |
| **A. Moisture-first (recommended pilot kit)** | S1–S6, ESP32, 1 ADS1115, PCB, enclosure, PSU, andon, relay | **≈ 6,060** |
| B. Moisture + 3 heater zones | A + 3 × S7 + second ADS1115 | ≈ 7,560 |
| C. Moisture + 5 heater zones | A + 5 × S7 + second ADS1115 | ≈ 8,460 |
| Shared per plant | V1 halogen analyzer | ₹25,000–1,68,800 once, spread over all presses |
| Not included | Operator tablet (one per line), electrician time, monthly service | |

Kit A stays under the ₹10,700 competing kit and close to our ₹6,000 target. Kit C goes past the old ₹6,950 figure, so heater zones should be added only where heater failures appear in the plant's rejection log.

If dryers are central rather than one per press, S1–S5 are bought **per dryer**, not per press, and the per-press cost drops to about S6 + electronics.

## 8. Recommendation

1. **Pilot one PA6 press with Kit A plus one shared halogen analyzer.** It goes straight at the mentor's stated problem, and it is the cheapest complete loop: predict, lock, verify, calibrate.
2. **Read the press's own pressure and temperature data where Euromap is available.** Don't buy sensors the press already has.
3. **Add heater-zone CTs (S7) only after the rejection log shows heater-caused scrap.**
4. **Not building:** inline NIR/microwave moisture sensors (cost), extra pressure or barrel thermocouples (duplicate), vibration-based moisture detection (no physical basis), any write to the press.

**Success criteria for the pilot**

- Every dryer heater trip or blower fault in the pilot is flagged before suspect resin reaches the barrel (bench test first: heater off, filter blocked).
- Predicted risk agrees with halogen readings: at least 90% of readings above 0.2% were flagged beforehand (to be confirmed on the pilot data, not assumed).
- False soft locks ≤ 1 per press per shift (SIG-06).
- Moisture-caused rejections (splay, brittleness, voids) drop measurably against the plant's own before-log, countersigned by their QC lead.

## 9. Open questions for the plant (answers change the kit)

1. **Dryer type and layout:** hot-air or desiccant? One per press or central? Does it display dew point? (Changes S1–S5 count and whether a dew-point transmitter is needed.)
2. **Controller interface:** which press brands/controllers, and do they have Euromap 63 or 77? (Decides whether §3c is available.)
3. **Current moisture practice:** do they own a moisture analyzer today? (If yes, V1 may already exist.)
4. **Rejection log by cause:** how much scrap is moisture vs heater vs other? (Decides whether S7 is worth adding.)

## Sources

- Thesis BOM sources for SCT-013, ESP32, ADS1115, SHT30, andon: see `Process Guardian (₹6,950) Product Effectiveness Thesis.md`
- [Robocraze — DS18B20 waterproof probe](https://robocraze.com/products/ds18b20-waterproof-digital-thermometer-sensor-probe)
- [Robocraze — DS18B20 probe, 3 m cable](https://robocraze.com/products/ds18b20-digital-temperature-sensor-probe-with-3m-waterproof-cable-7semi)
- [IndiaMART — moisture analyzer listings](https://m.indiamart.com/impcat/moisture-analyzer.html)
- [Tradeindia — halogen moisture analyzers](https://www.tradeindia.com/products/halogen-moisture-analyzers-5824989.html)
- [Aadarsh Technologies — Mettler Toledo moisture analyzers](https://m.indiamart.com/aadarshtechnologies/moisture-analyzers.html)
- [DuPont — Zytel processing guide](https://dupont.materialdatacenter.com/links/processing/Zytel.pdf)
- [Envalior — Akulon processing guide](https://plasticsfinder.envalior.com/api/document/proc/Akulon%C2%AE%20Ultraflow%20K-FG0/wgCLu8vYB/en)
- [Plastics Technology — allowable moisture in nylons, part 1](https://ptonline.com/articles/what-is-the-allowable-moisture-content-in-nylons-it-depends-part-1-)
- [ARBURG — guide values for injection moulding compounds](https://www.globalspec.com/reference/48196/203279/chapter-8-guide-values-and-processing-instructions-for-the-most-important-thermoplastic-injection-moulding-compounds)
- [OPC Foundation — EUROMAP 77](https://opcfoundation.org/markets-collaboration/plastics-and-rubber-machinery/)
- [OPC 40077 specification (read-only user role)](https://reference.opcfoundation.org/specs/OPC-40077/full)
- [Software Toolbox — Euromap 63 driver manual](https://help.softwaretoolbox.com/hubfs/faq/files/documentation/topserver/euromap63-manual.pdf?hsLang=en)
