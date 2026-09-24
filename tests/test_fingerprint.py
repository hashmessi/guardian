"""Unit tests for Process Fingerprint Engine and Context Baseline Storage (FPRN-01, FPRN-02, FPRN-03)."""

import pytest
import numpy as np
from pathlib import Path

from process_guardian.core.types import MachineContext, RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.fingerprint.store import FingerprintStore
from process_guardian.core.constants import NOMINAL_PP_PARAMS


def test_fingerprint_builder_and_envelope():
    """Verify context-specific baseline fitting and empirical operating envelope computation (FPRN-01)."""
    sim = InjectionMoldingSimulator(seed=42)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(60)]

    builder = FingerprintBuilder()
    fp = builder.fit(records)

    assert fp.sample_count == 60
    assert fp.context.machine_id == "IMM-01"
    assert "barrel_temp_z3" in fp.signal_stats
    assert "injection_pressure" in fp.signal_stats

    # Check statistical precision
    z3_stat = fp.signal_stats["barrel_temp_z3"]
    assert abs(z3_stat.mean - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 0.4
    assert 0.15 < z3_stat.std < 0.85
    assert z3_stat.min_val <= z3_stat.p01 <= z3_stat.mean <= z3_stat.p99 <= z3_stat.max_val

    # Check operating envelope bounds (mu +/- 3*sigma)
    z3_env = fp.operating_envelopes["barrel_temp_z3"]
    assert abs(z3_env.lower_limit - (z3_stat.mean - 3.0 * z3_stat.std)) < 0.01
    assert abs(z3_env.upper_limit - (z3_stat.mean + 3.0 * z3_stat.std)) < 0.01

    # Check multivariate structure
    assert len(fp.mean_vector) == 15
    inv_cov = np.array(fp.inv_cov_matrix)
    assert inv_cov.shape == (15, 15)
    assert not np.isnan(inv_cov).any()
    assert not np.isinf(inv_cov).any()


def test_context_specific_baselines():
    """Verify that different contexts produce distinct baselines, avoiding global thresholds (FPRN-02)."""
    builder = FingerprintBuilder()

    # Context A: Polypropylene standard housing
    ctx_a = MachineContext(machine_id="IMM-01", recipe_id="RECIPE-PP-V2.1")
    sim_a = InjectionMoldingSimulator(seed=10, context=ctx_a)
    pipe_a = TelemetryPipeline(context=ctx_a)
    records_a = [pipe_a.process(sim_a.step()) for _ in range(30)]
    fp_a = builder.fit(records_a)

    # Context B: Custom engineering recipe with modified parameters
    ctx_b = MachineContext(machine_id="IMM-02", recipe_id="RECIPE-ABS-V1", recipe_version="1.0")
    sim_b = InjectionMoldingSimulator(seed=20, context=ctx_b)
    pipe_b = TelemetryPipeline(context=ctx_b)
    # Inject offset for Context B
    sim_b.inject_event("intervention_temp_offset", cycle=1, severity=1.0, params={"delta_temp_z3": 12.0})
    records_b = [pipe_b.process(sim_b.step()) for _ in range(30)]
    fp_b = builder.fit(records_b)

    # Assert distinct context keys
    assert fp_a.context_key != fp_b.context_key

    # Assert distinct baseline means and operating envelopes
    mean_a = fp_a.signal_stats["barrel_temp_z3"].mean
    mean_b = fp_b.signal_stats["barrel_temp_z3"].mean
    assert abs(mean_b - mean_a) > 8.0
    assert fp_a.operating_envelopes["barrel_temp_z3"].upper_limit < fp_b.operating_envelopes["barrel_temp_z3"].lower_limit


def test_fingerprint_storage_and_retrieval(tmp_path: Path):
    """Verify storage and retrieval of fingerprints per context with JSON persistence (FPRN-03)."""
    sim = InjectionMoldingSimulator(seed=55)
    pipeline = TelemetryPipeline()
    records = [pipeline.process(sim.step()) for _ in range(35)]
    fp = FingerprintBuilder().fit(records)

    store = FingerprintStore(storage_dir=tmp_path)
    store.save(fp)

    # Retrieve from in-memory cache
    cached_fp = store.get(fp.context_key)
    assert cached_fp is not None
    assert cached_fp.fingerprint_id == fp.fingerprint_id

    # Retrieve using EnrichedContext object
    ctx_fp = store.get(fp.context)
    assert ctx_fp is not None
    assert ctx_fp.context_key == fp.context_key

    # Retrieve from new cold store instance via disk persistence
    cold_store = FingerprintStore(storage_dir=tmp_path)
    assert len(cold_store.list_contexts()) == 1
    disk_fp = cold_store.get(fp.context_key)
    assert disk_fp is not None
    assert disk_fp.fingerprint_id == fp.fingerprint_id
    assert disk_fp.signal_stats["barrel_temp_z3"].mean == fp.signal_stats["barrel_temp_z3"].mean
