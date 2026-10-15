from fastapi import Header, HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from pydantic import BaseModel
from core.config import settings

class AuthenticatedUser(BaseModel):
    user_id: str
    email: str

def get_current_user(
    x_goog_iap_jwt_assertion: str | None = Header(None, alias="X-Goog-IAP-JWT-Assertion")
) -> AuthenticatedUser:
    """
    IAP JWTアサーションを検証して認証済みユーザーを返却するFastAPI依存性。
    DEBUG=True かつローカル実行時のみモックユーザーを返却。本番環境では署名検証を強制。
    """
    # 開発環境・ローカル実行時のセーフティバイパス
    if settings.DEBUG:
        if settings.ALLOW_LOCAL_AUTH_BYPASS:
            return AuthenticatedUser(
                user_id="local-dev-user-001",
                email="dev@example.com"
            )

    if not x_goog_iap_jwt_assertion:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required IAP JWT assertion header."
        )

    try:
        # Google 公開鍵による署名検証および Audience 検証
        payload = id_token.verify_token(
            x_goog_iap_jwt_assertion,
            requests.Request(),
            audience=settings.IAP_AUDIENCE
        )
        return AuthenticatedUser(
            user_id=payload["sub"],
            email=payload.get("email", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid IAP JWT assertion: {str(e)}"
        )
