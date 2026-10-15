from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone

router = APIRouter()

class ItemResponse(BaseModel):
    id: str
    name: str
    updated_at: str

@router.get("/items", response_model=List[ItemResponse])
def get_items():
    """サンプルアイテム一覧取得 (Aware UTC 日時形式)"""
    now_utc = datetime.now(timezone.utc).isoformat()
    return [
        {"id": "1", "name": "ローカルプロジェクトA", "updated_at": now_utc},
        {"id": "2", "name": "ローカルプロジェクトB", "updated_at": now_utc},
    ]
