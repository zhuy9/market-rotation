from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_only_the_documented_dev_origin():
    """The dev frontend runs on 5173 and nothing else is allowed, including
    another localhost port."""
    client = TestClient(app)

    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    for origin in ("http://localhost:5174", "https://evil.example"):
        blocked = client.get("/api/health", headers={"Origin": origin})
        assert "access-control-allow-origin" not in blocked.headers, origin
