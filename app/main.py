"""API Gateway — single entry point for the chatbot.

Endpoints:
  POST /login          authenticate, get an access + refresh token
  POST /refresh        trade a refresh token for a new access token
  GET  /accounts       the customer's accounts
  GET  /transactions   recent transactions + this month's category spend
  GET  /cards          the primary account's (illustrative) debit card
  POST /cards/freeze   freeze the debit card (persisted)
  POST /cards/unfreeze unfreeze the debit card (persisted)
  POST /chat           send a message, get a reply
  POST /service/action execute a confirmed service action (address, KYC, cheque book)
  GET  /metrics        agent call counts/latency + this process's CPU/memory
  GET  /health         liveness check
"""

import time
import uuid
from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.agents import account_agent, transaction_agent
from app.agents import service_agent
from app.auth import create_access_token, create_refresh_token, decode_token, verify_password
from app.coordinator import classify_intent, run as coordinator_run
from app.database import get_db
from app.models import Account, Transaction, User
from app.observability import AGENT_NAMES, record_agent_call, snapshot as metrics_snapshot
from app.pii_masker import mask, unmask
from app.rate_limiter import is_rate_limited
from app.schemas import (
    AccountOut, CardOut, CategorySpend,
    ChatRequest, ChatResponse, ErrorResponse,
    LoginResponse, MetricsOut, RefreshRequest, TokenResponse,
    ServiceActionRequest, ServiceActionResponse,
    TransactionOut, TransactionsResponse,
)
from app.session_store import add_message, get_history

app = FastAPI(title="Bank Chatbot Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# tokenUrl points at /login so FastAPI's docs "Authorize" button can fetch a
# token for you; the dependency itself just reads the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ── middleware ────────────────────────────────────────────────────────────────

@app.middleware("http")
async def inject_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── auth dependency ───────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return decode_token(token, expected_type="access")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── context fetcher ───────────────────────────────────────────────────────────

def get_context(intent: str, customer_id: str, db: Session) -> str:
    if intent == "account":
        return account_agent.get_context(customer_id, db)
    if intent == "transaction":
        return transaction_agent.get_context(customer_id, db)
    if intent == "service":
        return service_agent.get_context(customer_id, db)
    return ""


def _primary_account(customer_id: str, db: Session) -> Account:
    """The customer's first account — same "primary account" convention
    transaction_agent.get_context() already uses for the chat prompt."""
    account = (
        db.query(Account)
        .join(User)
        .filter(User.customer_id == customer_id)
        .order_by(Account.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="No account found.")
    return account


def _merchant_name(description: str) -> str:
    """Seed data writes descriptions like "Netflix payment" / "Monthly salary
    credit" — strip the trailing verb so the UI shows just the merchant."""
    for suffix in (" payment", " credit"):
        if description.endswith(suffix):
            return description[: -len(suffix)]
    return description


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm names the customer ID field "username" — it's
    # the standard OAuth2 password-grant field name, not a literal username.
    user = db.query(User).filter(User.customer_id == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid customer ID or password")
    return LoginResponse(
        access_token=create_access_token(user.customer_id, user.name),
        refresh_token=create_refresh_token(user.customer_id),
        customer_id=user.customer_id,
        name=user.name,
    )


@app.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(User).filter(User.customer_id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return TokenResponse(access_token=create_access_token(user.customer_id, user.name))


# ── dashboard (real DB data for the UI) ─────────────────────────────────────────

@app.get("/accounts", response_model=list[AccountOut])
def list_accounts(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = (
        db.query(Account).join(User).filter(User.customer_id == user["sub"]).order_by(Account.id).all()
    )
    return [
        AccountOut(
            account_number_masked=a.masked_number,
            account_type=a.account_type,
            balance=a.balance,
            available_balance=a.balance,
            status=a.status,
            ifsc=a.ifsc,
            branch=a.branch,
        )
        for a in accounts
    ]


@app.get("/transactions", response_model=TransactionsResponse)
def list_transactions(
    limit: int = 10,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = _primary_account(user["sub"], db)

    recent = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.date.desc())
        .limit(limit)
        .all()
    )

    month_start = date.today().replace(day=1)
    monthly_debits = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account.id,
            Transaction.type == "debit",
            Transaction.date >= month_start,
        )
        .all()
    )
    by_category: dict[str, float] = {}
    for txn in monthly_debits:
        cat = (txn.category or "other").capitalize()
        by_category[cat] = by_category.get(cat, 0) + txn.amount
    total_this_month = sum(by_category.values()) if by_category else 0

    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    total_last_month = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account.id,
            Transaction.type == "debit",
            Transaction.date >= last_month_start,
            Transaction.date < month_start,
        )
        .all()
    )
    last_month_sum = sum(t.amount for t in total_last_month)
    pct = round(float((total_this_month - last_month_sum) / last_month_sum) * 100, 1) if last_month_sum else None

    return TransactionsResponse(
        transactions=[
            TransactionOut(
                id=txn.txn_id,
                merchant=_merchant_name(txn.description or txn.category or "Transaction"),
                category=txn.category,
                date=txn.date,
                amount=txn.amount,
                type=txn.type,
            )
            for txn in recent
        ],
        spending_by_category=[CategorySpend(category=c, amount=a) for c, a in by_category.items()],
        total_this_month=total_this_month,
        month_over_month_pct=pct,
    )


def _card_out(account: Account, holder_name: str) -> CardOut:
    return CardOut(last4=account.account_number[-4:], holder=holder_name, frozen=account.card_frozen)


@app.get("/cards", response_model=CardOut)
def get_card(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    account = _primary_account(user["sub"], db)
    return _card_out(account, user["name"])


@app.post("/cards/freeze", response_model=CardOut)
def freeze_card(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    account = _primary_account(user["sub"], db)
    account.card_frozen = True
    db.commit()
    return _card_out(account, user["name"])


@app.post("/cards/unfreeze", response_model=CardOut)
def unfreeze_card(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    account = _primary_account(user["sub"], db)
    account.card_frozen = False
    db.commit()
    return _card_out(account, user["name"])


# ── observability ────────────────────────────────────────────────────────────

@app.get("/metrics", response_model=MetricsOut)
def get_metrics(user: dict = Depends(get_current_user)):
    """Agent call counts/latency (recorded from every /chat call, this
    process only — see app/observability.py) plus this process's own
    CPU/memory. Gated behind login same as everything else here; in a real
    deployment this would be admin-only, not any signed-in customer."""
    return metrics_snapshot()


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if is_rate_limited(user["sub"]):
        return JSONResponse(status_code=429, content={"error": "Too many requests. Please wait a moment."})

    masked = mask(body.message)
    history = get_history(body.session_id)
    intent = classify_intent(masked.masked_text)
    context = get_context(intent, user["sub"], db)

    started = time.perf_counter()
    reply = coordinator_run(intent=intent, message=masked.masked_text, history=history, context=context)
    record_agent_call(intent, (time.perf_counter() - started) * 1000)

    reply = unmask(reply, masked.mapping)
    add_message(body.session_id, "user", masked.masked_text)
    add_message(body.session_id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=body.session_id, agent=AGENT_NAMES.get(intent))


@app.post("/service/action", response_model=ServiceActionResponse)
def service_action(
    body: ServiceActionRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a confirmed service action.

    The chat flow works like this:
      1. User: "I want to change my address to 5 MG Road, Bengaluru"
      2. Agent: "I'll update your address to 5 MG Road, Bengaluru, Karnataka - 560001.
                 Can you confirm? (yes/no)"
      3. User: "yes"
      4. Frontend calls POST /service/action with the parsed details
      5. We write to the DB and return a confirmation message

    Why a separate endpoint instead of writing in /chat?
      The agent only generates text — it doesn't write to the DB.
      Keeping mutations out of the chat flow makes it easy to test and audit.
    """
    customer_id = user["sub"]

    if body.action == "update_address":
        if not all([body.line1, body.city, body.state, body.pincode]):
            raise HTTPException(status_code=400, detail="Address fields are required.")
        message = service_agent.update_address(
            customer_id, body.line1, body.city, body.state, body.pincode, db
        )

    elif body.action == "request_cheque_book":
        message = service_agent.request_cheque_book(customer_id, db)

    elif body.action == "update_kyc":
        if not body.document_type:
            raise HTTPException(status_code=400, detail="document_type is required.")
        message = service_agent.update_kyc(customer_id, body.document_type, db)

    else:
        raise HTTPException(status_code=400, detail="Unknown action.")

    return ServiceActionResponse(message=message)