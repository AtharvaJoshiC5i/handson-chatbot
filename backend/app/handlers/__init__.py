"""NexaTel intent handlers."""

from app.handlers.account import get_account_status
from app.handlers.billing import (
    get_bill_comparison,
    get_bill_history_for_customer,
    get_current_bill,
    get_total_spending,
)
from app.handlers.devices import get_device_information
from app.handlers.payments import (
    get_payment_history_for_customer,
    get_payment_status,
)
from app.handlers.plans import (
    get_current_plan,
    get_plan_renewal,
)
from app.handlers.support import (
    get_customer_support_tickets,
)
from app.handlers.usage import (
    get_data_usage,
    get_voice_usage,
)

__all__ = [
    "get_account_status",
    "get_current_plan",
    "get_plan_renewal",
    "get_data_usage",
    "get_voice_usage",
    "get_current_bill",
    "get_bill_history_for_customer",
    "get_total_spending",
    "get_bill_comparison",
    "get_payment_status",
    "get_payment_history_for_customer",
    "get_customer_support_tickets",
    "get_device_information",
]