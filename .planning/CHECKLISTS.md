# v2.0 Checklists — Plant-Ready Guardian

Operational checklists for taking Process Guardian from simulator to live plants. Requirement IDs refer to `REQUIREMENTS.md`. Tick only with evidence (photo, log, test output, signature).

---

## 1. Before anything else (long-lead items, start this week)

- [ ] Ask Ragam for: rejection log by cause for the last 3 months, list of presses (tonnage, controller age), resins run per press, dryer type per press (PILOT-01, PILOT-04)
- [ ] Pick the pilot press: PA6 part, has a hopper dryer, has a history of splay/brittleness rejects
- [ ] Draft the pilot agreement (scope, data use, no machine writes, who owns the data) and send it (PILOT-01)
- [ ] Get the resin datasheets for every pilot material; record drying temperature, time and max moisture (SIG-05)
- [ ] Request supplier quotes at 10 and 100 units for: ESP32 module, split-core CTs (heater-zone and pump-motor ranges), dryer temp/RH probe, relay + 3-colour andon, enclosure, isolated PSU (EDGE-08)

## 2. Edge kit bench bring-up

- [ ] CT readings match a reference clamp meter within ±3% at 3 loads (EDGE-03)
- [ ] Pump-motor CT pattern counts cycles on a bench load profile; firmware logs cycle start/end (EDGE-02)
- [ ] Dryer probe vs reference hygrometer over 24 h: ±1 °C, dew point ±2 °C (EDGE-04)
- [ ] Wi-Fi off for 12 h → 0 lost cycles, gap reported on reconnect (EDGE-05)
- [ ] Unplug each sensor → SENSOR_FAULT within 3 cycles (EDGE-06)
- [ ] Andon relay isolated from mains/press, checked by electrician (EDGE-07)
- [ ] Costed BOM ≤ ₹6,000 with quotes committed (EDGE-08)
- [ ] Record 3 bench sessions (normal, heater element off, dryer off/humid) as replay files (LIVE-06)

## 3. Software live-path readiness

- [ ] New signals accepted and bounds-checked on `/cycles` (LIVE-01)
- [ ] Live baseline fits from 30–50 live cycles; simulator baseline not used in LIVE mode (LIVE-02)
- [ ] Heater + dryer-only payload runs the whole loop (LIVE-04)
- [ ] LIVE / SIMULATOR badge on every screen (LIVE-05)
- [ ] Replay of each recorded bench session gives identical transitions twice (LIVE-06)
- [ ] Signature A flags the right zone in ≤5 cycles on the heater-off recording (SIG-01)
- [ ] Signature B locks on the dryer-off recording (SIG-02)
- [ ] Sensor unplugged → maintenance ticket, not production lock (SIG-03)
- [ ] No path from lock to production without a compliant reading (GATE-01)
- [ ] Auth on every endpoint, CORS restricted, `/containment/release` needs supervisor (FLEET-01)
- [ ] Full existing test suite still green

## 4. Pilot install day (Ragam press)

- [ ] Signed pilot agreement on file (PILOT-01)
- [ ] Licensed electrician present; panel isolation procedure followed (COMM-02)
- [ ] CTs on heater-zone feeds and pump motor; no PLC access; time recorded (target ≤30 min) (EDGE-01)
- [ ] Dryer probe at outlet; andon mounted in operator view
- [ ] Device claimed to plant/press by QR (FLEET-03)
- [ ] Shot counter photographed at start and end of day for the cycle-count check (EDGE-02)
- [ ] Tablet on the press, Tamil/English checked by the operator (OPS-01)
- [ ] Recipe QR codes printed and fixed to the mold (OPS-03)
- [ ] Live baseline captured for the running recipe (LIVE-02)
- [ ] Shadow mode on (no alerts shown to the operator)

## 5. Pilot weeks

- [ ] Weeks 1–2 shadow: daily rejection log by cause from Ragam QC; Guardian events logged but hidden (PILOT-02)
- [ ] Mid-pilot review: tune Signature A/B thresholds on shadow data, freeze them before active weeks
- [ ] Weeks 3–4 active: locks, checklists, quarantines live; false soft locks counted per shift (SIG-06)
- [ ] Every quarantine report exported and checked by the QC lead (GATE-05)
- [ ] Shift handover summaries generated (OPS-04)
- [ ] Any sensor fault handled as a maintenance ticket, not a lock (SIG-03)

## 6. Evidence pack (go / no-go for selling)

- [ ] Rejection % before vs after, by cause (PILOT-03)
- [ ] Incidents caught early, with lead time in cycles
- [ ] False alarms per press per shift ≤1 (SIG-06)
- [ ] Parts quarantined per incident vs status-quo estimate
- [ ] ROI calculated from Ragam's own incident rate and part cost; every assumption visible (PILOT-04)
- [ ] QC lead countersigns the numbers (PILOT-03)
- [ ] **Go** if rejection fell measurably on the targeted causes and false alarms ≤1/shift; otherwise fix and extend the pilot, don't scale

## 7. Plant go-live (each new plant)

- [ ] Tenant created; users and roles assigned (FLEET-01, FLEET-02)
- [ ] Devices claimed by QR; per-device credentials issued (FLEET-03)
- [ ] OTA channel set; current firmware signed (FLEET-05)
- [ ] TLS verified from plant network (FLEET-06)
- [ ] Per-recipe limits loaded from datasheets (SIG-05)
- [ ] Live baselines captured per mold/recipe (LIVE-02, LIVE-03)
- [ ] Plant appears in fleet view with device health (FLEET-04)
- [ ] Operators trained (30 min) on lock, checklist, release
- [ ] SLA, spares and support contacts handed over (COMM-03)
- [ ] Backup restore rehearsed for the tenant (FLEET-02)

## 8. Finals / customer demo

- [ ] Live kit on the table: CT on a heater or kettle cable, probe near a humidifier
- [ ] Heater off → Signature A advisory naming the zone, with countdown
- [ ] Humid air → Signature B soft lock → failed reading keeps lock → compliant reading → 5-cycle release
- [ ] Quarantine window shown as "6 parts, not 50", with the residence calculation
- [ ] Unplug a sensor → maintenance ticket, production keeps running (shows the cross-sensor check)
- [ ] Price slide: per-press cost and 12-month TCO vs ₹10,700 kit, Trevoga, MoldSense (COMM-01)
- [ ] Replay file ready as fallback if the live kit fails (LIVE-06)
- [ ] Every number on screen labelled LIVE, REPLAY or MODELLED
