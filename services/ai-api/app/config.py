"""Application settings.

Everything that differs between a laptop, a CI run and the public demo is an
environment variable, never a constant in the code. Values are read from the
process environment first and from a local `.env` file second.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    # service boundaries
    enterprise_sim_url: str = "http://localhost:8001"
    database_url: str = "postgresql+psycopg://orderops:orderops@localhost:5432/orderops"

    # llm providers (keys stay server side, never reach the browser)
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    minimax_api_key: str = ""
    minimax_base_url: str = ""
    minimax_model: str = ""

    # budgets: a public demo must not be able to run up a bill
    run_token_budget: int = 40_000
    run_time_budget_seconds: int = 90
    max_tool_calls: int = 12
    demo_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the environment is parsed once per process."""
    return Settings()
