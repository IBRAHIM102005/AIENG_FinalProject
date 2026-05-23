"""
CacheEntry unit tests

Scope:
- Key generation logic (deterministic + case-insensitive behavior)
- TTL expiration rules (pure model logic, no I/O)
"""

from __future__ import annotations

import pytest
from freezegun import freeze_time

from src.models import CacheEntry


# ============================================================
# Key generation
# ============================================================

class TestCacheEntryKeyGeneration:

    def test_key_is_deterministic(self) -> None:
        key1 = CacheEntry.make_key("wikipedia", "photosynthesis")
        key2 = CacheEntry.make_key("wikipedia", "photosynthesis")

        assert key1 == key2

    def test_key_is_case_insensitive(self) -> None:
        assert CacheEntry.make_key("wikipedia", "PHOTO") == \
               CacheEntry.make_key("wikipedia", "photo")

    def test_key_is_source_sensitive(self) -> None:
        assert CacheEntry.make_key("wikipedia", "topic") != \
               CacheEntry.make_key("arxiv", "topic")


# ============================================================
# TTL / expiration logic
# ============================================================

class TestCacheEntryExpiration:

    def test_new_entry_is_valid(self) -> None:
        entry = CacheEntry(key="k", value=[], ttl_seconds=3600)
        assert not entry.is_expired()

    def test_zero_ttl_never_expires(self) -> None:
        entry = CacheEntry(key="k", value=[], ttl_seconds=0)
        assert not entry.is_expired()

    @freeze_time("2024-01-01 12:00:00")
    def test_entry_expires_after_ttl(self) -> None:
        """
        Entry created at 10:00 with TTL=1h.
        At 12:00 it should be expired.
        """
        with freeze_time("2024-01-01 10:00:00"):
            entry = CacheEntry(key="k", value=[], ttl_seconds=3600)

        assert entry.is_expired()

    @freeze_time("2024-01-01 10:00:30")
    def test_entry_still_valid_within_ttl(self) -> None:
        """
        Entry created at 10:00 with TTL=1h.
        At 10:00:30 it should still be valid.
        """
        with freeze_time("2024-01-01 10:00:00"):
            entry = CacheEntry(key="k", value=[], ttl_seconds=3600)

        assert not entry.is_expired()