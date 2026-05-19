"""
Async Research Assistant — SE Layer
AIENG Final Project / topic-4-research-assistant
 
This package forms the Software Engineering layer that wraps the provided
ai/ module with production-grade infrastructure:
 
    1. Typed configuration management via Pydantic Settings
    2. Domain models for sessions and cache entries
    3. AI service with retry/timeout/logging decorators
    4. TTL-aware caching keyed by (source, query)
 
Key responsibilities:
    - Centralise all env-var handling in one validated Settings object
    - Provide serialisable domain models consumed by the CLI and tests
    - Shield callers from transient provider failures via tenacity retries
    - Reduce redundant network calls through a disk-backed TTL cache
 
Public surface (import shortcuts):
    from src.config import settings
    from src.models import ResearchSession, CacheEntry
"""