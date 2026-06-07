"""Market signals endpoint: returns mock relative performance data for seed entities."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.api.schemas import MarketSignalEntry, MarketSignalsResponse
from backend.tools.market_signals import get_signals

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/signals", response_model=MarketSignalsResponse)
async def get_market_signals():
    """Return all market signals with last_updated and is_live=false flag.
    TODO: replace mock data with live Alpha Vantage / yfinance feed."""
    try:
        raw = get_signals().get_all_signals()
        entries = [MarketSignalEntry(**s) for s in raw]
        return MarketSignalsResponse(
            signals=entries,
            last_updated=datetime.now(timezone.utc),
            is_live=False,
        )
    except Exception as e:
        logger.error(f"market signals failed: {e}")
        return MarketSignalsResponse(signals=[], last_updated=datetime.now(timezone.utc), is_live=False)
