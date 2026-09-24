"""Storage and retrieval repository for process fingerprints."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from process_guardian.adapter.schemas import EnrichedContext
from process_guardian.fingerprint.models import ProcessFingerprint


class FingerprintStore:
    """
    In-memory and file-backed repository for process fingerprints.
    
    Permits storing and fetching validated fingerprints by their unique context key.
    """

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        self._cache: Dict[str, ProcessFingerprint] = {}
        self.storage_dir = Path(storage_dir) if storage_dir is not None else None
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_key(self, context_key: str) -> str:
        """Sanitize context key for safe filesystem storage."""
        return context_key.replace(":", "__").replace("/", "_")

    def save(self, fingerprint: ProcessFingerprint) -> None:
        """Store fingerprint in memory cache and persist to disk if configured."""
        self._cache[fingerprint.context_key] = fingerprint

        if self.storage_dir is not None:
            filename = f"{self._sanitize_key(fingerprint.context_key)}.json"
            file_path = self.storage_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fingerprint.model_dump_json(indent=2))

    def get(self, context_key_or_context: Union[str, EnrichedContext]) -> Optional[ProcessFingerprint]:
        """
        Retrieve fingerprint by context key or EnrichedContext object.
        Checks cache first, then disk storage.
        """
        if isinstance(context_key_or_context, EnrichedContext):
            ctx = context_key_or_context
            key = f"{ctx.machine_id}:{ctx.mold_id}:{ctx.part_id}:{ctx.recipe_id}:{ctx.recipe_version}"
        else:
            key = str(context_key_or_context)

        # 1. Cache hit
        if key in self._cache:
            return self._cache[key]

        # 2. Disk lookup
        if self.storage_dir is not None:
            filename = f"{self._sanitize_key(key)}.json"
            file_path = self.storage_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    fp = ProcessFingerprint.model_validate(data)
                    self._cache[key] = fp
                    return fp
                except Exception:
                    return None

        return None

    def list_contexts(self) -> List[str]:
        """Return list of all context keys currently available in the store."""
        keys = set(self._cache.keys())
        if self.storage_dir is not None and self.storage_dir.exists():
            for p in self.storage_dir.glob("*.json"):
                key = p.stem.replace("__", ":")
                keys.add(key)
        return sorted(list(keys))
