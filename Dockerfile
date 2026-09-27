# Backend image — the FastAPI gateway (app/main.py). Deployed as a single
# container; Postgres and Redis are managed services (Neon, Upstash), not
# part of this image (see docker-compose.yml for local dev instead).
FROM python:3.13-slim

WORKDIR /app

# Install deps first so this layer caches across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Render (and most PaaS free tiers) inject $PORT at runtime rather than
# fixing it at build time — bind to it via the shell form, not a hardcoded
# port. Locally: docker run -e PORT=8000 -p 8000:8000 ...
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
