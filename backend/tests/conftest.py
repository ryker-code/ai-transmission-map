"""Shared test fixtures. Sets AITM_API_KEY so all TestClient calls can use it."""
import os
import pytest

# Ensure the test key matches the default in auth.py
os.environ.setdefault("AITM_API_KEY", "dev-key-change-in-production")

AUTH_HEADERS = {"X-Api-Key": "dev-key-change-in-production"}
