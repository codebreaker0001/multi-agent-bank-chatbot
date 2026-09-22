"""Authentication helpers.

Three responsibilities:
  1. Hash and verify passwords (bcrypt via passlib).
  2. Create signed access/refresh JWTs when the user logs in.
  3. Decode and validate a JWT on every protected request.

Why access + refresh tokens instead of one long-lived token?
  The access token is short-lived (15 min) and sent on every request, so a
  leaked one has a small blast radius. The refresh token lives longer
  (7 days) and is only sent to /refresh to mint a new access token — that
  narrows where a long-lived credential is exposed.

Why JWT instead of server-side sessions?
  The server doesn't need to store anything. The token is self-contained —
  it carries the user's ID and expiry. Any server instance can verify it
  by checking the signature, which makes it easy to scale horizontally.

What's inside the token?
  { "sub": "CUST1001", "type": "access"|"refresh", "exp": <timestamp> }
  'sub' (subject) is the standard JWT claim for the user identifier.
  'type' stops a refresh token being used where an access token is expected.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGO,
    JWT_SECRET,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(customer_id: str, token_type: str, expire_minutes: int, **claims) -> str:
    payload = {
        "sub": customer_id,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expire_minutes),
        **claims,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def create_access_token(customer_id: str, name: str) -> str:
    return _create_token(customer_id, "access", ACCESS_TOKEN_EXPIRE_MINUTES, name=name)


def create_refresh_token(customer_id: str) -> str:
    return _create_token(customer_id, "refresh", REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decode and validate a JWT. Raises JWTError if invalid, expired, or
    the wrong type (e.g. a refresh token presented as an access token)."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    if payload.get("type") != expected_type:
        raise JWTError(f"Expected a {expected_type} token")
    return payload