import os

os.environ["JWT_SECRET"] = "test-only-secret-that-is-at-least-32-chars"
os.environ["MAX_PROMPT_LENGTH"] = "12000"
os.environ["RATE_LIMIT"] = "30/minute"

from fastapi.testclient import TestClient

from app.auth import create_access_token
import app.main as main

client = TestClient(main.app)


def test_chat_rejects_missing_token():
    response = client.post(
        "/v1/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )

    assert response.status_code == 401


def test_chat_returns_mocked_response(monkeypatch):
    monkeypatch.setattr(main, "generate_response", lambda _payload: "Mock reply")
    token = create_access_token("test-user")

    response = client.post(
        "/v1/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Mock reply"


def test_chat_rejects_oversized_prompt():
    token = create_access_token("test-user")
    response = client.post(
        "/v1/chat",
        json={"messages": [{"role": "user", "content": "x" * 12001}]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 413
