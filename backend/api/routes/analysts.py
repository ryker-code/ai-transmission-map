"""Analyst collaboration stubs: list unique analysts from house view + claims."""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=dict)
async def list_analysts():
    """
    List unique analyst user_ids from house view and claim stores.
    Shows who has active positions and when they last made changes.
    """
    analyst_map: dict[str, dict] = {}

    try:
        from backend.db.house_view_store import all_entries
        for entity_id, record in all_entries().items():
            uid = record.get("user_id", "default")
            if uid not in analyst_map:
                analyst_map[uid] = {"user_id": uid, "house_view_count": 0, "claim_count": 0}
            analyst_map[uid]["house_view_count"] += 1
    except Exception as exc:
        logger.warning(f"analysts: house_view_store error: {exc}")

    try:
        from backend.db.claims_store import get_all_claims
        for claim in get_all_claims():
            uid = claim.get("user_id", "default")
            if uid not in analyst_map:
                analyst_map[uid] = {"user_id": uid, "house_view_count": 0, "claim_count": 0}
            analyst_map[uid]["claim_count"] += 1
    except Exception:
        pass

    # Always include default analyst
    if not analyst_map:
        analyst_map["default"] = {"user_id": "default", "house_view_count": 0, "claim_count": 0}

    analysts = sorted(analyst_map.values(), key=lambda a: a["user_id"])
    return {"analysts": analysts, "total": len(analysts)}
