<!-- GSD:project-start source:PROJECT.md -->
## Project

**Process Guardian**

Process Guardian is a vendor-neutral injection-molding intervention engine that detects temperature, pressure, moisture and operational drift early, predicts quality-contract risk, evaluates constrained corrective actions, recommends the minimum effective intervention, verifies recovery, and contains affected production — before process drift becomes uncontrolled scrap. Built for Indian automotive Tier-2/Tier-3 plastic injection molders under the Hack4Purpose PS02 problem statement.

**Core Value:** **The closed operational decision loop: detect drift → diagnose cause → evaluate constrained interventions → recommend minimum-cost action → verify recovery → contain affected production.** If everything else fails, this complete loop — from early detection through verified recovery and scrap containment — must work end-to-end in the demo scenario.

### Constraints

- **Timeline**: 10-day build window (23 Sep - 2 Oct 2026) — aggressive, requires daily exit conditions
- **Data source**: Software simulator only for prototype — no hardware dependency
- **Safety**: Read-only machine integration, no automatic PLC write-back, ABSTAIN mandatory
- **ML approach**: XGBoost/LightGBM with calibrated probabilities — no massive deep learning
- **Database**: SQLite for MVP — no cloud infrastructure first
- **Honesty**: All synthetic/modelled values clearly labeled as prototype results, never claimed factory results
- **Language**: "likely contributor", "evidence", "modeled effect", "confidence" — never "guaranteed cause" or "proven causal effect"
- **Tech stack**: Python (FastAPI backend), web frontend (React/Vite or similar), SQLite storage
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
