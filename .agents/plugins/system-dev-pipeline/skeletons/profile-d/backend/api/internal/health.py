from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import get_db

router = APIRouter()

@router.get("/health")
def health_check(deep: bool = False, db: Session = Depends(get_db)):
    """Tauri Core 起動時のヘルスチェック・ポーリング用エンドポイント (Deep Health Probe対応)"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "engine": "sqlite",
            },
            "deep": deep,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}",
        )
