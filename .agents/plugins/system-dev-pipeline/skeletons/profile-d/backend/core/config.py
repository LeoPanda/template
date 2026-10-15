from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_PORT: int = 54321
    APP_SESSION_TOKEN: str = "local-dev-token"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./app.db"

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
