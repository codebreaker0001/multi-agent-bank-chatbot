# DemoBank — AI Banking Assistant

A multi-agent banking chatbot: a coordinator classifies each message and
routes it to a specialist agent, with PII masked before anything reaches the
LLM and every account/transaction number backed by a real Postgres database.

```
User → API Gateway → Coordinator → Account Agent      (balance, details)
                                 → Transaction Agent  (history, spending)
                                 → Service Agent      (address, KYC, cheque book)
```

> **Portfolio project, not production banking software.** It demonstrates
> real patterns (PII masking before the LLM sees anything, confirm-before-write
> for every mutation, JWT-scoped queries) but skips things a real bank
> requires — MFA, fraud/velocity controls, audit logging, a compliance
> review of sending data to a third-party LLM API. See "Known limitations"
> below.

## Live demo

- App: https://multi-agent-bank-chatbot.vercel.app
- API: https://bank-chatbot-backend-p1o6.onrender.com
- Demo login: `CUST1001` / `CUST1001` (also `CUST1002`, `CUST1003`, same password pattern)

The backend is on a free instance and sleeps after 15 min idle — the first
request after a gap takes 30-60s to wake up.

## Features

- **Multi-agent routing** — one LLM call classifies intent, a second call
  (routed to the matching specialist prompt) answers, with the customer's
  real account/transaction data injected as context.
- **PII masking** — account numbers, phone, email, PAN, and Aadhaar are
  replaced with tokens before any prompt reaches the LLM, and unmasked in
  the reply. See `app/pii_masker.py`.
- **Auth** — bcrypt password hashing, OAuth2-shaped JWT access (15 min) +
  refresh (7 day) tokens, auto-refresh on the frontend.
- **Real dashboard** — balances, transactions, spending by category, and
  card freeze/unfreeze are backed by actual Postgres rows via
  `GET /accounts`, `GET /transactions`, `GET /cards`, not mock data.
- **Confirm-before-write** — the LLM can only *propose* an address change,
  KYC update, or cheque book request; a separate confirmed endpoint
  (`POST /service/action`) is what actually writes to the database.
- **Observability** — `/metrics` tracks which agent answered each message,
  latency, and this process's CPU/memory, surfaced in an in-app
  Observability page.
- **Rate limiting** — Redis-backed token bucket on `/chat` (20 req/min).

## Tech stack

| | |
|---|---|
| Backend | FastAPI, SQLAlchemy, Postgres, Redis, Groq (LLM) |
| Frontend | React (CRA), Tailwind CSS, Framer Motion |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Deployed on | Render (backend), Vercel (frontend), Neon (Postgres), Upstash (Redis) — all free tier |

## Project structure

```
app/
  main.py            API gateway — every route
  coordinator.py      intent classification + agent routing
  agents/              account_agent.py, transaction_agent.py, service_agent.py
  auth.py              password hashing, JWT issue/verify
  pii_masker.py        mask/unmask before and after the LLM call
  observability.py      per-agent call tracking, CPU/memory
  models.py, schemas.py, database.py, config.py
ui/
  src/components/
    chat/              the conversational UI
    banking/           balance card, transaction list, spending chart, card preview
    layout/            sidebar, header, right context panel
    views/              Overview/Accounts/Transactions/Cards/Analytics/Observability pages
scripts/
  seed.py / reset.py    create tables + demo data / wipe and recreate
  test_*.py             pytest suite
```

## Local setup

**Backend**

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in GROQ_API_KEY at minimum

docker compose up -d          # starts local Postgres + Redis
python scripts/seed.py        # creates tables, loads 3 demo customers
uvicorn app.main:app --reload # http://localhost:8000
```

**Frontend**

```bash
cd ui
npm install
npm start                     # http://localhost:3000
```

**Tests**

```bash
pytest scripts/ --ignore=scripts/test_gateway.py
```

(`test_gateway.py` predates the real auth system and is currently stale —
everything else passes. A handful of `test_models.py`/`test_auth.py` cases
depend on cross-test SQLite state or a live LLM call and can flake in
isolation; that's a known, pre-existing gap, not new breakage.)

## Environment variables

See `.env.example` (backend) and `ui/.env.example` (frontend) for the full
list with explanations. The essentials:

| Variable | Where | Notes |
|---|---|---|
| `GROQ_API_KEY` | backend | required for `/chat` to work at all |
| `DATABASE_URL` | backend | defaults to the local docker-compose Postgres |
| `REDIS_URL` | backend | defaults to the local docker-compose Redis |
| `JWT_SECRET` | backend | **must** be overridden outside local dev |
| `REACT_APP_API_URL` | frontend | points the UI at a backend — baked in at build time |

## Deployment

`render.yaml` is a ready-to-use Render Blueprint (Docker runtime, free
plan). The stack this project is actually deployed on, all free tier:

1. **Neon** — Postgres. Create a project, run `python scripts/seed.py`
   locally with `DATABASE_URL` pointed at it once, to create tables and load
   demo data.
2. **Upstash** — Redis. Use the TCP connection string (`rediss://default:...`),
   not the REST API URL/token — this app uses `redis-py` over the standard
   protocol.
3. **Render** — New + → Blueprint → select this repo. It reads `render.yaml`
   and prompts for `DATABASE_URL`, `REDIS_URL`, `GROQ_API_KEY`; `JWT_SECRET`
   is auto-generated.
4. **Vercel** — import the repo with root directory `ui`, set
   `REACT_APP_API_URL` to the Render URL.
5. Set `FRONTEND_URL` on Render to the Vercel URL to close the CORS loop.

## Known limitations

This is a learning/portfolio project — see the full list of gaps in
`.env.example` comments and the codebase's inline notes, but the headline
ones: no MFA or account lockout, no fraud/velocity controls, refresh tokens
aren't revocable, no DB migrations (schema changes mean `scripts/reset.py` +
reseed, not an Alembic migration), and sending masked customer context to a
third-party LLM API is a real compliance question a real bank would need to
clear before this pattern could go anywhere near production.
