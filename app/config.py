"""App configuration. Reads from environment variables with sensible defaults."""

import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://bankuser:bankpass@localhost:5432/bankdb"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGO = "HS256"
JWT_EXPIRY_MINUTES = 60

# Rate limiting
RATE_LIMIT = 20       # requests
RATE_WINDOW = 60      # per seconds

# Groq (Day 5)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")