from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_or_health():
    # adjust to your actual route(s)
    r = client.get("/")
    assert r.status_code in (200, 404)


def test_foods_crud_smoke(monkeypatch):
    # If your endpoints require auth, override that dependency for tests:
    # Example shown if you have a Depends(CurrentUser).
    try:
        from app.main import CurrentUser  # adjust import to wherever you define it

        app.dependency_overrides[CurrentUser] = lambda: "test@example.com"
    except Exception:
        pass  # if not needed, ignore

    payload = {
        "name": "Oats",
        "calories": 380,
        "protein": 13,
        "carbs": 67,
        "fat": 7,
        "fiber": 8,
        "sugar": 1,
    }
    r = client.post("/foods", json=payload)
    assert r.status_code in (200, 201)

    r = client.get("/foods")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
