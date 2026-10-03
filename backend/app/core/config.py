from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Coding Agent API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    session_cookie_name: str = "ai_agent_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 7
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    auth_rate_limit: int = 10
    auth_rate_window_seconds: int = 60
    secret_key: str = "change-me-in-development"
    cors_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    github_client_id: str = ""
    github_client_secret: str = ""
    github_callback_url: str = "http://localhost:8000/api/v1/github/callback"
    github_scopes: str = "repo,read:user"
    token_encryption_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
