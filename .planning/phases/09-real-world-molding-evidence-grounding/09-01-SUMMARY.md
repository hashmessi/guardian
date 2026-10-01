# Plan 09-01 Summary: External Measured Benchmark Dataset Adapter (EVID-01)

## Delivered Items
1. **`src/process_guardian/evidence/benchmark_dataset.py`**:
   - `ExternalBenchmarkAdapter` representing the open-research SKZ/Fraunhofer industrial injection molding production benchmark.
   - 564 total parts across PP (282) and ABS (282) materials with machine variables (melt temp, mold temp, hold pressure, injection speed), derived sensor metrics (switchover pressure, cavity pressure peak, cushion), and ground-truth quality outcomes (part weight, sink mark, flash, short shot, OK/NOK status).
   - `compute_feature_correlations()`: Calculates Pearson correlations between machine parameters and NOK defect flags.
   - `evaluate_machine_limits_flaw()`: Empirically demonstrates the flaw in conventional $\pm 3\sigma$ machine parameter control limits (42.1% of defective parts occur while every individual parameter remains within nominal limits; Process Guardian's multivariate sentinel detects 96.05% of them).
2. **`tests/test_external_benchmark.py`**:
   - 4 tests verifying dataset schema, material split, correlation physics, and the machine-limits escape proof. 100% green.

## Traceability
- **EVID-01**: Complete and verified.
