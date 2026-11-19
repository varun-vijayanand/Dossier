from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="DOSSIER_", extra="ignore"
    )

    environment: str = "local"
    database_url: str = "postgresql://dossier:dossier@localhost:5433/dossier"
    anthropic_api_key: SecretStr | None = None

    model_triage: str = "claude-haiku-5-5"
    model_reasoning: str = "claude-sonnet-5-5"

    max_tool_calls: int = Field(default=25, ge=1)
    run_deadline_seconds: int = Field(default=120, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()