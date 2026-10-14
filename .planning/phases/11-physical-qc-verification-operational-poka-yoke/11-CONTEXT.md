# Phase 11: Physical QC Verification & Operational Poka-Yoke — Context

**Gathered:** 2026-10-02  
**Status:** Locked for Planning & Execution  
**Target Requirements:** QCHK-01, QCHK-02, CNTN-05

<domain>
## Phase Boundary
Deliver the closed-loop Physical Quality Control (QC) verification gate, shop-floor operational poka-yoke checkpoints, and physical scrap containment boundary visualization for automotive injection molders.
Downstream components require:
1. State machine transition to `MANDATORY_QC_CHECKPOINT` post-parameter stabilization, refusing `RELEASE` until physical Critical-To-Quality (CTQ) measurements (part weight in grams within tolerance, visual blemish inspection pass-fail, inspector sign-off) are recorded.
2. PS02 shop-floor operational checkpoints engine: recipe verification lock, resin moisture batch sign-off, and mold-release spray interval tracking.
3. Physical scrap containment boundary card explicitly tracing cycle milestones: Last Verified Good, Drift Start, Suspect Lot, Action Applied, Stabilized, QC Passed, and Lot Release.
4. REST API endpoints and UI panels for physical QC submission and containment boundary display.
</domain>

<decisions>
## Implementation Decisions

### 1. Mandatory QC Checkpoint (QCHK-01)
- **D-01:** State Machine Extension:
  - Add `MANDATORY_QC_CHECKPOINT = "MANDATORY_QC_CHECKPOINT"` to `ProcessState`.
  - Allowed transitions:
    - `RECOVERY_CHECK -> MANDATORY_QC_CHECKPOINT`
    - `MANDATORY_QC_CHECKPOINT -> RELEASE` (on recorded CTQ PASS)
    - `MANDATORY_QC_CHECKPOINT -> DIAGNOSING` (on recorded CTQ FAIL)
    - Preserve `RECOVERY_CHECK -> RELEASE` for backward compatibility in mock automated benchmarks.
- **D-02:** CTQ Measurement Contract:
  - Part weight: nominal 220.0g $\pm 1.5$g (218.5g to 221.5g).
  - Visual inspection: sink mark depth $< 0.10$mm, flash = False, burn marks = False, short shot = False.
  - Inspector metadata: `inspector_id` (e.g., `QC-402`), `sample_cycle`, `timestamp`.
  - Poka-Yoke rule: Attempting to call `/api/recovery/release` or transitioning to `RELEASE` without passing recorded QC record raises 400 Bad Request error.

### 2. PS02 Operational Checkpoints (QCHK-02)
- **D-03:** 3 Shop-Floor Checkpoints:
  1. **Recipe Verification Lock**: Compare current machine parameters (temperatures, holding pressures, cooling times) against master recipe `R-12`. Returns `VERIFIED_LOCKED` or `UNAUTHORIZED_OVERRIDE` with delta list.
  2. **Resin Moisture Batch Sign-Off**: Checks resin moisture $\le 0.15\%$ (grounded in Fraunhofer benchmark). If moisture $> 0.15\%$ or sign-off missing, status is `BLOCKED_DRYING_REQUIRED`.
  3. **Mold-Release Spray Interval**: Tracks cycle count since last spray application against scheduled interval (50 cycles). If overdue $> 60$ cycles, status is `SPRAY_OVERDUE`.
- **D-04:** Unified Clearance:
  - Overall operational clearance is only granted when all 3 checkpoints pass.

### 3. Physical Containment Boundary Card (CNTN-05)
- **D-05:** Physical cycle milestones tracked and displayed:
  - `Last Verified Good`: Cycle $N_{good}$
  - `Drift Start Detected`: Cycle $N_{drift}$
  - `Suspect Lot Quarantine Window`: $[N_{drift}, N_{applied}]$
  - `Corrective Action Applied`: Cycle $N_{applied}$
  - `Process Stabilized`: Cycle $N_{stabilized}$
  - `Physical QC Passed`: Cycle $N_{qc}$
  - `Lot Release`: Cycle $N_{release}$
- **D-06:** UI Presentation:
  - `ContainmentBoundaryCard.jsx`: Timeline milestone track with clear visual status tags (Green Good, Red Suspect Quarantine, Orange Applied, Blue Stabilized, Emerald Released).
  - `QCCheckpointModal.jsx`: Modal for operator/inspector to record physical CTQ part weight and visual check.
  - `OperationalCheckpointsCard.jsx`: Checklist card for the 3 PS02 shop-floor gates.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/REQUIREMENTS.md` §Category 3: Quality Checkpoint & Operational Poka-Yoke (QCHK-01, QCHK-02)
- `.planning/REQUIREMENTS.md` §Category 5: Physical Scrap Containment Boundary (CNTN-05)
- `src/process_guardian/state_machine/engine.py` (State machine transition graph)
- `src/process_guardian/recovery/verifier.py` (Parameter recovery verifier)
- `src/process_guardian/containment/engine.py` (Scrap containment engine)
</canonical_refs>
