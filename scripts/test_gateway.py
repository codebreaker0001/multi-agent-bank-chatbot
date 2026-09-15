"""Gateway tests.

Uses FastAPI's TestClient so no server needs to be running.
The rate limiter is mocked so tests don't need a real Redis instance.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

HEADERS = {"Authorization": "Bearer user-123"}


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_chat_returns_200():
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "hello", "session_id": "s1"}, headers=HEADERS)
    assert res.status_code == 200
    assert "reply" in res.json()
    assert res.json()["session_id"] == "s1"


def test_empty_message_rejected():
    """Pydantic should reject an empty message before it hits any logic."""
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "", "session_id": "s1"}, headers=HEADERS)
    assert res.status_code == 422


def test_message_too_long_rejected():
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "x" * 1001, "session_id": "s1"}, headers=HEADERS)
    assert res.status_code == 422


def test_missing_body_rejected():
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", headers=HEADERS)
    assert res.status_code == 422


def test_missing_auth_rejected():
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "hello", "session_id": "s1"})
    assert res.status_code == 422  # Header(...) makes it required


def test_rate_limit_returns_429():
    with patch("app.main.is_rate_limited", return_value=True):
        res = client.post("/chat", json={"message": "hello", "session_id": "s1"}, headers=HEADERS)
    assert res.status_code == 429
    assert "Too many requests" in res.json()["error"]


def test_request_id_in_response_headers():
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "hi", "session_id": "s1"}, headers=HEADERS)
    assert "x-request-id" in res.headers