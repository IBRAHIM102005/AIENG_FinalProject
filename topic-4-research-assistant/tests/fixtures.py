"""
Shared test fixtures for Async Research Assistant.

Design goals:
- Fully deterministic tests (no real network / IO side effects)
- Lightweight fake client instead of MagicMock
- Centralized service initialization
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from src.config import Settings
from src.services.ai_service import AIService
from src.services.cache import CacheService


# ============================================================
# Fake AI Client (deterministic test double)
# ============================================================

class FakeAIClient:
    """
    Minimal deterministic replacement for AIClient.

    Each method is an AsyncMock so tests can control:
    - return_value (success path)
    - side_effect (errors / timeouts)
    """

    def __init__(self, overrides: Dict[str, Any] | None = None) -> None:
        overrides = overrides or {}

        self.fetch_wikipedia = AsyncMock()
        self.fetch_arxiv = AsyncMock()
        self.fetch_web = AsyncMock()
        self.synthesize = AsyncMock()

        # optional preconfiguration
        for key, value in overrides.items():
            if hasattr(self, key):
                getattr(self, key).return_value = value


# ============================================================
# Settings Factory (pytest-friendly)
# ============================================================

@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """
    Creates isolated Settings instance for each test run.
    """
    return Settings(
        llm_provider="anthropic",
        llm_model="claude-sonnet-4-6",
        anthropic_api_key="test-key",
        cache_dir=tmp_path / "cache",
        cache_ttl_seconds=3600,
        retry_max_attempts=3,
        retry_min_wait_seconds=0.01,
        retry_max_wait_seconds=0.05,
        per_source_timeout_seconds=5.0,
    )


# ============================================================
# Core Fixtures
# ============================================================

@pytest.fixture
def fake_client() -> FakeAIClient:
    return FakeAIClient()


@pytest.fixture
def ai_service(fake_client: FakeAIClient) -> AIService:
    """
    AIService with fully mocked dependencies.
    No real network calls possible.
    """
    return AIService(client=fake_client)


@pytest.fixture
def file_cache(tmp_path: Path) -> CacheService:
    """
    Disk-backed cache used for integration-level tests.
    """
    return CacheService(cache_dir=tmp_path / "cache", ttl_seconds=3600)


@pytest.fixture
def cache_service(tmp_path: Path) -> CacheService:
    """
    Unified cache fixture (recommended over memory_cache naming).

    NOTE:
    This is NOT true in-memory cache.
    It's file-backed but isolated per test.
    """
    return CacheService(cache_dir=tmp_path / "cache", ttl_seconds=3600)