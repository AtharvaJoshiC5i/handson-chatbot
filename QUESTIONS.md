# NexaTel Chatbot — Questions You Can Ask

Select a **demo customer** in the app before chatting. Every answer comes from the **SQLite database** for that customer only: handlers run SQL, apply business rules, and return verified facts. The LLM may **classify** your wording and **phrase** the reply; it does **not** invent balances, usage, or tickets.

Natural phrasing is fine, but only **supported intents** (see below) return data. Unsupported or ambiguous requests get a clarification, a validation message, or `UNSUPPORTED`.

---

## How periods and dates work

| You want | Ask like this | Backend behavior |
|----------|---------------|------------------|
| Current calendar month | “this month”, “current month” | `time_range` = current month |
| Last month | “last month” | Previous calendar month |
| This year | “this year” | Year-to-date usage or filters |
| One named month | “data usage in **June**”, “in **August 2026**” | `month` (+ optional `year`) |
| Last N months (rolling) | “last **3** months”, “last **6** months” | `month_count` on history/trend/bills |
| Month range (two endpoints) | “from **June to August**”, “between June and August” | Usage **history** for that many months (rolling window ending today, not a fixed calendar slice) |
| Compare two months | “Compare **June** and **August** data usage” | `GET_USAGE_COMPARISON` (two months only) |
| Specific bill | “Show bill **BILL009**” | Bill must belong to selected customer |

**Not supported:** arbitrary calendar ranges (“1 June through 31 August 2025 only”), free-form multi-year reports, or questions that need data outside the seed window (demo data is roughly **Oct 2025 – Oct 2026**).

**Common error (fixed):** “Data usage from June to August” used to send invalid parameters to the wrong intent. It now routes to **usage history** with a 3‑month window. For an exact calendar month, name one month: “How much data did I use in **June 2026**?”

---

## Account and plan

- What is my account status?
- Is my account active, suspended, or cancelled?
- What plan and subscription do I have?
- What services are on my account? (mobile and/or fiber — try **CUST003** for both)
- What are the details of my current plan?
- When does my plan renew?
- Is my account and subscription active?
- List my subscriptions.
- What fiber plans do you offer? / What mobile plans are available?
- Compare **PLAN001** and **PLAN003**.
- Show details for plan **PLAN001** (catalog row by ID).
- Give me a summary of my account and plan.
- List my **active** subscriptions only. (filter on subscription status)
- What is my **mobile** plan? / **fiber** plan? (multi-line accounts such as **CUST003**)

**Database explorer parity** (daily rows and line items, not only monthly rollups):

- Show my **daily usage records** / **usage records** for the last **25** days (optional **SUB** id).
- List **bill line items** across my bills (optional **BILL** id or charge type).
- List **all support ticket updates** on my account (optional **TKT** id).  
  For one ticket’s timeline only, ask: “Latest update on ticket **TKT003**” or “Show the timeline for **TKT003**” (`GET_SUPPORT_TICKET_UPDATES`).

---

## Usage — data, voice, SMS

**Single period**

- How much **data** have I used this month / last month / this year?
- How many **voice minutes** did I use last month?
- How many **SMS** did I send this month?
- Show my SMS usage this month.
- How much data did I use in **June**? / in **August 2026**?

**Allowance**

- How much data (or voice) do I have **remaining**?
- What **percentage** of my data allowance have I used?

**Summary**

- Summarize my usage this month.
- Summarize all my usage for last month.

**History and trends** (often includes a chart if enough months)

- Show my **data usage history** for the last **3** months.
- Show my **voice usage history** for the last **6** months.
- What is my **data usage trend** over the last **6** months?
- What is the trend in my **voice** usage?
- Tell my **data usage from June to August** (history over a 3‑month window).

**Compare and analytics**

- Compare my **voice** usage **this month with last month**.
- Compare **June** and **August** data usage.
- What is my **average** monthly data usage? (over recent months in seed)
- Which month had my **highest** data usage?
- Which month had my **lowest** voice usage?

**Fiber note:** Voice/SMS questions may return not applicable on **fiber-only** lines; data on fiber may show as unlimited depending on plan.

---

## Bills

**Current and specific**

- What is my **current bill**, and when is it due?
- Show my **mobile** bill / **fiber** bill.
- What will my bill be **this month**? (projected estimate from plan + usage)
- Show bill **BILL009** (must be yours — e.g. **CUST005**).
- Break down my **current** bill / bill for **September 2026**.

**History and trends**

- Show my **last 5** bills.
- Show my **bill trend** over the last **6** months.
- Show my **unpaid** bills, newest first.

**Compare and explain**

- Compare my **latest bill with the previous one**.
- Compare **BILL009** and **BILL010**.
- Why did my bill **change** from last month?

**Aggregates**

- How much have I spent on my **last 3** bills?
- What is my **average** bill?
- Which of my last **6** bills was the **highest** / **lowest**?
- How much did I spend on **roaming** in the last **6** months?
- How much **tax** was on my recent bills? (charge-type summary)

**Filters**

- Show bills over a minimum amount or with a given status (when phrasing matches filter intents).

---

## Payments

- What is the status of my **latest payment**?
- Has my latest payment **gone through**?
- Did my **last payment fail**? Why did it fail?
- Is **autopay** enabled? Which **payment method** is on file? (only some customers have a profile row)
- Do I have any **account credits**?
- Show my **last 5** payments.
- List my **failed** payments this year.
- Payment with reference **TXN2026000006** (if it exists for your customer).
- How much is still **outstanding** on my current bill?
- **Reconcile** my current bill and payments.
- Summarize my payments this year.
- How many payments were **successful** this month?

---

## Support tickets

- What support tickets do I have?
- Show my **open** support cases.
- List my **high-priority billing** tickets.
- Do I have any **unresolved** tickets?
- How many support tickets do I have?
- What is my most common support-ticket **category**?
- Summarize my support history.
- Latest update on ticket **TKT003** (must be yours — e.g. **CUST002**).
- Show the full **timeline** for ticket **TKT003**.
- Is my billing ticket linked to a bill? (when `related_bill_id` is set in data — e.g. **BILL027** for **CUST002**)

---

## Devices

- What devices are on my account?
- Show my **active** phones.
- Do I have a **router** registered?
- Show device **DEV001**.
- How many **active** devices do I have?
- Which device was added most recently?
- Summarize devices on my account.

**Not supported:** live network diagnostics (“why is my phone slow?”) — the bot only reads **device records**.

---

## Combined / cross-domain (structured only)

- How am I doing on my **plan and data allowance**?
- What is my **current bill and payment status**?
- Explain my **bill charges and payment status**.
- Do I have any **billing-related** support tickets?
- Do I have any **payment-related** support tickets?
- Is anything on my account **in need of attention**?
- Give me an **overview** of my account (Customer **360**): plan, usage, bill, payment, support, devices.

The bot does **not** assume a billing ticket is about a specific bill unless the database links them (`related_bill_id` / `related_payment_id`).

---

## Welcome screen and quick actions

The home view can show **attention chips** (overdue bill, failed payment, high usage, credits, open SR) that send a **fixed follow-up question** into chat. Quick prompts include plan, usage, latest bill, payments, support, **roaming spend**, **bill trend**, and **recent bill spend**.

---

## Clarifications (the bot should ask, not guess)

- “How much have I **used**?” → data vs voice vs SMS.
- “Show my **information**.” → account, plan, usage, bill, payment, support, or devices.
- “**Help with payment**.” → status, history, reconciliation, or payment tickets.
- “What are my **latest details**?” → narrow the topic.

---

## Security and limits (demo)

- Answers are scoped to the **selected customer** only.
- “Show my last **3** bills / **5** payments” should respect the number you ask for.
- **BILL** / **TKT** / **DEV** IDs must belong to the selected customer.
- Typing another customer’s ID in the message does **not** switch accounts.

---

## Unsupported — read-only demo

These should **not** run database writes or made-up answers:

- Cancel, upgrade, or change my plan.
- **Pay** my bill or recharge.
- **Open** or update a support ticket.
- Troubleshoot **network** / speed test / outage map.
- Weather, trivia, or general knowledge.
- Apply credits, change autopay, or edit payment methods.

---

## Questions that often include charts

When enough monthly points exist in the database, the UI may show a **chart** plus tables:

- Data or voice **usage history** (typically 3+ months).
- Data or voice **usage trend**.
- **Bill history** or **bill trend** (e.g. last 5–6 bills).
- Bill **comparison** hero + breakdown.

Fewer than three periods usually stay as a **table** only.

---

## Demo customers (stories in seed data)

| Customer | Good for |
|----------|----------|
| **CUST002** | Roaming bill spike, failed payment, open billing SR, credits |
| **CUST003** | Mobile + fiber, service address, two latest bills by line |
| **CUST004** | Suspended account, overdue payment |
| **CUST005** | Stable account, **BILL009** / **BILL010** comparison |
| **CUST006** | High data usage, partial payment |
| **CUST009** | Varied bill history amounts |

Use the **Database explorer** page to inspect raw tables for any customer.
