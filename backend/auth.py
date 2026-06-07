"""API key authentication for write endpoints."""
import os
import logging
from typing import Optional
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

API_KEY = os.getenv("AITM_API_KEY", "dev-key-change-in-production")


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """Dependency: require a valid X-Api-Key on write endpoints."""
    if x_api_key != API_KEY:
        logger.warning(f"Auth failure: received key '{x_api_key}'")
        raise HTTPException(status_code=401, detail="Invalid API key. Set X-Api-Key header.")
    return x_api_key


def optional_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Dependency: accept optional key on read endpoints (logged if provided)."""
    return x_api_key
