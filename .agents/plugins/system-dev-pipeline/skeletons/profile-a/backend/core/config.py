from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Profile A Web System"
    DEBUG: bool = False
    ALLOW_LOCAL_AUTH_BYPASS: bool = False
    
    # DB & インフラ設定
    DATABASE_URL: str = "sqlite:////data/app.db"
    LITESTREAM_BUCKET: str = ""
    
    # IAP 設定 (本番では必須)
    IAP_AUDIENCE: str = ""
    
    # 外部API設定
    EXTERNAL_API_KEY: str = ""

    @field_validator("IAP_AUDIENCE")
    def validate_iap_audience(cls, v, info):
        # 本番環境 (DEBUG=False) では IAP_AUDIENCE の未設定やプレースホルダーを禁止
        debug = info.data.get("DEBUG", False)
        if not debug:
            if not v or v.startswith("[YOUR_") or "example" in v:
                raise ValueError("FATAL: IAP_AUDIENCE must be properly configured in production!")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
