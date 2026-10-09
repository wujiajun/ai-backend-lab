from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str

    # Risk service configuration
    risk_service_base_url: str
    risk_connect_timeout: float = 2.0
    risk_read_timeout: float = 5.0
    risk_write_timeout: float = 5.0
    risk_pool_timeout: float = 2.0
    risk_max_attempts: int = 3
    risk_retry_initial_wait: float = 0.2
    risk_retry_max_wait: float = 2.0

    # LLM configuration
    openai_api_key: SecretStr
    llm_model: str
    llm_timeout_seconds: float = 60.0
    llm_max_output_tokens: int = 1000
    llm_max_attempts: int = 2
    llm_retry_initial_wait: float = 0.5
    llm_retry_max_wait: float = 4.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def load_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
