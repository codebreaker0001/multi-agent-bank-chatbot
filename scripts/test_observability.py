"""Observability tests — GET /metrics reflects real /chat traffic."""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.auth import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models import User
from app.observability import _counts, _recent_calls  # reset between tests

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)


def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    db = TestSession()
    db.add(User(customer_id="CUST1001", name="Ananya Sharma", email="ananya@example.com",
                phone="9800000000", password_hash=hash_password("CUST1001")))
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = override_db
    _counts.clear()
    _recent_calls.clear()
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {create_access_token('CUST1001', 'Ananya Sharma')}"}


def mock_groq_response(content: str):
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


def test_metrics_shape_before_any_chat(client, headers):
    res = client.get("/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_calls"] == 0
    assert data["agent_counts"] == {}
    assert data["recent_calls"] == []
    assert data["memory_mb"] > 0


@patch("app.coordinator.client")
def test_metrics_records_agent_after_chat(mock_groq, client, headers):
    mock_groq.chat.completions.create.side_effect = [
        mock_groq_response("account"),  # classify_intent, in app/main.py
        mock_groq_response("Your balance is ₹50,000."),  # the sub-agent
    ]
    with patch("app.main.is_rate_limited", return_value=False), \
         patch("app.main.get_history", return_value=[]), \
         patch("app.main.add_message"):
        client.post("/chat", json={"message": "what is my balance?", "session_id": "s1"}, headers=headers)

    res = client.get("/metrics", headers=headers)
    data = res.json()
    assert data["total_calls"] == 1
    assert data["agent_counts"] == {"account": 1}
    assert data["recent_calls"][0]["agent"] == "Account Agent"
    assert data["recent_calls"][0]["latency_ms"] >= 0


def test_metrics_requires_auth(client):
    assert client.get("/metrics").status_code == 401
