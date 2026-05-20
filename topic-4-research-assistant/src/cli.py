"""Click command line interface for the research assistant."""

from __future__ import annotations

import asyncio
import logging
import os

import click

from ai import AnswerWithCitations

from src.core.researcher import ResearchResult, research_question
from src.offline import OfflineLLM, offline_fetchers


def _split_sources(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [piece.strip() for piece in value.split(",") if piece.strip()]


def render_answer(result: ResearchResult) -> str:
    """Render an answer and references for terminal output."""

    answer: AnswerWithCitations = result.answer
    lines = [f"Q: {answer.question}", "", f"A: {answer.answer}", ""]
    if result.failures:
        lines.append("Source notes:")
        for failure in result.failures:
            lines.append(f"  - {failure.source} failed: {failure.error}")
        lines.append("")
    if answer.citations:
        lines.append("References:")
        for citation in answer.citations:
            src = citation.source
            lines.append(f"  [{citation.index}] ({src.origin}) {src.title}")
            lines.append(f"      {src.url}")
    return "\n".join(lines)


@click.group()
def cli() -> None:
    """Async research assistant."""

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


@cli.command()
@click.argument("question")
@click.option("--sources", help="Comma-separated list: wiki,arxiv,web.")
@click.option(
    "--limit",
    type=int,
    default=lambda: int(os.getenv("MAX_SOURCES_PER_QUERY", "3")),
    show_default="env/default",
)
@click.option(
    "--timeout",
    type=float,
    default=lambda: float(os.getenv("PER_SOURCE_TIMEOUT_SECONDS", "10")),
    show_default="env/default",
    help="Per-source timeout in seconds.",
)
@click.option("--concurrency", default=3, show_default=True, help="Maximum concurrent source fetches.")
@click.option("--no-cache", is_flag=True, help="Accepted for compatibility; cache is owned by service layer.")
@click.option("--offline", is_flag=True, help="Use deterministic fake sources and fake LLM.")
def ask(
    question: str,
    sources: str | None,
    limit: int,
    timeout: float,
    concurrency: int,
    no_cache: bool,
    offline: bool,
) -> None:
    """Answer QUESTION with cited research sources."""

    del no_cache
    try:
        result = asyncio.run(
            research_question(
                question,
                sources=_split_sources(sources),
                max_results=limit,
                per_source_timeout=timeout,
                semaphore_limit=concurrency,
                fetchers=offline_fetchers() if offline else None,
                llm=OfflineLLM() if offline else None,
            )
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_answer(result))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
