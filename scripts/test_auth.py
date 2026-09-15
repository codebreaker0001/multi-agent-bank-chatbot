"""Auth tests — login, JWT, and protected routes."""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.auth import create_token, decode_token, hash_password, verify_password
from app.database import Base, get_db
from app.main import app
from app.models import User

# One shared in-memory engine for this test file
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
def token():
    return create_token("CUST1001", "Ananya Sharma")


# ── password ──────────────────────────────────────────────────────────────────

def test_password_hash_is_not_plaintext():
    h = hash_password("mysecret")
    assert h != "mysecret" and len(h) > 20


def test_correct_password_verifies():
    assert verify_password("mysecret", hash_password("mysecret")) is True


def test_wrong_password_fails():
    assert verify_password("wrong", hash_password("mysecret")) is False


# ── JWT ───────────────────────────────────────────────────────────────────────

def test_token_contains_customer_id_and_name():
    payload = decode_token(create_token("CUST1001", "Ananya Sharma"))
    assert payload["sub"] == "CUST1001"
    assert payload["name"] == "Ananya Sharma"


def test_tampered_token_is_rejected():
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_token("not.a.real.token")


# ── login endpoint ────────────────────────────────────────────────────────────

def test_login_returns_token(client):
    res = client.post("/login", json={"customer_id": "CUST1001", "password": "CUST1001"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["name"] == "Ananya Sharma"


def test_wrong_password_returns_401(client):
    res = client.post("/login", json={"customer_id": "CUST1001", "password": "wrongpass"})
    assert res.status_code == 401


def test_unknown_user_returns_401(client):
    res = client.post("/login", json={"customer_id": "CUST9999", "password": "anything"})
    assert res.status_code == 401


# ── protected /chat ───────────────────────────────────────────────────────────

def test_chat_requires_token(client):
    # HTTPBearer returns 403 when the Authorization header is missing entirely
    res = client.post("/chat", json={"message": "hello", "session_id": "s1"})
    assert res.status_code == 401


def test_chat_rejects_invalid_token(client):
    res = client.post("/chat", json={"message": "hello", "session_id": "s1"},
                      headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401


def test_chat_works_with_valid_token(client, token):
    with patch("app.main.is_rate_limited", return_value=False):
        res = client.post("/chat", json={"message": "hello", "session_id": "s1"},
                          headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "Ananya Sharma" in res.json()["reply"]


def test_chat_rate_limited_returns_429(client, token):
    with patch("app.main.is_rate_limited", return_value=True):
        res = client.post("/chat", json={"message": "hello", "session_id": "s1"},
                          headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 429