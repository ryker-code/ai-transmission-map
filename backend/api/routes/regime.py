import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


class RegimeResponse(BaseModel):
    regime: str
    confidence: float
    description: str
    scores: dict


@router.get("/", response_model=RegimeResponse)
async def get_regime():
    """
    Detect and return the dominant market regime from the active claim graph.
    Regime is determined by confidence-weighted claim regime_tag distribution.
    """
    from backend.tools.regime_detector import detect_regime
    result = detect_regime()
    return RegimeResponse(**result)
