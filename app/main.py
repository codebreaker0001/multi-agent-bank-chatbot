"""API Gateway — single entry point for the chatbot.

Endpoints:
  POST /login          authenticate, get an access + refresh token
  POST /refresh        trade a refresh token for a new access token
  POST /chat           send a message, get a reply
  POST /service/action execute a confirmed service action (address, KYC, cheque book)
  GET  /health         liveness check
"""

import uuid

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
from app.models import User
from app.pii_masker import mask, unmask
from app.rate_limiter import is_rate_limited
from app.schemas import (
    ChatRequest, ChatResponse, ErrorResponse,
    LoginResponse, RefreshRequest, TokenResponse,
    ServiceActionRequest, ServiceActionResponse,
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

    reply, intent = coordinator_run(
        message=masked.masked_text,
        history=history,
        context=context,
    )

    reply = unmask(reply, masked.mapping)
    add_message(body.session_id, "user", masked.masked_text)
    add_message(body.session_id, "assistant", reply)

    return ChatResponse(reply=reply, session_id=body.session_id)


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