import time
import json
import hashlib
from typing import Any, Callable, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text
from db.base import Base

class ApiCache(Base):
    __tablename__ = "api_cache"

    cache_key = Column(String(255), primary_key=True, index=True)
    response_data = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

# L1: メモリキャッシュ
_memory_cache: dict[str, tuple[float, Any]] = {}

def get_cached_response(
    cache_key: str,
    db: Session,
    fetch_func: Callable[[], Any],
    memory_ttl: int = 60,
    db_ttl: int = 300,
) -> Any:
    """
    TTLメモリキャッシュ (L1) + DBキャッシュ (L2) の二重キャッシュ。
    外部障害時はDB上の期限切れキャッシュへのフォールバック（Graceful Degradation）を行う。
    """
    now = time.time()
    now_utc = datetime.now(timezone.utc)

    # 1. メモリキャッシュ確認
    if cache_key in _memory_cache:
        expire_time, data = _memory_cache[cache_key]
        if now < expire_time:
            return data

    # 2. DBキャッシュ確認
    cached_record = db.query(ApiCache).filter(ApiCache.cache_key == cache_key).first()
    if cached_record and cached_record.expires_at > now_utc:
        data = json.loads(cached_record.response_data)
        _memory_cache[cache_key] = (now + memory_ttl, data)
        return data

    # 3. 外部APIから取得
    try:
        fresh_data = fetch_func()
        # メモリ保存
        _memory_cache[cache_key] = (now + memory_ttl, fresh_data)
        # DB保存
        serialized = json.dumps(fresh_data)
        expires_at = datetime.fromtimestamp(now + db_ttl, tz=timezone.utc)
        
        if cached_record:
            cached_record.response_data = serialized
            cached_record.expires_at = expires_at
        else:
            new_record = ApiCache(
                cache_key=cache_key,
                response_data=serialized,
                expires_at=expires_at
            )
            db.add(new_record)
        db.commit()
        return fresh_data
    except Exception as e:
        # 外部障害時: 期限切れDBキャッシュがあればフォールバック返却
        if cached_record:
            return json.loads(cached_record.response_data)
        raise e
