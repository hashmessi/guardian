# Phase 03 Plan 03: Root Cause Attribution Engine & Honest Evidence Generator Summary

## Overview
Implemented the **Root Cause Evidence Engine** providing percentage-normalized contributor attribution summing strictly to 100.0%, empirical evidence generation, subsystem category aggregations, and strict epistemic honesty linting (ROOT-01, ROOT-02, ROOT-03).

## Key Deliverables Completed
1. **Schemas (`src/process_guardian/root_cause/schemas.py`)**:
   - `ContributorItem`: Single parameter attribution with display name, subsystem category, percentage contribution ($[0, 100]\%$), z-score, rolling slope, and honest evidence text.
   - `SubsystemAttribution`: Four-category breakdown (`thermal_pct`, `pressure_pct`, `timing_pct`, `material_pct`) summing strictly to 100.0%.
   - `RootCauseReport`: Complete cycle attribution report with primary contributor, category breakdown, ranked items, and honesty compliance flag.
2. **Evidence Generator (`src/process_guardian/root_cause/evidence.py`)**:
   - `EvidenceGenerator`: Generates empirical statements itemizing physical shifts, standard deviations from baseline, and rate-of-change per cycle.
   - Honest Epistemic Language Policy:
     - Enforces approved terms: `"likely contributor"`, `"observed evidence"`, `"modeled effect"`, `"confidence"`.
     - Strictly bans certainty claims: `"guaranteed cause"`, `"proven root cause"`, `"definite cause"`, `"definitely caused by"`.
3. **Root Cause Analyzer (`src/process_guardian/root_cause/analyzer.py`)**:
   - `RootCauseAnalyzer`: Formulates multivariate divergence scores $S_j = (|z_j|^{1.6} + 2.0 \frac{|\beta_j|}{\sigma_j}) \cdot (1.0 + 3.0 w_j)$.
   - Normalizes all scores so individual percentages and subsystem category percentages sum strictly to $100.0\%$.
4. **Unit Verification (`tests/test_root_cause.py`)**:
   - 3/3 tests green:
     - `test_ranked_contributors_sum_100` (exact 100.0% sum check across individual and category breakdowns)
     - `test_supporting_evidence_generation` (empirical numbers and thermal dominance validation)
     - `test_honest_epistemic_language` (banned phrase filter and compliance checks)
