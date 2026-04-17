from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Literal

# config.py 位于 backend/app/core/，向上三级到达项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = str(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-change-in-prod"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./trendsee.db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── AI Provider ──────────────────────────────────────────────────────────
    # Set to "openai" or "deepseek". When both keys are present,
    # AI_PROVIDER determines which one is used as the primary.
    AI_PROVIDER: Literal["openai", "deepseek"] = "openai"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # DeepSeek  (OpenAI-compatible API)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"          # deepseek-chat | deepseek-reasoner
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Reddit
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "TrendSee/1.0"

    # Platform cookies (required for real data from XHS / Douyin)
    # Copy from browser DevTools → Application → Cookies after logging in.
    XHS_COOKIE: str = ""
    DOUYIN_COOKIE: str = ""

    # Proxy
    HTTP_PROXY: str = ""
    HTTPS_PROXY: str = ""

    class Config:
        env_file = _ENV_FILE
        case_sensitive = True


settings = Settings()
