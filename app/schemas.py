"""Request and response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    customer_id: str
    name: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=100)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    # Which sub-agent answered — None for "unknown" intent, where no
    # sub-agent runs and the coordinator's canned reply is returned instead.
    agent: Optional[str] = None


class ServiceActionRequest(BaseModel):
    """Called after the user confirms a service change in chat."""
    action: Literal["update_address", "request_cheque_book", "update_kyc"]
    # update_address fields
    line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # update_kyc field
    document_type: Optional[str] = None


class ServiceActionResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str


# ── dashboard (real DB data, for the UI's right panel / overview pages) ────────

class AccountOut(BaseModel):
    account_number_masked: str
    account_type: str
    balance: Decimal
    # The schema has one balance field, not a separate "available" figure
    # (no holds/pending-authorization concept) — this always equals balance.
    available_balance: Decimal
    status: str
    ifsc: str
    branch: str


class TransactionOut(BaseModel):
    id: str
    merchant: str
    category: Optional[str]
    date: datetime
    amount: Decimal
    type: Literal["debit", "credit"]


class CategorySpend(BaseModel):
    category: str
    amount: Decimal


class TransactionsResponse(BaseModel):
    transactions: list[TransactionOut]
    spending_by_category: list[CategorySpend]  # current calendar month, debits only
    total_this_month: Decimal
    # None when last month had no spending to compare against (divide-by-zero).
    month_over_month_pct: Optional[float]


class CardOut(BaseModel):
    """The account's debit card. Only `frozen` is persisted state — network
    and expiry aren't modeled anywhere, so they're fixed illustrative values."""
    last4: str
    holder: str
    network: str = "Visa"
    expiry: str = "09/28"
    frozen: bool


# ── observability ────────────────────────────────────────────────────────────

class AgentCallOut(BaseModel):
    timestamp: float
    intent: str
    agent: Optional[str]
    latency_ms: float


class MetricsOut(BaseModel):
    uptime_seconds: float
    cpu_percent: float
    memory_mb: float
    total_calls: int
    agent_counts: dict[str, int]
    recent_calls: list[AgentCallOut]