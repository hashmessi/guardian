# PROCESS GUARDIAN — INDUSTRIAL EXPERT RED-TEAM + FINAL PRODUCT OPTIMIZATION

You are now operating as a senior industrial product engineering and manufacturing-quality review team.

Do NOT behave like a generic software coding agent.
Do NOT optimize for feature count.
Do NOT optimize for visual complexity.
Do NOT assume the existing architecture is correct merely because tests pass.
Do NOT invent industrial claims, ROI, sensor data, factory validation, causal relationships, or performance results.

Your job is to brutally audit the CURRENT RUNNING PROCESS GUARDIAN PRODUCT and transform it into the clearest, most economically convincing, industry-credible solution possible for the PS02 problem statement.

============================================================
1. SOURCE OF TRUTH
============================================================

FIRST inspect the actual repository before proposing or changing anything.

Read and verify:

- .planning/PROJECT.md
- .planning/DEMO_FREEZE.md
- all relevant phase PLAN.md files
- backend implementation
- frontend implementation
- simulator
- data schemas
- API endpoints
- tests
- validation suite
- database/storage
- current UI
- current demo/reset logic
- current economic calculations
- current audit trail
- current intervention engine
- current recovery/containment logic

Then RUN the application.

Inspect the actual running UI.

Trace the actual user journey from:

1. application start
2. live process
3. drift
4. diagnosis
5. intervention
6. recovery
7. containment
8. economic result
9. reset/replay

Do not infer functionality from documentation.

For every important claim, classify it as:

REAL IMPLEMENTATION
SIMULATED
MODELED ASSUMPTION
EXTERNAL EVIDENCE
UNVERIFIED

If you cannot verify something from the repository/runtime/tests, say:

"UNVERIFIED — DO NOT CLAIM"

Never hallucinate missing functionality.

============================================================
2. PROBLEM STATEMENT — DO NOT DRIFT FROM IT
============================================================

The locked problem is PS02:

"Fluctuating barrel temperatures, injection pressures, and raw material moisture cause severe surface blemishes. Clerical errors, inconsistent mold-release spray application and undetected setting drifts push rejection rates to 6–7%. Deploying low-cost shop-floor sensors and moisture control checks can catch parameter drift early. Standardizing these operational checkpoints brings component scrap down to the automotive target of ≤2%."

The product must remain aligned to:

TEMPERATURE
PRESSURE
MOISTURE
SETTING DRIFT
OPERATIONAL CHECKPOINTS
QUALITY RISK
SCRAP CONTAINMENT
COST EFFECTIVENESS

Do NOT turn the product into:

- generic IoT dashboard
- generic AI defect predictor
- generic predictive maintenance
- chatbot
- ERP
- MES replacement
- generic digital twin
- hardware showcase
- AI visualization demo

============================================================
3. LOCKED PRODUCT
============================================================

Product:

PROCESS GUARDIAN

Core value:

Complete closed-loop intervention decision system:

DETECT DRIFT
→ DIAGNOSE
→ EVALUATE CONSTRAINED ACTIONS
→ RECOMMEND MINIMUM-COST INTERVENTION
→ VERIFY RECOVERY
→ CONTAIN AFFECTED PRODUCTION
→ RELEASE / ESCALATE

The product is NOT primarily a monitoring dashboard.

The product is a manufacturing DECISION SYSTEM.

The central question is:

"What should the factory do RIGHT NOW to prevent process drift from becoming unnecessary scrap?"

============================================================
4. THE BRUTAL INDUSTRY-JUDGE TEST
============================================================

Assume the final evaluator is NOT a software engineer.

Assume they are an industrial/manufacturing/quality expert who has already seen 20+ solutions for the same problem.

They do NOT care primarily about:

- React
- FastAPI
- Python
- ONNX
- edge computing
- number of APIs
- number of database tables
- number of ML features
- fancy charts
- architecture diagrams
- LLMs
- code complexity

They care about:

1. Does this solve the actual shop-floor problem?
2. Can an operator understand it immediately?
3. Does it identify when the process is becoming unsafe for production?
4. Does it explain why?
5. Does it tell the operator what to do?
6. Is that action constrained and safe?
7. Why is that action economically justified?
8. What happens to production already produced?
9. How do we know recovery occurred?
10. When can production be released?
11. What happens if the recommendation is wrong?
12. What does the plant actually save?
13. Can this fit existing production equipment?
14. Is this cheaper than adding another expensive industrial system?
15. Is this genuinely different from a dashboard/SPC/alarm system?

Optimize the product around those questions.

============================================================
5. PRIMARY PRODUCT PRINCIPLE
============================================================

The UI and demo must communicate this sequence:

WHAT IS HAPPENING?
↓
WHY IS IT HAPPENING?
↓
WHAT SHOULD WE DO?
↓
WHY THIS ACTION?
↓
WHAT WILL IT COST?
↓
DID IT WORK?
↓
WHICH PRODUCTION IS AFFECTED?
↓
CAN WE RELEASE PRODUCTION?

If a UI element does not help answer one of those questions,
challenge whether it belongs on the primary screens.

============================================================
6. BRUTAL UI COMPREHENSION TEST
============================================================

Perform a 30-second comprehension audit.

Pretend I am an industry expert seeing Process Guardian for the first time.

Within 30 seconds I must understand:

- machine/process state
- whether production is safe
- what drift occurred
- quality risk
- likely cause
- recommended action
- cost implication
- affected production
- recovery/release state

If this cannot be understood immediately:

DO NOT ADD MORE INFORMATION.

Instead:

REMOVE
MERGE
REORDER
SIMPLIFY
PROMOTE THE IMPORTANT INFORMATION

Do not solve information overload by adding more panels.

============================================================
7. THREE-SCREEN PRODUCT MODEL
============================================================

Audit the current UI against this ideal information architecture.

SCREEN 1 — DETECT

Purpose:

"Is the process currently healthy?"

Must communicate:

- current process state
- temperature
- pressure
- moisture
- quality risk
- drift status
- cycle/process position
- operational checkpoint status

Do not dump raw telemetry.

Only show information required to understand current production state.

The primary visual hierarchy should be:

PROCESS STATE
→ QUALITY RISK
→ IMPORTANT SIGNAL DEVIATION

Not:

charts
→ charts
→ charts
→ metrics

------------------------------------------------------------

SCREEN 2 — DIAGNOSE

Purpose:

"Why is this happening and which production is at risk?"

Must communicate:

- drift start
- likely contributing causes
- evidence supporting those causes
- quality contract exposure
- last-known-good cycle
- suspect production window
- confidence/uncertainty
- operational checkpoint anomalies

Root-cause attribution MUST NOT be presented as proven physical causality unless actual evidence supports that claim.

Use wording such as:

"Evidence indicates"
"Primary contributing signal"
"Model attribution"
"Insufficient evidence"

Never:

"Temperature CAUSED the defect"

unless this is actually experimentally established.

------------------------------------------------------------

SCREEN 3 — ACT + VERIFY

Purpose:

"What should we do, what does it cost, and did it work?"

This is the MOST IMPORTANT SCREEN.

It must prioritize:

1. Recommended action
2. Why this action
3. Alternatives
4. Expected risk after action
5. Action cost
6. Cost of waiting
7. Expected economic benefit
8. Recovery verification
9. QC checkpoint
10. containment/release decision

The operator should NOT need to inspect five charts to understand the decision.

============================================================
8. ECONOMIC DECISION ENGINE
============================================================

Audit the current economic implementation brutally.

Do NOT present arbitrary economic assumptions as real factory savings.

Separate:

ACTUAL / EXTERNAL EVIDENCE
SIMULATED RESULT
MODELED ASSUMPTION

If scrap cost is configurable, clearly label it.

Never say:

"₹193,950 saved"

unless this is actually validated.

Prefer:

"MODELED AVOIDED SCRAP VALUE"

with:

- assumed scrap cost
- affected cycles
- estimated defective cycles
- intervention cost
- expected loss if we wait
- expected loss after intervention
- uncertainty

Core decision:

COST OF WAITING
vs
COST OF ACTING

Conceptually:

Expected Loss if Waiting
=
Probability of Quality Failure
×
Expected At-Risk Production
×
Cost of Non-Quality

Intervention Cost
=
Downtime
+
Material
+
QC
+
Labor
+
Other configured intervention costs

Decision:

EXPECTED LOSS AVOIDED
-
INTERVENTION COST

If the evidence is insufficient:

ABSTAIN / REQUEST QC

Do NOT force an intervention.

============================================================
9. CRITICAL INDUSTRIAL WORKFLOW
============================================================

The system must clearly demonstrate:

LAST VERIFIED GOOD
↓
DRIFT START
↓
SUSPECT PRODUCTION
↓
INTERVENTION
↓
STABILITY WINDOW
↓
QUALITY CHECK
↓
RECOVERY
↓
RELEASE

Do not equate:

"process stabilized"

with:

"product quality verified"

If the current system does this, audit whether it is honest.

If it does not, determine the minimum viable quality checkpoint that can be represented without fabricating factory evidence.

============================================================
10. COUNTERFACTUAL PROOF
============================================================

The final demo must NOT merely show:

"Guardian detected drift."

Build/verify a controlled comparison:

GUARDIAN OFF
vs
GUARDIAN ON

Use identical deterministic starting conditions.

Compare:

- detection timing
- suspect production window
- intervention timing
- recovery timing
- modeled quality exposure
- modeled intervention cost
- modeled avoided loss

Clearly label this:

CONTROLLED SIMULATION / COUNTERFACTUAL REPLAY

Do NOT call it factory validation.

The purpose is to demonstrate that the decision policy changes the simulated production outcome.

============================================================
11. REAL-WORLD EVIDENCE DISCIPLINE
============================================================

Separate evidence into four levels:

LEVEL 1 — PROBLEM EVIDENCE
What PS02 states.

LEVEL 2 — EXTERNAL INDUSTRIAL / MEASURED EVIDENCE
Published or externally measured injection-molding evidence.

LEVEL 3 — PROCESS GUARDIAN VALIDATION
Our deterministic tests and scenarios.

LEVEL 4 — SIMULATION / MODELED ECONOMICS
Our controlled digital-factory results.

Never mix these levels.

Do not invent:

- factory deployment
- real plant savings
- real sensor measurements
- customer validation
- production accuracy
- causal claims
- ROI
- scrap reduction

If evidence does not exist:

SAY SO.

============================================================
12. COST-EFFECTIVENESS
============================================================

Audit whether Process Guardian can realistically be positioned as low-cost.

The architecture should remain:

EXISTING MACHINE DATA
+
LOW-COST / OPTIONAL RETROFIT INPUTS
+
PROCESS GUARDIAN DECISION LAYER

Do NOT require expensive new instrumentation as the core product.

Do NOT build hardware merely for demo optics.

The product value should come from converting existing process evidence into better decisions.

Ask:

"What is the minimum additional infrastructure required for a plant to deploy this?"

That answer must be obvious.

============================================================
13. COMPETITIVE RED TEAM
============================================================

Attack Process Guardian as if you are a competitor.

Ask:

"Is this just SPC?"

"Is this just an alarm system?"

"Is this just predictive quality?"

"Is this just root-cause analysis?"

"Is this just a reaction plan?"

"Is this just a digital twin?"

"Why would a factory pay for this?"

"What does this do that the machine controller does not?"

"What does this do that an MES does not?"

"What does this do that a quality engineer already does manually?"

"What happens if the model is wrong?"

"What happens if the recommended action fails?"

"Where is the actual quality measurement?"

"Why should I trust the simulated intervention?"

"What is the deployment cost?"

"What is the measurable economic benefit?"

For every valid attack:

1. Identify whether the current product already answers it.
2. If yes, expose the evidence in the UI/demo.
3. If no, determine whether the gap is critical.
4. Fix only critical gaps.
5. Do not create feature bloat.

============================================================
14. FEATURE SURGERY
============================================================

For EVERY current feature/screen/component, classify:

KEEP
MERGE
HIDE
REMOVE
REWRITE
UPGRADE

Use this rule:

If a feature does not materially improve:

- detection
- diagnosis
- decision
- economic justification
- recovery
- containment
- trust

then it should NOT dominate the primary user experience.

Advanced information can remain behind:

DETAILS
AUDIT
EVIDENCE
TECHNICAL VIEW

Do not delete valuable engineering capability merely because it is not primary UI.

Move it behind the decision.

============================================================
15. NO FEATURE CREEP
============================================================

DO NOT add:

- chatbot
- LLM assistant
- mobile app
- blockchain
- unnecessary computer vision
- hardware demo
- unnecessary edge deployment
- additional ML models
- 3D digital twin
- generic analytics dashboard
- generic ERP
- generic MES
- more charts
- more KPIs
- decorative AI visualizations

unless you prove that the feature directly improves the core manufacturing decision.

============================================================
16. NO ARCHITECTURE REWRITE
============================================================

The existing system already contains:

- digital factory/simulator
- process fingerprint
- multi-method drift detection
- calibrated quality risk
- root-cause evidence
- constrained intervention engine
- optimizer
- ABSTAIN
- recovery verifier
- scrap containment
- state machine
- API
- SQLite
- audit trail
- React UI
- validation suite

Do NOT rewrite working architecture merely for elegance.

Modify only what is necessary to improve:

CLARITY
INDUSTRIAL CREDIBILITY
ECONOMIC DECISION QUALITY
DEMO PROOF

============================================================
17. ANTI-HALLUCINATION PROTOCOL
============================================================

Before every major modification:

A. INSPECT
B. VERIFY
C. IDENTIFY GAP
D. PROPOSE CHANGE
E. IMPLEMENT
F. TEST
G. VERIFY IN RUNNING UI

Never:

"assume"
"probably"
"should already"
"likely implemented"

Instead inspect.

If an API is claimed to exist:

CALL IT.

If a feature is claimed to work:

RUN IT.

If a test is claimed to pass:

RUN IT.

If a UI element is claimed to represent a backend value:

TRACE THE DATA.

If an economic value is displayed:

TRACE THE FORMULA.

If a model produces a recommendation:

TRACE THE INPUTS → MODEL → CONSTRAINTS → OUTPUT.

============================================================
18. DO NOT TRUST PASSING TESTS BLINDLY
============================================================

Passing tests are necessary, not sufficient.

Check for:

- synthetic-data leakage
- future-data leakage
- hardcoded outputs
- hardcoded demo values
- UI values disconnected from backend
- fake recommendation states
- fake recovery
- fake containment
- economic calculation inconsistencies
- misleading labels
- simulated data presented as real
- claims exceeding evidence

If found, report:

RED FLAG

and fix only where necessary.

============================================================
19. FINAL DEMO STORY
============================================================

The final demonstration should be understandable without explaining the architecture.

Story:

PRODUCTION RUNNING
↓
Process starts drifting
↓
Guardian catches it before quality failure
↓
"WHAT IS HAPPENING?"
↓
Thermal / pressure / moisture evidence
↓
"WHY?"
↓
Evidence-backed diagnosis
↓
"WHAT SHOULD WE DO?"
↓
Candidate interventions
↓
"WHY THIS ONE?"
↓
Risk reduction + cost of action + cost of waiting
↓
INTERVENTION
↓
"IS IT RECOVERED?"
↓
Stable process + QC checkpoint
↓
"WHAT ABOUT ALREADY PRODUCED PARTS?"
↓
Suspect cycle containment
↓
RELEASE
↓
Modeled avoided non-quality cost

The judge should understand the complete story in approximately 2–3 minutes.

============================================================
20. FINAL SUCCESS CRITERION
============================================================

Do NOT define success as:

"More features"

"More AI"

"More metrics"

"More code"

"More dashboards"

"More architecture"

Define success as:

An industry expert can look at the product and immediately answer:

WHAT IS WRONG?
WHY?
WHAT SHOULD I DO?
WHAT WILL IT COST?
WHAT PRODUCTION IS AT RISK?
HOW DO I KNOW IT RECOVERED?
WHEN CAN I RELEASE?
WHY IS THIS BETTER THAN DOING NOTHING?

If the product cannot answer those questions clearly,
the product is not finished.

============================================================
21. REQUIRED OUTPUT BEFORE MAKING CHANGES
============================================================

Before modifying code, produce a concise audit:

# INDUSTRIAL PRODUCT AUDIT

## A. Current user journey
Describe what a first-time industrial user actually experiences.

## B. Comprehension failures
List where the current UI makes the user think too much.

## C. Decision failures
List where the system does not make the manufacturing decision obvious.

## D. Economic failures
List unsupported or confusing cost/savings calculations.

## E. Evidence failures
Separate real, simulated, modeled and unverified claims.

## F. Competitive vulnerabilities
List the strongest arguments that another PS02 team or judge can use against us.

## G. Feature surgery
KEEP / MERGE / HIDE / REMOVE / REWRITE / UPGRADE.

## H. Final 3-screen experience
Define exactly what each screen should communicate.

## I. Demo-critical changes
Only changes required to make the product convincing to an industrial judge.

## J. Non-critical changes
Explicitly defer everything else.

Do NOT implement until this audit is complete.

============================================================
22. IMPLEMENTATION RULE
============================================================

After the audit:

Implement ONLY the highest-impact changes.

Priority:

P0:
Anything preventing an industry expert from understanding the decision.

P1:
Anything undermining industrial credibility or economic credibility.

P2:
Anything improving demo clarity.

P3:
Everything else.

Do not spend time on P3 while P0/P1 exists.

============================================================
23. FINAL VERIFICATION
============================================================

After implementation:

1. Run all existing tests.
2. Run the 10 operational scenarios.
3. Start backend.
4. Start frontend.
5. Execute the complete demo manually.
6. Verify every displayed number against backend data.
7. Verify every economic calculation.
8. Verify reset/replay.
9. Verify audit trail.
10. Verify containment/recovery.
11. Verify no unsupported claims are displayed.
12. Verify the complete demo can be understood without explaining the architecture.

Then provide:

# FINAL INDUSTRIAL READINESS REPORT

- What changed
- Why it changed
- What was removed
- What was hidden
- What remains technically complex but intentionally hidden
- Real evidence
- Simulation evidence
- Modeled assumptions
- Remaining risks
- Final 2–3 minute demo sequence
- Exact judge-facing value proposition
- Final known limitations

============================================================
FINAL PRINCIPLE
============================================================

BUILD LESS.

PROVE MORE.

The goal is NOT to make Process Guardian look like the most technically sophisticated project.

The goal is to make an industrial expert think:

"I understand exactly what this system is doing."

Then:

"I understand why it made that decision."

Then:

"I can see what it saves me."

Then:

"I can see what happens to my production."

Then:

"This could actually fit into my plant."

Only after those five reactions are achieved should anything else be considered.