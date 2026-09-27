"""Dashboard tests — /accounts, /transactions, /cards."""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.auth import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Account, Transaction, User

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
    user = User(customer_id="CUST1001", name="Ananya Sharma", email="ananya@example.com",
                phone="9800000000", password_hash=hash_password("CUST1001"))
    db.add(user)
    db.flush()
    account = Account(account_number="9012345678", user_id=user.id, account_type="savings",
                       balance=50000, ifsc="DEMO0001234", branch="Test Branch")
    db.add(account)
    db.flush()
    db.add(Transaction(txn_id="TXN1", account_id=account.id, date=datetime.combine(date.today(), datetime.min.time()),
                        type="debit", amount=649, balance_after=49351, category="entertainment",
                        description="Netflix payment"))
    db.commit()
    db.close()
    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def headers():
    token = create_access_token("CUST1001", "Ananya Sharma")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)


def test_accounts_returns_real_balance(client, headers):
    res = client.get("/accounts", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data[0]["balance"] == "50000.00"
    assert data[0]["account_number_masked"] == "XXXXXX5678"


def test_transactions_strips_merchant_suffix_and_sums_category(client, headers):
    res = client.get("/transactions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["transactions"][0]["merchant"] == "Netflix"  # "Netflix payment" -> "Netflix"
    assert data["total_this_month"] == "649.00"
    assert data["spending_by_category"] == [{"category": "Entertainment", "amount": "649.00"}]
    assert data["month_over_month_pct"] is None  # no transactions last month to compare against


def test_card_freeze_persists(client, headers):
    assert client.get("/cards", headers=headers).json()["frozen"] is False
    assert client.post("/cards/freeze", headers=headers).json()["frozen"] is True
    # Persisted, not just returned — a fresh GET still sees it.
    assert client.get("/cards", headers=headers).json()["frozen"] is True
    assert client.post("/cards/unfreeze", headers=headers).json()["frozen"] is False


def test_dashboard_routes_require_auth(client):
    assert client.get("/accounts").status_code == 401
    assert client.get("/transactions").status_code == 401
    assert client.get("/cards").status_code == 401
