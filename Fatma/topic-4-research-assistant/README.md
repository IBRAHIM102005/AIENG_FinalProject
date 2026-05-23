# Async Research Assistant

> A concurrent multi-source research pipeline that fetches Wikipedia, arXiv, and web results in parallel, caches them with a TTL-aware disk cache, and synthesizes a cited answer using a configurable LLM provider.

**Team:** Fatma (Solo)  •  **Topic:** 4  •  **Course:** AI-ENG-110 Software Engineering, AI Academy

**Due:** **May 23, 2026 at 23:59 (UTC+4)**

---

## Quick start

```bash
# 1. Clone & install
cd topic-4-research-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r ../requirements.txt

# 2. Configure
cp .env.example .env       # then fill in real API keys

# 3. Run the smoke tests
pytest tests/test_ai_smoke.py -v
pytest --cov=src --cov-report=term-missing

# 4. Ask a question
python -m src.cli ask "What is the transformer attention mechanism?"
```

## Run with Docker

```bash
# Build from repo root
docker build -t finalproj .
docker run --env-file topic-4-research-assistant/.env finalproj ask "What is reinforcement learning?"

# Bypass cache for a fresh fetch
docker run --env-file topic-4-research-assistant/.env finalproj ask "What is RLHF?" --no-cache
```

## Environment variables

| Variable | Required? | Default | What it controls |
|---|---|---|---|
| `LLM_PROVIDER` | yes | `anthropic` | `anthropic` \| `openai` \| `gemini` |
| `LLM_MODEL` | yes | `claude-sonnet-4-6` | model id |
| `ANTHROPIC_API_KEY` | if anthropic | — | Anthropic API key |
| `OPENAI_API_KEY` | if openai | — | OpenAI API key |
| `GOOGLE_API_KEY` | if gemini | — | Google API key |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CACHE_DIR` | no | `.cache` | directory for cache JSON files |
| `CACHE_TTL_SECONDS` | no | `86400` | cache TTL in seconds (0 = disabled) |
| `PER_SOURCE_TIMEOUT_SECONDS` | no | `10` | per-source fetch timeout |
| `MAX_SOURCES_PER_QUERY` | no | `3` | max results per source |
| `MAX_QUESTION_LENGTH` | no | `1000` | max question character length |
| `RETRY_MAX_ATTEMPTS` | no | `3` | LLM retry attempts |
| `CONCURRENCY_SEMAPHORE_LIMIT` | no | `5` | max parallel source fetches |

Full list in `.env.example`.

## How to run the CLI

```bash
# Basic query (uses cache by default)
python -m src.cli ask "What is quantum entanglement?"

# Restrict to specific sources
python -m src.cli ask "Latest transformer architectures" --sources arxiv,wiki

# Skip cache
python -m src.cli ask "Today's AI news" --no-cache

# Offline mode (no API keys needed, deterministic output)
python -m src.cli ask "Test question" --offline

# Adjust concurrency and timeout
python -m src.cli ask "Parallel computing history" --concurrency 5 --timeout 15
```

## Sequential vs concurrent benchmark

| Workload | N | Sequential | Concurrent (sem=3) | Speedup |
|---|---|---|---|---|
| 3 sources × 20 questions | 20 | ~48.3 s | ~9.1 s | **5.3×** |

**Reproduce:**
```bash
python scripts/bench.py
```

Bottleneck after parallelization is **network RTT to external APIs** (arXiv ~3–4 s, Wikipedia ~1–2 s, web search ~2–3 s). The semaphore limit of 3 matches the number of sources, so all three run fully in parallel. See `report/report.pdf` §4 for details.

## Testing

```bash
# Full suite with coverage
pytest --cov=src --cov-report=term-missing

# Smoke tests only (provided, must not fail)
pytest tests/test_ai_smoke.py -v

# Single file
pytest tests/test_cache_service.py -v
```

- Total coverage: **≥ 60%**
- All tests run **offline** (HTTP mocked with `respx`/`pytest-httpx`, LLM mocked)
- Provided smoke tests: **passing**

## Project layout

```
topic-4-research-assistant/
├── ai/                          # PROVIDED — do not modify
├── src/
│   ├── config.py                # pydantic-settings typed config
│   ├── models.py                # CacheEntry, ResearchSession
│   ├── services/
│   │   ├── ai_service.py        # tenacity retry + FailoverAIClient
│   │   └── cache.py             # async TTL disk cache (wired into pipeline)
│   ├── core/researcher.py       # main research pipeline
│   ├── concurrency/orchestrator.py  # asyncio.gather parallel fetcher
│   ├── storage/                 # SQLite CacheStore + SessionRepository
│   ├── offline.py               # offline stubs
│   └── cli.py                   # Click CLI
├── tests/
├── scripts/
│   ├── demo.py
│   └── bench.py                 # sequential vs parallel timing
├── data/research_questions.json
├── .env.example
├── pytest.ini
└── README.md  ← you are here

../src/storage/                  # also at repo root for Dockerfile compatibility
../requirements.txt
../Dockerfile
```

## Architecture

```
+-------+
|  CLI  |  python -m src.cli ask "..."
+---+---+
    |
    v
+------------------+
| researcher.py    |  validate_question → orchestrate → synthesize
+--------+---------+
         |
         v
+---------------------+    cache hit?
| orchestrator.py     | ---------> CacheService (disk JSON, TTL)
| asyncio.gather      |              ^
| per-source timeout  |              | cache miss → store
+-----+------+-------+              |
      |      |      |               |
      v      v      v               |
  wiki   arxiv   web  --------+-----+
                              |
                              v
                    +------------------+
                    | ai_service.py    |  tenacity retry + failover
                    | FailoverAIClient |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  ai/ (provided)  |  synthesize answer + citations
                    +------------------+
                             |
                             v
                    +------------------+
                    | src/storage/     |  SQLite (CacheStore, sessions)
                    +------------------+
```

## Limitations

- No HTTP server (CLI-only as per Topic 4 spec)
- Cache does not deduplicate across different question phrasings (keyed by exact query string)
- No rate limiting on CLI: rapid repeated calls may exhaust API quota
- Session management CLI subcommands (`sessions list`, `cache stats`) not implemented

See `report/report.pdf` §6 for a full discussion.

## Tools & acknowledgements

AI assistants (Claude) were used for scaffolding as disclosed in `templates/CONTRIBUTION_STATEMENT.md` and report §8.
