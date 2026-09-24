"""Production context enrichment for machine, mold, recipe, and material metadata."""

from typing import Dict, Any, Optional
from process_guardian.core.types import MachineContext
from process_guardian.adapter.schemas import EnrichedContext


class ContextEnricher:
    """Enriches cycle telemetry with factory operational context."""

    def __init__(self, default_context: Optional[MachineContext] = None):
        self.default_context = default_context or MachineContext()

    def enrich(self, raw_data: Dict[str, Any]) -> EnrichedContext:
        """
        Merge default machine context with any field-level overrides present in raw telemetry.
        """
        return EnrichedContext(
            machine_id=str(raw_data.get("machine_id", self.default_context.machine_id)),
            mold_id=str(raw_data.get("mold_id", self.default_context.mold_id)),
            part_id=str(raw_data.get("part_id", self.default_context.part_id)),
            recipe_id=str(raw_data.get("recipe_id", self.default_context.recipe_id)),
            recipe_version=str(raw_data.get("recipe_version", self.default_context.recipe_version)),
            material_batch=str(raw_data.get("material_batch", self.default_context.material_batch)),
            operator_id=str(raw_data.get("operator_id", self.default_context.operator_id)),
        )
