# PROCESS GUARDIAN — FINAL UI SURGERY
## NO FEATURE EXPANSION

Implement the approved UI redesign from the industrial product audit.

The goal is NOT to add capability.

The goal is to make the existing Process Guardian capability immediately understandable to an automotive injection-molding / quality professional.

CORE RULE:

WHAT → WHY → ACTION → COST → RECOVERY → QC → CONTAINMENT → RELEASE

--------------------------------------------------
1. NAVIGATION
--------------------------------------------------

Replace the current 4 equal-weight tabs with exactly:

DETECT
DIAGNOSE
ACT & VERIFY

Do NOT create a fourth primary tab.

Counterfactual Replay must be embedded as a compact proof block inside ACT & VERIFY with an expandable detailed replay.

--------------------------------------------------
2. HEADER
--------------------------------------------------

Reduce the global header to:

PROCESS GUARDIAN
Injection Process Intelligence

Machine / mold / part / recipe / cycle context

SIMULATION · 2S STREAM
PROTOTYPE ADVISORY · NO PLC WRITE-BACK

Keep Reset Demo as a small secondary action.

REMOVE the primary:
Industrial Evidence
Decision Economics
Physical QC

Those become contextual links where needed.

--------------------------------------------------
3. SCREEN 1 — DETECT
--------------------------------------------------

Primary question:

"IS PRODUCTION SAFE RIGHT NOW?"

First visual must be a single process-state banner.

Example:

PROCESS DRIFT DETECTED
QUALITY RISK HIGH

Then show only the 3 primary PS02 process signals:

Barrel Temperature
Injection Pressure
Material Moisture

Each signal must show:

current value
direction/delta
normal/drift status

Cycle time remains secondary.

Make the process lifecycle a compact primary visual:

HEALTHY → DRIFT → RISK → ACTION → RECOVERY

Remove from primary screen:

Quality Contract table
Governance widget
Operational Context card
duplicate stability KPI
detector internals
economics
audit trail

Keep Quality Contract behind a secondary view.

--------------------------------------------------
4. SCREEN 2 — DIAGNOSE
--------------------------------------------------

Primary question:

"WHY IS THIS HAPPENING AND WHICH PRODUCTION IS AT RISK?"

Show:

- concise drift summary
- primary contributing signal
- short evidence explanation
- other signal states
- last verified good cycle
- suspect production window
- lead-time callout

Example:

PRIMARY CONTRIBUTOR
Barrel Temperature — Zone 3

Sustained deviation over 14 cycles.

Use evidence-based wording.

NEVER claim an unverified physical cause.

Do not state causal certainty from model attribution alone.

Move these to Evidence:

EWMA
CUSUM
Mahalanobis
Slope
full risk trajectory
confidence graphics
technical detector table

--------------------------------------------------
5. SCREEN 3 — ACT & VERIFY
--------------------------------------------------

Primary question:

"WHAT SHOULD WE DO, WHAT WILL IT COST, AND DID IT WORK?"

BEFORE ACTION:

Make recommended action the dominant visual.

Example:

REDUCE BARREL ZONE 3 BY 3°C

Then:

Why this action
Constraint status
Expected impact

Primary action:

APPLY CORRECTIVE ACTION

Do not use the word "Demo".

--------------------------------------------------
6. ECONOMICS
--------------------------------------------------

Use ONE economic model throughout the application.

Primary display:

NET BENEFIT OF ACTING
+₹X

Secondary:

Cost of acting
Expected exposure if waiting

Use plain business language.

Remove:

SIGNED DECISION VALUE
ECON-01
ECON-02
engineering formula labels

Clearly label:

MODELED ESTIMATE
CONFIGURABLE PLANT ASSUMPTIONS

All economic figures shown in different UI locations must reconcile.

--------------------------------------------------
7. CANDIDATE ACTIONS
--------------------------------------------------

Keep the existing optimization capability.

Do not put all candidate details above the recommendation.

Show:

Why this action?

4 feasible actions evaluated.

VIEW EVALUATED ACTIONS →

Expandable detailed candidate table.

--------------------------------------------------
8. AFTER ACTION
--------------------------------------------------

After applying the corrective action, transform the ACT section into:

RECOVERY IN PROGRESS

X / Y stable cycles

Risk before → after

Process stability before → after

Then:

QUALITY CHECK REQUIRED

Process stabilization is NOT equivalent to product-quality verification.

Require QC before release.

--------------------------------------------------
9. CONTAINMENT
--------------------------------------------------

Show a compact production disposition:

LAST VERIFIED GOOD
SUSPECT / HOLD
POST-RECOVERY

Clearly show the affected cycle range.

Release must remain locked until the QC gate passes.

--------------------------------------------------
10. COUNTERFACTUAL
--------------------------------------------------

Do not delete the existing counterfactual implementation.

Embed only a compact summary:

GUARDIAN OFF
X defective

GUARDIAN ON
Y defective

Suspect hold
A → B cycles

Add:

CONTROLLED SIMULATION

VIEW DETAILED REPLAY →

Keep the detailed replay in expandable/secondary view.

--------------------------------------------------
11. OPERATIONAL CHECKPOINTS
--------------------------------------------------

Keep only the PS02-relevant checks:

Recipe
Material moisture
Mold-release spray

Display as compact status.

Expand when a checkpoint actually requires operator action.

--------------------------------------------------
12. AUDIT
--------------------------------------------------

Keep immutable audit trail.

Display only:

AUDIT TRAIL · 10 EVENTS
View evidence chain →

Do not show the full event chain by default.

--------------------------------------------------
13. EVIDENCE LABELS
--------------------------------------------------

Fix every epistemic label.

Simulated telemetry must NOT say MEASURED.

Use:

SIMULATION
MODELED RISK
MODELED ESTIMATE
EXTERNAL EVIDENCE

Do not put large epistemic badges on every card.

Do not claim factory validation.

Do not claim real savings.

Do not claim causal certainty unless externally/experimentally verified.

--------------------------------------------------
14. REMOVE FROM PRIMARY UI
--------------------------------------------------

Remove:

L2 MEASURED
L3 INVARIANT
internal requirement codes
technical detector names
confidence arc
full technical detector table
duplicated economics
duplicated context
decorative KPIs
extra CTA buttons
"Apply Demo Intervention"

--------------------------------------------------
15. DO NOT CHANGE BACKEND
--------------------------------------------------

Preserve:

simulator
process fingerprint
drift engine
quality risk
root-cause logic
intervention optimizer
constraints
ABSTAIN
recovery verifier
QC gate
containment
state machine
API
storage
audit
validation suite

This is UI surgery, NOT an architecture rewrite.

--------------------------------------------------
16. FINAL USER TEST
--------------------------------------------------

Run the application from a fresh session.

Without developer explanation, verify that a first-time industrial user can answer:

1. What is happening?
2. Why?
3. What should I do?
4. What does it cost?
5. Did it recover?
6. What production is affected?
7. Can production be released?

If any answer requires navigating irrelevant technical information:

REMOVE / MERGE / HIDE.

Do not solve clarity problems by adding more content.

--------------------------------------------------
17. FINAL QUALITY BAR
--------------------------------------------------

The finished UI should feel:

CLEAN
BOLD
INDUSTRIAL
CALM
DECISIVE
EVIDENCE-DRIVEN

It should NOT feel:

TECH DEMO
AI DASHBOARD
ENGINEERING CONSOLE
ANALYTICS WALL
FEATURE SHOWCASE

The sophisticated implementation remains underneath.

The operator sees the decision.