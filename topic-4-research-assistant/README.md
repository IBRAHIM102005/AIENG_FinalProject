# Async Research Assistant

Topic 4 implementation for the AI Engineering Software Engineering final project.
The project wraps the provided `ai/` package with configuration, retry-safe
services, async orchestration, persistent storage, CLI tools, tests, Docker, and
demo artefacts.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

The offline demo and tests do not require API keys. Live provider calls use
values from `.env`.

## CLI

Run a deterministic offline question:

```powershell
python -m src.cli ask "What is photosynthesis?" --offline --limit 2
```

Useful options:

- `--sources wiki,arxiv,web`
- `--limit 3`
- `--timeout 10`
- `--concurrency 5`
- `--no-cache`
- `--offline`

## Benchmark And Demo

Compare sequential and parallel source fetching:

```powershell
python scripts\bench.py
```

Run the sample questions:

```powershell
python scripts\demo.py --limit 5
```

## Tests

```powershell
pytest -q
```

Current verified result:

```text
194 passed
```

## Architecture

- `src/config.py`: Pydantic settings and environment validation.
- `src/models.py`: cache/session domain models.
- `src/services/ai_service.py`: retry, timeout, logging, graceful degradation.
- `src/services/cache.py`: TTL source cache.
- `src/concurrency/orchestrator.py`: async source fetching with semaphore and timeout.
- `src/core/researcher.py`: research workflow and synthesis.
- `src/cli.py`: Click command line interface.
- `src/storage/cache_store.py`: SQLite cache storage.
- `src/storage/repository.py`: persisted research sessions.

## Contribution Split

- Member A: configuration, models, AI service wrapper, cache service, service tests.
- Member B: async orchestration, researcher workflow, CLI, benchmark/demo, concurrency and E2E tests.
- Member C: SQLite storage, repository, Docker, requirements, shared fixtures, core tests, README and artefacts.

## Docker

```powershell
docker build -t async-research-assistant .
docker run --rm async-research-assistant
```

Use an env file for live provider calls:

```powershell
docker run --rm --env-file .env async-research-assistant
```
