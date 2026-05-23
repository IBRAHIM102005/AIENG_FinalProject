# Contribution Statement

**Team:** Fatma (Solo Submission)
**Topic:** Topic 4 — Async Research Assistant (SE Layer)
**Repository:** AIENG_FinalProject-Fatma
**Final tag:** `v1.0-final`
**Submission date:** 2026-05-23

---

## Member — Fatma

**Owned (sole author of these files):**
- `topic-4-research-assistant/src/config.py` — pydantic-settings configuration layer
- `topic-4-research-assistant/src/models.py` — domain models (CacheEntry, ResearchSession)
- `topic-4-research-assistant/src/services/ai_service.py` — tenacity retry wrapper, FailoverAIClient
- `topic-4-research-assistant/src/services/cache.py` — async file-based CacheService
- `topic-4-research-assistant/src/core/researcher.py` — research pipeline business logic
- `topic-4-research-assistant/src/concurrency/orchestrator.py` — asyncio parallel source orchestration
- `topic-4-research-assistant/src/cli.py` — Click CLI (ask command)
- `topic-4-research-assistant/src/offline.py` — offline stubs (OfflineLLM, offline_fetchers)
- `src/storage/cache_store.py` — SQLite CacheStore with WAL mode, thread-safety, TTL
- `src/storage/repository.py` — SessionRepository CRUD layer
- `topic-4-research-assistant/tests/` — full test suite (~1,980 lines)
- `topic-4-research-assistant/scripts/bench.py` — sequential vs parallel benchmark
- `topic-4-research-assistant/Dockerfile` — multi-stage Docker build

**Co-owned:** N/A (solo submission)

**Reviewed:** N/A (solo submission)

**Approximate share of commits:** 100%

---

## AI tool disclosure

I used AI coding assistants as follows:

| Module / file | Assistant | What I did with it |
|---|---|---|
| `src/services/ai_service.py` | AI assistant | Drafted initial retry decorator skeleton; rewrote jitter logic and FailoverAIClient chaos behavior manually after testing. |
| `src/concurrency/orchestrator.py` | AI assistant | Suggested asyncio.gather pattern; hand-wrote semaphore logic, timeout handling, and graceful degradation. |
| `tests/test_core.py` | AI assistant | Suggested parametrized test structure; reviewed, kept ~60%, wrote all edge cases (Unicode, concurrency, TTL) manually. |
| `src/storage/cache_store.py` | AI assistant | WAL mode and UPSERT syntax suggested; wrote transaction management, threading.Lock, and context manager protocol myself. |

I affirm that I **can defend every line of code** in this repository during the oral defense.

---

## Signatures

By signing below, I affirm that:
- The contributions described above are accurate.
- Every line of code in the repository can be defended.
- AI assistant usage has been disclosed as described above.

| Member | Signature | Date |
|---|---|---|
| Fatma | Fatma | 2026-05-23 |
