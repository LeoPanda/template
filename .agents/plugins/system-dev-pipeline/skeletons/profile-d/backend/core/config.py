from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_PORT: int = 54321
    APP_SESSION_TOKEN: str = "local-dev-token"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./app.db"

    @property
    def resolved_database_url(self) -> str:
        """ホスト/コンテナ環境自動適応型 Database URL リゾルバ (Core-Absorbed Resilience)"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            raw_path = self.DATABASE_URL.replace("sqlite:///", "")
            path_obj = Path(raw_path)
            if not path_obj.parent.exists() and (str(path_obj).startswith("/data") or str(path_obj).startswith("/app/")):
                fallback_dir = Path("data")
                fallback_dir.mkdir(parents=True, exist_ok=True)
                return f"sqlite:///{fallback_dir / path_obj.name}"
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        return self.DATABASE_URL

    @field_validator("APP_SESSION_TOKEN")
    @classmethod
    def validate_token(cls, v: str) -> str:
        # 本番モードでのプレースホルダー即死ガードレール
        if v in ["[YOUR_APP_SESSION_TOKEN]", "changeme", "secret", "xxxxxx"]:
            raise ValueError(f"Insecure placeholder session token detected: {v}")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
