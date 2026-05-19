"""
AI Service Layer

Handles all interaction with external AI providers in a resilient way:
- Retries transient failures (network, timeouts)
- Applies per-call timeouts
- Logs all operations
- Validates inputs early
- Returns structured results instead of failing silently

Designed to be testable via dependency injection.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.config import get_settings

logger = logging.getLogger(__name__)


# Only retry transient errors — not logic/validation bugs
_RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
)


# ─────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────

class AIServiceError(Exception):
    """Raised when an AI operation fails definitively."""


class ValidationError(AIServiceError):
    """Raised when input validation fails."""


# ─────────────────────────────────────────────────────────────
# Result Model
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceResult:
    """
    Represents the outcome of a single source fetch.

    Always returned — even on failure — so the pipeline can continue.
    """

    source: str
    results: list[Any] = field(default_factory=list)
    success: bool = True
    error: str | None = None

    @classmethod
    def degraded(cls, source: str, reason: str) -> "SourceResult":
        logger.warning("Source '%s' degraded: %s", source, reason)
        return cls(source=source, success=False, error=reason)


# ─────────────────────────────────────────────────────────────
# AI Client Interface (for DI & testing)
# ─────────────────────────────────────────────────────────────

class AIClient(Protocol):
    async def fetch_wikipedia(self, question: str) -> list[Any]: ...
    async def fetch_arxiv(self, question: str) -> list[Any]: ...
    async def fetch_web(self, question: str) -> list[Any]: ...
    async def synthesize(self, question: str, sources: list[Any]) -> Any: ...


# ─────────────────────────────────────────────────────────────
# Retry configuration (cached)
# ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def _build_retry(max_attempts: int, min_wait: float, max_wait: float):
    return retry(
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False,
    )


def _retry():
    s = get_settings()
    return _build_retry(
        s.retry_max_attempts,
        s.retry_min_wait_seconds,
        s.retry_max_wait_seconds,
    )


# ─────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────

def _validate_question(question: str) -> None:
    if not question or not question.strip():
        raise ValidationError("Question must not be empty.")

    max_len = get_settings().max_question_length
    if len(question) > max_len:
        raise ValidationError(f"Question too long ({len(question)} > {max_len})")


# ─────────────────────────────────────────────────────────────
# Service Layer
# ─────────────────────────────────────────────────────────────

class AIService:
    """
    High-level wrapper around AIClient.

    Adds:
    - retry
    - timeout
    - logging
    - validation
    """

    def __init__(self, client: AIClient) -> None:
        self._client = client

    # ── Public API ────────────────────────────────────────────

    async def fetch_wikipedia(self, question: str) -> SourceResult:
        _validate_question(question)
        return await self._fetch("wikipedia", self._client.fetch_wikipedia, question)

    async def fetch_arxiv(self, question: str) -> SourceResult:
        _validate_question(question)
        return await self._fetch("arxiv", self._client.fetch_arxiv, question)

    async def fetch_web(self, question: str) -> SourceResult:
        _validate_question(question)
        return await self._fetch("web", self._client.fetch_web, question)

    async def synthesize(self, question: str, sources: list[Any]) -> Any:
        _validate_question(question)
        logger.info("Synthesizing answer...")

        timeout = get_settings().per_source_timeout_seconds * 3
        fn = _retry()(self._client.synthesize)

        try:
            return await asyncio.wait_for(
                _run_async(fn, question, sources),
                timeout=timeout,
            )

        except asyncio.TimeoutError:
            raise AIServiceError("Synthesis timed out")

        except RetryError as exc:
            raise AIServiceError(f"Synthesis failed after retries: {exc}") from exc

        except Exception as exc:
            logger.exception("Unexpected synthesis error")
            raise AIServiceError(str(exc)) from exc

    # ── Internal ──────────────────────────────────────────────

    async def _fetch(
        self,
        source: str,
        fn: Callable[[str], Awaitable[list[Any]]],
        question: str,
    ) -> SourceResult:
        timeout = get_settings().per_source_timeout_seconds
        fn = _retry()(fn)

        try:
            data = await asyncio.wait_for(
                _run_async(fn, question),
                timeout=timeout,
            )
            return SourceResult(source=source, results=data)

        except asyncio.TimeoutError:
            return SourceResult.degraded(source, f"timeout after {timeout}s")

        except RetryError as exc:
            return SourceResult.degraded(source, f"retries failed: {exc}")

        except Exception as exc:
            logger.exception("Unexpected error from %s", source)
            return SourceResult.degraded(source, str(exc))


# ─────────────────────────────────────────────────────────────
# Async helper
# ─────────────────────────────────────────────────────────────

async def _run_async(fn: Callable[..., Any], *args: Any) -> Any:
    if asyncio.iscoroutinefunction(fn):
        return await fn(*args)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fn, *args)