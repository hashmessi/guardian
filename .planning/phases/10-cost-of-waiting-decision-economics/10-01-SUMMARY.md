# Plan 10-01: Parametric Cost of Poor Quality (CoPQ) Engine — Summary

## Executed Work
- Implemented `CoPQParameters` and `CoPQBreakdown` Pydantic schemas in `src/process_guardian/economics/models.py`.
- Replaced flat ₹450 with granular shop-floor formulas:
  - Material scrap cost taking into account part shot weight (220g), cold runner scrap (8%), and regrind credit (25%).
  - Machine hourly burden allocated per cycle (₹1,650/hr on 24.0s cycle = ₹11.00/cycle).
  - Energy consumption allocated per cycle (18.5 kW * 24s/3600 * ₹9.80/kWh = ₹1.21/cycle).
  - Secondary containment sorting labor (₹22.00/part).
  - Downstream OEM warranty / assembly line stoppage penalty exposure (₹150.00/defect).
- Implemented `CoPQCalculator` in `src/process_guardian/economics/engine.py`.
- Created comprehensive test suite in `tests/test_copq_model.py` covering defaults, engineering polymers (PA66-GF30), zero-sorting edge cases, and bounds validation.

## Verification
- `pytest tests/test_copq_model.py`: 4/4 tests passed in 0.04s.
