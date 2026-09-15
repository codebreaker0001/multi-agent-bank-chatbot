"""Tests for the service agent and /service/action endpoint."""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.agents.service_agent import get_context, request_cheque_book, update_address, update_kyc
from app.auth import create_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models import KYC, Account, Address, ServiceRequest, User

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
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def user_with_data(db):
    user = User(customer_id="CUST1001", name="Ananya Sharma",
                email="ananya@example.com", phone="9800000000",
                password_hash=hash_password("CUST1001"))
    db.add(user)
    db.flush()

    db.add(Account(account_number="9001234567890", user_id=user.id,
                   account_type="savings", balance=52340,
                   ifsc="DEMO0001234", branch="Gurugram Branch"))
    db.add(Address(user_id=user.id, line1="10 Park Avenue", city="Gurugram",
                   state="Haryana", pincode="122002", is_current=True))
    db.add(KYC(user_id=user.id, document_type="pan",
               document_number="XXXXX1234X", status="verified"))
    db.commit()
    return user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_token('CUST1001', 'Ananya Sharma')}"}


# ── get_context ───────────────────────────────────────────────────────────────

def test_context_shows_current_address(db, user_with_data):
    context = get_context("CUST1001", db)
    assert "10 Park Avenue" in context
    assert "Gurugram" in context


def test_context_shows_kyc_status(db, user_with_data):
    context = get_context("CUST1001", db)
    assert "PAN" in context
    assert "verified" in context


def test_context_unknown_customer(db):
    context = get_context("CUST9999", db)
    assert "No customer" in context


# ── update_address ────────────────────────────────────────────────────────────

def test_update_address_creates_new_row(db, user_with_data):
    update_address("CUST1001", "5 MG Road", "Bengaluru", "Karnataka", "560001", db)
    addresses = db.query(Address).filter(Address.user_id == user_with_data.id).all()
    assert len(addresses) == 2  # old + new


def test_update_address_deactivates_old(db, user_with_data):
    update_address("CUST1001", "5 MG Road", "Bengaluru", "Karnataka", "560001", db)
    current = db.query(Address).filter(
        Address.user_id == user_with_data.id, Address.is_current == True
    ).all()
    assert len(current) == 1
    assert current[0].city == "Bengaluru"


def test_update_address_returns_confirmation(db, user_with_data):
    result = update_address("CUST1001", "5 MG Road", "Bengaluru", "Karnataka", "560001", db)
    assert "Bengaluru" in result
    assert "updated" in result.lower()


# ── request_cheque_book ───────────────────────────────────────────────────────

def test_cheque_book_creates_service_request(db, user_with_data):
    request_cheque_book("CUST1001", db)
    tickets = db.query(ServiceRequest).filter(
        ServiceRequest.user_id == user_with_data.id
    ).all()
    assert len(tickets) == 1
    assert tickets[0].request_type == "cheque_book"
    assert tickets[0].status == "submitted"


def test_cheque_book_returns_ticket_id(db, user_with_data):
    result = request_cheque_book("CUST1001", db)
    assert "SR" in result
    assert "Ticket ID" in result


# ── update_kyc ────────────────────────────────────────────────────────────────

def test_update_kyc_sets_status_pending(db, user_with_data):
    update_kyc("CUST1001", "pan", db)
    kyc = db.query(KYC).filter(KYC.user_id == user_with_data.id).first()
    assert kyc.status == "pending"


def test_update_kyc_creates_record_if_missing(db, user_with_data):
    update_kyc("CUST1001", "aadhaar", db)
    aadhaar = db.query(KYC).filter(
        KYC.user_id == user_with_data.id, KYC.document_type == "aadhaar"
    ).first()
    assert aadhaar is not None
    assert aadhaar.status == "pending"


# ── /service/action endpoint ──────────────────────────────────────────────────

def test_service_action_update_address(client, auth_headers, user_with_data):
    res = client.post("/service/action", json={
        "action": "update_address",
        "line1": "5 MG Road", "city": "Bengaluru",
        "state": "Karnataka", "pincode": "560001"
    }, headers=auth_headers)
    assert res.status_code == 200
    assert "Bengaluru" in res.json()["message"]


def test_service_action_cheque_book(client, auth_headers, user_with_data):
    res = client.post("/service/action",
                      json={"action": "request_cheque_book"},
                      headers=auth_headers)
    assert res.status_code == 200
    assert "SR" in res.json()["message"]


def test_service_action_kyc_update(client, auth_headers, user_with_data):
    res = client.post("/service/action",
                      json={"action": "update_kyc", "document_type": "aadhaar"},
                      headers=auth_headers)
    assert res.status_code == 200
    assert "AADHAAR" in res.json()["message"]


def test_service_action_address_missing_fields(client, auth_headers, user_with_data):
    res = client.post("/service/action", json={
        "action": "update_address",
        "line1": "5 MG Road"  # missing city, state, pincode
    }, headers=auth_headers)
    assert res.status_code == 400


def test_service_action_requires_auth(client):
    res = client.post("/service/action", json={"action": "request_cheque_book"})
    assert res.status_code == 401