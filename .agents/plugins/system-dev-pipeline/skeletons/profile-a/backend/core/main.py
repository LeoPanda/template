import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.config import settings
from db.session import engine
from api.internal.health import router as health_router
from api.internal.litestream import router as litestream_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時フェイルファスト検証 (Fail-Fast Lifespan Probe)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"FATAL: Database connection failed during startup lifespan probe: {e}", file=sys.stderr)
        raise e
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 監視・ヘルスチェックルーターの登録
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(health_router, prefix="/api/internal", tags=["internal"])
app.include_router(litestream_router, prefix="/api/internal", tags=["internal"])

# 静的SPAファイルの配信（本番環境）
STATIC_DIR = "/app/frontend/dist"
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
