import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.internal.health import router as health_router
from api.internal.litestream import router as litestream_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内部監視ルーターの登録
app.include_router(health_router, prefix="/api/internal", tags=["internal"])
app.include_router(litestream_router, prefix="/api/internal", tags=["internal"])

# 静的SPAファイルの配信（本番環境）
STATIC_DIR = "/app/frontend/dist"
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
