# Banking Chatbot

A multi-agent banking assistant. A coordinator agent routes customer questions
to three specialist agents, each with its own MCP server and mock bank data.

```
User → API Gateway → Coordinator Agent → Account Agent      (balance, details)
                                       → Transaction Agent  (history, statements)
                                       → Service Agent      (address, KYC, cheque book)
```

**Day 1 of 14 is complete:** project setup, database models, and sample data.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env

docker compose up -d          # start postgres and redis
python scripts/seed.py        # create tables and add sample data
pytest                        # run tests
```

Without Docker, use SQLite instead — set this in `.env`:

```
DATABASE_URL=sqlite:///./bank.db
```

## Project structure

```
app/
  config.py      environment variables
  database.py    engine and session setup
  models.py      six database tables
scripts/
  seed.py        creates tables and sample data
  reset.py       drops and recreates tables
tests/
  test_models.py basic model tests
```

## Database

Six tables, grouped by which agent uses them:

| Table | Used by |
|---|---|
| `users`, `accounts` | Account agent — balance and account details |
| `transactions` | Transaction agent — history and statements |
| `addresses`, `kyc_records`, `service_requests` | Service agent — address change, KYC, cheque book |

Three decisions worth knowing:

- **Money uses `Numeric`, not `Float`.** Float can't represent decimal values
  exactly, so `0.1 + 0.2` becomes `0.30000000000000004`. Not acceptable for balances.
- **Transactions store `balance_after`.** Otherwise generating a statement means
  recalculating from the first ever transaction each time.
- **Address changes add a new row** and mark the old one `is_current = False`,
  instead of overwriting it. So the customer can still ask what their old address was.

## Sample data

3 customers, 3-4 accounts, ~430 transactions over 3 months. Generation is
seeded with a fixed value so the data is identical on every run.

The data includes some edge cases on purpose, so the agents have real situations
to handle: one customer with pending KYC, one with expired KYC, and an old
address for each customer.

## Next: Day 2

FastAPI gateway with a `/chat` endpoint, rate limiting using Redis, and
request validation.