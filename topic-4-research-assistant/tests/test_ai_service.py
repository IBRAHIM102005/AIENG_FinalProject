"""
AIService — Unit Tests

Scope:
    - Fetch methods (wikipedia, arxiv, web)
    - Synthesize flow
    - Input validation
    - Error handling (degraded responses)

All tests are fully offline.
External dependencies are replaced with FakeAIClient.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.services.ai_service import AIService, SourceResult, ValidationError
from tests.fixtures import FakeAIClient, ai_service, fake_client


# ============================================================
# Helpers
# ============================================================

def _call(client: FakeAIClient, method: str):
    """Helper to dynamically access FakeAIClient methods."""
    return getattr(client, method)


# ============================================================
# Fetch Operations — Happy Path
# ============================================================

class TestAIServiceFetchSuccess:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method, source, payload",
        [
            ("fetch_wikipedia", "wikipedia", [{"title": "Photosynthesis"}]),
            ("fetch_arxiv",     "arxiv",     [{"id": "2101.00001"}]),
            ("fetch_web",       "web",       [{"url": "https://example.com"}]),
        ],
    )
    async def test_fetch_returns_success_result(
        self,
        ai_service: AIService,
        fake_client: FakeAIClient,
        method: str,
        source: str,
        payload: list[Any],
    ) -> None:
        _call(fake_client, method).return_value = payload

        result: SourceResult = await getattr(ai_service, method)("test question")

        assert isinstance(result, SourceResult)
        assert result.success
        assert result.source == source
        assert result.results == payload


# ============================================================
# Synthesize — Happy Path
# ============================================================

class TestAIServiceSynthesize:

    @pytest.mark.asyncio
    async def test_returns_client_response(
        self,
        ai_service: AIService,
        fake_client: FakeAIClient,
    ) -> None:
        expected = {
            "answer": "Photosynthesis converts light to energy.",
            "citations": [],
        }

        fake_client.synthesize.return_value = expected

        result = await ai_service.synthesize(
            "What is photosynthesis?",
            [{"title": "Source"}],
        )

        assert result == expected
        fake_client.synthesize.assert_awaited_once()


# ============================================================
# Input Validation
# ============================================================

class TestAIServiceValidation:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method",
        ["fetch_wikipedia", "fetch_arxiv", "fetch_web"],
    )
    @pytest.mark.parametrize(
        "question",
        ["", "   ", "\t\n"],
    )
    async def test_empty_question_is_rejected(
        self,
        ai_service: AIService,
        method: str,
        question: str,
    ) -> None:
        with pytest.raises(ValidationError):
            await getattr(ai_service, method)(question)

    @pytest.mark.asyncio
    async def test_synthesize_empty_question_is_rejected(
        self,
        ai_service: AIService,
    ) -> None:
        with pytest.raises(ValidationError):
            await ai_service.synthesize("   ", [{"title": "Source"}])


# ============================================================
# Degraded Behavior
# ============================================================

class TestAIServiceErrorHandling:

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method, source",
        [
            ("fetch_wikipedia", "wikipedia"),
            ("fetch_arxiv",     "arxiv"),
            ("fetch_web",       "web"),
        ],
    )
    async def test_connection_failure_returns_degraded_result(
        self,
        ai_service: AIService,
        fake_client: FakeAIClient,
        method: str,
        source: str,
    ) -> None:
        _call(fake_client, method).side_effect = ConnectionError("network unreachable")

        result = await getattr(ai_service, method)("question")

        assert not result.success
        assert result.source == source
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_timeout_is_handled_gracefully(
        self,
        ai_service: AIService,
        fake_client: FakeAIClient,
    ) -> None:
        fake_client.fetch_arxiv.side_effect = asyncio.TimeoutError

        result = await ai_service.fetch_arxiv("question")

        assert not result.success
        assert result.source == "arxiv"