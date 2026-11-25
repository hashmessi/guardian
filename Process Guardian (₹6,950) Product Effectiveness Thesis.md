# Process Guardian (₹6,950): Product Effectiveness Thesis

Nov 17, 2026 · @JK

Process Guardian stops heater and drying faults before bad parts are molded, and when drift does happen it quarantines about 6 parts instead of a shift. It does this with a ₹6,950 clamp-on kit that never touches the press. It measures the cause (heater current, dryer air), not the symptom (barrel temperature, finished parts), so it sees faults earlier, with fewer false alarms, at roughly 35% below the cheapest competing kit.

## The five claims

Each claim rests on a physical mechanism and has a test that can prove it wrong. None is proven on a plant yet; the status column says where each stands.

| # | Claim | Mechanism | Test that proves it | Status |
| --- | --- | --- | --- | --- |
| C1 | Sees heater failure earlier than a temperature sensor | Press controller hides a weak band by raising on-time; on-state current drops at once | One of two parallel elements off under a closed-loop controller: zone flagged within 5 cycles while temperature still reads in band | Designed (SIG-01) |
| C2 | Sees a drying fault before wet resin reaches the barrel | Dryer outlet air changes minutes after a heater trip; resin in the hopper is still dry | Dryer heater off on the bench: soft lock fires before the hopper residence time runs out | Designed (SIG-02) |
| C3 | The kit cannot harm or stop the press | Clamp-on CTs, isolated andon relay, no wire to the machine | Electrician inspection; kit unplugged mid-run leaves the press unaffected | Designed (EDGE-07) |
| C4 | Contains a fault to about 6 parts instead of a shift | Quarantine from detection minus barrel residence to the hold; release only after 5 stable cycles | Unit test of the 98–103 example; pilot quarantine counts vs the status-quo estimate | Logic exists; live test pending |
| C5 | Costs less per press than any competing hardware kit | 6 clamp-on CTs, ESP32, one probe | Costed BOM with supplier quotes | Retail estimate ₹6,950; quotes pending |

## C1 — Heater failure: measure the cause, not the symptom

A weak or burnt-out heater band is invisible to a temperature sensor at first, because the press's own controller compensates. A current clamp sees it the moment it happens.

A barrel zone is held at its setpoint by a closed-loop controller that switches the heaters on and off. When one band in a zone weakens, the controller simply keeps the remaining bands on longer. Zone temperature stays in band, so a thermocouple-based kit reports "normal". The fault surfaces only when the controller runs out of headroom, which is often after short shots or warp have started.

| Stage of a heater failure | What happens in the zone | Temperature-based kit sees | Process Guardian sees |
| --- | --- | --- | --- |
| 1. Band weakens or one element opens | Less heat per second while on | Nothing (temperature held) | On-state current drops |
| 2. Controller compensates | On-time rises to hold setpoint | Nothing (temperature held) | On-time rises; current × on-time pattern flags the zone |
| 3. Controller saturates | Heater on \~100%, zone still short of heat | Temperature starts to sag | Already flagged 1–2 stages earlier |
| 4. Cold zone affects melt | Short shots, warp, flow marks | Alarm, parts already made | Advisory issued, zone named, countdown shown |

This only holds if the kit measures on-state current and on-time separately. Average current is not enough: while the controller compensates, average power can stay almost flat. Both quantities are now written into the requirements (EDGE-03, SIG-01).

The signal is also large and nearly binary. An opened element removes a fixed fraction of the zone's current, so the threshold can sit far from normal noise, which keeps false alarms low.

## C2 — Moisture: catch the dryer, not the defect

Wet resin is caused by a dryer that stopped drying, so Process Guardian watches the dryer's outlet air and warns while the resin in the hopper is still dry.

The failure chain at a coastal plant (70–85% RH) runs: dryer heater trips or airflow drops → outlet air cools and gets wetter → resin in the hopper picks up moisture over the next residence time → wet resin reaches the barrel → splay, voids, brittle parts. A sensor in the barrel or a check on finished parts sees only the last step. The outlet probe sees the first step, minutes after it happens.

The lock is timed against hopper and barrel residence, so it fires before suspect resin is molded, and the quarantine window starts from the resin that was in the hopper when the dryer failed.

**Honest caveat: dryer type decides the signal.**

- **Desiccant dryers** produce air with a controlled low dew point. A rising outlet dew point is a strong, early signal.
- **Hot-air dryers**, common in MSME plants, just heat ambient air. Their outlet dew point follows the humid ambient air whatever the dryer does. On these the strong signal is outlet temperature (a heater trip), not dew point.

PA6 is the material where this matters most, because it absorbs water readily; virgin PP barely does. The pilot press should run PA6, and Ragam's dryer types still need to be confirmed.

## C3 — A kit that is reliable by construction

The kit's design removes the usual ways shop-floor sensors fail: loose mounts, heat damage, wiring into the machine, and silent data gaps.

| Failure mode in typical kits | How Process Guardian avoids it | Requirement |
| --- | --- | --- |
| Contact sensors loosen on a hot, vibrating barrel | Split-core CTs sit around cables in a cool panel; nothing touches hot or moving parts | EDGE-01 |
| Wiring into the press risks the machine and its warranty | No electrical connection to the press; andon on its own isolated relay | EDGE-07 |
| A dead kit stops or confuses the press | A failed kit means "no advisory", never "press stopped" | SAFE-01 |
| Wi-Fi drops lose data silently | 12-hour offline buffer, every cycle numbered, gaps reported on reconnect | EDGE-05 |
| A loose sensor looks like a process fault | Cross-sensor check: a reading near zero is tested against neighbouring zones; a sensor fault raises a maintenance ticket, never a production lock | SIG-03 |
| An unplugged sensor goes unnoticed | Per-sensor heartbeat; SENSOR\_FAULT within 3 cycles | EDGE-06 |

The cross-sensor check is not unique to us: the ₹10,700 ESP32 kit has one too. What we add is that a sensor fault can never lock production, so a bad clamp costs a maintenance visit, not output.

## C4 — Effective outcome: contain, verify, release

Detection alone doesn't cut scrap. Process Guardian turns an alert into a procedure the operator cannot skip, and limits the suspect lot to the cycles that could actually be affected.

1. **Soft lock and QC gate.** On a drying fault the operator tablet locks to a checklist: dryer temperature, moisture reading, purge check. Production view returns only after a compliant reading is logged. A failed reading keeps the lock; a supervisor override needs a PIN and a reason and is audited (GATE-01, GATE-02).
2. **Quarantine sized by barrel residence.** Suspect cycles run from (detection cycle − shots of material in the barrel) to the hold. In the worked example, detection at cycle 101 with 4 shots of residence and a hold at cycle 103 quarantines cycles 98–103: 6 parts, against the 30–50 a shift typically loses before visual discovery (GATE-03).
3. **Verified release.** Production is tagged VERIFIED only after 5 consecutive stable cycles (GATE-04).
4. **False-alarm budget.** At most 1 false soft lock per press per shift, measured in the pilot. A system that alarms often gets switched off, which is how most of these products fail (SIG-06).

**What one avoided incident is worth (modelled, to be replaced by Ragam's numbers):**

| Input | Value | Basis |
| --- | --- | --- |
| Parts lost per incident without Guardian | 40 shells | Strategy guide estimate (30–50) |
| Raw-material cost per shell | ₹450 | Strategy guide assumption; not verified |
| Loss per incident | ₹18,000 | 40 × ₹450 |
| Kit cost per press | ₹6,950 | BOM below |
| Incidents to pay back one kit | Less than 1 | ₹6,950 ÷ ₹18,000 = 0.39 |

The strategy guide's ₹2.1–3.8 lakh per month across 6 lines assumes 12–21 such incidents a month. That figure stays out of any pitch until Ragam's rejection log confirms the incident rate (PILOT-04).

## C5 — Cost: ₹6,950 per press

At single-unit retail prices the kit costs about ₹6,950 per press (range ₹5,824–₹13,048), for 5 heater zones, 1 pump motor and a dryer probe. Volume buying should bring it near ₹6,000; that is an assumption until supplier quotes arrive.

| Part | Qty | Typical (₹) | Range (₹) |
| --- | --- | --- | --- |
| SCT-013-030 split-core CT, heater zones | 5 | 2,250 | 1,875–3,070 |
| SHT30 IP67 temperature/humidity probe, dryer outlet | 1 | 899 | 899–1,999 |
| 3-tier 24 V andon light | 1 | 750 | 750–3,185 |
| PCB, burden resistors, terminals, cable (estimate) | 1 | 600 | 400–900 |
| IP65 enclosure and glands (estimate) | 1 | 550 | 400–900 |
| ESP32 dev board | 1 | 500 | 390–812 |
| 24 V power supply + 5 V converter (estimate) | 1 | 500 | 400–800 |
| SCT-013-100 split-core CT, pump motor | 1 | 450 | 340–600 |
| ADS1115 16-bit ADC | 2 | 300 | 250–532 |
| 4-channel relay (estimate) | 1 | 150 | 120–250 |
| **Total** |  | **6,949** | **5,824–13,048** |

The clamps are about 40% of the cost, so the kit is sized to the press: 3 zones instead of 5 saves about ₹900. Not included: the shared operator tablet (one per line), the electrician's install time and the monthly service fee.

| Solution | Hardware per press | What you get after the alert |
| --- | --- | --- |
| MoldSense | No hardware (phone) | Alerts from photos operators take; not real-time |
| **Process Guardian** | **₹6,950** | **Enforced QC gate, residence-sized quarantine, verified release** |
| ESP32 kit | ₹10,700 | Alert and drift countdown |
| Trevoga | ₹25,200 | Automatic shot diversion |
| DriftGuard | Not stated | Alerts |

Process Guardian is about 35% below the ₹10,700 kit and 72% below Trevoga. MoldSense is cheaper upfront; our case against it is real-time detection, and the QR recipe lock (OPS-03) matches its zero-hardware entry point.

## What we do not claim

The thesis is narrow on purpose; overclaiming is what loses a technical room.

- **Not full process visibility.** CTs cannot see melt pressure or moisture inside the melt. We cover the two failure chains that drive Ragam's scrap, heaters and drying; a pressure or thermocouple input can be added later.
- **Not proven on a plant.** Until the pilot, every claim is "designed for" and "to be measured". Bench numbers are the evidence available now.
- **No moisture detection from vibration and no crash detection.** Neither has a defensible basis; presses already have low-pressure mold protection.
- **No machine control.** The kit never writes to or stops the press. A machine-level stop, if ever wanted, is an OEM-installed contact, not our software.
- **No unique sensor-fault check.** Competitors have one too; our difference is that a sensor fault never locks production.

## How the thesis gets proven

Every claim has a bench test now and a plant test in the 4-week Ragam pilot; the thesis stands or falls on these.

**Bench (before the finals):**

- [ ] On-state current within ±3% of a reference clamp meter at 3 loads; on-time within ±2% (EDGE-03)
- [ ] One of two parallel elements off under a closed-loop controller: zone flagged within 5 cycles while temperature reads in band (SIG-01)
- [ ] Dryer heater off: soft lock fires before hopper residence runs out (SIG-02)
- [ ] Sensor unplugged: maintenance ticket within 3 cycles, production not locked (SIG-03, EDGE-06)
- [ ] Wi-Fi off 12 hours: 0 cycles lost, gap reported (EDGE-05)
- [ ] Costed BOM backed by supplier quotes at 10 and 100 units (EDGE-08)

**Pilot (one PA6 press, 2 weeks shadow + 2 weeks active):**

- [ ] Cycle count within ±2% of the press shot counter over 500+ cycles (EDGE-02)
- [ ] Install under 30 minutes, no PLC access (EDGE-01)
- [ ] False soft locks at or below 1 per press per shift (SIG-06)
- [ ] Rejection rate before vs after on heater and drying causes, countersigned by Ragam's QC lead (PILOT-03)
- [ ] ROI recalculated from Ragam's own incident rate and part cost (PILOT-04)

**Go / no-go:** scale to more presses only if targeted rejections fall measurably and false alarms stay within budget; otherwise fix and extend the pilot.

## Sources

Prices are Indian retail listings as found in search results on 2026-11-17, mostly including GST; rows marked "estimate" in the BOM were not looked up. Competitor prices and features come from their PS02 one-line pitches. Prices change often, so confirm with supplier quotes before ordering.

- [Robocraze — SCT-013 30A](https://robocraze.com/products/non-invasive-sct-013-30a-ac-sensor-split-core-current-transformer)
- [Zbotic — SCT-013-030](https://zbotic.in/product/sct-013-030-non-invasive-ac-current-clamp-sensor-30a/)
- [Electronicscomp — SCT-013-030](https://electronicscomp.com/sct-013-030-30a-non-invasive-ac-current-sensor-clamp-sensor)
- [Electropi — SCT-013-000 100A](https://www.electropi.in/sct-013-000-100a-non-invasive-ac-current-sensor-split-core-type-clamp-meter-sensor)
- [Robodo — 100A SCT-013](https://robodo.in/products/100a-sct-013-000-non-invasive-ac-current-sensor-split-core-current-transformer)
- [Probots — ESP32 WROOM-32 38-pin](https://probots.co.in/esp32-wroom-32-nodemcu-38-pin-micro-usb-development-board.html)
- [Robocraze — SmartElex ESP32](https://robocraze.com/products/smartelex-esp32-wroom-32-development-kit)
- [Probots — ADS1115](https://probots.co.in/ads1115-adc-16-bit-amplifier-4-channel-converter-module.html)
- [Probots — SHT30 IP67 probe](https://probots.co.in/sht30-temperature-humidity-sensor-module-probe-cable-waterproof-digital-capacitance-sensors-i2c-output.html)
- [IndiaMART — Orbit 24 V tower light](https://m.indiamart.com/orbittechnosolutions/tower-light.html)
- [Industrybuying — tower lights](https://www.industrybuying.com/industrial-automation-2325/towering-lights-18785)
