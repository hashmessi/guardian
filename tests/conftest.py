"""Pytest fixtures for Process Guardian tests."""

import pytest
from process_guardian.core.types import MachineContext


@pytest.fixture
def default_context() -> MachineContext:
    """Standard automotive housing production context fixture."""
    return MachineContext(
        machine_id="IMM-01",
        mold_id="MOLD-HOUSING-04",
        part_id="PART-AUTO-HOUSING-A",
        recipe_id="RECIPE-PP-V2.1",
        recipe_version="2.1",
        material_batch="BATCH-20260924-A",
        operator_id="OP-102",
    )


@pytest.fixture
def default_seed() -> int:
    """Standard reproducible seed."""
    return 42
