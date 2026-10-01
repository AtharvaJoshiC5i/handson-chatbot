# NexaTel AI Support Backend

FastAPI service for customer-scoped, read-only NexaTel account queries. It classifies supported requests, validates intent parameters, retrieves facts from SQLite, performs calculations/reconciliation, and returns JSON or a streamed SSE response. The LLM is used for intent interpretation when needed and for phrasing backend-produced answers; it is not the source of account facts.

For full feature scope and repository setup, see the [project README](../README.md) and [question guide](../QUESTIONS.md).

## Setup

From this directory, using PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` in `.env`. `DATABASE_PATH` defaults to `data/nexatel.db`. Initialize sample data with `python scripts/init_db.py`.

Only copy `.env.example` on first setup. If `.env` already exists, edit it in place to preserve local credentials and settings.

**Caution:** `scripts/init_db.py` resets and reseeds the configured database. Do not run it against local data you need to preserve.

The current sample usage seed covers April through September 2026; requests for periods without seeded rows return no matching usage records.

Start the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Routes

- `GET /health`: basic process health only.
- `GET /api/chat/profile`: selected customer’s display name.
- `POST /api/chat`: complete JSON turn.
- `POST /api/chat/stream`: SSE response (`metadata`, `delta`, `done`/`error`).
- `POST /api/chat/reset`: clears selected customer conversation context.

Every customer-scoped route uses `X-Customer-ID`. This is a demo selector context, not production authentication.

## Tests and Utilities

```powershell
python -m pytest -q
python -m pytest -q tests/unit/test_chart_presentations.py tests/unit/test_intent_extraction_reliability.py tests/integration/test_chat_stream.py
python scripts/run_evaluation.py --mode deterministic
python scripts/verify_db.py
python scripts/view_database.py
```

Use `python scripts/run_evaluation.py --mode live` only when `GROQ_API_KEY` is configured. The database viewer prints complete rows; handle its output as sensitive.
