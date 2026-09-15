"""Tests for account and transaction agents.

All tests use an in-memory SQLite database — no containers needed.
We test that get_context() returns the right data in the right format.
"""

import os
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.agents.account_agent import get_context as account_context
from app.agents.transaction_agent import get_context as transaction_context
from app.auth import hash_password
from app.database import Base
from app.models import Account, Transaction, User

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def user_with_account(db):
    user = User(customer_id="CUST1001", name="Ananya Sharma",
                email="ananya@example.com", phone="9800000000",
                password_hash=hash_password("CUST1001"))
    db.add(user)
    db.flush()

    account = Account(account_number="9001234567890", user_id=user.id,
                      account_type="savings", balance=Decimal("52340.50"),
                      ifsc="DEMO0001234", branch="Gurugram Main Branch",
                      status="active")
    db.add(account)
    db.flush()

    # Add some transactions
    txns = [
        Transaction(txn_id="TXN001", account_id=account.id,
                    date=datetime(2025, 1, 10, 10, 0), type="credit",
                    amount=Decimal("80000"), balance_after=Decimal("80000"),
                    category="salary", description="Monthly salary credit"),
        Transaction(txn_id="TXN002", account_id=account.id,
                    date=datetime(2025, 1, 12, 14, 0), type="debit",
                    amount=Decimal("25000"), balance_after=Decimal("55000"),
                    category="rent", description="House rent payment"),
        Transaction(txn_id="TXN003", account_id=account.id,
                    date=datetime(2025, 1, 15, 19, 0), type="debit",
                    amount=Decimal("450"), balance_after=Decimal("54550"),
                    category="food", description="Swiggy payment"),
    ]
    db.add_all(txns)
    db.commit()
    return user, account


# ── account agent tests ───────────────────────────────────────────────────────

def test_account_context_contains_masked_number(db, user_with_account):
    user, account = user_with_account
    context = account_context("CUST1001", db)
    assert "XXXXXX7890" in context          # masked
    assert "9001234567890" not in context   # full number never shown


def test_account_context_contains_balance(db, user_with_account):
    context = account_context("CUST1001", db)
    assert "52,340.50" in context


def test_account_context_contains_customer_name(db, user_with_account):
    context = account_context("CUST1001", db)
    assert "Ananya Sharma" in context


def test_account_context_unknown_customer(db):
    context = account_context("CUST9999", db)
    assert "No account" in context


# ── transaction agent tests ───────────────────────────────────────────────────

def test_transaction_context_contains_recent_txns(db, user_with_account):
    context = transaction_context("CUST1001", db)
    assert "salary" in context.lower()
    assert "rent" in context.lower()
    assert "food" in context.lower()


def test_transaction_context_shows_balance(db, user_with_account):
    context = transaction_context("CUST1001", db)
    assert "52,340.50" in context


def test_transaction_context_shows_debit_credit(db, user_with_account):
    context = transaction_context("CUST1001", db)
    assert "+" in context   # credit
    assert "-" in context   # debit


def test_transaction_context_unknown_customer(db):
    context = transaction_context("CUST9999", db)
    assert "No" in context