import json, uuid, logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENTITIES_FILE = Path("backend/db/seed_data/entities.json")
CHAINS_FILE = Path("backend/db/seed_data/transmission_chains.json")

def load_seed_data():
    from backend.config import settings
    from backend.db.bigquery_client import BigQueryClient

    client = BigQueryClient(settings.google_cloud_project, settings.bigquery_dataset)

    entities = json.loads(ENTITIES_FILE.read_text())
    logger.info(f"Loading {len(entities)} entities...")
    client.insert_rows("entities", entities)

    chains = json.loads(CHAINS_FILE.read_text())
    logger.info(f"Loading {len(chains)} transmission chains...")

    entity_map = {e["canonical_name"]: e["id"] for e in entities}

    claims = []
    for chain in chains:
        subject_id = entity_map.get(chain["subject"])
        object_id = entity_map.get(chain["object"])
        if not subject_id or not object_id:
            logger.warning(f"Skipping chain — entity not found: {chain['subject']} -> {chain['object']}")
            continue
        claims.append({
            "id": str(uuid.uuid4()),
            "subject_id": subject_id,
            "predicate": chain["predicate"],
            "object_id": object_id,
            "direction": chain["direction"],
            "magnitude": chain.get("confidence", 0.7),
            "confidence": chain.get("confidence", 0.7),
            "time_lag_days": 0,
            "horizon": chain["horizon"],
            "regime_tag": chain["regime_tag"],
            "status": "accepted",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

    client.insert_rows("claims", claims)
    logger.info(f"Seed complete: {len(entities)} entities, {len(claims)} claims loaded")

if __name__ == "__main__":
    load_seed_data()
