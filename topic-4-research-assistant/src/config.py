"""
Async Research Assistant — Configuration Layer
AIENG Final Project / topic-4-research-assistant

Central configuration system for the entire application.
Handles environment loading, validation, and runtime-safe settings access.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide configuration schema.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM configuration
    llm_provider: Literal["anthropic", "openai", "gemini"] = Field(default="anthropic")
    llm_model: str = Field(default="claude-sonnet-4-6")

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None

    # Web search configuration
    web_search_provider: Literal["tavily", "serper", "duckduckgo"] = Field(default="tavily")
    tavily_api_key: str | None = None
    serper_api_key: str | None = None

    # Runtime parameters
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    cache_dir: Path = Field(default=Path(".cache"))
    cache_ttl_seconds: int = Field(default=86_400, ge=0)

    per_source_timeout_seconds: float = Field(default=10.0, gt=0)
    max_sources_per_query: int = Field(default=3, ge=1, le=10)
    max_question_length: int = Field(default=1_000, gt=0)

    # Retry policy
    retry_max_attempts: int = Field(default=3, ge=1)
    retry_min_wait_seconds: float = Field(default=1.0, ge=0)
    retry_max_wait_seconds: float = Field(default=30.0, ge=1)

    # Concurrency control
    concurrency_semaphore_limit: int = Field(default=5, ge=1)

    @field_validator("cache_dir", mode="before")
    @classmethod
    def _coerce_cache_dir(cls, v: Any) -> Path:
        return Path(v)

    @field_validator("llm_model", mode="after")
    @classmethod
    def _validate_model(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("llm_model cannot be empty")
        return v

    def ensure_cache_dir(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def active_api_key(self) -> str:
        key_map = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "gemini": self.google_api_key,
        }

        key = key_map.get(self.llm_provider)

        if not key:
            raise RuntimeError(
                f"Missing API key for provider: {self.llm_provider}"
            )

        return key

    def active_web_search_api_key(self) -> str | None:
        key_map = {
            "tavily": self.tavily_api_key,
            "serper": self.serper_api_key,
            "duckduckgo": None,
        }
        return key_map.get(self.web_search_provider)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns cached application settings instance.
    """
    return Settings()
