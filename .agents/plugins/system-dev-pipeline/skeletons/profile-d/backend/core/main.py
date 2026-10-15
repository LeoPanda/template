from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.security import SessionTokenAuthMiddleware
from api.internal.health import router as health_router
from api.v1.example import router as example_router

app = FastAPI(
    title="Profile D Local Engine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (Tauri / Localhost 開発対応)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 動的セッショントークン認証ミドルウェア
app.add_middleware(SessionTokenAuthMiddleware)

# ルーター登録
app.include_router(health_router, prefix="/api/internal", tags=["internal"])
app.include_router(example_router, prefix="/api/v1", tags=["example"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.main:app", host="127.0.0.1", port=settings.APP_PORT, reload=settings.DEBUG)
