from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Tauri Core 起動時のヘルスチェック・ポーリング用エンドポイント"""
    return {"status": "ok"}
