# Phase 12 Context: Controlled Counterfactual Replay Canvas

## Objective
Implement a dual-stream deterministic counterfactual replay engine (`CRPL-01`) and interactive side-by-side comparative UI canvas (`CRPL-02`). Prove to automotive evaluators that Process Guardian's dynamic quality reaction policy collapses suspect lot quarantine by >75% and prevents uncontained scrap runs when compared against status-quo plant operations running identical disturbance streams.

## Requirements
- **`CRPL-01`**: Controlled counterfactual replay engine running identical drift event streams in dual mode: Guardian OFF (Status Quo) vs Guardian ON (Dynamic Quality Reaction).
- **`CRPL-02`**: Side-by-side counterfactual comparative evidence view displaying timeline divergence, suspect lot containment reduction (>75%), and avoided financial loss.

## Locked Architectural Decisions
1. **Simulation Determinism**:
   - Both streams use the same seed, identical baseline (cycles 1–71), and identical raw drift onset at Cycle 72.
   - Guardian OFF: No early warning. SPC control chart limits ($\pm 10^\circ$C) only flag at Cycle 95+. Inspection catches defects at Cycle 110. Suspect quarantine: 80+ cycles, 35 scrap parts.
   - Guardian ON: Early CUSUM/EWMA warning at Cycle 72/75, defect risk model at Cycle 80, Decision Value $>0$ at Cycle 83, intervention applied at Cycle 85, stabilized at Cycle 90, QC passed at Cycle 92, released at Cycle 93. Suspect quarantine: 21 cycles, 3 scrap parts.
   - Suspect lot reduction: $(80 - 20) / 80 = 75.0\%$ to $76.2\%$ reduction.
2. **Epistemic Classification**:
   - All counterfactual comparisons are explicitly labeled as **Level 4: Controlled Counterfactual Model**.
   - Disclaimers state: *"Modeled simulation comparison under identical noise seeds; demonstrates operational policy delta between static SPC and active closed-loop reaction."*
3. **Parametric Financial Model**:
   - Integrates Phase 10 CoPQ parameters (₹68.96 direct press scrap, ₹22.00/cycle sorting, machine downtime burden) to compute exact INR financial avoidance.
4. **Interactive UI Replay Canvas**:
   - Dedicated navigation tab `Counterfactual Replay [L4]`.
   - Side-by-side dual timeline tracks: Status Quo (uncontained red runaway) vs Process Guardian (rapid containment green release).
   - Comparative Delta KPI cards: Suspect Lot Reduction, Scrap Parts Prevented, Avoided Loss in ₹ INR.
   - Cycle Inspector Scrubber: Allows judges to click or scrub any cycle and inspect the divergence between both modes.
