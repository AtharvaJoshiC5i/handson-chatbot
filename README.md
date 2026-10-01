# NexaTel AI Support

A read-only telecom customer-support chatbot. The backend scopes every lookup to the customer selected in the frontend, retrieves and calculates account facts from SQLite, and returns a concise answer with optional structured details. The final answer is streamed to the chat UI as it is generated.

## Capabilities

- **Account and plans:** account status, current plan and subscription, renewal dates, and account summaries.
- **Usage:** data, voice, and SMS usage; named months and years; remaining allowance; history, comparisons, averages, extremes, and trends.
- **Bills:** current and specific bills, history, line-item breakdowns, payment reconciliation, comparisons, spending, averages, filters, and trends.
- **Payments:** latest status, successful or failed payments, history, transaction-reference lookup, outstanding balances, reconciliation, summaries, and aggregates.
- **Support:** ticket history, status/priority/category filtering, counts, summaries, latest updates, and billing/payment-related tickets.
- **Devices:** associated devices, status/type filters, counts, summaries, and recorded device details.
- **Combined answers:** plan/usage, bill/payment, support/billing, account-attention, and customer-overview questions.
- **Visualizations:** usage history/trends render as line charts; bill history renders as bars and bill trends as lines. Exact values remain listed below each chart. Short histories fall back to tables.
- **Personalized welcome:** the selected customer name is loaded from the customer record and shown on the landing page.

The assistant is read-only. It cannot change plans, make payments, open support tickets, or perform live network/device diagnostics. Ambiguous questions should be clarified rather than guessed. The full question guide is in [QUESTIONS.md](QUESTIONS.md).

## How It Works

1. The frontend sends the message and selected customer ID to FastAPI.
2. The backend resolves an intent and validates its parameters against the registered capabilities. Common requests are classified deterministically; the LLM is used for other wording and must return the intent schema. Invalid schema output is retried once, then converted to a clarification rather than an HTTP 503.
3. Backend handlers run parameterized, customer-scoped SQLite queries and perform all authoritative calculations and reconciliation.
4. The backend builds plain-language source text and optional structured presentation data. The LLM only phrases that backend answer; if final phrasing fails, the backend answer is used as a fallback.
5. The frontend renders the prose, tables/summaries, or time-series visualizations. For chart data, the backend sends numeric points, labels, units, and statuses; the frontend does not infer values from display text. If final-answer generation fails before the first streamed token, the backend-formatted answer is used; a failure after partial output is reported as a stream error.

The selected customer is supplied through `X-Customer-ID`. This selector is a development/demo account context, **not production authentication or authorization**. Do not expose this demo API to untrusted users without adding real authentication and authorization.

## Repository Layout

```text
backend/
	app/api/          FastAPI routes and dependencies
	app/database/     SQLite schema, connection, seed data, and queries
	app/handlers/     Customer-scoped read handlers and calculations
	app/intent/       Intent registry, parameter validation, and routing
	app/llm/          Groq adapter and intent/response prompts
	app/services/     Chat orchestration and response presentations
	tests/            Unit, integration, security, and evaluation tests
	scripts/          Database and evaluation utilities
frontend/
	src/App.tsx       Application shell, account selection, and chat state
	src/components/   Chat, structured response, and chart components
	src/services/     Backend API and SSE client
QUESTIONS.md        Supported question examples and safety checks
```

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+
- npm
- A Groq API key for LLM intent classification and final-answer wording

## Local Setup

### Backend

In PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` in `backend/.env`. The checked-in `.env.example` uses `openai/gpt-oss-120b`; `GROQ_MODEL` may be changed to another model available to your Groq account. Never commit `.env` or API keys.

Only copy `.env.example` when creating `.env` for the first time. If `.env` already exists, edit it in place so you do not overwrite your local key or settings.

`DATABASE_PATH` defaults to `backend/data/nexatel.db`; relative paths are resolved from the backend directory. Initialize the sample database with:

```powershell
python scripts/init_db.py
```

**Warning:** `init_db.py` calls the seed routine with `reset=True`. It recreates the sample database and will overwrite local database contents.

The bundled usage seed currently contains monthly records from April through September 2026. A request for a period with no seeded rows (for example, October 2026 before data is added) can correctly return no usage records.

Start the API from `backend`:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` and `/health` to `http://127.0.0.1:8001`.

For macOS/Linux, activate the virtual environment with `source .venv/bin/activate` instead of the PowerShell activation command.

## API

All chat endpoints use the `X-Customer-ID` header to select the customer. The ID in the message body does not change customer scope.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Basic process health and environment; does not test Groq or the database. |
| `GET` | `/api/chat/profile` | Returns only the selected customer’s display name. |
| `POST` | `/api/chat` | Processes a chat turn and returns a complete JSON response. |
| `POST` | `/api/chat/stream` | Processes a chat turn and streams the final answer as server-sent events (SSE). |
| `POST` | `/api/chat/reset` | Clears conversation context for the selected customer and conversation ID. |

Example non-streaming request:

```json
{
	"message": "How much data did I use in September?",
	"conversation_id": "demo-conversation-1"
}
```

Send it as JSON to `/api/chat` with `X-Customer-ID: CUST001`. The stream endpoint sends `metadata` first, then `delta` events containing text, followed by `done`; an interrupted generation can emit `error`. Metadata contains the backend status, source, options, and structured presentation.

PowerShell example:

```powershell
$body = @{ message = "How much data did I use in September?"; conversation_id = "demo-1" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/api/chat" -Headers @{ "X-Customer-ID" = "CUST001" } -ContentType "application/json" -Body $body
```

## Visualizations

- Usage history with at least three periods: line chart.
- Usage trend with at least two periods: line chart.
- Bill history with at least three periods: bar chart.
- Bill trend with at least two periods: line chart.

Charts include axis/hover values and an adjacent exact-value list. If there are too few periods or values are not numeric, the existing table presentation is used. See the chart examples in [QUESTIONS.md](QUESTIONS.md).

## Development Checks

Backend tests, from `backend`:

```powershell
python -m pytest -q
```

Focused chart, stream, and intent-recovery tests:

```powershell
python -m pytest -q tests/unit/test_chart_presentations.py tests/unit/test_intent_extraction_reliability.py tests/integration/test_chat_stream.py
```

Run deterministic evaluation without calling Groq:

```powershell
python scripts/run_evaluation.py --mode deterministic
```

Live evaluation uses the configured Groq credentials:

```powershell
python scripts/run_evaluation.py --mode live
```

Frontend checks, from `frontend`:

```powershell
npm run lint
npm run build
```

## Database Utilities

Run these from `backend`:

```powershell
python scripts/verify_db.py
python scripts/view_database.py
python scripts/view_database.py --table customers --table bills
```

`view_database.py` prints complete rows, including personal sample data. Treat its output as sensitive and do not paste it into public logs or issue reports.
