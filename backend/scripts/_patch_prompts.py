from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/llm/prompts.py"
text = path.read_text(encoding="utf-8")
if "GET_SUPPORT_TICKET_UPDATES" in text:
    raise SystemExit(0)
insert = """
Also use these structured intents when the wording matches:
- GET_LIST_SUBSCRIPTIONS: list all mobile/fiber services on the account.
- GET_PLAN_CATALOG / GET_PLAN_COMPARISON: available plans and side-by-side plan IDs.
- GET_BILL_CHARGE_SUMMARY: roaming, tax, or add-on totals (bill_item_type).
- GET_PROJECTED_BILL: estimated current-month bill from plan price and usage.
- GET_PAYMENT_PROFILE: autopay and payment method on file.
- GET_ACCOUNT_CREDITS: credit balance and credit history.
- GET_SUPPORT_TICKET_UPDATES: full ticket timeline (not only latest update).
- GET_LAST_FAILED_PAYMENT: include failure_reason from records when present.
- GET_CURRENT_BILL with plan_type for mobile vs fiber bills.

"""
text = text.replace(
    "GET_CUSTOMER_360\n\n\n"
    "============================================================\n"
    "REGISTERED BACKEND CAPABILITIES",
    "GET_CUSTOMER_360\n"
    + insert
    + "\n============================================================\n"
    "REGISTERED BACKEND CAPABILITIES",
)
path.write_text(text, encoding="utf-8")
