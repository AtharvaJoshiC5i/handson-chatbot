# NexaTel AI Support

NexaTel AI Support is a conversational customer service assistant for everyday account questions. It helps customers find information about their NexaTel service quickly, using a simple chat experience.

## What the Chatbot Can Help With

### Account and Plan

- Check whether an account is active, suspended, or cancelled
- View the current mobile or service plan
- Find the next plan renewal date

### Usage

- Check data usage for the current month
- Review data usage from the previous month
- View data usage for the current year
- Check voice and call-minute usage for supported time periods

### Bills and Spending

- View the current bill and amount due
- Review recent bills
- Calculate total spending across recent bills
- Compare the current bill with the previous bill

### Payments

- Check the latest payment status
- Review recent payment history
- See whether a payment was successful, pending, or unsuccessful

### Support and Devices

- View existing support tickets
- Check the status of support requests
- View devices connected with the customer account

## Example Questions

You can ask questions such as:

- What plan am I currently on?
- When will my plan renew?
- Is my account active?
- How much data have I used this month?
- How many voice minutes did I use last month?
- What is my current bill?
- Show me my last five bills.
- How much have I spent in total?
- Compare my current bill with the previous bill.
- What is the status of my latest payment?
- Show me my payment history.
- Do I have any open support tickets?
- What devices are associated with my account?

## Getting the Best Results

Choose the correct customer account before asking a question. For usage questions, include the period you want to review, such as “this month,” “last month,” or “this year.” For lists such as bills, payments, or support tickets, you can request a specific number of recent records.

The chatbot uses the selected customer account when answering questions. It does not rely on a customer number written inside the message to identify the account.

## Clear and Reliable Answers

The assistant is designed to answer questions about supported NexaTel account information. When information is unavailable, unclear, or outside the assistant's capabilities, it will say so instead of inventing an answer.

For questions about topics such as weather, general trivia, unrelated products, or services outside NexaTel account support, the chatbot will explain that the request is not currently supported.

## Current Scope

NexaTel AI Support focuses on looking up account information and customer records. It does not currently change plans, make payments, open new tickets, troubleshoot network problems, or perform account actions on a customer's behalf.

## Inspect the Database

From the `backend` directory, run:

```powershell
python scripts/view_database.py
```

This displays every application table, its columns, row count, and complete contents. To inspect selected tables only:

```powershell
python scripts/view_database.py --table customers --table bills
```

The complete question checklist is in [QUESTIONS.md](QUESTIONS.md).
