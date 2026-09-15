"""Mock bank database models.

Six tables, one group per agent:
    User, Account            -> account agent (balance, account details)
    Transaction              -> transaction agent (history, statements)
    Address, KYC, ServiceRequest -> service agent (address change, KYC, cheque book)
"""

from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    # Filled in on day 3 when Keycloak creates the login.
    password_hash = Column(String(200), nullable=False)

    accounts = relationship("Account", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    kyc_records = relationship("KYC", back_populates="user")
    requests = relationship("ServiceRequest", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    account_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_type = Column(String(20), nullable=False)  # savings / current
    # Numeric, never Float. Float rounding errors are unacceptable for money.
    balance = Column(Numeric(12, 2), nullable=False, default=0)
    ifsc = Column(String(15), nullable=False)
    branch = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    opened_on = Column(Date, default=date.today)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

    @property
    def masked_number(self):
        """Only the last 4 digits are ever shown to the user or written to logs."""
        return "XXXXXX" + self.account_number[-4:]


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    txn_id = Column(String(30), unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.now)
    type = Column(String(10), nullable=False)  # debit / credit
    amount = Column(Numeric(12, 2), nullable=False)
    # Balance after this transaction, so statements don't need recalculating.
    balance_after = Column(Numeric(12, 2), nullable=False)
    category = Column(String(30))  # food, shopping, salary, rent...
    description = Column(String(200))

    account = relationship("Account", back_populates="transactions")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    line1 = Column(String(150), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    pincode = Column(String(10), nullable=False)
    # Changing an address adds a new row and sets this to False on the old one,
    # so the old address is still available if the customer asks.
    is_current = Column(Boolean, default=True)
    updated_on = Column(Date, default=date.today)

    user = relationship("User", back_populates="addresses")


class KYC(Base):
    __tablename__ = "kyc_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(20), nullable=False)  # pan / aadhaar
    # Only the masked number is stored. The chatbot never needs the full one.
    document_number = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)  # verified / pending / expired
    updated_on = Column(Date, default=date.today)

    user = relationship("User", back_populates="kyc_records")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(String(30), nullable=False)  # address_change / cheque_book / kyc_update
    status = Column(String(20), default="submitted")
    details = Column(String(300))
    created_on = Column(Date, default=date.today)

    user = relationship("User", back_populates="requests")