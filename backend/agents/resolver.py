"""
Standalone entity resolver.

Builds an alias index from seed data and resolves free-text entity names
to canonical entity records using substring + lowercase normalization.
No external fuzzy-matching library required.
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_SEED_PATH = Path("backend/db/seed_data/entities.json")


class EntityResolver:
    """Resolves arbitrary entity name strings to canonical entity records."""

    def __init__(self):
        self._entities: list[dict] = []
        self._index: dict[str, dict] = {}  # normalised_key → entity
        self._merger_map: dict[str, str] = {}  # alias_id → canonical_id
        self._load()

    def _load(self):
        """Build alias index from seed data."""
        if not _SEED_PATH.exists():
            logger.warning("resolver: seed entities file not found")
            return
        self._entities = json.loads(_SEED_PATH.read_text())
        for entity in self._entities:
            self._index_entity(entity)
        logger.info(f"resolver: indexed {len(self._entities)} entities, {len(self._index)} keys")

    def _index_entity(self, entity: dict):
        """Add entity and all its aliases/ticker to the index."""
        keys = [entity["canonical_name"]]
        keys.extend(entity.get("aliases", []))
        if entity.get("ticker"):
            keys.append(entity["ticker"])
        for key in keys:
            self._index[self._normalise(key)] = entity

    @staticmethod
    def _normalise(name: str) -> str:
        return name.strip().lower().replace(".", "").replace(",", "").replace("-", " ")

    def resolve(self, name: str) -> Optional[dict]:
        """
        Resolve a name to a canonical entity.
        Tries exact normalised match first, then substring match.
        Returns None if no match found.
        """
        if not name:
            return None
        key = self._normalise(name)

        # Exact match
        if key in self._index:
            entity = self._index[key]
            # Follow merger map
            canonical_id = self._merger_map.get(entity["id"], entity["id"])
            if canonical_id != entity["id"]:
                entity = next((e for e in self._entities if e["id"] == canonical_id), entity)
            return entity

        # Substring match: key is contained in any index key
        for idx_key, entity in self._index.items():
            if key in idx_key or idx_key in key:
                return entity

        return None

    def resolve_batch(self, names: list[str]) -> dict[str, Optional[dict]]:
        """Resolve a list of names. Returns {name: entity_or_None}."""
        return {name: self.resolve(name) for name in names}

    def merge_duplicate(self, entity_a_id: str, entity_b_id: str) -> None:
        """
        Mark entity_b as an alias of entity_a.
        Subsequent resolve() calls for entity_b will return entity_a.
        """
        self._merger_map[entity_b_id] = entity_a_id
        logger.info(f"resolver: merged {entity_b_id} → {entity_a_id}")

    def canonical_name(self, name: str) -> Optional[str]:
        """Resolve and return just the canonical_name, or None."""
        entity = self.resolve(name)
        return entity["canonical_name"] if entity else None


# Module-level singleton — shared across pipeline runs
_resolver: Optional[EntityResolver] = None


def get_resolver() -> EntityResolver:
    """Return the module-level singleton, initialising on first call."""
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver()
    return _resolver
