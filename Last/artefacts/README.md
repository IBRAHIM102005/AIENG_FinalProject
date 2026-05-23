# Artefacts

This directory contains demo run outputs for the Async Research Assistant (Topic 4).

## Generating artefacts

```bash
cd topic-4-research-assistant

# Run a demo query and capture output
python -m src.cli ask "What is the transformer attention mechanism?" \
    --sources wiki,arxiv > artefacts/cli_research_output.log

# Run in offline mode (no API keys needed)
python -m src.cli ask "What is neural scaling?" --offline \
    > artefacts/cli_offline_output.log

# Run benchmark
python scripts/bench.py > artefacts/bench_results.log
```

## CLI usage

```bash
# Basic query
python -m src.cli ask "Your question here"

# Available options
python -m src.cli ask --help
```

The `ask` command supports: `--sources`, `--limit`, `--timeout`, `--concurrency`, `--no-cache`, `--offline`.

See `README.md` for full documentation.
