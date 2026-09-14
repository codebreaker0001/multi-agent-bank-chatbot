"""Basic tests for the database models. Uses an in-memory SQLite database."""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Account, Address, User


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def add_user(db):
    user = User(customer_id="CUST1001", name="Test User",
                email="test@example.com", phone="9800000000")
    db.add(user)
    db.flush()
    return user


def test_account_number_is_masked(db):
    user = add_user(db)
    account = Account(account_number="9001234567", user_id=user.id,
                      account_type="savings", balance=Decimal("1000"),
                      ifsc="DEMO0001234", branch="Test Branch")
    assert account.masked_number == "XXXXXX4567"


def test_balance_uses_exact_decimals(db):
    """Money must not lose precision. This is why we use Numeric, not Float."""
    user = add_user(db)
    account = Account(account_number="9001234567", user_id=user.id,
                      account_type="savings",
                      balance=Decimal("0.10") + Decimal("0.20"),
                      ifsc="DEMO0001234", branch="Test Branch")
    db.add(account)
    db.commit()
    assert account.balance == Decimal("0.30")


def test_user_can_have_multiple_accounts(db):
    user = add_user(db)
    for i in range(2):
        db.add(Account(account_number=f"900123456{i}", user_id=user.id,
                       account_type="savings", balance=Decimal("1000"),
                       ifsc="DEMO0001234", branch="Test Branch"))
    db.commit()
    assert len(user.accounts) == 2


def test_old_address_is_kept_after_change(db):
    """Changing an address adds a new row instead of overwriting, so the
    customer can still ask what their previous address was."""
    user = add_user(db)
    old = Address(user_id=user.id, line1="Old Street", city="Gurugram",
                  state="Haryana", pincode="122002", is_current=True)
    db.add(old)
    db.commit()

    old.is_current = False
    db.add(Address(user_id=user.id, line1="New Street", city="Mumbai",
                   state="Maharashtra", pincode="400050", is_current=True))
    db.commit()

    assert len(user.addresses) == 2
    current = [a for a in user.addresses if a.is_current]
    assert len(current) == 1
    assert current[0].city == "Mumbai"