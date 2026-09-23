"""NexaTel database query layer."""

from app.database.queries.customers import get_customer
from app.database.queries.plans import get_plan_by_id
from app.database.queries.subscriptions import (
    get_current_subscription,
    get_subscription_by_id,
)
from app.database.queries.usage import (
    get_usage_by_customer_and_date_range,
)
from app.database.queries.bills import (
    get_bill_by_id,
    get_bill_history,
    get_bill_items,
    get_current_bill,
)
from app.database.queries.payments import (
    get_payment_history,
    get_payment_status_for_customer,
)
from app.database.queries.support_tickets import (
    get_support_tickets,
)
from app.database.queries.devices import (
    get_customer_devices,
)

__all__ = [
    "get_customer",
    "get_plan_by_id",
    "get_current_subscription",
    "get_subscription_by_id",
    "get_usage_by_customer_and_date_range",
    "get_bill_by_id",
    "get_bill_history",
    "get_bill_items",
    "get_current_bill",
    "get_payment_history",
    "get_payment_status_for_customer",
    "get_support_tickets",
    "get_customer_devices",
]