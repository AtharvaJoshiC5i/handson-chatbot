# NexaTel Chatbot Questions

Select a customer in the frontend before asking these questions. The
responses below should be grounded in the selected customer's database data.

## Direct-Answer Checks

These should be answered directly from SQLite without the LLM generating the
answer text:

## Account

- What is my account status?
- Is my account active?
- Is my account suspended?
- Is my account cancelled?
- Tell me about my account status.

## Plans

- What plan am I currently on?
- Which NexaTel plan do I have?
- What subscription am I using?
- What are my current plan details?
- When will my plan renew?
- When is my next plan renewal?
- What date does my subscription renew?
- When does my plan expire?

## Data Usage

- How much data have I used this month?
- Show me my data usage for this month.
- How much mobile data have I consumed this month?
- How much data did I use last month?
- Show my data consumption from last month.
- How much data have I used this year?
- What is my data usage?

## Voice Usage

- How many voice minutes have I used this month?
- How many call minutes have I consumed this month?
- Show my voice usage for last month.
- How many minutes have I used this year?
- What is my call usage?

## Bills

- What is my current bill?
- How much is my current bill?
- What do I currently owe?
- Show me my current invoice.
- Show my bill history.
- Show me my last 5 bills.
- Show my last 3 billing records.
- Show my most recent bill.
- How much have I spent?
- How much have I spent in total?
- What is my total spending for my last 3 bills?
- Compare my current bill with last month's bill.
- Compare my current bill with the previous bill.
- Compare BILL003 and BILL004.

## Payments

- What is the status of my latest payment?
- Is my latest payment pending?
- Was my last payment successful?
- Show me my payment history.
- Show my last 5 payments.
- Payments

## Support Tickets

- What support tickets do I have?
- Do I have any open support tickets?
- Show my open support cases.
- What is the status of my support requests?
- Show my last 3 tickets.

## Devices

- What devices are on my account?
- What devices are associated with my account?
- Show my phones.
- What router do I have?
- List the devices connected to my account.

## Additional Supported Variations

- Can you tell me my current plan?
- What happened with my recent payment?
- How much have I spent on my bills?
- Is my account currently active?
- What is the current status of my account?
- What service plan do I have?
- When will my subscription expire?
- Show me my current-year data usage.
- How many minutes did I use last month?
- Show my voice usage for this month.
- What is the amount due?
- How much is my latest invoice?
- Show me my phone bill.
- What were my previous bills?
- List my recent invoices.
- How much did I spend across my last 3 bills?
- What is the total amount I have paid?
- Why is my current bill different from last month?
- Show the difference between BILL009 and BILL010.
- Which of my last two bills was higher?
- What is the status of my payment?
- Did my last payment fail?
- Has my latest payment gone through?
- List my recent payments.
- Do I have any unresolved tickets?
- List my active devices.
- Do I have a router registered?
- What phones and routers are linked to my account?

## Clarification Checks

These are intentionally ambiguous. The chatbot should ask a clarification
question instead of choosing a database query:

- How much have I used?
- What are my latest details?
- Show me my information.
- What happened with my account?

For the first question, the clarification should distinguish between data
usage and voice/call-minute usage.

## Payment Status Synonyms

These should return the latest payment status, not payment history:

- Has my latest payment gone through?
- Was my latest payment successful?
- Did my last payment fail?
- Is my payment pending?
- What happened with my recent payment?

## Parameter Safety Checks

These should use the requested limit or bill IDs and remain restricted to the
selected customer's records:

- Show my last 3 bills.
- Show my last 5 payments.
- List my last 3 support tickets.
- Compare BILL003 and BILL004.
- Show the difference between BILL009 and BILL010.

Try the bill-ID questions while different customers are selected. A bill that
does not belong to the selected customer should not be disclosed.

## Unsupported Action or Unrelated Questions

These should receive an unsupported response because the chatbot currently
only reads account data:

- Cancel my subscription.
- Upgrade my plan.
- Make a payment for me.
- Open a support ticket.
- Troubleshoot my network.
- What will the weather be tomorrow?
- Tell me a general trivia fact.
