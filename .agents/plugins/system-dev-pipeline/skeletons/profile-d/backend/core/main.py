import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.config import settings
from core.security import SessionTokenAuthMiddleware
from db.session import engine
from api.internal.health import router as health_router
from api.v1.example import router as example_router

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
    title="Profile D Local Engine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(health_router, prefix="/api/internal", tags=["internal"])
app.include_router(example_router, prefix="/api/v1", tags=["example"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.main:app", host="127.0.0.1", port=settings.APP_PORT, reload=settings.DEBUG)
