"""Phase 5 cross-domain intelligence for NexaTel."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.config.attention import (
    ATTENTION_ACCOUNT_STATUSES,
    ATTENTION_BILL_STATUSES,
    ATTENTION_PAYMENT_STATUSES,
    ATTENTION_SUBSCRIPTION_STATUSES,
    ATTENTION_SUPPORT_PRIORITIES,
    ATTENTION_SUPPORT_STATUSES,
    HIGH_USAGE_ATTENTION_PERCENTAGE,
)
from app.database.queries.credits import (
    get_available_credit_total,
)
from app.handlers.account import get_account_status
from app.handlers.billing import (
    get_bill_breakdown,
    get_current_bill,
)
from app.handlers.devices import get_device_summary
from app.handlers.payments import (
    get_payment_status,
    reconcile_bill_payment,
)
from app.handlers.plans import (
    get_current_plan,
    get_latest_subscription_overview,
)
from app.handlers.support import (
    filter_support_tickets,
    get_support_ticket_count,
)
from app.handlers.usage import (
    get_usage_percentage,
    get_usage_remaining,
)
from app.database.queries.customer_360 import (
    get_customer_360_records,
)
from app.models.domain import (
    CustomerContext,
    SupportTicketCategory,
    TruthStatus,
    UsagePercentageType,
    UsageType,
)
from app.truth.result import (
    TruthResult,
    not_found_result,
    verified_result,
)
from app.truth.sources import DATABASE_SOURCE


def _verified_data(
    result: TruthResult[Any],
) -> dict[str, Any] | None:
    if not result.is_verified:
        return None

    if not isinstance(
        result.data,
        dict,
    ):
        return None

    return result.data


def _database_error(
    *results: TruthResult[Any],
) -> TruthResult[Any] | None:
    return next(
        (
            result
            for result in results
            if result.status
            == TruthStatus.DATABASE_ERROR
        ),
        None,
    )


def _money(
    value: Any,
) -> float:
    return round(
        float(value),
        2,
    )


def _support_tickets(
    result: TruthResult[Any],
) -> list[dict[str, Any]]:
    data = _verified_data(
        result
    )

    if data is None:
        return []

    tickets = data.get(
        "tickets"
    )

    if not isinstance(
        tickets,
        list,
    ):
        return []

    return [
        ticket
        for ticket in tickets
        if isinstance(
            ticket,
            dict,
        )
    ]


def get_plan_usage_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Compose plan and Phase 1 usage intelligence.

    No usage arithmetic is duplicated here.
    """

    plan_result = get_current_plan(
        db,
        customer,
    )

    remaining_result = (
        get_usage_remaining(
            db,
            customer,
            usage_type=UsageType.DATA,
        )
    )

    percentage_result = (
        get_usage_percentage(
            db,
            customer,
            usage_type=UsageType.DATA,
            percentage_type=(
                UsagePercentageType.CONSUMED
            ),
        )
    )

    error = _database_error(
        plan_result,
        remaining_result,
        percentage_result,
    )

    if error is not None:
        return error

    plan = _verified_data(
        plan_result
    )

    remaining = _verified_data(
        remaining_result
    )

    percentage = _verified_data(
        percentage_result
    )

    if plan is None:
        return not_found_result(
            source=DATABASE_SOURCE,
            message=(
                "I couldn't retrieve an active plan "
                "for your account."
            ),
        )

    if remaining is None:
        return not_found_result(
            source=DATABASE_SOURCE,
            message=(
                "I can see your current plan, but I "
                "don't have the required usage records "
                "for the current period."
            ),
        )

    consumed_percentage = (
        percentage.get(
            "consumed_percentage"
        )
        if percentage is not None
        else remaining.get(
            "consumed_percentage"
        )
    )

    return verified_result(
        {
            "result_type": (
                "CROSS_PLAN_USAGE_STATUS"
            ),
            "plan": {
                "plan_name": plan[
                    "plan_name"
                ],
                "plan_type": plan[
                    "plan_type"
                ],
                "monthly_price": plan[
                    "monthly_price"
                ],
                "subscription_status": plan[
                    "subscription_status"
                ],
                "renewal_date": plan[
                    "renewal_date"
                ],
            },
            "usage": {
                "period": remaining[
                    "period"
                ],
                "used": remaining[
                    "used"
                ],
                "unit": remaining[
                    "unit"
                ],
                "allowance": remaining[
                    "allowance"
                ],
                "remaining": remaining[
                    "remaining"
                ],
                "over_allowance": remaining[
                    "over_allowance"
                ],
                "is_unlimited": remaining[
                    "is_unlimited"
                ],
                "consumed_percentage": (
                    consumed_percentage
                ),
            },
            "supporting_domains": [
                "plan",
                "usage",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "plans,subscriptions,usage"
            ),
        },
    )


def get_bill_payment_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Compose current bill and Phase 3 payment reconciliation.
    """

    bill_result = get_current_bill(
        db,
        customer,
    )

    reconciliation_result = (
        reconcile_bill_payment(
            db,
            customer,
        )
    )

    error = _database_error(
        bill_result,
        reconciliation_result,
    )

    if error is not None:
        return error

    bill = _verified_data(
        bill_result
    )

    reconciliation = _verified_data(
        reconciliation_result
    )

    if bill is None:
        return not_found_result(
            source=DATABASE_SOURCE,
            message=(
                "I don't have a current bill record "
                "for your account."
            ),
        )

    if reconciliation is None:
        return verified_result(
            {
                "result_type": (
                    "CROSS_BILL_PAYMENT_STATUS"
                ),
                "bill": bill,
                "payment": {
                    "attempt_count": 0,
                    "successful_paid_amount": 0.0,
                    "pending_amount": 0.0,
                    "outstanding_amount": (
                        bill["amount"]
                    ),
                    "is_fully_paid": False,
                    "latest_attempt": None,
                },
                "supporting_domains": [
                    "billing",
                    "payment",
                ],
            },
            source=DATABASE_SOURCE,
            metadata={
                "domains": (
                    "bills,payments"
                ),
            },
        )

    attempts = reconciliation.get(
        "payment_attempts",
        [],
    )

    latest_attempt = (
        attempts[-1]
        if attempts
        else None
    )

    return verified_result(
        {
            "result_type": (
                "CROSS_BILL_PAYMENT_STATUS"
            ),
            "bill": reconciliation[
                "bill"
            ],
            "payment": {
                "attempt_count": reconciliation[
                    "attempt_count"
                ],
                "successful_attempt_count": (
                    reconciliation[
                        "successful_attempt_count"
                    ]
                ),
                "failed_attempt_count": (
                    reconciliation[
                        "failed_attempt_count"
                    ]
                ),
                "pending_attempt_count": (
                    reconciliation[
                        "pending_attempt_count"
                    ]
                ),
                "successful_paid_amount": (
                    reconciliation[
                        "successful_paid_amount"
                    ]
                ),
                "pending_amount": reconciliation[
                    "pending_amount"
                ],
                "outstanding_amount": (
                    reconciliation[
                        "outstanding_amount"
                    ]
                ),
                "is_fully_paid": reconciliation[
                    "is_fully_paid"
                ],
                "reconciliation_consistent": (
                    reconciliation[
                        "reconciliation_consistent"
                    ]
                ),
                "latest_attempt": (
                    latest_attempt
                ),
            },
            "supporting_domains": [
                "billing",
                "payment",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "bills,payments"
            ),
        },
    )


def get_bill_payment_explanation(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Compose current bill items with payment reconciliation.

    Bill-item and payment calculations remain inside their
    existing domain handlers.
    """

    bill_result = get_current_bill(
        db,
        customer,
    )

    breakdown_result = (
        get_bill_breakdown(
            db,
            customer,
        )
    )

    reconciliation_result = (
        reconcile_bill_payment(
            db,
            customer,
        )
    )

    bill = _verified_data(
        bill_result
    )

    breakdown = _verified_data(
        breakdown_result
    )

    reconciliation = _verified_data(
        reconciliation_result
    )

    if bill is None:
        return not_found_result(
            source=DATABASE_SOURCE,
            message=(
                "I don't have a current bill record "
                "for your account."
            ),
        )

    items = (
        breakdown.get(
            "items",
            [],
        )
        if breakdown is not None
        else []
    )

    payment_data: dict[str, Any]

    if reconciliation is None:
        payment_data = {
            "attempt_count": 0,
            "successful_paid_amount": 0.0,
            "pending_amount": 0.0,
            "outstanding_amount": (
                bill["amount"]
            ),
            "is_fully_paid": False,
            "latest_attempt": None,
        }

    else:
        attempts = reconciliation.get(
            "payment_attempts",
            [],
        )

        payment_data = {
            "attempt_count": reconciliation[
                "attempt_count"
            ],
            "successful_paid_amount": (
                reconciliation[
                    "successful_paid_amount"
                ]
            ),
            "pending_amount": reconciliation[
                "pending_amount"
            ],
            "outstanding_amount": (
                reconciliation[
                    "outstanding_amount"
                ]
            ),
            "is_fully_paid": reconciliation[
                "is_fully_paid"
            ],
            "reconciliation_consistent": (
                reconciliation[
                    "reconciliation_consistent"
                ]
            ),
            "latest_attempt": (
                attempts[-1]
                if attempts
                else None
            ),
        }

    return verified_result(
        {
            "result_type": (
                "CROSS_BILL_PAYMENT_EXPLANATION"
            ),
            "bill": bill,
            "items": items,
            "payment": payment_data,
            "supporting_domains": [
                "billing",
                "bill_items",
                "payment",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "bills,bill_items,payments"
            ),
        },
    )


def get_billing_support_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Report billing-category support tickets without claiming that
    any ticket is linked to a particular bill.
    """

    bill_result = get_current_bill(
        db,
        customer,
    )

    support_result = (
        filter_support_tickets(
            db,
            customer,
            ticket_category=(
                SupportTicketCategory.BILLING
            ),
        )
    )

    bill = _verified_data(
        bill_result
    )

    tickets = _support_tickets(
        support_result
    )

    return verified_result(
        {
            "result_type": (
                "CROSS_BILLING_SUPPORT_STATUS"
            ),
            "current_bill": bill,
            "billing_tickets": tickets,
            "ticket_count": len(
                tickets
            ),
            "direct_bill_link_established": False,
            "supporting_domains": [
                "billing",
                "support",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "bills,support_tickets"
            ),
        },
    )


def get_payment_support_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Report payment-category support tickets without inventing a
    transaction-to-ticket relationship.
    """

    payment_result = (
        get_payment_status(
            db,
            customer,
        )
    )

    support_result = (
        filter_support_tickets(
            db,
            customer,
            ticket_category=(
                SupportTicketCategory.PAYMENT
            ),
        )
    )

    payment = _verified_data(
        payment_result
    )

    tickets = _support_tickets(
        support_result
    )

    return verified_result(
        {
            "result_type": (
                "CROSS_PAYMENT_SUPPORT_STATUS"
            ),
            "latest_payment": (
                payment.get(
                    "payment"
                )
                if payment
                else None
            ),
            "payment_tickets": tickets,
            "ticket_count": len(
                tickets
            ),
            "direct_transaction_link_established": (
                False
            ),
            "supporting_domains": [
                "payment",
                "support",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "payments,support_tickets"
            ),
        },
    )


def get_account_plan_status(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Compose account, subscription and plan state."""

    account_result = (
        get_account_status(
            db,
            customer,
        )
    )

    active_plan_result = get_current_plan(
        db,
        customer,
    )

    error = _database_error(
        account_result,
        active_plan_result,
    )

    if error is not None:
        return error

    plan_result = (
        active_plan_result
        if active_plan_result.is_verified
        else get_latest_subscription_overview(
            db,
            customer,
        )
    )

    error = _database_error(
        plan_result,
    )

    if error is not None:
        return error

    account = _verified_data(
        account_result
    )

    plan = _verified_data(
        plan_result
    )

    if account is None:
        return not_found_result(
            source=DATABASE_SOURCE,
            message=(
                "I couldn't retrieve your account "
                "status."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "CROSS_ACCOUNT_PLAN_STATUS"
            ),
            "account": {
                "account_status": account[
                    "account_status"
                ],
            },
            "subscription": (
                {
                    "subscription_id": plan[
                        "subscription_id"
                    ],
                    "subscription_status": plan[
                        "subscription_status"
                    ],
                    "renewal_date": plan[
                        "renewal_date"
                    ],
                }
                if plan is not None
                else None
            ),
            "plan": (
                {
                    "plan_name": plan[
                        "plan_name"
                    ],
                    "plan_type": plan[
                        "plan_type"
                    ],
                    "monthly_price": plan[
                        "monthly_price"
                    ],
                }
                if plan is not None
                else None
            ),
            "supporting_domains": [
                "account",
                "subscription",
                "plan",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "customers,subscriptions,plans"
            ),
        },
    )


def _attention_item(
    domain: str,
    severity: str,
    message: str,
    prompt: str,
) -> dict[str, str]:
    return {
        "domain": domain,
        "severity": severity,
        "message": message,
        "prompt": prompt,
    }


def get_account_attention_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Build a small deterministic attention summary.

    This deliberately selects only the Phase 5 attention rules
    instead of dumping every available customer observation.
    """

    attention_items: list[
        dict[str, str]
    ] = []

    # --------------------------------------------------------
    # Account / subscription
    # --------------------------------------------------------

    account_plan_result = (
        get_account_plan_status(
            db,
            customer,
        )
    )

    account_plan = _verified_data(
        account_plan_result
    )

    error = _database_error(
        account_plan_result
    )

    if error is not None:
        return error

    if account_plan is not None:
        account_status = (
            account_plan[
                "account"
            ][
                "account_status"
            ]
        )

        if (
            account_status
            in ATTENTION_ACCOUNT_STATUSES
        ):
            attention_items.append(
                _attention_item(
                    "Account",
                    "high",
                    "Your account is suspended.",
                    "What is my account status?",
                )
            )

        subscription = (
            account_plan.get(
                "subscription"
            )
        )

        if subscription is not None:
            subscription_status = (
                subscription[
                    "subscription_status"
                ]
            )

            if (
                subscription_status
                in ATTENTION_SUBSCRIPTION_STATUSES
            ):
                attention_items.append(
                    _attention_item(
                        "Plan",
                        "high",
                        "Your subscription is suspended.",
                        "Is my account and subscription active?",
                    )
                )

    # --------------------------------------------------------
    # Current bill
    # --------------------------------------------------------

    bill_result = get_current_bill(
        db,
        customer,
    )

    bill = _verified_data(
        bill_result
    )

    error = _database_error(
        bill_result
    )

    if error is not None:
        return error

    if bill is not None:
        bill_status = bill[
            "status"
        ]

        if (
            bill_status
            in ATTENTION_BILL_STATUSES
        ):
            attention_items.append(
                _attention_item(
                    "Billing",
                    (
                        "high"
                        if bill_status
                        == "OVERDUE"
                        else "medium"
                    ),
                    (
                        f"Your current bill is "
                        f"{bill_status.lower().replace('_', ' ')}."
                    ),
                    "What is my current bill and its payment status?",
                )
            )

    # --------------------------------------------------------
    # Latest payment
    # --------------------------------------------------------

    payment_result = (
        get_payment_status(
            db,
            customer,
        )
    )

    payment = _verified_data(
        payment_result
    )

    error = _database_error(
        payment_result
    )

    if error is not None:
        return error

    if payment is not None:
        latest_payment = payment.get(
            "payment"
        )

        if latest_payment is not None:
            payment_status = (
                latest_payment[
                    "status"
                ]
            )

            if (
                payment_status
                in ATTENTION_PAYMENT_STATUSES
            ):
                if (
                    payment_status
                    == "FAILED"
                ):
                    message = (
                        "Your latest payment attempt "
                        "failed."
                    )

                else:
                    message = (
                        "Your latest payment attempt "
                        "is still pending."
                    )

                attention_items.append(
                    _attention_item(
                        "Payment",
                        "high",
                        message,
                        (
                            "Why did my payment fail?"
                            if payment_status == "FAILED"
                            else "What is the status of my latest payment?"
                        ),
                    )
                )

    # --------------------------------------------------------
    # High / critical unresolved support
    # --------------------------------------------------------

    unresolved_result = (
        filter_support_tickets(
            db,
            customer,
            unresolved_only=True,
        )
    )

    unresolved_tickets = (
        _support_tickets(
            unresolved_result
        )
    )

    error = _database_error(
        unresolved_result
    )

    if error is not None:
        return error

    important_tickets = [
        ticket
        for ticket
        in unresolved_tickets
        if (
            ticket[
                "status"
            ]
            in ATTENTION_SUPPORT_STATUSES
            and ticket[
                "priority"
            ]
            in ATTENTION_SUPPORT_PRIORITIES
        )
    ]

    if important_tickets:
        highest = (
            "critical"
            if any(
                ticket[
                    "priority"
                ]
                == "CRITICAL"
                for ticket
                in important_tickets
            )
            else "high-priority"
        )

        count = len(
            important_tickets
        )

        attention_items.append(
            _attention_item(
                "Support",
                "high",
                (
                    f"You have {count} unresolved "
                    f"{highest} support "
                    f"{'ticket' if count == 1 else 'tickets'}."
                ),
                "Show my open support tickets.",
            )
        )

    # --------------------------------------------------------
    # High limited-plan data usage
    # --------------------------------------------------------

    plan_usage_result = (
        get_plan_usage_status(
            db,
            customer,
        )
    )

    plan_usage = _verified_data(
        plan_usage_result
    )

    error = _database_error(
        plan_usage_result
    )

    if error is not None:
        return error

    if plan_usage is not None:
        usage = plan_usage[
            "usage"
        ]

        percentage = usage.get(
            "consumed_percentage"
        )

        if (
            not usage.get(
                "is_unlimited"
            )
            and percentage
            is not None
            and float(
                percentage
            )
            >= HIGH_USAGE_ATTENTION_PERCENTAGE
        ):
            attention_items.append(
                _attention_item(
                    "Usage",
                    "medium",
                    (
                        f"You've used "
                        f"{float(percentage):.1f}% "
                        "of your current data allowance."
                    ),
                    "How much data have I used this month?",
                )
            )

    try:
        credit_total = get_available_credit_total(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        credit_total = 0.0

    if credit_total > 0:
        attention_items.append(
            _attention_item(
                "Credits",
                "medium",
                (
                    f"You have ₹{credit_total:.0f} in "
                    "available account credits."
                ),
                "Do I have any account credits?",
            )
        )

    return verified_result(
        {
            "result_type": (
                "CROSS_ACCOUNT_ATTENTION_SUMMARY"
            ),
            "attention_count": len(
                attention_items
            ),
            "items": attention_items,
            "thresholds": {
                "high_usage_percentage": (
                    HIGH_USAGE_ATTENTION_PERCENTAGE
                ),
            },
            "supporting_domains": [
                "account",
                "plan",
                "usage",
                "billing",
                "payment",
                "support",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "customers,subscriptions,plans,"
                "usage,bills,payments,support_tickets"
            ),
        },
    )


def get_customer_360(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Compose the customer's verified account intelligence."""

    account_plan_result = get_account_plan_status(
        db,
        customer,
    )

    if not account_plan_result.is_verified:
        return account_plan_result

    plan_usage_result = get_plan_usage_status(
        db,
        customer,
    )

    bill_payment_result = get_bill_payment_status(
        db,
        customer,
    )

    support_count_result = get_support_ticket_count(
        db,
        customer,
        unresolved_only=True,
    )

    unresolved_result = filter_support_tickets(
        db,
        customer,
        unresolved_only=True,
    )

    device_result = get_device_summary(
        db,
        customer,
    )

    attention_result = get_account_attention_summary(
        db,
        customer,
    )

    account_record_result = get_account_status(
        db,
        customer,
    )

    error = _database_error(
        plan_usage_result,
        bill_payment_result,
        support_count_result,
        unresolved_result,
        device_result,
        attention_result,
        account_record_result,
    )

    if error is not None:
        return error

    account_plan = _verified_data(
        account_plan_result
    )

    plan_usage = _verified_data(
        plan_usage_result
    )

    bill_payment = _verified_data(
        bill_payment_result
    )

    support_count = _verified_data(
        support_count_result
    )

    devices = _verified_data(
        device_result
    )

    attention = _verified_data(
        attention_result
    )

    unresolved = _verified_data(
        unresolved_result
    )

    account_record = _verified_data(
        account_record_result
    )

    try:
        records = get_customer_360_records(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve all records for your "
                "Customer 360 view."
            ),
        )

    unresolved_tickets = (
        unresolved.get(
            "tickets",
            [],
        )
        if unresolved is not None
        else []
    )
    important_ticket = next(
        (
            ticket
            for ticket in unresolved_tickets
            if ticket.get(
                "priority"
            )
            == "CRITICAL"
        ),
        None,
    ) or next(
        (
            ticket
            for ticket in unresolved_tickets
            if ticket.get(
                "priority"
            )
            == "HIGH"
        ),
        None,
    )

    if important_ticket is not None:
        important_ticket = {
            "ticket_id": important_ticket[
                "ticket_id"
            ],
            "category": important_ticket[
                "category"
            ],
            "status": important_ticket[
                "status"
            ],
            "priority": important_ticket[
                "priority"
            ],
            "related_bill_id": important_ticket.get(
                "related_bill_id"
            ),
            "related_payment_id": important_ticket.get(
                "related_payment_id"
            ),
        }

    device_summary = (
        devices
        if devices is not None
        else {
            "total_devices": 0,
            "active_count": 0,
            "active_devices": [],
        }
    )

    return verified_result(
        {
            "result_type": "CUSTOMER_360",
            "account": account_record or account_plan[
                "account"
            ],
            "subscription": account_plan.get(
                "subscription"
            ),
            "plan": account_plan.get(
                "plan"
            ),
            "usage": (
                plan_usage["usage"]
                if plan_usage is not None
                else None
            ),
            "usage_message": (
                plan_usage_result.message
                if plan_usage is None
                else None
            ),
            "billing": (
                bill_payment["bill"]
                if bill_payment is not None
                else None
            ),
            "payment": (
                bill_payment["payment"]
                if bill_payment is not None
                else None
            ),
            "support": {
                "unresolved_count": (
                    support_count["count"]
                    if support_count is not None
                    else None
                ),
                "important_ticket": important_ticket,
            },
            "devices": {
                "available": devices is not None,
                "total_count": device_summary[
                    "total_devices"
                ],
                "active_count": device_summary[
                    "active_count"
                ],
                "active_devices": device_summary[
                    "active_devices"
                ],
            },
            "attention": {
                "count": (
                    attention["attention_count"]
                    if attention is not None
                    else None
                ),
                "items": (
                    attention["items"]
                    if attention is not None
                    else []
                ),
            },
            "records": records,
            "supporting_domains": [
                "account",
                "subscription",
                "plan",
                "usage",
                "billing",
                "payment",
                "support",
                "devices",
            ],
        },
        source=DATABASE_SOURCE,
        metadata={
            "domains": (
                "customers,subscriptions,plans,usage,bills,"
                "payments,support_tickets,devices"
            ),
        },
    )


