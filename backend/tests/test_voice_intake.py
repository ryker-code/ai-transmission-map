"""Tests for the voice note intake tool."""
import pytest
from backend.tools.voice_intake import STUB_TRANSCRIPT


@pytest.mark.asyncio
async def test_transcribe_stub():
    """With placeholder API key, transcription returns stub transcript."""
    from backend.tools.voice_intake import transcribe_audio
    # Minimal WAV header (44 bytes) — enough bytes to avoid empty guard
    wav_header = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little") + b"\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data" + (0).to_bytes(4, "little")
    transcript = await transcribe_audio(wav_header, "test.wav")
    assert isinstance(transcript, str)
    assert len(transcript) > 0


@pytest.mark.asyncio
async def test_transcribe_empty_bytes_returns_stub():
    """Empty audio bytes triggers stub fallback."""
    from backend.tools.voice_intake import transcribe_audio
    transcript = await transcribe_audio(b"", "empty.wav")
    assert transcript == STUB_TRANSCRIPT


@pytest.mark.asyncio
async def test_extract_claims_from_transcript():
    """Claim extraction from a stub transcript returns a list."""
    from backend.tools.voice_intake import extract_claims_from_transcript
    claims = await extract_claims_from_transcript(STUB_TRANSCRIPT, "AI infrastructure transformer bottleneck")
    assert isinstance(claims, list)
    assert len(claims) > 0


@pytest.mark.asyncio
async def test_voice_claim_structure():
    """Each claim from transcript extraction has required fields."""
    from backend.tools.voice_intake import extract_claims_from_transcript
    claims = await extract_claims_from_transcript(STUB_TRANSCRIPT, "test context")
    required = {"subject", "predicate", "object", "direction"}
    for claim in claims:
        missing = required - set(claim.keys())
        assert not missing, f"Missing fields: {missing}"


def test_voice_endpoint_accepts_wav():
    """POST /evidence/voice with minimal WAV bytes returns 200."""
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    wav_bytes = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little") + b"\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data" + (0).to_bytes(4, "little")
    response = client.post(
        "/evidence/voice",
        files={"audio": ("test.wav", wav_bytes, "audio/wav")},
        data={"analyst_context": "Testing voice note intake for AI infrastructure transformer bottleneck analysis"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data or "error" in data
