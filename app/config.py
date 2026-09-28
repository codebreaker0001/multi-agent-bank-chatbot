"""App configuration. Reads from environment variables with sensible defaults."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://bankuser:bankpass@localhost:5432/bankdb"
)
# Managed Postgres providers (Neon, Render, etc.) hand out a bare
# "postgresql://" URL. SQLAlchemy needs the driver in the scheme, and this
# project uses psycopg3 (see requirements.txt), not the psycopg2 that bare
# scheme would default to — rewrite it rather than make every deploy target
# remember to add "+psycopg" by hand.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60  # 7 days

# Rate limiting
RATE_LIMIT = 20       # requests
RATE_WINDOW = 60      # per seconds

# LLM provider — "groq" (cloud, what the deployed backend uses) or "ollama"
# (local, nothing leaves the machine it runs on — see coordinator.py).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Groq (Day 5)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Ollama — local dev only. OLLAMA_BASE_URL points at Ollama's OpenAI-compatible
# endpoint (its default port, no auth needed — the "ollama" api_key below is
# a placeholder the OpenAI SDK requires but Ollama itself ignores).
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# CORS — the deployed frontend's origin (e.g. https://your-app.vercel.app).
# Falls back to the local CRA dev server so `npm start` keeps working untouched.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")