# NexaTel Chatbot — Questions You Can Ask

Select a **demo customer** in the app before chatting. Answers come from the **SQLite database** for that customer only. The LLM classifies wording and may phrase replies; it does not invent balances, usage, or tickets.

The server keeps a rolling window of the last **10** user turns per chat session (`conversation_id`, configurable via `CONVERSATION_TURN_WINDOW`)—structured intents and verified outcomes only, not assistant wording—to help with follow-ups like “that bill” or “last month.” Restarting the API or using **reset conversation** clears that history.

This demo supports the full **[DEMO_QUESTIONS.md](DEMO_QUESTIONS.md)** bank (usage, bills, payments, support, devices, plan catalog, and Customer 360). Transaction, bill, ticket, and device IDs must belong to the selected customer.

---

## How periods and dates work


| You want                    | Ask like this                                  | Backend behavior                   |
| --------------------------- | ---------------------------------------------- | ---------------------------------- |
| Current calendar month      | “this month”, “current month”                  | `time_range` = current month       |
| Last month                  | “last month”                                   | Previous calendar month            |
| This year                   | “this year”                                    | Year-to-date where supported       |
| One named month             | “data usage in **June**”, “in **August 2026**” | `month` (+ optional `year`)        |
| Last N months (rolling)     | “last **3** months”, “last **6** months”       | `month_count` on usage **history** |
| Month range (two endpoints) | “from **June to August**”                      | Usage **history** over that window |


**Read-only:** plan changes, payments, opening tickets, and general knowledge (see the **Unsupported** section in `DEMO_QUESTIONS.md`).

**Compare two usage months:** e.g. “Compare **June** and **August** data usage” → side-by-side comparison (not a rolling history chart).

---



## Account and plan

- What is my account status?
- What plan and subscription do I have?
- What services are on my account? (mobile and/or fiber)
- When does my plan renew?
- List my subscriptions.
- Compare **PLAN001** and **PLAN003** (two plan IDs you name).
- Am I on the right plan? / Recommend a plan for me.
- Give me a summary of my account (**Customer 360**).

---



## Usage — data, voice, SMS

**Single period**

- How much **data** have I used this month / last month?
- How many **voice minutes** / **SMS** this month?

**Allowance**

- How much data do I have **remaining**?
- What **percentage** of my data allowance have I used?

**Summary and history**

- Summarize my usage this month.
- Show my **data usage history** for the last **6** months.

---



## Bills

- What is my **current bill**, and when is it due?
- Show my **mobile** / **fiber** bill.
- What will my bill be **this month**? (projected)
- Break down my **current** bill.
- Show my **last 5** bills.
- **Compare my latest bill with the previous one**.
- **Why is my bill higher this month?** / Why did my bill change?
- Show bill **history** (e.g. last 6 bills) instead of a “trend” report.

---



## Payments

- What is the status of my **latest payment**?
- Has my latest payment **gone through**? (use payment **status**, not separate “last failed” intents)
- Is **autopay** enabled? Payment method on file?
- Do I have any **account credits**?
- Show my **payment history** (e.g. last 5 payments).
- How much is still **outstanding** on my current bill?
- **Reconcile** my current bill and payments.

---



## Support tickets

- What support tickets do I have?
- Show my **open** cases.
- What is my **latest** support ticket?

---



## Devices

- What devices are on my account?
- Do I have a **router** registered?

**Not supported:** device counts, newest/oldest analytics, filtering devices, **device ID** lookup, or network **diagnostics** (“why is my internet slow?”).

---



## Combined / cross-domain

- How am I doing on my **plan and data allowance**?
- Current **bill and payment status**?
- **Billing-** or **payment-related** support tickets?
- Is anything on my account **in need of attention**?
- Full **Customer 360** overview.

---



## Unsupported — demo limits

- Cancel, upgrade, or change plan; pay bill; open tickets.
- Network outage maps, speed tests, device diagnostics.
- Retired analytics (averages, extremes, trends, aggregates, filters, catalog browse).

Use the **Database explorer** page to inspect raw tables; those granular list intents are not exposed in chat.