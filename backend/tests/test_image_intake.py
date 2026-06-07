"""Tests for the multimodal image intake tool."""
import base64
import pytest
import asyncio

# Minimal 1×1 white PNG (67 bytes)
STUB_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
)
STUB_PNG = base64.b64decode(STUB_PNG_B64)


@pytest.mark.asyncio
async def test_image_intake_returns_claims():
    """extract_claims_from_image returns a non-empty list (stub fallback when API unavailable)."""
    from backend.tools.image_intake import extract_claims_from_image
    claims = await extract_claims_from_image(STUB_PNG, "Test chart showing AI infrastructure claims")
    assert isinstance(claims, list)
    assert len(claims) > 0


@pytest.mark.asyncio
async def test_image_intake_claim_structure():
    """Each returned claim has required fields."""
    from backend.tools.image_intake import extract_claims_from_image
    claims = await extract_claims_from_image(STUB_PNG, "Stub test context")
    required = {"subject", "predicate", "object", "direction", "confidence"}
    for claim in claims:
        missing = required - set(claim.keys())
        assert not missing, f"Claim missing fields: {missing}"


@pytest.mark.asyncio
async def test_image_intake_empty_bytes_returns_stub():
    """Empty image bytes triggers stub fallback gracefully."""
    from backend.tools.image_intake import extract_claims_from_image, STUB_CLAIMS
    claims = await extract_claims_from_image(b"", "Empty image test")
    assert claims == STUB_CLAIMS


@pytest.mark.asyncio
async def test_image_intake_confidence_range():
    """Confidence scores are in 0-1 range."""
    from backend.tools.image_intake import extract_claims_from_image
    claims = await extract_claims_from_image(STUB_PNG, "Range test")
    for claim in claims:
        assert 0.0 <= float(claim["confidence"]) <= 1.0
