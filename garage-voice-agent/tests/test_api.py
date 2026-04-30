from pathlib import Path

from fastapi.testclient import TestClient

from api.config import PROJECT_ROOT, ApiSettings, get_api_settings
from api.main import app


def _client(tmp_path: Path) -> TestClient:
    settings = ApiSettings(
        livekit_url="wss://demo.livekit.cloud",
        livekit_api_key="devkey",
        livekit_api_secret="devsecret-devsecret-devsecret-devsecret",
        local_call_store_path=tmp_path / "calls.json",
    )
    app.dependency_overrides[get_api_settings] = lambda: settings
    return TestClient(app)


def test_health(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.get("/health").json() == {"status": "ok"}
    app.dependency_overrides.clear()


def test_create_session_returns_livekit_token_and_call_id(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.post(
        "/sessions",
        json={"garage_id": "demo-garage", "scenario": "revision", "voice": "femme"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["room_name"].startswith("garage-demo-revision-")
    assert payload["participant_identity"].startswith("demo-user-")
    assert payload["token"].count(".") == 2
    assert payload["call_id"].startswith("call-")
    app.dependency_overrides.clear()


def test_calls_endpoint_is_not_exposed(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.get("/calls").status_code == 404
    assert client.get("/calls/call-demo").status_code == 404
    app.dependency_overrides.clear()


def test_demo_seed_endpoint_is_not_exposed(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post("/demo/seed").status_code == 404
    app.dependency_overrides.clear()


def test_garage_profile_endpoint_is_not_exposed(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.get("/garage-profile").status_code == 404
    assert client.put("/garage-profile", json={}).status_code == 404
    app.dependency_overrides.clear()


def test_project_root_points_to_repo() -> None:
    assert (PROJECT_ROOT / "pyproject.toml").exists()
