from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings

class SessionTokenAuthMiddleware(BaseHTTPMiddleware):
    """
    ローカル HTTP 通信における動的セッショントークン検証ミドルウェア
    (Tauri Core から注入されたトークンを照合し、マシン内別プロセスからのアクセスを遮断)
    """
    async def dispatch(self, request: Request, call_next):
        # ヘルスチェックおよびドキュメントはバイパス可能
        if request.url.path in ["/api/internal/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        token = request.headers.get("X-App-Session-Token")
        if not token or token != settings.APP_SESSION_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized local access: Invalid or missing session token."
            )
        return await call_next(request)
