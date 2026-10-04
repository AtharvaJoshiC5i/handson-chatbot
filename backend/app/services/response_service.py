"""Customer-facing response generation for NexaTel."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.models.domain import TruthStatus
from app.truth.result import TruthResult


# ============================================================
# SHARED FORMATTING
# ============================================================


def _number(
    value: Any,
) -> str:
    if value is None:
        return ""

    if isinstance(
        value,
        bool,
    ):
        return str(value)

    if isinstance(
        value,
        int,
    ):
        return f"{value:,}"

    if isinstance(
        value,
        float,
    ):
        if value.is_integer():
            return f"{int(value):,}"

        return (
            f"{value:,.2f}"
            .rstrip("0")
            .rstrip(".")
        )

    return str(value)


def _money(
    value: Any,
) -> str:
    return f"₹{_number(value)}"


def _label(
    value: Any,
) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .replace("_", " ")
        .title()
    )


def _customer_date(
    value: Any,
) -> str:
    if not value:
        return "date unavailable"

    try:
        parsed_date = date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)

    return parsed_date.strftime("%d %b %Y").lstrip("0")


def _metric_label(
    usage_type: str,
) -> str:
    return {
        "DATA": "Data",
        "VOICE": "Voice",
        "SMS": "SMS",
    }.get(
        usage_type,
        usage_type.title(),
    )


def _get_result_type(
    data: dict[str, Any],
) -> str | None:
    result_type = data.get(
        "result_type"
    )

    if isinstance(
        result_type,
        str,
    ):
        return result_type

    return None


# ============================================================
# PHASE 1 — USAGE
# ============================================================


def _format_current_usage(
    data: dict[str, Any],
) -> str:
    used = _number(
        data["used"]
    )

    unit = data["unit"]
    period = data["period"]

    usage_type = data[
        "usage_type"
    ]

    if usage_type == "DATA":
        if data.get(
            "is_unlimited"
        ):
            return (
                f"You used {used} {unit} of data in "
                f"{period}. Your "
                f"{data['plan_name']} plan has "
                "unlimited data."
            )

        return (
            f"You used {used} {unit} of data in "
            f"{period}."
        )

    if usage_type == "VOICE":
        return (
            f"You used {used} voice minutes in "
            f"{period}."
        )

    return (
        f"You used {used} SMS in {period}."
    )


def _format_usage_remaining(
    data: dict[str, Any],
) -> str:
    used = _number(
        data["used"]
    )

    unit = data["unit"]

    label = _metric_label(
        data["usage_type"]
    ).lower()

    if data.get(
        "is_unlimited"
    ):
        return (
            f"You've used {used} {unit} of data in "
            f"{data['period']}. Your "
            f"{data['plan_name']} plan has unlimited "
            "data, so there is no fixed remaining "
            "data allowance."
        )

    over = data.get(
        "over_allowance",
        0,
    )

    if (
        over is not None
        and float(over) > 0
    ):
        return (
            f"You've used {used} {unit} of {label} "
            f"against your "
            f"{_number(data['allowance'])} {unit} "
            f"allowance in {data['period']}. "
            f"That's {_number(over)} {unit} above "
            "the included allowance."
        )

    return (
        f"You've used {used} {unit} of {label} in "
        f"{data['period']}. You have "
        f"{_number(data['remaining'])} {unit} "
        "remaining."
    )


def _format_usage_percentage(
    data: dict[str, Any],
) -> str:
    label = _metric_label(
        data["usage_type"]
    ).lower()

    if data.get(
        "is_unlimited"
    ):
        return (
            f"You've used {_number(data['used'])} "
            f"{data['unit']} of data in "
            f"{data['period']}. Your "
            f"{data['plan_name']} plan has unlimited "
            "data, so there is no fixed allowance "
            "percentage."
        )

    if (
        data.get(
            "percentage_type"
        )
        == "REMAINING"
    ):
        return (
            f"You have "
            f"{_number(data['remaining_percentage'])}% "
            f"of your {label} allowance remaining "
            f"in {data['period']}."
        )

    return (
        f"You've used "
        f"{_number(data['consumed_percentage'])}% "
        f"of your {label} allowance in "
        f"{data['period']}."
    )


def _format_usage_summary(
    data: dict[str, Any],
) -> str:
    lines = [
        f"Usage for {data['period']}:"
    ]

    for metric in data.get(
        "metrics",
        [],
    ):
        usage_type = metric[
            "usage_type"
        ]

        used = _number(
            metric["used"]
        )

        unit = metric[
            "unit"
        ]

        if (
            usage_type == "DATA"
            and metric.get(
                "is_unlimited"
            )
        ):
            lines.append(
                f"Data: {used} {unit} used "
                "(unlimited plan)"
            )

            continue

        allowance = _number(
            metric["allowance"]
        )

        remaining = _number(
            metric["remaining"]
        )

        over = metric.get(
            "over_allowance",
            0,
        )

        if (
            over is not None
            and float(over) > 0
        ):
            lines.append(
                f"{_metric_label(usage_type)}: "
                f"{used} of {allowance} {unit} used; "
                f"{_number(over)} {unit} above the "
                "included allowance"
            )

        else:
            lines.append(
                f"{_metric_label(usage_type)}: "
                f"{used} of {allowance} {unit} used; "
                f"{remaining} {unit} remaining"
            )

    return "\n".join(
        lines
    )


def _format_usage_history(
    data: dict[str, Any],
) -> str:
    history = data.get(
        "history",
        [],
    )
    label = _metric_label(
        data["usage_type"],
    ).lower()

    if not history:
        return (
            f"No {label} usage history is "
            "available for this period."
        )

    count = len(history)

    return (
        f"Your {label} usage across {count} "
        f"{'period' if count == 1 else 'periods'} "
        "is shown in the breakdown below."
    )


def _format_usage_average(
    data: dict[str, Any],
) -> str:
    return (
        f"Your average monthly "
        f"{_metric_label(data['usage_type']).lower()} "
        f"usage over the available "
        f"{data['month_count']} months is "
        f"{_number(data['average'])} "
        f"{data['unit']}."
    )


def _format_usage_extreme(
    data: dict[str, Any],
) -> str:
    extreme = (
        "highest"
        if data[
            "extreme_type"
        ]
        == "HIGHEST"
        else "lowest"
    )

    return (
        f"Your {extreme} "
        f"{_metric_label(data['usage_type']).lower()} "
        "usage in the available usage history was "
        f"{data['period']} at "
        f"{_number(data['value'])} "
        f"{data['unit']}."
    )


def _format_usage_comparison(
    data: dict[str, Any],
) -> str:
    label = _metric_label(
        data["usage_type"],
    ).lower()

    return (
        f"Your {label} usage for "
        f"{data['period_1']} versus "
        f"{data['period_2']} is compared below."
    )


def _format_usage_trend(
    data: dict[str, Any],
) -> str:
    label = _metric_label(
        data["usage_type"],
    ).lower()
    months = data.get(
        "month_count",
        0,
    )

    return (
        f"Your {label} usage trend over "
        f"{months} months is shown in the chart below."
    )


# ============================================================
# PHASE 2 — BILLING
# ============================================================


def _format_bill(
    data: dict[str, Any],
) -> str:
    return (
        f"Your {data['period']} bill is "
        f"{_money(data['amount'])}. "
        f"It is {_label(data['status']).lower()} "
        f"and its due date is "
        f"{data['due_date']}."
    )


def _format_bill_history(
    data: dict[str, Any],
) -> str:
    bills = data.get(
        "bills",
        [],
    )

    if not bills:
        return (
            "I don't have any billing records "
            "for the requested period."
        )

    return (
        f"I found {len(bills)} "
        f"{'bill' if len(bills) == 1 else 'bills'} "
        "in your billing history."
    )


def _format_bill_breakdown(
    data: dict[str, Any],
) -> str:
    bill = data[
        "bill"
    ]

    items = data.get(
        "items",
        [],
    )

    if not items:
        return (
            f"Your {bill['period']} bill totals "
            f"{_money(bill['amount'])}. "
            "Item-level charge details aren't "
            "available for this bill."
        )

    return (
        f"Your {bill['period']} bill totals "
        f"{_money(bill['amount'])} across "
        f"{len(items)} recorded "
        f"{'charge' if len(items) == 1 else 'charges'}."
    )


def _format_bill_comparison(
    data: dict[str, Any],
) -> str:
    current = data[
        "current_bill"
    ]

    previous = data[
        "comparison_bill"
    ]

    if (
        data["direction"]
        == "NO_CHANGE"
    ):
        return (
            f"Your {current['period']} and "
            f"{previous['period']} bills were both "
            f"{_money(current['amount'])}."
        )

    higher = (
        data["direction"]
        == "INCREASE"
    )

    return (
        f"Your {current['period']} bill is "
        f"{_money(data['absolute_difference'])} "
        f"{'higher' if higher else 'lower'} than "
        f"{previous['period']}."
    )


def _format_bill_change(
    data: dict[str, Any],
) -> str:
    current = data[
        "current_bill"
    ]

    previous = data[
        "comparison_bill"
    ]

    difference = float(
        data[
            "total_difference"
        ]
    )

    if difference == 0:
        return (
            f"Your {current['period']} bill is the "
            f"same as {previous['period']} at "
            f"{_money(current['amount'])}."
        )

    return (
        f"Your bill "
        f"{'increased' if difference > 0 else 'decreased'} "
        f"by {_money(abs(difference))}, from "
        f"{_money(previous['amount'])} in "
        f"{previous['period']} to "
        f"{_money(current['amount'])} in "
        f"{current['period']}."
    )


def _format_insufficient_bill_change(
    data: dict[str, Any],
) -> str:
    difference = float(
        data[
            "total_difference"
        ]
    )

    return (
        f"I can confirm the bill changed by "
        f"{_money(abs(difference))}, but the "
        "available data doesn't contain enough "
        "item-level detail to explain the cause."
    )


def _format_total_spending(
    data: dict[str, Any],
) -> str:
    return (
        f"Your total billed amount across "
        f"{data['bill_count']} bill"
        f"{'' if data['bill_count'] == 1 else 's'} "
        f"is {_money(data['total_billed_amount'])}."
    )


def _format_average_bill(
    data: dict[str, Any],
) -> str:
    return (
        f"Your average bill across the available "
        f"{data['bill_count']} bill"
        f"{'' if data['bill_count'] == 1 else 's'} "
        f"is {_money(data['average_amount'])}."
    )


def _format_bill_extreme(
    data: dict[str, Any],
) -> str:
    bill = data[
        "bill"
    ]

    extreme = (
        "highest"
        if data[
            "extreme_type"
        ]
        == "HIGHEST"
        else "lowest"
    )

    return (
        f"Your {extreme} bill in the available "
        f"history was {_money(bill['amount'])} in "
        f"{bill['period']}."
    )


def _format_bill_trend(
    data: dict[str, Any],
) -> str:
    phrase = {
        "GENERALLY_INCREASING": (
            "generally increased"
        ),
        "GENERALLY_DECREASING": (
            "generally decreased"
        ),
        "STABLE": (
            "remained relatively stable"
        ),
    }.get(
        data["trend"],
        "changed",
    )

    return (
        f"Your recorded bills have {phrase} across "
        f"the available {data['bill_count']}-bill "
        "history."
    )


def _format_bill_filter(
    data: dict[str, Any],
) -> str:
    bills = data.get(
        "bills",
        [],
    )

    return (
        f"I found {len(bills)} matching "
        f"{'bill' if len(bills) == 1 else 'bills'}."
    )


# ============================================================
# PHASE 3 — PAYMENTS
# ============================================================


def _payment_reference(
    payment: dict[str, Any],
) -> str | None:
    value = (
        payment.get(
            "transaction_reference"
        )
        or payment.get(
            "reference"
        )
    )

    if value is None:
        return None

    return str(value)


def _format_latest_payment(
    data: dict[str, Any],
) -> str:
    payment = data[
        "payment"
    ]

    text = (
        "Your latest payment attempt was "
        f"{_money(payment['amount'])} via "
        f"{_label(payment['payment_method'])} on "
        f"{payment['payment_date']}. "
        f"It is recorded as "
        f"{_label(payment['status']).lower()}."
    )

    reference = _payment_reference(
        payment
    )

    if reference:
        text += (
            f" Transaction reference: "
            f"{reference}."
        )

    return text


def _format_payment_history(
    data: dict[str, Any],
) -> str:
    payments = data.get(
        "payments",
        [],
    )

    if not payments:
        return (
            "I don't have any payment records "
            "for the requested period."
        )

    successful = sum(
        1
        for payment in payments
        if payment.get(
            "status"
        )
        == "SUCCESS"
    )

    failed = sum(
        1
        for payment in payments
        if payment.get(
            "status"
        )
        == "FAILED"
    )

    pending = sum(
        1
        for payment in payments
        if payment.get(
            "status"
        )
        == "PENDING"
    )

    parts = [
        (
            f"I found {len(payments)} payment "
            f"{'record' if len(payments) == 1 else 'records'}."
        )
    ]

    status_parts = []

    if successful:
        status_parts.append(
            f"{successful} successful"
        )

    if failed:
        status_parts.append(
            f"{failed} failed"
        )

    if pending:
        status_parts.append(
            f"{pending} pending"
        )

    if status_parts:
        parts.append(
            " ".join(
                [
                    "They include",
                    ", ".join(
                        status_parts
                    )
                    + ".",
                ]
            )
        )

    return " ".join(
        parts
    )


def _format_last_successful(
    data: dict[str, Any],
) -> str:
    payment = data[
        "payment"
    ]

    return (
        "Your most recent successful payment was "
        f"{_money(payment['amount'])} via "
        f"{_label(payment['payment_method'])} on "
        f"{payment['payment_date']}."
    )


def _format_last_failed(
    data: dict[str, Any],
) -> str:
    payment = data[
        "payment"
    ]

    reason = payment.get(
        "failure_reason"
    )

    if reason:
        return (
            "Your latest failed payment attempt was "
            f"{_money(payment['amount'])} via "
            f"{_label(payment['payment_method'])} on "
            f"{payment['payment_date']}. "
            f"The recorded failure reason is "
            f"{_label(reason).lower()}."
        )

    return (
        "Your latest failed payment attempt was "
        f"{_money(payment['amount'])} via "
        f"{_label(payment['payment_method'])} on "
        f"{payment['payment_date']}. "
        "The available payment data does not "
        "contain a failure reason."
    )


def _format_payment_transaction(
    data: dict[str, Any],
) -> str:
    payment = data[
        "payment"
    ]

    reference = (
        _payment_reference(
            payment
        )
        or "the requested transaction"
    )

    return (
        f"Transaction {reference} is recorded as "
        f"{_label(payment['status']).lower()}. "
        f"The amount is {_money(payment['amount'])}, "
        f"using {_label(payment['payment_method'])}."
    )


def _format_reconciliation(
    data: dict[str, Any],
) -> str:
    bill = data[
        "bill"
    ]

    if not data[
        "reconciliation_consistent"
    ]:
        return (
            "The available billing and payment "
            "records are inconsistent, so I can't "
            "reliably confirm the payment state."
        )

    if data[
        "attempt_count"
    ] == 0:
        return (
            f"Your {bill['period']} bill is "
            f"{_money(bill['amount'])}. "
            "I don't have a payment attempt recorded "
            "for this bill."
        )

    if data[
        "is_fully_paid"
    ]:
        message = (
            f"Your {bill['period']} bill of "
            f"{_money(bill['amount'])} has been "
            "fully paid."
        )

    else:
        message = (
            f"Your {bill['period']} bill is "
            f"{_money(bill['amount'])}. "
            f"You've successfully paid "
            f"{_money(data['successful_paid_amount'])}, "
            f"with {_money(data['outstanding_amount'])} "
            "currently outstanding."
        )

    attempts = data.get(
        "payment_attempts",
        [],
    )
    if attempts:
        latest_attempt = attempts[-1]
        message += (
            " The latest recorded payment attempt is "
            f"{_label(latest_attempt['status']).lower()}."
        )

    return message


def _format_outstanding(
    data: dict[str, Any],
) -> str:
    if not data[
        "reconciliation_consistent"
    ]:
        return (
            "The available billing and payment "
            "records are inconsistent, so I can't "
            "reliably calculate the outstanding "
            "amount."
        )

    if data[
        "is_fully_paid"
    ]:
        return (
            f"Your {data['bill']['period']} bill has "
            "been fully paid. There is no outstanding "
            "amount based on the recorded successful "
            "payments."
        )

    return (
        f"You've successfully paid "
        f"{_money(data['successful_paid_amount'])} "
        f"toward the "
        f"{_money(data['bill']['amount'])} "
        f"{data['bill']['period']} bill, leaving "
        f"{_money(data['outstanding_amount'])} "
        "outstanding."
    )


def _format_payment_aggregate(
    data: dict[str, Any],
) -> str:
    kind = data[
        "aggregation_type"
    ]

    if (
        kind
        == "TOTAL_SUCCESSFUL_AMOUNT"
    ):
        return (
            "Your total successfully paid amount for "
            "the requested period is "
            f"{_money(data['successful_paid_amount'])}."
        )

    if (
        kind
        == "AVERAGE_SUCCESSFUL_AMOUNT"
    ):
        return (
            "Your average successful payment for the "
            "requested period is "
            f"{_money(data['average_successful_amount'])}."
        )

    if kind == "COUNT_SUCCESSFUL":
        return (
            f"You have "
            f"{data['successful_payment_count']} "
            "successful payment records in the "
            "requested period."
        )

    if kind == "COUNT_FAILED":
        return (
            f"You have "
            f"{data['failed_payment_count']} failed "
            "payment attempts in the requested period."
        )

    if kind == "COUNT_PENDING":
        return (
            f"You have "
            f"{data['pending_payment_count']} pending "
            "payment attempts in the requested period."
        )

    return (
        f"You have "
        f"{data['payment_attempt_count']} payment "
        "attempts in the requested period."
    )


# ============================================================
# PHASE 4 — SUPPORT
# ============================================================


def _format_support_latest(
    data: dict[str, Any],
) -> str:
    ticket = data[
        "ticket"
    ]

    return (
        f"Your latest support ticket is "
        f"{ticket['ticket_id']} for "
        f"{_label(ticket['category']).lower()}. "
        f"It is {_label(ticket['status']).lower()} "
        f"with {_label(ticket['priority']).lower()} "
        "priority."
    )


def _format_support_specific(
    data: dict[str, Any],
) -> str:
    ticket = data[
        "ticket"
    ]

    return (
        f"Ticket {ticket['ticket_id']} is a "
        f"{_label(ticket['category']).lower()} issue "
        f"with {_label(ticket['priority']).lower()} "
        f"priority. Its status is "
        f"{_label(ticket['status']).lower()}."
    )


def _format_support_history(
    data: dict[str, Any],
) -> str:
    tickets = data.get(
        "tickets",
        [],
    )

    return (
        f"I found {len(tickets)} support "
        f"{'ticket' if len(tickets) == 1 else 'tickets'} "
        "in the available records."
    )


def _format_support_count(
    data: dict[str, Any],
) -> str:
    count = data[
        "count"
    ]

    return (
        f"You have {count} support "
        f"{'ticket' if count == 1 else 'tickets'} "
        "matching those criteria."
    )


def _format_support_common_category(
    data: dict[str, Any],
) -> str:
    categories = [
        _label(
            category
        )
        for category in data[
            "categories"
        ]
    ]

    if data[
        "is_tie"
    ]:
        return (
            f"{', '.join(categories)} are tied as "
            "your most common support categories."
        )

    return (
        f"Your most common support category is "
        f"{categories[0]}."
    )


def _format_support_summary(
    data: dict[str, Any],
) -> str:
    return (
        f"You have {data['total_tickets']} support "
        f"{'ticket' if data['total_tickets'] == 1 else 'tickets'} "
        f"in the available records. "
        f"{data['unresolved_count']} are currently "
        "unresolved."
    )


def _format_support_last_updated(
    data: dict[str, Any],
) -> str:
    ticket = data[
        "ticket"
    ]

    if data.get("update_content_available"):
        return (
            f"Ticket {ticket['ticket_id']} was last "
            f"updated on {ticket['updated_at']}. "
            "Structured update history is available "
            "for this ticket."
        )

    return (
        f"Ticket {ticket['ticket_id']} was last "
        f"updated on {ticket['updated_at']}. "
        "The available structured data doesn't "
        "contain the content of that update."
    )


def _format_support_ticket_updates(
    data: dict[str, Any],
) -> str:
    ticket = data["ticket"]
    updates = data.get("updates", [])
    count = len(updates)

    if count == 0:
        return (
            f"Ticket {ticket['ticket_id']} has no "
            "recorded updates yet."
        )

    return (
        f"Ticket {ticket['ticket_id']} has {count} "
        f"update{'s' if count != 1 else ''} on file."
    )


# ============================================================
# PHASE 4 — DEVICES
# ============================================================


def _format_device_list(
    data: dict[str, Any],
) -> str:
    devices = data.get(
        "devices",
        [],
    )

    return (
        f"I found {len(devices)} "
        f"{'device' if len(devices) == 1 else 'devices'} "
        "associated with your account."
    )


def _format_device_specific(
    data: dict[str, Any],
) -> str:
    device = data[
        "device"
    ]

    return (
        f"{device['device_name']} is recorded as a "
        f"{_label(device['device_type']).lower()} "
        f"with {_label(device['status']).lower()} "
        "status."
    )


def _format_device_count(
    data: dict[str, Any],
) -> str:
    count = data[
        "count"
    ]

    return (
        f"You have {count} "
        f"{'device' if count == 1 else 'devices'} "
        "matching those criteria."
    )


def _format_device_extreme(
    data: dict[str, Any],
) -> str:
    device = data[
        "device"
    ]

    if (
        data[
            "extreme_type"
        ]
        == "NEWEST"
    ):
        return (
            f"Your newest recorded device is "
            f"{device['device_name']}, purchased on "
            f"{device['purchase_date']}."
        )

    return (
        "Your oldest device in the available "
        f"records is {device['device_name']}, "
        f"with a recorded purchase date of "
        f"{device['purchase_date']}."
    )


def _format_device_summary(
    data: dict[str, Any],
) -> str:
    return (
        f"You have {data['total_devices']} "
        f"{'device' if data['total_devices'] == 1 else 'devices'} "
        f"in the available records, including "
        f"{data['active_count']} active."
    )


def _format_device_diagnostic_limitation(
    data: dict[str, Any],
) -> str:
    return (
        "I can see the devices associated with your "
        "account and their recorded status, but I "
        "don't have device diagnostic information "
        "to determine why a device isn't working."
    )


# ============================================================
# PHASE 5 — CROSS DOMAIN
# ============================================================


def _format_plan_usage_status(
    data: dict[str, Any],
) -> str:
    plan = data[
        "plan"
    ]

    usage = data[
        "usage"
    ]

    if usage[
        "is_unlimited"
    ]:
        return (
            f"You're on the {plan['plan_name']} plan "
            f"at {_money(plan['monthly_price'])} per "
            f"month. You've used "
            f"{_number(usage['used'])} "
            f"{usage['unit']} in {usage['period']}; "
            "your plan has unlimited data."
        )

    return (
        f"You're on the {plan['plan_name']} plan. "
        f"You've used {_number(usage['used'])} "
        f"{usage['unit']} in {usage['period']} and "
        f"have {_number(usage['remaining'])} "
        f"{usage['unit']} remaining."
    )


def _format_bill_payment_status(
    data: dict[str, Any],
) -> str:
    bill = data[
        "bill"
    ]

    payment = data[
        "payment"
    ]

    if payment.get(
        "is_fully_paid"
    ):
        return (
            f"Your {bill['period']} bill is "
            f"{_money(bill['amount'])} and is fully "
            "paid based on the recorded successful "
            "payments."
        )

    return (
        f"Your {bill['period']} bill is "
        f"{_money(bill['amount'])}. "
        f"{_money(payment['successful_paid_amount'])} "
        "has been successfully paid and "
        f"{_money(payment['outstanding_amount'])} "
        "remains outstanding."
    )


def _format_bill_payment_explanation(
    data: dict[str, Any],
) -> str:
    bill = data[
        "bill"
    ]

    payment = data[
        "payment"
    ]

    items = data.get(
        "items",
        [],
    )

    return (
        f"Your {bill['period']} bill totals "
        f"{_money(bill['amount'])} across "
        f"{len(items)} recorded "
        f"{'charge' if len(items) == 1 else 'charges'}. "
        f"Recorded successful payments total "
        f"{_money(payment['successful_paid_amount'])}, "
        f"with {_money(payment['outstanding_amount'])} "
        "currently outstanding."
    )


def _format_billing_support_status(
    data: dict[str, Any],
) -> str:
    tickets = data.get(
        "billing_tickets",
        [],
    )

    if not tickets:
        return (
            "I don't have any billing-category "
            "support tickets in the available records."
        )

    return (
        f"You have {len(tickets)} billing-category "
        f"support "
        f"{'ticket' if len(tickets) == 1 else 'tickets'} "
        "in the available records. The data does not "
        "establish that they are linked to your "
        "current bill."
    )


def _format_payment_support_status(
    data: dict[str, Any],
) -> str:
    tickets = data.get(
        "payment_tickets",
        [],
    )

    if not tickets:
        return (
            "I don't have any payment-category "
            "support tickets in the available records."
        )

    return (
        f"You have {len(tickets)} payment-category "
        f"support "
        f"{'ticket' if len(tickets) == 1 else 'tickets'} "
        "in the available records. The data does not "
        "establish that they are linked to a specific "
        "payment transaction."
    )


def _format_account_plan_status(
    data: dict[str, Any],
) -> str:
    account = data[
        "account"
    ]

    text = (
        "Your account is "
        f"{_label(account['account_status']).lower()}."
    )

    subscription = data.get(
        "subscription"
    )

    if subscription:
        text += (
            " Your subscription is "
            f"{_label(subscription['subscription_status']).lower()}."
        )

    plan = data.get(
        "plan"
    )

    if plan:
        text += (
            f" Your current plan is "
            f"{plan['plan_name']}."
        )

    return text


def _format_attention_summary(
    data: dict[str, Any],
) -> str:
    items = data.get(
        "items",
        [],
    )

    if not items:
        return (
            "Based on the available structured "
            "records, nothing currently matches the "
            "configured account-attention rules."
        )

    return (
        "Here are the items that currently need "
        "attention: "
        + " ".join(
            str(
                item[
                    "message"
                ]
            )
            for item in items
        )
    )


def _format_customer_360(
    data: dict[str, Any],
) -> str:
    account = data.get(
        "account",
        {},
    )
    account_status = _label(
        account.get("account_status"),
    ).lower() or "unavailable"

    plan = data.get("plan")
    plan_name = (
        plan.get("plan_name")
        if plan is not None
        else "your plan"
    )

    attention = data.get(
        "attention",
        {},
    )
    attention_items = attention.get(
        "items",
        [],
    )

    lead = (
        f"Here is your account overview. Your account is "
        f"{account_status} on {plan_name}."
    )

    if attention_items:
        lead += (
            f" {attention_items[0]['message']}"
        )
    else:
        lead += (
            " Open the sections below for usage, billing, "
            "payments, and support."
        )

    return lead




def _format_plan_renewal(
    data: dict[str, Any],
) -> str:
    plan_name = data.get(
        "plan_name",
        "your plan",
    )
    renewal_date = data.get(
        "renewal_date",
        "the recorded date",
    )
    status = _label(
        data.get(
            "subscription_status",
        )
    ).lower()

    return (
        f"Your {plan_name} subscription is {status} "
        f"and renews on {renewal_date}."
    )


def _format_subscription_list(data: dict) -> str:
    lines = [
        f"You have {data['count']} subscription(s) on your account:",
    ]
    for sub in data["subscriptions"]:
        lines.append(
            f"- {sub['plan_name']} ({sub['plan_type']}): "
            f"{sub['status']}, renews {sub['renewal_date']}"
        )
    return " ".join(lines)


def _format_plan_catalog(data: dict) -> str:
    lines = [f"{data['count']} NexaTel plan(s) available:"]
    for plan in data["plans"]:
        data_label = (
            "unlimited data"
            if plan["is_data_unlimited"]
            else f"{plan['data_limit_gb']} GB data"
        )
        lines.append(
            f"- {plan['plan_name']} ({plan['plan_type']}): "
            f"₹{plan['monthly_price']}/month, {data_label}"
        )
    return " ".join(lines)


def _format_plan_comparison(data: dict) -> str:
    left = data["current"]
    right = data["previous"]
    return (
        f"{left['plan_name']} (₹{left['monthly_price']}) vs "
        f"{right['plan_name']} (₹{right['monthly_price']}). "
        f"Data limits: {left['data_limit_gb']} GB vs "
        f"{right['data_limit_gb']} GB."
    )


def _format_plan_details(data: dict) -> str:
    plan = data["plan"]
    data_label = (
        "unlimited data"
        if plan["is_data_unlimited"]
        else f"{plan['data_limit_gb']} GB data"
    )
    return (
        f"{plan['plan_name']} ({plan['plan_id']}): "
        f"₹{plan['monthly_price']}/month, {data_label}, "
        f"{plan['voice_limit_minutes']} voice minutes, "
        f"{plan['sms_limit']} SMS."
    )


def _format_account_status(data: dict) -> str:
    address = data.get("service_address_line", "")
    city = data.get("city", "")
    location = ", ".join(
        part for part in (address, city) if part
    )
    return (
        f"Account {data.get('customer_id')} is "
        f"{_label(data.get('account_status', '')).lower()}. "
        f"Contact: {data.get('email')}, {data.get('phone')}. "
        f"{f'Service address: {location}.' if location else ''} "
        f"Registered {data.get('registration_date', 'on file')}."
    ).strip()


def _format_current_plan(data: dict) -> str:
    if data.get("is_data_unlimited"):
        allowance = "unlimited data"
    else:
        allowance = f"{_number(data.get('data_limit_gb'))} GB of data"
    return (
        f"You're on {data['plan_name']} ({data['plan_type']}) at "
        f"{_money(data['monthly_price'])} per month with {allowance}. "
        f"Subscription {data.get('subscription_status', '').lower()} — "
        f"renews {data.get('renewal_date')}."
    )


def _format_usage_record_list(data: dict) -> str:
    return (
        f"I found {data['count']} daily usage "
        f"{'record' if data['count'] == 1 else 'records'} "
        "in the available data."
    )


def _format_bill_item_list(data: dict) -> str:
    return (
        f"I found {data['count']} bill line "
        f"{'item' if data['count'] == 1 else 'items'}."
    )


def _format_ticket_update_list(data: dict) -> str:
    return (
        f"I found {data['count']} support ticket "
        f"{'update' if data['count'] == 1 else 'updates'}."
    )


def _format_bill_charge_summary(data: dict) -> str:
    scope = (
        f" across your last {data['month_count']} bills"
        if data.get("month_count")
        else ""
    )
    return (
        f"Total {data['item_type'].replace('_', ' ').lower()} "
        f"charges{scope}: ₹{data['total_amount']} "
        f"from {data['bill_count']} bill(s)."
    )


def _format_projected_bill(data: dict) -> str:
    return (
        f"Estimated {data['plan_name']} bill as of "
        f"{data['as_of_date']}: ₹{data['estimated_amount']} "
        f"(plan price ₹{data['base_plan_amount']}). "
        f"{data['note']}"
    )


def _format_payment_profile(data: dict) -> str:
    autopay = (
        "enabled" if data["autopay_enabled"] else "disabled"
    )
    label = data.get("payment_method_label") or "not on file"
    method = data.get("default_payment_method") or "none"
    return (
        f"Autopay is {autopay}. Default payment method: "
        f"{method} ({label})."
    )


def _format_account_credits(data: dict) -> str:
    if data["available_total"] <= 0:
        return "You have no available account credits."
    return (
        f"Available credit balance: ₹{data['available_total']}. "
        f"{len(data['credits'])} credit record(s) on file."
    )


# ============================================================
# RESULT TYPE DISPATCH
# ============================================================


FORMATTERS = {
    # Phase 1
    "USAGE_CURRENT": _format_current_usage,
    "USAGE_REMAINING": _format_usage_remaining,
    "USAGE_PERCENTAGE": _format_usage_percentage,
    "USAGE_SUMMARY": _format_usage_summary,
    "USAGE_HISTORY": _format_usage_history,
    "USAGE_AVERAGE": _format_usage_average,
    "USAGE_EXTREME": _format_usage_extreme,
    "USAGE_COMPARISON": _format_usage_comparison,
    "USAGE_TREND": _format_usage_trend,

    # Phase 2
    "BILL_CURRENT": _format_bill,
    "BILL_SPECIFIC": _format_bill,
    "BILL_HISTORY": _format_bill_history,
    "BILL_BREAKDOWN": _format_bill_breakdown,
    "BILL_COMPARISON": _format_bill_comparison,
    "BILL_CHANGE_EXPLANATION": _format_bill_change,
    "SUBSCRIPTION_LIST": _format_subscription_list,
    "PLAN_RENEWAL": _format_plan_renewal,
    "PLAN_CATALOG": _format_plan_catalog,
    "PLAN_COMPARISON": _format_plan_comparison,
    "PLAN_DETAILS": _format_plan_details,
    "ACCOUNT_STATUS": _format_account_status,
    "CURRENT_PLAN": _format_current_plan,
    "USAGE_RECORD_LIST": _format_usage_record_list,
    "BILL_ITEM_LIST": _format_bill_item_list,
    "TICKET_UPDATE_LIST": _format_ticket_update_list,
    "BILL_CHARGE_SUMMARY": _format_bill_charge_summary,
    "PROJECTED_BILL": _format_projected_bill,
    "PAYMENT_PROFILE": _format_payment_profile,
    "ACCOUNT_CREDITS": _format_account_credits,
    "BILL_CHANGE_INSUFFICIENT_DETAIL": (
        _format_insufficient_bill_change
    ),
    "BILL_TOTAL_SPENDING": _format_total_spending,
    "BILL_AVERAGE": _format_average_bill,
    "BILL_EXTREME": _format_bill_extreme,
    "BILL_TREND": _format_bill_trend,
    "BILL_FILTER": _format_bill_filter,

    # Phase 3
    "PAYMENT_LATEST": _format_latest_payment,
    "PAYMENT_HISTORY": _format_payment_history,
    "PAYMENT_FILTER": _format_payment_history,
    "PAYMENT_LAST_SUCCESSFUL": _format_last_successful,
    "PAYMENT_LAST_FAILED": _format_last_failed,
    "PAYMENT_TRANSACTION": _format_payment_transaction,
    "PAYMENT_RECONCILIATION": _format_reconciliation,
    "PAYMENT_SUMMARY": _format_reconciliation,
    "PAYMENT_RECONCILIATION_INCONSISTENT": (
        _format_reconciliation
    ),
    "PAYMENT_OUTSTANDING": _format_outstanding,
    "PAYMENT_AGGREGATE": _format_payment_aggregate,

    # Phase 4
    "SUPPORT_LATEST": _format_support_latest,
    "SUPPORT_SPECIFIC": _format_support_specific,
    "SUPPORT_HISTORY": _format_support_history,
    "SUPPORT_FILTER": _format_support_history,
    "SUPPORT_COUNT": _format_support_count,
    "SUPPORT_COMMON_CATEGORY": (
        _format_support_common_category
    ),
    "SUPPORT_SUMMARY": _format_support_summary,
    "SUPPORT_LAST_UPDATED": _format_support_last_updated,
    "SUPPORT_TICKET_UPDATES": _format_support_ticket_updates,

    "DEVICE_LIST": _format_device_list,
    "DEVICE_SPECIFIC": _format_device_specific,
    "DEVICE_FILTER": _format_device_list,
    "DEVICE_COUNT": _format_device_count,
    "DEVICE_EXTREME": _format_device_extreme,
    "DEVICE_SUMMARY": _format_device_summary,
    "DEVICE_DIAGNOSTIC_LIMITATION": (
        _format_device_diagnostic_limitation
    ),

    # Phase 5
    "CROSS_PLAN_USAGE_STATUS": (
        _format_plan_usage_status
    ),
    "CROSS_BILL_PAYMENT_STATUS": (
        _format_bill_payment_status
    ),
    "CROSS_BILL_PAYMENT_EXPLANATION": (
        _format_bill_payment_explanation
    ),
    "CROSS_BILLING_SUPPORT_STATUS": (
        _format_billing_support_status
    ),
    "CROSS_PAYMENT_SUPPORT_STATUS": (
        _format_payment_support_status
    ),
    "CROSS_ACCOUNT_PLAN_STATUS": (
        _format_account_plan_status
    ),
    "CROSS_ACCOUNT_ATTENTION_SUMMARY": (
        _format_attention_summary
    ),
    "CUSTOMER_360": _format_customer_360,
}


# ============================================================
# LEGACY RESULT NORMALIZATION
# ============================================================


def _format_legacy_result(
    data: Any,
) -> str | None:
    """
    Protect the UI from raw Python repr output produced by older
    handlers that have not yet adopted result_type envelopes.

    This is deliberately presentation-only compatibility logic.
    It does not calculate business facts.
    """

    if isinstance(
        data,
        list,
    ):
        if not data:
            return (
                "I don't have any matching records "
                "in the available data."
            )

        first = data[0]

        if isinstance(
            first,
            dict,
        ):
            # Legacy payment history.
            if (
                "payment_id" in first
                and "payment_date" in first
                and "status" in first
            ):
                successful = sum(
                    1
                    for item in data
                    if isinstance(
                        item,
                        dict,
                    )
                    and item.get(
                        "status"
                    )
                    == "SUCCESS"
                )

                failed = sum(
                    1
                    for item in data
                    if isinstance(
                        item,
                        dict,
                    )
                    and item.get(
                        "status"
                    )
                    == "FAILED"
                )

                pending = sum(
                    1
                    for item in data
                    if isinstance(
                        item,
                        dict,
                    )
                    and item.get(
                        "status"
                    )
                    == "PENDING"
                )

                parts = [
                    (
                        f"I found {len(data)} payment "
                        f"{'record' if len(data) == 1 else 'records'}."
                    )
                ]

                statuses = []

                if successful:
                    statuses.append(
                        f"{successful} successful"
                    )

                if failed:
                    statuses.append(
                        f"{failed} failed"
                    )

                if pending:
                    statuses.append(
                        f"{pending} pending"
                    )

                if statuses:
                    parts.append(
                        "They include "
                        + ", ".join(
                            statuses
                        )
                        + "."
                    )

                return " ".join(
                    parts
                )

            # Legacy bill history.
            if (
                "bill_id" in first
                and "amount" in first
                and "due_date" in first
            ):
                return (
                    f"I found {len(data)} "
                    f"{'bill' if len(data) == 1 else 'bills'} "
                    "in your billing history."
                )

            # Legacy support history.
            if (
                "ticket_id" in first
                and "category" in first
                and "priority" in first
            ):
                return (
                    f"I found {len(data)} support "
                    f"{'ticket' if len(data) == 1 else 'tickets'} "
                    "in the available records."
                )

            # Legacy device list.
            if (
                "device_id" in first
                and "device_name" in first
                and "device_type" in first
            ):
                return (
                    f"I found {len(data)} "
                    f"{'device' if len(data) == 1 else 'devices'} "
                    "associated with your account."
                )

        return (
            f"I found {len(data)} matching "
            f"{'record' if len(data) == 1 else 'records'}."
        )

    if isinstance(
        data,
        dict,
    ):
        # Legacy current plan.
        if (
            "plan_name" in data
            and "monthly_price" in data
        ):
            if data.get(
                "is_data_unlimited"
            ):
                allowance = (
                    "unlimited data"
                )

            else:
                data_limit = data.get(
                    "data_limit_gb"
                )

                allowance = (
                    f"{_number(data_limit)} GB of data"
                    if data_limit
                    is not None
                    else "the recorded plan allowance"
                )

            return (
                f"You're on the "
                f"{data['plan_name']} plan at "
                f"{_money(data['monthly_price'])} "
                f"per month with {allowance}."
            )

        # Legacy account status.
        if (
            "account_status"
            in data
        ):
            return (
                "Your account status is "
                f"{_label(data['account_status']).lower()}."
            )

        # Legacy payment.
        if (
            "payment_id" in data
            and "amount" in data
            and "status" in data
        ):
            return (
                f"The payment of "
                f"{_money(data['amount'])} is recorded "
                f"as {_label(data['status']).lower()}."
            )

        # Legacy bill.
        if (
            "bill_id" in data
            and "amount" in data
        ):
            return (
                f"Your recorded bill amount is "
                f"{_money(data['amount'])}."
            )

        if (
            "renewal_date" in data
            and "subscription_id" in data
        ):
            plan_name = data.get(
                "plan_name",
                "your plan",
            )
            return (
                f"Your {plan_name} subscription renews on "
                f"{data['renewal_date']}."
            )

    return None


# ============================================================
# PUBLIC SERVICE
# ============================================================


class ResponseService:
    """
    Convert deterministic backend results into readable
    customer-facing text.

    Raw Python list/dict representations must never be returned
    as the user-facing response.
    """

    def build_response(
        self,
        result: TruthResult[Any],
    ) -> str:
        if (
            result.status
            != TruthStatus.VERIFIED
        ):
            return (
                result.message
                or (
                    "I couldn't retrieve "
                    "that information."
                )
            )

        data = result.data

        if isinstance(
            data,
            dict,
        ):
            result_type = (
                _get_result_type(
                    data
                )
            )

            if result_type:
                formatter = (
                    FORMATTERS.get(
                        result_type
                    )
                )

                if formatter is not None:
                    return formatter(
                        data
                    )

        if result.message:
            return result.message

        legacy_response = (
            _format_legacy_result(
                data
            )
        )

        if legacy_response is not None:
            return legacy_response

        return (
            "I found the requested information, "
            "but it isn't available in a supported "
            "display format yet."
        )

    def generate(
        self,
        result: TruthResult[Any],
    ) -> str:
        return self.build_response(
            result
        )