"""Session store — conversation history in Redis.

Each session is a list of messages stored under the key "session:<session_id>".
The full history is sent to the LLM on every request so it remembers context.

Why Redis and not the database?
  Sessions are temporary — they expire after 30 minutes of inactivity.
  Redis has built-in TTL (time-to-live) for keys, so cleanup is automatic.
  It's also much faster than a DB query for something that happens on every message.

Structure of each message:
  {"role": "user" | "assistant", "content": "the message text"}
"""

import json

import redis

from app.config import REDIS_URL

SESSION_TTL = 1800  # 30 minutes in seconds

r = redis.from_url(REDIS_URL, decode_responses=True)


def get_history(session_id: str) -> list[dict]:
    """Return all messages for this session, oldest first."""
    key = f"session:{session_id}"
    messages = r.lrange(key, 0, -1)
    return [json.loads(m) for m in messages]


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message and reset the 30-minute expiry timer."""
    key = f"session:{session_id}"
    r.rpush(key, json.dumps({"role": role, "content": content}))
    r.expire(key, SESSION_TTL)


def clear_session(session_id: str) -> None:
    """Delete a session (e.g. on logout)."""
    r.delete(f"session:{session_id}")