# NexaTel Chatbot Questions

Select a customer in the frontend before asking a question. The backend uses
that selected account to retrieve records and perform all authoritative
calculations and checks. The LLM may help classify a request and phrases the
final response from backend-produced answer text; it does not query the
database or calculate account facts.

The examples below cover the supported intent families. Natural phrasing may
vary, but answers depend on the selected customer's available records and the
requested period or filters.

## Account and Plan

- What is my account status?
- Is my account active, suspended, or cancelled?
- What plan and subscription do I have?
- What are the details of my current plan?
- When does my plan renew?
- Is my account and subscription active?
- Give me a summary of my account.

## Usage

Ask about data or voice usage for a supported period, or request an analysis
of the available usage records.

- How much data have I used this month, last month, or this year?
- How many voice minutes did I use last month?
- How much data or voice allowance do I have remaining?
- What percentage of my data allowance have I used?
- Summarize my usage this month.
- Show my data usage history for the last 3 months.
- Compare my voice usage this month with last month.
- What is my average monthly data usage?
- Which month had my highest data usage?
- What is the trend in my voice usage?

## Bills

- What is my current bill, and when is it due?
- What do I currently owe?
- Show bill BILL003.
- Show my last 5 bills.
- Break down my current bill.
- Compare my current bill with last month's bill.
- Why did my bill change from last month?
- How much have I spent on my last 3 bills?
- What is my average bill?
- Which of my last 6 bills was the highest?
- Show my bill trend over the last 6 months.
- Show my unpaid bills, newest first.

## Payments

- What is the status of my latest payment?
- Has my latest payment gone through?
- Did my last payment fail?
- Show my last 5 payments.
- List my failed payments this year.
- What is the payment with transaction reference TXN2026000006?
- How much is still outstanding on my current bill?
- Reconcile my current bill and payments.
- Summarize my payments this year.
- How many payments were successful this month?

## Support Tickets

- What support tickets do I have?
- Show my open support cases.
- List my high-priority billing tickets.
- Do I have any unresolved tickets?
- How many support tickets do I have?
- What is my most common support-ticket category?
- Summarize my support history.
- What is the latest update on ticket TKT003?

## Devices

- What devices are associated with my account?
- Show my active phones.
- Do I have a router registered?
- Show device DEV001.
- How many active devices do I have?
- Which device was added most recently?
- Summarize the devices on my account.
- Can you diagnose why my device is malfunctioning?

The chatbot can report device records, but it cannot perform live device,
network, or connectivity diagnostics.

## Combined Account Questions

- How am I doing on my plan and data allowance?
- What is my current bill and its payment status?
- Explain my bill charges and payment status.
- Do I have any billing-related support tickets?
- Do I have any payment-related support tickets?
- Is anything on my account in need of attention?
- Give me an overview of my account, plan, usage, bills, payments, support
	tickets, and devices.

The chatbot does not assume that a billing-category ticket is about a
particular bill, or that a payment-category ticket is about a particular
transaction, unless the backend explicitly establishes that relationship.

## Clarification Checks

The chatbot should ask a follow-up question when a request does not identify
which data to retrieve, rather than guessing.

- How much have I used? (Clarify data versus voice usage.)
- Show me my information. (Offer account, plan, usage, billing, payment,
	support, or device topics.)
- Help with a payment. (Clarify payment status, payment history, bill/payment
	status, or payment-related support.)
- What are my latest details?

## Account and Parameter Safety

- Try the same question with different customers selected; results must stay
	scoped to the selected account.
- Show my last 3 bills, last 5 payments, or last 3 support tickets. The
	response should respect the requested limit.
- Compare BILL003 and BILL004. Only return details if both bills belong to the
	selected customer.
- Ask about another customer's bill ID. The chatbot must not disclose it.
- A customer ID typed into the message must not change the selected account.

## Unsupported Requests

The chatbot is read-only and limited to the capabilities above. These should
not trigger a database action or an invented answer:

- Cancel my subscription.
- Upgrade my plan.
- Make a payment for me.
- Open a support ticket.
- Troubleshoot my network connection.
- What will the weather be tomorrow?
- Tell me a general trivia fact.

## Questions With Visualizations

These time-series questions can include a chart alongside the written
answer. Exact period values remain visible beneath the chart. Histories with
fewer than three periods remain in the existing table format.

- Show my data usage history for the last 3 months.
- Show my voice usage history for the last 6 months.
- Show my data usage trend over the last 6 months.
- Show my voice usage trend over the last 6 months.
- Show my last 5 bills.
- Show my bill trend over the last 6 months.
