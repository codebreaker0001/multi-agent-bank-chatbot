"""Authentication helpers.

Three responsibilities:
  1. Hash and verify passwords (bcrypt via passlib).
  2. Create a signed JWT when the user logs in.
  3. Decode and validate a JWT on every protected request.

Why JWT instead of server-side sessions?
  The server doesn't need to store anything. The token is self-contained —
  it carries the user's ID and expiry. Any server instance can verify it
  by checking the signature, which makes it easy to scale horizontally.

What's inside the token?
  { "sub": "CUST1001", "name": "Ananya Sharma", "exp": <timestamp> }
  'sub' (subject) is the standard JWT claim for the user identifier.
"""


from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import JWT_ALGO, JWT_EXPIRY_MINUTES, JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(customer_id: str, name: str) -> str:
    """Sign a JWT that expires in JWT_EXPIRY_MINUTES."""
    payload = {
        "sub": customer_id,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises JWTError if invalid or expired."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])