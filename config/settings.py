"""
config/settings.py
Central config — reads from .env via pydantic-settings.
"""
from functools import lru_cache
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings   # pip install pydantic-settings
from pydantic import AliasChoices, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
os.environ.setdefault("CREWAI_STORAGE_DIR", str(PROJECT_ROOT / ".crewai"))


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────
    groq_api_key: str = Field("", env="GROQ_API_KEY")
    groq_model: str = Field(
        "llama3-70b-8192",
        env="GROQ_MODEL",
        validation_alias=AliasChoices("GROQ_MODEL", "MODEL", "model"),
    )

    # ── GitHub ────────────────────────────────────────────────────────────
    github_token: str = Field("", env="GITHUB_TOKEN")

    # ── Web Search ────────────────────────────────────────────────────────
    tavily_api_key: str = Field("", env="TAVILY_API_KEY")

    # ── LangSmith ────────────────────────────────────────────────────────
    langchain_tracing_v2: bool = Field(True, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field("", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field("multi-agent-outreach", env="LANGCHAIN_PROJECT")

    # ── Google ────────────────────────────────────────────────────────────
    google_client_id: str = Field("", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        "http://localhost:8000/auth/callback", env="GOOGLE_REDIRECT_URI"
    )

    # ── App behaviour ────────────────────────────────────────────────────
    max_projects_to_scout: int = Field(10, env="MAX_PROJECTS_TO_SCOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    human_approval_required: bool = Field(True, env="HUMAN_APPROVAL_REQUIRED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
