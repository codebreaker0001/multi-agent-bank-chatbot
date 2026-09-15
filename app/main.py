"""API Gateway — the single entry point for the chatbot.

Request lifecycle:
  POST /login  ->  verify credentials -> return JWT
  POST /chat   ->  validate JWT -> rate limit -> coordinator agent (Day 5)

Auth flow in plain English:
  1. User posts their customer_id + password to /login.
  2. We look them up in the DB and verify the bcrypt hash.
  3. If correct, we return a signed JWT.
  4. Every subsequent /chat request must include: Authorization: Bearer <token>
  5. The get_current_user dependency decodes the JWT and rejects anything invalid.
"""

import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth import create_token, decode_token, verify_password
from app.database import get_db
from app.models import User
from app.rate_limiter import is_rate_limited
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
)

app = FastAPI(title="Bank Chatbot Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server (Day 8)
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer()


# ── middleware ────────────────────────────────────────────────────────────────


@app.middleware("http")
async def inject_request_id(request: Request, call_next):
    """Attach a unique ID to every request so logs can be correlated."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── auth dependency ───────────────────────────────────────────────────────────


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency — decode the JWT and return the payload.

    Add this as a parameter to any route that requires authentication.
    FastAPI runs it automatically before the route handler.
    If the token is missing, expired, or tampered with, it raises 401.
    """
    try:
        return decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── routes ────────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and return a signed JWT.

    The password stored in the DB is a bcrypt hash — we never store plaintext.
    Default credentials for the seeded users: password = customer_id
      e.g.  customer_id: CUST1001  password: CUST1001
    """
    user = db.query(User).filter(User.customer_id == body.customer_id).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid customer ID or password")

    token = create_token(user.customer_id, user.name)
    return LoginResponse(access_token=token, customer_id=user.customer_id, name=user.name)


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),   # 401 if token missing/invalid
    db: Session = Depends(get_db),
):
    """Protected chat endpoint. JWT is required.

    user dict contains: { "sub": "CUST1001", "name": "Ananya Sharma", "exp": ... }
    """
    if is_rate_limited(user["sub"]):
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Please wait a moment."},
        )

    # ── Day 5: replace this stub with coordinator_agent.run() ────────────────
    reply = f"Hello {user['name']}! You said: '{body.message}'. (Coordinator coming Day 5)"
    # ─────────────────────────────────────────────────────────────────────────

    return ChatResponse(reply=reply, session_id=body.session_id)