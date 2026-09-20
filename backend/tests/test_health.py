from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_any_localhost_port_but_not_a_remote_origin():
    """Vite moves off 5173 when the port is taken, so pinning a single origin
    broke the dashboard with only a console error to show for it."""
    client = TestClient(app)

    for origin in ("http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:4173"):
        response = client.get("/api/health", headers={"Origin": origin})
        assert response.headers.get("access-control-allow-origin") == origin, origin

    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in blocked.headers
