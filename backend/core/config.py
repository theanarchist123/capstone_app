from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from pathlib import Path
import os
import shutil
import sqlite3
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    # Database
    database_url: str
    supabase_url: str
    supabase_key: str
    supabase_bucket: str = "case-reports"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # App
    app_env: str = "development"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004,http://localhost:3005"
    cors_allowed_origin_regex: str = r"^https://.*\.vercel\.app$"

    # AI
    ollama_api_key: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 60

    @property
    def origins_list(self) -> list[str]:
        origins: list[str] = []
        for origin in self.allowed_origins.split(","):
            normalized = origin.strip()
            if not normalized:
                continue
            origins.append(normalized)
            if "localhost" in normalized:
                origins.append(normalized.replace("localhost", "127.0.0.1"))
            elif "127.0.0.1" in normalized:
                origins.append(normalized.replace("127.0.0.1", "localhost"))
        return list(dict.fromkeys(origins))

    @property
    def cors_origin_regex(self) -> str:
        return self.cors_allowed_origin_regex

    model_config = {"env_file": str(Path(__file__).resolve().parent.parent / ".env"), "case_sensitive": False}

    @model_validator(mode="after")
    def _normalize_database_url(self):
        if not self.database_url:
            return self

        if self.database_url.startswith("sqlite") and (os.getenv("VERCEL") == "1" or self.app_env.lower() == "production"):
            parsed_url = make_url(self.database_url)
            database_name = Path(parsed_url.database or "capstone_app.db").name
            runtime_db_path = Path(f"/tmp/{database_name}")
            needs_seed = True
            if runtime_db_path.exists():
                try:
                    with sqlite3.connect(runtime_db_path) as conn:
                        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
                        needs_seed = (row is None) or int(row[0] or 0) == 0
                except sqlite3.Error:
                    needs_seed = True

            if needs_seed:
                bundled_sources = []
                for candidate in [
                    database_name,
                    "oncopilot.db",
                ]:
                    bundled_sources.extend([
                        Path(__file__).resolve().parent.parent / candidate,
                        Path(__file__).resolve().parent.parent.parent / candidate,
                    ])
                for source in bundled_sources:
                    if source.exists():
                        runtime_db_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, runtime_db_path)
                        break
            parsed_url = parsed_url.set(database=str(runtime_db_path))
            self.database_url = str(parsed_url)

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
