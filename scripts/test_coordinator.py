"""Coordinator tests.

The Groq API is mocked in all tests — no real API key needed.
We test that:
  - classify_intent returns the right category for different messages
  - run() routes to the correct agent prompt
  - run() handles unknown intents gracefully
  - the /chat endpoint calls the coordinator and returns its reply
"""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.auth import create_token, hash_password
from app.coordinator import UNKNOWN_REPLY, classify_intent, run
from app.database import Base, get_db
from app.main import app
from app.models import User

# ── helpers ───────────────────────────────────────────────────────────────────

def mock_groq_response(content: str):
    """Build a mock that looks like a Groq API response."""
    mock = MagicMock()
    mock.choices[0].message.content = content
    return mock


# ── classify_intent tests ─────────────────────────────────────────────────────

@patch("app.coordinator.client")
def test_classifies_account_intent(mock_client):
    mock_client.chat.completions.create.return_value = mock_groq_response("account")
    assert classify_intent("what is my balance?") == "account"


@patch("app.coordinator.client")
def test_classifies_transaction_intent(mock_client):
    mock_client.chat.completions.create.return_value = mock_groq_response("transaction")
    assert classify_intent("show my last 5 transactions") == "transaction"


@patch("app.coordinator.client")
def test_classifies_service_intent(mock_client):
    mock_client.chat.completions.create.return_value = mock_groq_response("service")
    assert classify_intent("I want to change my address") == "service"


@patch("app.coordinator.client")
def test_unknown_intent_falls_back(mock_client):
    mock_client.chat.completions.create.return_value = mock_groq_response("something_random")
    assert classify_intent("who won the cricket match?") == "unknown"


# ── run() tests ───────────────────────────────────────────────────────────────

@patch("app.coordinator.client")
def test_run_returns_reply_and_intent(mock_client):
    # First call = classify, second call = agent response
    mock_client.chat.completions.create.side_effect = [
        mock_groq_response("account"),
        mock_groq_response("Your balance is ₹50,000."),
    ]
    reply, intent = run("what is my balance?", history=[])
    assert intent == "account"
    assert "balance" in reply.lower()


@patch("app.coordinator.client")
def test_run_unknown_returns_help_message(mock_client):
    mock_client.chat.completions.create.return_value = mock_groq_response("unknown")
    reply, intent = run("who is the president?", history=[])
    assert intent == "unknown"
    assert reply == UNKNOWN_REPLY


@patch("app.coordinator.client")
def test_run_passes_history_to_agent(mock_client):
    mock_client.chat.completions.create.side_effect = [
        mock_groq_response("transaction"),
        mock_groq_response("Here are your transactions."),
    ]
    history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    run("show my transactions", history=history)

    # Second call is the agent call — check history was passed
    agent_call_messages = mock_client.chat.completions.create.call_args_list[1][1]["messages"]
    roles = [m["role"] for m in agent_call_messages]
    assert "user" in roles and "assistant" in roles


@patch("app.coordinator.client")
def test_run_injects_context_into_system_prompt(mock_client):
    mock_client.chat.completions.create.side_effect = [
        mock_groq_response("account"),
        mock_groq_response("Your balance is ₹50,000."),
    ]
    run("what is my balance?", history=[], context="Balance: 50000")

    system_msg = mock_client.chat.completions.create.call_args_list[1][1]["messages"][0]["content"]
    assert "Balance: 50000" in system_msg


# ── /chat endpoint integration ────────────────────────────────────────────────

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
    db.add(User(customer_id="CUST1001", name="Ananya Sharma",
                email="ananya@example.com", phone="9800000000",
                password_hash=hash_password("CUST1001")))
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_token('CUST1001', 'Ananya Sharma')}"}


@patch("app.coordinator.client")
def test_chat_endpoint_returns_coordinator_reply(mock_groq, client, auth_headers):
    mock_groq.chat.completions.create.side_effect = [
        mock_groq_response("account"),
        mock_groq_response("Your balance is ₹50,000."),
    ]
    with patch("app.main.is_rate_limited", return_value=False), \
         patch("app.main.get_history", return_value=[]), \
         patch("app.main.add_message"):
        res = client.post("/chat", json={"message": "what is my balance?", "session_id": "s1"},
                          headers=auth_headers)
    assert res.status_code == 200
    assert "₹50,000" in res.json()["reply"]


@patch("app.coordinator.client")
def test_chat_endpoint_handles_unknown_intent(mock_groq, client, auth_headers):
    mock_groq.chat.completions.create.return_value = mock_groq_response("unknown")
    with patch("app.main.is_rate_limited", return_value=False), \
         patch("app.main.get_history", return_value=[]), \
         patch("app.main.add_message"):
        res = client.post("/chat", json={"message": "tell me a joke", "session_id": "s1"},
                          headers=auth_headers)
    assert res.status_code == 200
    assert "balance" in res.json()["reply"].lower()  # the fallback message mentions balance