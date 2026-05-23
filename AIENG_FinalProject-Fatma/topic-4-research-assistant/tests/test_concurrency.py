from __future__ import annotations

import asyncio

import pytest

from ai import Source
from src.concurrency.orchestrator import fetch_selected_sources, normalize_sources


async def _ok(query: str, *, max_results: int = 3, client=None) -> list[Source]:
    await asyncio.sleep(0.01)
    return [
        Source(
            title=f"Result for {query}",
            url="https://example.com/result",
            snippet="A useful source.",
            origin="web",
        )
    ][:max_results]


async def _fail(query: str, *, max_results: int = 3, client=None) -> list[Source]:
    await asyncio.sleep(0.01)
    raise RuntimeError("provider is down")


async def _slow(query: str, *, max_results: int = 3, client=None) -> list[Source]:
    await asyncio.sleep(0.2)
    return []


def test_normalize_sources_accepts_aliases_and_dedupes():
    assert normalize_sources(["wiki", "arxiv", "wikipedia"]) == ("wikipedia", "arxiv")


def test_normalize_sources_rejects_unknown_source():
    with pytest.raises(ValueError):
        normalize_sources(["wiki", "reddit"])


@pytest.mark.asyncio
async def test_fetch_selected_sources_degrades_when_one_source_fails():
    result = await fetch_selected_sources(
        "photosynthesis",
        sources=["wiki", "web"],
        fetchers={"wikipedia": _fail, "web": _ok},
    )

    assert len(result.sources) == 1
    assert result.failures[0].source == "wikipedia"
    assert "provider is down" in result.failures[0].error


@pytest.mark.asyncio
async def test_fetch_selected_sources_applies_per_source_timeout():
    result = await fetch_selected_sources(
        "photosynthesis",
        sources=["wiki", "web"],
        per_source_timeout=0.05,
        fetchers={"wikipedia": _slow, "web": _ok},
    )

    assert len(result.sources) == 1
    assert result.failures[0].source == "wikipedia"

