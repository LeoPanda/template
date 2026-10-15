import pytest
from fastapi.testclient import TestClient
from core.main import app
from core.config import settings

@pytest.fixture
def client():
    # テスト用クライアント（X-App-Session-Token ヘッダーを自動付与）
    c = TestClient(app)
    c.headers.update({"X-App-Session-Token": settings.APP_SESSION_TOKEN})
    return c
