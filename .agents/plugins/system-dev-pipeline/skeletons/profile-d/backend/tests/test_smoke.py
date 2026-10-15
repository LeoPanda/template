from fastapi.testclient import TestClient
from core.main import app

def test_health_check(client: TestClient):
    """ヘルスチェックエンドポイント疎通検証"""
    response = client.get("/api/internal/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthorized_access_without_token():
    """動的トークンなしでのリクエストが 403 で拒絶されることを検証"""
    unauthed_client = TestClient(app)
    response = unauthed_client.get("/api/v1/items")
    assert response.status_code == 403

def test_authorized_get_items(client: TestClient):
    """トークン付きリクエストが正常にアイテムを返却することを検証"""
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "updated_at" in data[0]
