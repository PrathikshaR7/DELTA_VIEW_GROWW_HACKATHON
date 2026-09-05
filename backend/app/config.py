"""
Centralised configuration. Everything is overridable via environment
variables / .env so the same image works in dev, docker-compose and prod.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- core ---
    app_env: str = "development"
    secret_key: str = "change-me-in-prod-please"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- database ---
    database_url: str = "postgresql://postgres:postgres@postgres:5432/watchlist"

    # --- redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- market data providers ---
    # Twelve Data offers a free-tier API key and real (delayed) quotes.
    # If not set, the system automatically falls back to yfinance
    # (no key required) and, outside market hours, to the replay engine.
    twelvedata_api_key: str = ""
    # Alpha Vantage is another option; set this to use it explicitly.
    alphavantage_api_key: str = ""
    data_provider: str = "auto"  # auto | twelvedata | yfinance | replay

    # --- ingestion ---
    ingest_interval_seconds: int = 15
    replay_speed_multiplier: float = 60.0  # 1 real historical minute -> 1 replay second

    # --- market hours (IST) ---
    market_open_hour: int = 9
    market_open_minute: int = 15
    market_close_hour: int = 15
    market_close_minute: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
