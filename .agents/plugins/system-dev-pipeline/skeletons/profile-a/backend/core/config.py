from pathlib import Path
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

    @property
    def resolved_database_url(self) -> str:
        """ホスト/コンテナ環境自動適応型 Database URL リゾルバ (Core-Absorbed Resilience)"""
        if self.DATABASE_URL.startswith("sqlite:///"):
            raw_path = self.DATABASE_URL.replace("sqlite:///", "")
            path_obj = Path(raw_path)
            # コンテナ内絶対パス (/data/... または /app/data/...) がホスト上で存在しない場合
            if not path_obj.parent.exists() and (str(path_obj).startswith("/data") or str(path_obj).startswith("/app/")):
                fallback_dir = Path("data")
                fallback_dir.mkdir(parents=True, exist_ok=True)
                return f"sqlite:///{fallback_dir / path_obj.name}"
            # 通常パスの親ディレクトリ自動作成
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        return self.DATABASE_URL

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
        extra = "ignore"

settings = Settings()
