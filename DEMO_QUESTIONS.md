# NexaTel Chatbot — Demo script & question bank

Use this file when **presenting** the app. For full capability notes, period rules, and unsupported behavior, see [QUESTIONS.md](QUESTIONS.md).

**Before you start**

1. Start backend + frontend; pick a **demo customer** in the header selector (answers are always scoped to that customer).
2. Open **Account** in the sidebar for a full read-only snapshot before or during the chat demo.
3. Seed window is roughly **Oct 2025 – Oct 2026** — avoid asking for years or date ranges outside that data.
4. Structured replies may show **tables**, **charts** (when enough months exist), **key-value** blocks, or **Customer 360** — markdown narrative is shortened when structured UI is present.

---

## Suggested 10-minute flow

| Step | Customer | What to show | Example question (copy-paste) |
|------|----------|--------------|----------------------------------|
| 1 | **CUST005** | Welcome stats + quick prompts | Click **Current plan** or ask: `What plan and subscription do I have?` |
| 2 | **CUST005** | Usage + allowance | `How much data have I used this month?` then `How much data do I have remaining?` |
| 3 | **CUST005** | Bill + breakdown | `Show my latest bill` then `Break down my current bill` |
| 4 | **CUST005** | Payment history table (date + time columns) | `Show my last 5 payments` |
| 5 | **CUST005** | Chart moment | `Show my data usage history for the last 6 months` |
| 6 | **CUST005** | Bill analytics | Expand **More insights** → **Bill trend**, or ask: `Show my bill trend over the last 6 months` |
| 7 | **CUST005** | Cross-domain | `Give me an overview of my account` (Customer 360) |
| 8 | **CUST002** | Attention + drama | Switch customer; use welcome **attention chips** or ask: `Is anything on my account in need of attention?` |
| 9 | **CUST002** | Failed payment + SR link | `Did my last payment fail? Why did it fail?` then `Latest update on ticket TKT003` |
| 10 | Any | Guardrails | `Cancel my plan` or `Pay my bill now` → unsupported / read-only |

---

## Demo customers (pick the story)

| ID | Story | Use for |
|----|--------|---------|
| **CUST002** | Roaming spike, **failed payment**, open billing SR, credits | Attention, payments, support, roaming spend, bill change |
| **CUST003** | **Mobile + fiber**, service address, router | Line-specific bills, fiber vs mobile usage, devices |
| **CUST004** | **Suspended**, overdue | Account status, outstanding balance, payment stress |
| **CUST005** | Stable “happy path” | Default demo; **BILL009** / **BILL010** comparisons |
| **CUST006** | High data usage, **partial payment** | Usage %, remaining allowance, reconcile / outstanding |
| **CUST009** | Varied bill amounts | Bill history, highest/lowest bill, averages |

Inspect raw rows anytime via **Database explorer**.

---

## Account & plan

**Default: CUST005**

- What is my account status?
- What plan and subscription do I have?
- When does my plan renew?
- List my subscriptions.
- Give me a summary of my account and plan.

**Catalog (any customer)**

- What mobile plans are available?
- What fiber plans do you offer?
- Compare PLAN001 and PLAN003.

**CUST003 — converged account**

- What services are on my account?
- Show my **mobile** bill.
- Show my **fiber** bill.

**CUST004 — status edge case**

- Is my account active, suspended, or cancelled?

---

## Usage (data, voice, SMS)

**Single period — CUST005 or CUST006**

- Review my data usage *(matches welcome quick prompt)*
- How much data have I used this month?
- How much data did I use last month?
- How many voice minutes did I use last month?
- How many SMS did I send this month?
- How much data did I use in June 2026?

**Allowance — CUST006**

- How much data do I have remaining?
- What percentage of my data allowance have I used?

**Summary**

- Summarize my usage this month.
- Summarize all my usage for last month.

**History & trends (charts when 3+ months)**

- Show my data usage history for the last 3 months.
- Show my voice usage history for the last 6 months.
- What is my data usage trend over the last 6 months?
- Tell my data usage from June to August.

**Compare & analytics**

- Compare my voice usage this month with last month.
- Compare June and August data usage.
- What is my average monthly data usage?
- Which month had my highest data usage?
- Which month had my lowest voice usage?

**CUST003 — fiber note**

- How much data have I used this month? *(fiber line may show unlimited / N/A for voice-SMS)*

---

## Bills

**Current & specific**

- Show my latest bill *(welcome quick prompt)*
- What is my current bill, and when is it due?
- What will my bill be this month? *(projected estimate)*
- Break down my current bill.
- Break down my bill for September 2026.

**CUST005 — bill IDs**

- Show bill BILL009.
- Compare BILL009 and BILL010.
- Why did my bill change from last month?

**History & trends**

- Show my last 5 bills.
- Show my bill trend over the last 6 months.
- Show my unpaid bills, newest first.

**Compare**

- Compare my latest bill with the previous one.

**Aggregates & charges — good with CUST002 / CUST009**

- How much have I spent on my last 3 bills?
- What is my average bill?
- Which of my last 6 bills was the highest?
- How much did I spend on roaming in the last 6 months?
- How much tax was on my recent bills?

**Filters (natural phrasing)**

- Show my paid bills from the last 6 months.
- Show bills over ₹900.

---

## Payments

**Default: CUST005**

- Show my recent payments *(welcome quick prompt)*
- Show my last 5 payments.
- What is the status of my latest payment?
- Has my latest payment gone through?
- Summarize my payments this year.
- How many payments were successful this month?

**CUST002 — failure narrative**

- Did my last payment fail? Why did it fail?
- List my failed payments this year.
- Do I have any account credits?

**CUST006 — balance**

- How much is still outstanding on my current bill?
- Reconcile my current bill and payments.

**Profile (only if customer has a row — e.g. CUST002, CUST003, CUST005)**

- Is autopay enabled?
- Which payment method is on file?

**Reference lookup (must belong to selected customer)**

- Payment with reference TXN2026000006.

---

## Support tickets

**Default: CUST005**

- Show my support tickets *(welcome quick prompt)*
- What support tickets do I have?
- Show my open support cases.
- Do I have any unresolved tickets?
- Summarize my support history.

**CUST002 — linked records**

- Latest update on ticket TKT003.
- Show the full timeline for ticket TKT003.
- List my high-priority billing tickets.
- What is my most common support-ticket category?

**Cross-domain**

- Do I have any billing-related support tickets?
- Do I have any payment-related support tickets?

---

## Devices

**CUST003 — router**

- What devices are on my account?
- Do I have a router registered?
- Show my active phones.
- Summarize devices on my account.

**Specific ID (must be yours)**

- Show device DEV001.

**Limitation demo**

- Why is my phone internet slow? *(should explain read-only device records, not live diagnostics)*

---

## Cross-domain & Customer 360

Strong closing slides for any “healthy” customer (**CUST005**):

- How am I doing on my plan and data allowance?
- What is my current bill and payment status?
- Explain my bill charges and payment status.
- Is anything on my account in need of attention?
- Give me an overview of my account.

**CUST002** for attention + billing + support in one story:

- Is anything on my account in need of attention?
- Explain my bill charges and payment status.

---

## Welcome UI (don’t skip)

- **Three stat tiles:** plan name, usage headline, latest bill amount.
- **Projected bill** line when estimate exists.
- **Mobile + fiber** mini tiles when `bills_by_line` has both (**CUST003**).
- **Attention chips** → pre-filled follow-up (**CUST002**, **CUST004**, **CUST006**).
- **Quick questions:** plan, data, bill, payments, support.
- **More insights:** roaming spend, bill trend, last 3 bills spend.

---

## Clarifications (show the bot asks instead of guessing)

Ask vaguely on purpose:

- `How much have I used?` → should narrow data vs voice vs SMS.
- `Show my information.` → should ask which area.
- `Help with payment.` → status vs history vs tickets.
- `What are my latest details?` → should narrow topic.

---

## Security talking points (30 seconds)

- Every answer is for the **selected customer** only.
- Putting another customer’s ID in chat does **not** switch accounts.
- Bill / ticket / device IDs must **belong** to the selected customer.

---

## Unsupported — show read-only boundary

These should **not** mutate data or invent answers:

- Cancel, upgrade, or change my plan.
- Pay my bill or recharge.
- Open or update a support ticket.
- Run a speed test or fix network outage.
- General knowledge: `What's the weather in Mumbai?`

---

## Chart-friendly questions (visual checklist)

Ask on **CUST005** or **CUST009** when you want graphs:

- Show my data usage history for the last 6 months.
- Show my bill trend over the last 6 months.
- Compare my latest bill with the previous one.
- Compare June and August data usage.

Fewer than three periods usually stays **table-only**.

---

## One-page cheat sheet (all domains)

| Domain | Go-to question |
|--------|----------------|
| Plan | Check my current plan |
| Usage | Review my data usage |
| Allowance | How much data do I have remaining? |
| Bill | Show my latest bill |
| Projected | What will my bill be this month? |
| Bill ID | Show bill BILL009 |
| Payments | Show my last 5 payments |
| Failed pay | Did my last payment fail? |
| Support | Show my support tickets |
| Ticket | Latest update on ticket TKT003 |
| Devices | What devices are on my account? |
| Roaming | How much did I spend on roaming in the last 6 months? |
| 360 | Give me an overview of my account |
| Attention | Is anything on my account in need of attention? |
| Unsupported | Cancel my plan |

---

## After the demo

- **QUESTIONS.md** — exhaustive list and period/date rules.
- **Database explorer** — prove answers match SQL seed data.
- Re-seed if needed: `python scripts/init_db.py` from `backend/`.
