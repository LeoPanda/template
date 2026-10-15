def test_health_check(client):
    response = client.get("/api/internal/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True

def test_litestream_status(client):
    response = client.get("/api/internal/litestream/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
