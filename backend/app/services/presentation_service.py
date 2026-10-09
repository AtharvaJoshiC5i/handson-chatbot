"""Build optional structured UI presentations from verified facts."""

from __future__ import annotations

from typing import Any

from app.models.api import (
    ChatPresentation,
    ComparisonColumn,
    ComparisonPresentation,
    ComparisonRow,
    Customer360Presentation,
    Customer360Table,
    KeyValueItem,
    KeyValuePresentation,
    ListItem,
    ListPresentation,
    PlanRecommendationPlan,
    PlanRecommendationPresentation,
    SummaryPresentation,
    SummarySection,
    TableColumn,
    TablePresentation,
    TimeSeriesPoint,
    TimeSeriesPresentation,
)
from app.models.domain import TruthStatus
from app.truth.result import TruthResult


def _number(
    value: Any,
) -> str:
    if value is None:
        return "—"

    if isinstance(
        value,
        bool,
    ):
        return (
            "Yes"
            if value
            else "No"
        )

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
        return "—"

    return (
        str(value)
        .replace("_", " ")
        .title()
    )


def _payment_method_label(
    value: Any,
) -> str:
    if value is None:
        return "—"

    key = str(value).upper()
    labels = {
        "UPI": "UPI",
        "CREDIT_CARD": "Credit card",
        "DEBIT_CARD": "Debit card",
        "NET_BANKING": "Net banking",
    }
    return labels.get(
        key,
        _label(value),
    )


def _bill_payment_paid_secondary(
    payment: dict[str, Any],
) -> str:
    successful_count = int(
        payment.get("successful_attempt_count") or 0
    )
    failed_count = int(
        payment.get("failed_attempt_count") or 0
    )

    if successful_count > 0:
        noun = (
            "attempt"
            if successful_count == 1
            else "attempts"
        )
        return f"{successful_count} successful {noun}"

    if failed_count > 0:
        noun = (
            "attempt"
            if failed_count == 1
            else "attempts"
        )
        return f"{failed_count} failed {noun} (not settled)"

    return "No payment settled yet"


def _bill_payment_outstanding_secondary(
    payment: dict[str, Any],
    bill: dict[str, Any],
) -> str:
    outstanding = float(
        payment.get("outstanding_amount") or 0
    )
    pending = float(
        payment.get("pending_amount") or 0
    )
    failed_count = int(
        payment.get("failed_attempt_count") or 0
    )

    if outstanding <= 0:
        if pending > 0:
            return (
                f"{_money(pending)} awaiting bank clearance"
            )
        return "Nothing due on this bill"

    parts: list[str] = []

    if pending > 0:
        parts.append(
            f"{_money(pending)} awaiting clearance"
        )

    if failed_count > 0:
        noun = (
            "attempt"
            if failed_count == 1
            else "attempts"
        )
        parts.append(f"{failed_count} failed {noun}")

    if parts:
        return " · ".join(parts)

    due_date = bill.get("due_date")
    status = str(bill.get("status", "")).upper()
    if due_date and status in {
        "UNPAID",
        "OVERDUE",
        "PARTIALLY_PAID",
    }:
        return f"Due by {due_date}"

    if status in {"UNPAID", "OVERDUE"}:
        return "Unpaid balance"

    return "Remaining on this bill"


def _split_datetime_to_date_time(
    value: Any,
) -> tuple[str, str]:
    if value is None or value == "":
        return "—", "—"

    raw = str(value).strip()
    if "T" not in raw:
        return raw, "—"

    date_part, time_part = raw.split(
        "T",
        1,
    )
    time_part = (
        time_part.split(".")[0]
        .split("+")[0]
        .split("Z")[0]
        .strip()
    )
    return date_part, time_part or "—"


def _usage_value(
    value: Any,
    unit: Any,
) -> str:
    return (
        f"{_number(value)} "
        f"{unit}"
    ).strip()


class PresentationService:
    """
    Convert verified structured results into optional UI payloads.

    Returning None intentionally falls back to ordinary chat text.
    """

    def build(
        self,
        result: TruthResult[Any],
    ) -> ChatPresentation | None:
        if (
            result.status
            != TruthStatus.VERIFIED
        ):
            return None

        if not isinstance(
            result.data,
            dict,
        ):
            return None

        data = result.data

        result_type = data.get(
            "result_type"
        )

        builders = {
            # Phase 1
            "USAGE_SUMMARY": (
                self._usage_summary
            ),
            "USAGE_HISTORY": (
                self._usage_history
            ),
            "USAGE_TREND": (
                self._usage_trend
            ),
            "USAGE_COMPARISON": (
                self._usage_comparison
            ),

            # Phase 2
            "BILL_HISTORY": (
                self._bill_history
            ),
            "BILL_TREND": (
                self._bill_trend
            ),
            "BILL_BREAKDOWN": (
                self._bill_breakdown
            ),
            "BILL_COMPARISON": (
                self._bill_comparison
            ),
            "BILL_FILTER": (
                self._bill_filter
            ),
            "PLAN_RENEWAL": (
                self._plan_renewal
            ),

            # Phase 3
            "PAYMENT_HISTORY": (
                self._payment_history
            ),
            "PAYMENT_FILTER": (
                self._payment_history
            ),

            # Phase 4
            "SUPPORT_HISTORY": (
                self._support_history
            ),
            "SUPPORT_FILTER": (
                self._support_history
            ),
            "SUPPORT_SUMMARY": (
                self._support_summary
            ),
            "DEVICE_LIST": (
                self._device_list
            ),
            "DEVICE_FILTER": (
                self._device_list
            ),
            "DEVICE_SUMMARY": (
                self._device_summary
            ),

            # Phase 5
            "CROSS_PLAN_USAGE_STATUS": (
                self._plan_usage
            ),
            "CROSS_BILL_PAYMENT_STATUS": (
                self._bill_payment
            ),
            "CROSS_BILL_PAYMENT_EXPLANATION": (
                self._bill_payment_explanation
            ),
            "CROSS_BILLING_SUPPORT_STATUS": (
                self._billing_support
            ),
            "CROSS_PAYMENT_SUPPORT_STATUS": (
                self._payment_support
            ),
            "CROSS_ACCOUNT_PLAN_STATUS": (
                self._account_plan
            ),
            "CROSS_ACCOUNT_ATTENTION_SUMMARY": (
                self._attention_summary
            ),
            "CUSTOMER_360": (
                self._customer_360
            ),
            "ACCOUNT_STATUS": (
                self._account_status
            ),
            "CURRENT_PLAN": (
                self._current_plan
            ),
            "PLAN_DETAILS": (
                self._plan_details
            ),
            "PLAN_COMPARISON": (
                self._plan_comparison
            ),
            "USAGE_RECORD_LIST": (
                self._usage_record_list
            ),
            "BILL_ITEM_LIST": (
                self._bill_item_list
            ),
            "TICKET_UPDATE_LIST": (
                self._ticket_update_list
            ),
            "BILL_ANOMALY_DETECTION": (
                self._bill_anomaly
            ),
            "PLAN_RECOMMENDATION": (
                self._plan_recommendation
            ),
        }

        builder = builders.get(
            result_type
        )

        if builder is None:
            return None

        return builder(
            data
        )

    # ========================================================
    # PHASE 1
    # ========================================================

    @staticmethod
    def _usage_summary(
        data: dict[str, Any],
    ) -> ChatPresentation:
        items: list[
            KeyValueItem
        ] = []

        for metric in data.get(
            "metrics",
            [],
        ):
            usage_type = _label(
                metric.get(
                    "usage_type"
                )
            )

            unit = metric.get(
                "unit",
                "",
            )

            used = _usage_value(
                metric.get(
                    "used"
                ),
                unit,
            )

            if metric.get(
                "is_unlimited"
            ):
                value = (
                    f"{used} used · Unlimited"
                )

            else:
                remaining = _usage_value(
                    metric.get(
                        "remaining"
                    ),
                    unit,
                )

                value = (
                    f"{used} used · "
                    f"{remaining} remaining"
                )

            items.append(
                KeyValueItem(
                    label=usage_type,
                    value=value,
                )
            )

        return KeyValuePresentation(
            title=(
                f"Usage · "
                f"{data.get('period', '')}"
            ),
            items=items,
        )

    @staticmethod
    def _usage_history(
        data: dict[str, Any],
    ) -> ChatPresentation:
        history = data.get("history", [])
        chart = PresentationService._usage_chart(
            data,
            title=(
                f"{_label(data.get('usage_type'))} usage history"
            ),
            chart_type="line",
            minimum_points=3,
        )
        if chart is not None:
            return chart

        rows = []
        for item in history:
            rows.append(
                {
                    "period": str(
                        item.get(
                            "period",
                            "",
                        )
                    ),
                    "usage": (
                        _usage_value(
                            item.get(
                                "value"
                            ),
                            item.get(
                                "unit",
                                "",
                            ),
                        )
                    ),
                }
            )

        return TablePresentation(
            title=(
                f"{_label(data.get('usage_type'))} "
                "usage history"
            ),
            columns=[
                TableColumn(
                    key="period",
                    label="Period",
                ),
                TableColumn(
                    key="usage",
                    label="Usage",
                    align="right",
                ),
            ],
            rows=rows,
        )

    @staticmethod
    def _usage_trend(
        data: dict[str, Any],
    ) -> ChatPresentation:
        chart = PresentationService._usage_chart(
            data,
            title=(
                f"{_label(data.get('usage_type'))} usage trend"
            ),
            chart_type="line",
            minimum_points=2,
        )
        return chart or PresentationService._usage_history(data)

    @staticmethod
    def _usage_chart(
        data: dict[str, Any],
        *,
        title: str,
        chart_type: str,
        minimum_points: int,
    ) -> TimeSeriesPresentation | None:
        history = data.get("history", [])
        if len(history) < minimum_points:
            return None

        points = []
        for item in history:
            value = item.get("value")
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return None

            points.append(
                TimeSeriesPoint(
                    period=str(item.get("period", "")),
                    value=float(value),
                )
            )

        unit = str(
            history[0].get("unit")
            or data.get("unit")
            or ""
        )
        return TimeSeriesPresentation(
            title=title,
            chart_type=chart_type,
            unit=unit,
            value_format="number",
            points=points,
        )

    @staticmethod
    def _usage_comparison(
        data: dict[str, Any],
    ) -> ChatPresentation:
        unit = data.get(
            "unit",
            "",
        )

        usage_label = _label(data.get("usage_type"))
        return ComparisonPresentation(
            title=f"{usage_label} usage comparison",
            columns=[
                ComparisonColumn(
                    key="previous",
                    label=str(
                        data.get(
                            "period_2",
                            "Previous",
                        )
                    ),
                ),
                ComparisonColumn(
                    key="current",
                    label=str(
                        data.get(
                            "period_1",
                            "Current",
                        )
                    ),
                ),
            ],
            rows=[
                ComparisonRow(
                    label="Usage",
                    values={
                        "current": (
                            _usage_value(
                                data.get(
                                    "period_1_usage"
                                ),
                                unit,
                            )
                        ),
                        "previous": (
                            _usage_value(
                                data.get(
                                    "period_2_usage"
                                ),
                                unit,
                            )
                        ),
                    },
                ),
            ],
        )

    # ========================================================
    # PHASE 2
    # ========================================================

    @staticmethod
    def _bill_history(
        data: dict[str, Any],
    ) -> ChatPresentation:
        bills = data.get("bills", [])
        chart = PresentationService._bill_chart(
            bills,
            title="Billing history",
            chart_type="bar",
            minimum_points=3,
        )
        if chart is not None:
            return chart

        plan_types = {
            str(bill.get("plan_type", ""))
            for bill in bills
            if bill.get("plan_type")
        }
        show_line = len(plan_types) > 1

        rows = []

        for bill in bills:
            row = {
                "period": str(
                    bill.get(
                        "period",
                        "",
                    )
                ),
                "amount": _money(
                    bill.get(
                        "amount"
                    )
                ),
                "status": _label(
                    bill.get(
                        "status"
                    )
                ),
                "due": str(
                    bill.get(
                        "due_date",
                        "",
                    )
                ),
            }
            if show_line:
                row["line"] = _label(
                    bill.get("plan_type")
                )
            rows.append(row)

        columns = [
            TableColumn(
                key="period",
                label="Period",
            ),
        ]
        if show_line:
            columns.append(
                TableColumn(
                    key="line",
                    label="Line",
                )
            )
        columns.extend(
            [
                TableColumn(
                    key="amount",
                    label="Amount",
                    align="right",
                ),
                TableColumn(
                    key="status",
                    label="Status",
                ),
                TableColumn(
                    key="due",
                    label="Due",
                ),
            ]
        )

        return TablePresentation(
            title="Billing history",
            columns=columns,
            rows=rows,
        )

    @staticmethod
    def _bill_trend(
        data: dict[str, Any],
    ) -> ChatPresentation:
        bills = data.get("bills", [])
        chart = PresentationService._bill_chart(
            bills,
            title="Billing trend",
            chart_type="line",
            minimum_points=2,
        )
        return chart or PresentationService._bill_history(data)

    @staticmethod
    def _bill_chart(
        bills: list[dict[str, Any]],
        *,
        title: str,
        chart_type: str,
        minimum_points: int,
    ) -> TimeSeriesPresentation | None:
        if len(bills) < minimum_points:
            return None

        plan_types = {
            str(bill.get("plan_type", ""))
            for bill in bills
            if bill.get("plan_type")
        }
        show_line = len(plan_types) > 1

        points = []
        for bill in bills:
            amount = bill.get("amount_value")
            if not isinstance(amount, (int, float)) or isinstance(amount, bool):
                return None

            detail = _label(bill.get("status"))
            plan_type = bill.get("plan_type")
            if show_line and plan_type:
                detail = (
                    f"{detail} · {_label(plan_type)}"
                )

            points.append(
                TimeSeriesPoint(
                    period=str(bill.get("period", "")),
                    value=float(amount),
                    detail=detail,
                )
            )

        return TimeSeriesPresentation(
            title=title,
            chart_type=chart_type,
            unit="₹",
            value_format="inr",
            points=points,
        )

    @staticmethod
    def _bill_breakdown(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []

        for item in data.get(
            "items",
            [],
        ):
            rows.append(
                {
                    "charge": str(
                        item.get(
                            "description",
                            "",
                        )
                    ),
                    "amount": _money(
                        item.get(
                            "amount"
                        )
                    ),
                }
            )

        bill = data.get(
            "bill",
            {},
        )

        rows.append(
            {
                "charge": "Total",
                "amount": _money(
                    bill.get(
                        "amount"
                    )
                ),
            }
        )

        return TablePresentation(
            title=(
                f"{bill.get('period', 'Bill')} "
                "breakdown"
            ),
            columns=[
                TableColumn(
                    key="charge",
                    label="Charge",
                ),
                TableColumn(
                    key="amount",
                    label="Amount",
                    align="right",
                ),
            ],
            rows=rows,
        )

    @staticmethod
    def _bill_comparison(
        data: dict[str, Any],
    ) -> ChatPresentation:
        current = data.get(
            "current_bill",
            {},
        )

        previous = data.get(
            "comparison_bill",
            {},
        )

        previous_period = str(
            previous.get("period") or "",
        ).strip()
        current_period = str(
            current.get("period") or "",
        ).strip()
        previous_label = (
            f"Previous bill ({previous_period})"
            if previous_period
            else "Previous bill"
        )
        current_label = (
            f"Current bill ({current_period})"
            if current_period
            else "Current bill"
        )

        return ComparisonPresentation(
            title="Bill comparison",
            columns=[
                ComparisonColumn(
                    key="previous",
                    label=previous_label,
                ),
                ComparisonColumn(
                    key="current",
                    label=current_label,
                ),
            ],
            rows=[
                ComparisonRow(
                    label="Amount",
                    values={
                        "current": _money(
                            current.get(
                                "amount"
                            )
                        ),
                        "previous": _money(
                            previous.get(
                                "amount"
                            )
                        ),
                    },
                ),
                ComparisonRow(
                    label="Status",
                    values={
                        "current": _label(
                            current.get(
                                "status"
                            )
                        ),
                        "previous": _label(
                            previous.get(
                                "status"
                            )
                        ),
                    },
                ),
            ],
        )

    @staticmethod
    def _bill_filter(
        data: dict[str, Any],
    ) -> ChatPresentation:
        return PresentationService._bill_history(
            {
                "bills": data.get(
                    "bills",
                    [],
                )
            }
        )

    # ========================================================
    # PLAN RENEWAL
    # ========================================================

    @staticmethod
    def _plan_renewal(
        data: dict[str, Any],
    ) -> ChatPresentation:
        renewal_raw = str(
            data.get(
                "renewal_date",
                "",
            )
        )
        renewal_display = renewal_raw.split(
            "T",
            1,
        )[0] or renewal_raw

        return KeyValuePresentation(
            title="Plan renewal",
            items=[
                KeyValueItem(
                    label="Plan",
                    value=str(
                        data.get(
                            "plan_name",
                            "—",
                        )
                    ),
                ),
                KeyValueItem(
                    label="Type",
                    value=_label(
                        data.get(
                            "plan_type",
                        )
                    ),
                ),
                KeyValueItem(
                    label="Renewal date",
                    value=renewal_display
                    or "—",
                ),
                KeyValueItem(
                    label="Subscription status",
                    value=_label(
                        data.get(
                            "subscription_status",
                        )
                    ),
                ),
            ],
        )

    # ========================================================
    # PHASE 3
    # ========================================================

    @staticmethod
    def _payment_history(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []

        for payment in data.get(
            "payments",
            [],
        ):
            date_display, time_display = _split_datetime_to_date_time(
                payment.get(
                    "payment_date",
                )
            )
            bill_period = payment.get("bill_period")
            rows.append(
                {
                    "bill_period": str(
                        bill_period or "—",
                    ),
                    "date": date_display,
                    "time": time_display,
                    "amount": _money(
                        payment.get(
                            "amount"
                        )
                    ),
                    "method": _payment_method_label(
                        payment.get(
                            "payment_method"
                        )
                    ),
                    "status": _label(
                        payment.get(
                            "status"
                        )
                    ),
                }
            )

        return TablePresentation(
            title="Payment history",
            columns=[
                TableColumn(
                    key="bill_period",
                    label="Bill period",
                ),
                TableColumn(
                    key="date",
                    label="Paid on",
                ),
                TableColumn(
                    key="time",
                    label="Time",
                ),
                TableColumn(
                    key="amount",
                    label="Amount",
                    align="right",
                ),
                TableColumn(
                    key="method",
                    label="Method",
                ),
                TableColumn(
                    key="status",
                    label="Status",
                ),
            ],
            rows=rows,
        )

    # ========================================================
    # PHASE 4
    # ========================================================

    @staticmethod
    def _support_history(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []

        for ticket in data.get(
            "tickets",
            [],
        ):
            rows.append(
                {
                    "ticket": str(
                        ticket.get(
                            "ticket_id",
                            "",
                        )
                    ),
                    "category": _label(
                        ticket.get(
                            "category"
                        )
                    ),
                    "status": _label(
                        ticket.get(
                            "status"
                        )
                    ),
                    "priority": _label(
                        ticket.get(
                            "priority"
                        )
                    ),
                }
            )

        return TablePresentation(
            title="Support tickets",
            columns=[
                TableColumn(
                    key="ticket",
                    label="Ticket",
                ),
                TableColumn(
                    key="category",
                    label="Category",
                ),
                TableColumn(
                    key="status",
                    label="Status",
                ),
                TableColumn(
                    key="priority",
                    label="Priority",
                ),
            ],
            rows=rows,
        )

    @staticmethod
    def _support_summary(
        data: dict[str, Any],
    ) -> ChatPresentation:
        return KeyValuePresentation(
            title="Support summary",
            items=[
                KeyValueItem(
                    label="Total",
                    value=_number(
                        data.get(
                            "total_tickets"
                        )
                    ),
                ),
                KeyValueItem(
                    label="Unresolved",
                    value=_number(
                        data.get(
                            "unresolved_count"
                        )
                    ),
                ),
                KeyValueItem(
                    label="Resolved / closed",
                    value=_number(
                        data.get(
                            "resolved_count"
                        )
                    ),
                ),
                KeyValueItem(
                    label="High / critical",
                    value=_number(
                        (
                            data.get(
                                "high_count",
                                0,
                            )
                            + data.get(
                                "critical_count",
                                0,
                            )
                        )
                    ),
                ),
            ],
        )

    @staticmethod
    def _device_list(
        data: dict[str, Any],
    ) -> ChatPresentation:
        items = []

        for device in data.get(
            "devices",
            [],
        ):
            items.append(
                ListItem(
                    label=str(
                        device.get(
                            "device_name",
                            "Device",
                        )
                    ),
                    value=_label(
                        device.get(
                            "status"
                        )
                    ),
                    detail=(
                        f"{_label(device.get('device_type'))}"
                        f" · {device.get('purchase_date', '')}"
                    ),
                )
            )

        return ListPresentation(
            title="Devices",
            items=items,
        )

    @staticmethod
    def _device_summary(
        data: dict[str, Any],
    ) -> ChatPresentation:
        return KeyValuePresentation(
            title="Device summary",
            items=[
                KeyValueItem(
                    label="Total",
                    value=_number(
                        data.get(
                            "total_devices"
                        )
                    ),
                ),
                KeyValueItem(
                    label="Active",
                    value=_number(
                        data.get(
                            "active_count"
                        )
                    ),
                ),
                KeyValueItem(
                    label="Inactive",
                    value=_number(
                        data.get(
                            "inactive_count"
                        )
                    ),
                ),
                KeyValueItem(
                    label="Replaced",
                    value=_number(
                        data.get(
                            "replaced_count"
                        )
                    ),
                ),
            ],
        )

    # ========================================================
    # PHASE 5
    # ========================================================

    @staticmethod
    def _plan_usage(
        data: dict[str, Any],
    ) -> ChatPresentation:
        plan = data.get(
            "plan",
            {},
        )

        usage = data.get(
            "usage",
            {},
        )

        usage_items = [
            KeyValueItem(
                label="Used",
                value=_usage_value(
                    usage.get(
                        "used"
                    ),
                    usage.get(
                        "unit",
                        "",
                    ),
                ),
            )
        ]

        if usage.get(
            "is_unlimited"
        ):
            usage_items.append(
                KeyValueItem(
                    label="Allowance",
                    value="Unlimited",
                )
            )

        else:
            usage_items.extend(
                [
                    KeyValueItem(
                        label="Allowance",
                        value=_usage_value(
                            usage.get(
                                "allowance"
                            ),
                            usage.get(
                                "unit",
                                "",
                            ),
                        ),
                    ),
                    KeyValueItem(
                        label="Remaining",
                        value=_usage_value(
                            usage.get(
                                "remaining"
                            ),
                            usage.get(
                                "unit",
                                "",
                            ),
                        ),
                    ),
                ]
            )

            if (
                usage.get(
                    "consumed_percentage"
                )
                is not None
            ):
                usage_items.append(
                    KeyValueItem(
                        label="Used %",
                        value=(
                            f"{_number(usage.get('consumed_percentage'))}%"
                        ),
                    )
                )

        return SummaryPresentation(
            title="Plan & usage",
            sections=[
                SummarySection(
                    label="Plan",
                    primary=str(
                        plan.get(
                            "plan_name",
                            "Current plan",
                        )
                    ),
                    secondary=(
                        f"{_money(plan.get('monthly_price'))}"
                        f" · {_label(plan.get('subscription_status'))}"
                    ),
                ),
                SummarySection(
                    label="Usage",
                    primary=(
                        f"{_usage_value(usage.get('used'), usage.get('unit', ''))} used"
                    ),
                    secondary=(
                        "Unlimited allowance"
                        if usage.get(
                            "is_unlimited"
                        )
                        else (
                            f"{_usage_value(usage.get('remaining'), usage.get('unit', ''))} remaining"
                        )
                    ),
                ),
            ],
        )

    @staticmethod
    def _bill_payment(
        data: dict[str, Any],
    ) -> ChatPresentation:
        bill = data.get(
            "bill",
            {},
        )

        payment = data.get(
            "payment",
            {},
        )

        return SummaryPresentation(
            title="Bill & payment",
            sections=[
                SummarySection(
                    label="Bill",
                    primary=_money(
                        bill.get(
                            "amount"
                        )
                    ),
                    secondary=(
                        f"{bill.get('period', '')}"
                        f" · {_label(bill.get('status'))}"
                    ),
                ),
                SummarySection(
                    label="Paid",
                    primary=_money(
                        payment.get(
                            "successful_paid_amount",
                            0,
                        )
                    ),
                    secondary=_bill_payment_paid_secondary(
                        payment,
                    ),
                ),
                SummarySection(
                    label="Outstanding",
                    primary=_money(
                        payment.get(
                            "outstanding_amount",
                            0,
                        )
                    ),
                    secondary=_bill_payment_outstanding_secondary(
                        payment,
                        bill,
                    ),
                ),
            ],
        )

    @staticmethod
    def _bill_payment_explanation(
        data: dict[str, Any],
    ) -> ChatPresentation:
        bill = data.get(
            "bill",
            {},
        )

        payment = data.get(
            "payment",
            {},
        )

        items = data.get(
            "items",
            [],
        )

        rows = [
            {
                "item": str(
                    item.get(
                        "description",
                        "",
                    )
                ),
                "amount": _money(
                    item.get(
                        "amount"
                    )
                ),
            }
            for item in items
        ]

        rows.append(
            {
                "item": "Bill total",
                "amount": _money(
                    bill.get(
                        "amount"
                    )
                ),
            }
        )

        rows.append(
            {
                "item": "Successfully paid",
                "amount": _money(
                    payment.get(
                        "successful_paid_amount",
                        0,
                    )
                ),
            }
        )

        rows.append(
            {
                "item": "Outstanding",
                "amount": _money(
                    payment.get(
                        "outstanding_amount",
                        0,
                    )
                ),
            }
        )

        return TablePresentation(
            title="Bill & payment details",
            columns=[
                TableColumn(
                    key="item",
                    label="Item",
                ),
                TableColumn(
                    key="amount",
                    label="Amount",
                    align="right",
                ),
            ],
            rows=rows,
        )

    @staticmethod
    def _billing_support(
        data: dict[str, Any],
    ) -> ChatPresentation:
        tickets = data.get(
            "billing_tickets",
            [],
        )

        items = [
            ListItem(
                label=str(
                    ticket.get(
                        "ticket_id",
                        "Ticket",
                    )
                ),
                value=_label(
                    ticket.get(
                        "status"
                    )
                ),
                detail=str(
                    ticket.get(
                        "description",
                        "",
                    )
                ),
            )
            for ticket in tickets
        ]

        return ListPresentation(
            title="Billing support",
            items=items,
        )

    @staticmethod
    def _payment_support(
        data: dict[str, Any],
    ) -> ChatPresentation:
        tickets = data.get(
            "payment_tickets",
            [],
        )

        items = [
            ListItem(
                label=str(
                    ticket.get(
                        "ticket_id",
                        "Ticket",
                    )
                ),
                value=_label(
                    ticket.get(
                        "status"
                    )
                ),
                detail=str(
                    ticket.get(
                        "description",
                        "",
                    )
                ),
            )
            for ticket in tickets
        ]

        return ListPresentation(
            title="Payment support",
            items=items,
        )

    @staticmethod
    def _account_plan(
        data: dict[str, Any],
    ) -> ChatPresentation:
        account = data.get(
            "account",
            {},
        )

        subscription = data.get(
            "subscription"
        )

        plan = data.get(
            "plan"
        )

        sections = [
            SummarySection(
                label="Account",
                primary=_label(
                    account.get(
                        "account_status"
                    )
                ),
            )
        ]

        if subscription is not None:
            sections.append(
                SummarySection(
                    label="Subscription",
                    primary=_label(
                        subscription.get(
                            "subscription_status"
                        )
                    ),
                    secondary=(
                        f"Renews {subscription.get('renewal_date', '')}"
                    ),
                )
            )

        if plan is not None:
            sections.append(
                SummarySection(
                    label="Plan",
                    primary=str(
                        plan.get(
                            "plan_name",
                            "",
                        )
                    ),
                    secondary=(
                        f"{_money(plan.get('monthly_price'))}"
                        f" · {_label(plan.get('plan_type'))}"
                    ),
                )
            )

        return SummaryPresentation(
            title="Account & plan",
            sections=sections,
        )

    @staticmethod
    def _attention_summary(
        data: dict[str, Any],
    ) -> ChatPresentation:
        items = data.get(
            "items",
            [],
        )

        if not items:
            return SummaryPresentation(
                title="Account attention",
                sections=[
                    SummarySection(
                        label="Status",
                        primary=(
                            "Nothing currently requires attention"
                        ),
                        secondary=(
                            "Based on the available structured records."
                        ),
                    )
                ],
            )

        return SummaryPresentation(
            title="Account attention",
            sections=[
                SummarySection(
                    label=str(
                        item.get(
                            "domain",
                            "Account",
                        )
                    ),
                    primary=str(
                        item.get(
                            "message",
                            "",
                        )
                    ),
                    secondary=(
                        f"{_label(item.get('severity'))} priority"
                    ),
                )
                for item in items
            ],
        )

    @staticmethod
    def _bill_anomaly(
        data: dict[str, Any],
    ) -> ChatPresentation:
        current = data.get("current_bill") or {}
        previous = data.get("comparison_bill") or {}
        scope = data.get("comparison_scope") or ""
        previous_period = str(previous.get("period") or "").strip()
        current_period = str(current.get("period") or "").strip()
        previous_label = (
            f"Previous bill ({previous_period})"
            if previous_period
            else "Previous bill"
        )
        current_label = (
            f"Current bill ({current_period})"
            if current_period
            else "Current bill"
        )

        items = [
            KeyValueItem(
                label="Compared",
                value=scope
                or (
                    f"{current.get('period', '')} vs "
                    f"{previous.get('period', '')}"
                ),
            ),
            KeyValueItem(
                label=previous_label,
                value=_money(previous.get("amount")),
            ),
            KeyValueItem(
                label=current_label,
                value=_money(current.get("amount")),
            ),
            KeyValueItem(
                label="Net increase",
                value=_money(data.get("total_difference")),
            ),
        ]
        pct = data.get("percent_increase")
        if pct is not None:
            items.append(
                KeyValueItem(
                    label="Percent increase",
                    value=f"{pct:g}%",
                )
            )
        return KeyValuePresentation(
            title="Bill anomaly check",
            items=items,
        )

    @staticmethod
    def _plan_recommendation(
        data: dict[str, Any],
    ) -> ChatPresentation:
        current = data.get("current_plan") or {}
        recommended = data.get("recommended_plan") or {}
        status = str(
            data.get("recommendation_status", "")
        )
        usage_fit = data.get("usage_fit") or {}
        reasons = list(
            data.get("recommendation_reasons") or []
        )

        title = "Plan recommendation"
        if status == "KEEP_CURRENT":
            title = "Your plan looks like a good fit"

        current_limit = (
            usage_fit.get("current_data_allowance_gb")
            or current.get("data_limit_gb")
        )
        avg = (
            usage_fit.get("average_monthly_data_gb")
            or data.get("average_monthly_data_gb")
        )
        utilization = usage_fit.get("utilization_percent")

        current_price = current.get("monthly_price")
        recommended_plan = None
        if recommended.get("plan_name") and status != "KEEP_CURRENT":
            recommended_plan = PlanRecommendationPlan(
                plan_name=str(recommended["plan_name"]),
                monthly_price=(
                    float(recommended["monthly_price"])
                    if recommended.get("monthly_price")
                    is not None
                    else None
                ),
                data_limit_gb=(
                    float(recommended["data_limit_gb"])
                    if recommended.get("data_limit_gb")
                    is not None
                    else None
                ),
            )

        savings = data.get("estimated_monthly_savings")
        savings_value = None
        if (
            status != "KEEP_CURRENT"
            and savings is not None
            and float(savings) > 0
        ):
            savings_value = float(savings)

        return PlanRecommendationPresentation(
            title=title,
            recommendation_status=status,
            current=PlanRecommendationPlan(
                plan_name=str(
                    current.get("plan_name", "Current plan")
                ),
                monthly_price=(
                    float(current_price)
                    if current_price is not None
                    else None
                ),
                data_limit_gb=(
                    float(current_limit)
                    if current_limit is not None
                    else None
                ),
            ),
            recommended=recommended_plan,
            average_monthly_data_gb=(
                float(avg) if avg is not None else None
            ),
            months_sampled=data.get("months_sampled"),
            utilization_percent=(
                float(utilization)
                if utilization is not None
                else None
            ),
            estimated_monthly_savings=savings_value,
            reasons=reasons,
        )

    @staticmethod
    def _account_status(
        data: dict[str, Any],
    ) -> ChatPresentation:
        return KeyValuePresentation(
            title="Account",
            items=[
                KeyValueItem(
                    label="Status",
                    value=_label(data.get("account_status")),
                ),
                KeyValueItem(
                    label="Email",
                    value=str(data.get("email", "")),
                ),
                KeyValueItem(
                    label="Phone",
                    value=str(data.get("phone", "")),
                ),
                KeyValueItem(
                    label="City",
                    value=str(data.get("city", "")),
                ),
                KeyValueItem(
                    label="Address",
                    value=str(
                        data.get("service_address_line", "")
                    ),
                ),
                KeyValueItem(
                    label="Registered",
                    value=str(
                        data.get("registration_date", "")
                    ),
                ),
            ],
        )

    @staticmethod
    def _current_plan(
        data: dict[str, Any],
    ) -> ChatPresentation:
        allowance = (
            "Unlimited data"
            if data.get("is_data_unlimited")
            else (
                f"{_number(data.get('data_limit_gb'))} GB"
            )
        )
        return KeyValuePresentation(
            title="Current plan",
            items=[
                KeyValueItem(
                    label="Plan",
                    value=str(data.get("plan_name", "")),
                ),
                KeyValueItem(
                    label="Type",
                    value=_label(data.get("plan_type")),
                ),
                KeyValueItem(
                    label="Price",
                    value=_money(data.get("monthly_price")),
                ),
                KeyValueItem(
                    label="Data",
                    value=allowance,
                ),
                KeyValueItem(
                    label="Renews",
                    value=str(data.get("renewal_date", "")),
                ),
            ],
        )

    @staticmethod
    def _plan_data_allowance(plan: dict[str, Any]) -> str:
        if plan.get("is_data_unlimited"):
            return "Unlimited"
        limit = plan.get("data_limit_gb")
        if limit is None:
            return "—"
        return f"{_number(limit)} GB"

    @staticmethod
    def _plan_comparison(
        data: dict[str, Any],
    ) -> ChatPresentation:
        left = data.get("current") or {}
        right = data.get("previous") or {}

        def column_label(plan: dict[str, Any]) -> str:
            name = str(plan.get("plan_name") or "Plan")
            plan_id = str(plan.get("plan_id") or "")
            if plan_id:
                return f"{name} ({plan_id})"
            return name

        return ComparisonPresentation(
            title="Plan comparison",
            columns=[
                ComparisonColumn(
                    key="left",
                    label=column_label(left),
                ),
                ComparisonColumn(
                    key="right",
                    label=column_label(right),
                ),
            ],
            rows=[
                ComparisonRow(
                    label="Monthly price",
                    values={
                        "left": _money(
                            left.get("monthly_price"),
                        ),
                        "right": _money(
                            right.get("monthly_price"),
                        ),
                    },
                ),
                ComparisonRow(
                    label="Data",
                    values={
                        "left": (
                            PresentationService._plan_data_allowance(
                                left,
                            )
                        ),
                        "right": (
                            PresentationService._plan_data_allowance(
                                right,
                            )
                        ),
                    },
                ),
                ComparisonRow(
                    label="Voice minutes",
                    values={
                        "left": _number(
                            left.get("voice_limit_minutes"),
                        ),
                        "right": _number(
                            right.get("voice_limit_minutes"),
                        ),
                    },
                ),
                ComparisonRow(
                    label="SMS",
                    values={
                        "left": _number(
                            left.get("sms_limit"),
                        ),
                        "right": _number(
                            right.get("sms_limit"),
                        ),
                    },
                ),
                ComparisonRow(
                    label="Line type",
                    values={
                        "left": _label(left.get("plan_type")),
                        "right": _label(right.get("plan_type")),
                    },
                ),
            ],
        )

    @staticmethod
    def _plan_details(
        data: dict[str, Any],
    ) -> ChatPresentation:
        plan = data.get("plan", {})
        return KeyValuePresentation(
            title="Plan details",
            items=[
                KeyValueItem(
                    label="ID",
                    value=str(plan.get("plan_id", "")),
                ),
                KeyValueItem(
                    label="Name",
                    value=str(plan.get("plan_name", "")),
                ),
                KeyValueItem(
                    label="Monthly price",
                    value=_money(plan.get("monthly_price")),
                ),
                KeyValueItem(
                    label="Type",
                    value=_label(plan.get("plan_type")),
                ),
            ],
        )

    @staticmethod
    def _usage_record_list(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []
        for record in data.get("records", []):
            rows.append(
                {
                    "date": str(record.get("usage_date", "")),
                    "data": _number(record.get("data_used_gb")),
                    "voice": _number(
                        record.get("voice_minutes")
                    ),
                    "sms": _number(record.get("sms_count")),
                }
            )
        return TablePresentation(
            title="Usage records",
            columns=[
                TableColumn(key="date", label="Date"),
                TableColumn(key="data", label="Data (GB)"),
                TableColumn(
                    key="voice",
                    label="Voice (min)",
                ),
                TableColumn(key="sms", label="SMS"),
            ],
            rows=rows,
        )

    @staticmethod
    def _bill_item_list(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []
        for item in data.get("items", []):
            rows.append(
                {
                    "bill_id": str(item.get("bill_id", "")),
                    "description": str(
                        item.get("description", "")
                    ),
                    "type": _label(item.get("item_type")),
                    "amount": _money(item.get("amount")),
                }
            )
        return TablePresentation(
            title="Bill line items",
            columns=[
                TableColumn(key="bill_id", label="Bill"),
                TableColumn(
                    key="description",
                    label="Description",
                ),
                TableColumn(key="type", label="Type"),
                TableColumn(
                    key="amount",
                    label="Amount",
                    align="right",
                ),
            ],
            rows=rows,
        )

    @staticmethod
    def _ticket_update_list(
        data: dict[str, Any],
    ) -> ChatPresentation:
        rows = []
        for update in data.get("updates", []):
            rows.append(
                {
                    "ticket_id": str(
                        update.get("ticket_id", "")
                    ),
                    "updated_at": str(
                        update.get("updated_at", "")
                    ),
                    "status": _label(update.get("status")),
                    "note": str(update.get("note", "")),
                }
            )
        return TablePresentation(
            title="Ticket updates",
            columns=[
                TableColumn(
                    key="ticket_id",
                    label="Ticket",
                ),
                TableColumn(
                    key="updated_at",
                    label="Updated",
                ),
                TableColumn(
                    key="status",
                    label="Status",
                ),
                TableColumn(key="note", label="Note"),
            ],
            rows=rows,
        )

    @staticmethod
    def _customer_360(
        data: dict[str, Any],
    ) -> ChatPresentation:
        sections: list[
            SummarySection
        ] = []

        account = data.get(
            "account",
            {},
        )
        address_line = account.get(
            "service_address_line"
        )
        account_secondary = None
        if address_line:
            city = account.get("city", "")
            account_secondary = (
                f"{address_line}, {city}".strip(", ")
            )

        sections.append(
            SummarySection(
                label="Account",
                primary=_label(
                    account.get(
                        "account_status"
                    )
                ),
                secondary=account_secondary,
            )
        )

        subscription = data.get(
            "subscription"
        )
        plan = data.get(
            "plan"
        )

        if plan is None:
            plan_primary = "No plan recorded"
            plan_secondary = None
        else:
            status = (
                _label(
                    subscription.get(
                        "subscription_status"
                    )
                )
                if subscription is not None
                else "Status unavailable"
            )
            plan_primary = (
                f"{plan.get('plan_name', 'Plan unavailable')} — {status}"
            )
            plan_secondary = None

            if (
                subscription is not None
                and subscription.get(
                    "subscription_status"
                )
                == "ACTIVE"
            ):
                plan_secondary = (
                    f"Renews {subscription.get('renewal_date', 'date unavailable')}"
                )

        sections.append(
            SummarySection(
                label="Plan",
                primary=plan_primary,
                secondary=plan_secondary,
            )
        )

        usage = data.get(
            "usage"
        )

        if usage is None:
            usage_primary = "Current usage unavailable"
            usage_secondary = data.get(
                "usage_message"
            )
        elif usage.get(
            "is_unlimited"
        ):
            usage_primary = (
                f"{_usage_value(usage.get('used'), usage.get('unit', ''))} used"
            )
            usage_secondary = "Unlimited data"
        else:
            usage_primary = (
                f"{_usage_value(usage.get('used'), usage.get('unit', ''))} "
                f"of {_usage_value(usage.get('allowance'), usage.get('unit', ''))} used"
            )
            usage_secondary = (
                f"{_usage_value(usage.get('remaining'), usage.get('unit', ''))} remaining"
            )

        sections.append(
            SummarySection(
                label="Usage",
                primary=usage_primary,
                secondary=usage_secondary,
            )
        )

        bill = data.get(
            "billing"
        )

        if bill is None:
            billing_primary = "No bill recorded"
            billing_secondary = None
        else:
            billing_primary = (
                f"{_money(bill.get('amount'))} — "
                f"{_label(bill.get('status'))}"
            )
            billing_secondary = (
                f"Due {bill.get('due_date', 'date unavailable')}"
                if bill.get("status") != "PAID"
                else None
            )

        sections.append(
            SummarySection(
                label="Billing",
                primary=billing_primary,
                secondary=billing_secondary,
            )
        )

        payment = data.get(
            "payment"
        )
        latest_attempt = (
            payment.get("latest_attempt")
            if payment is not None
            else None
        )

        if payment is None:
            payment_primary = "No payment attempt recorded"
            payment_secondary = None
        elif latest_attempt is None:
            payment_primary = (
                "No attempt recorded for this bill"
                if data.get("billing") is not None
                else "No payment attempt recorded"
            )
            payment_secondary = (
                f"Outstanding {_money(payment.get('outstanding_amount'))}"
                if payment.get("outstanding_amount") is not None
                and float(payment["outstanding_amount"]) > 0
                else None
            )
        else:
            payment_primary = (
                f"{_money(latest_attempt.get('amount'))} — "
                f"{_label(latest_attempt.get('status'))}"
            )
            outstanding = payment.get(
                "outstanding_amount"
            )
            payment_secondary = (
                f"Outstanding {_money(outstanding)}"
                if outstanding is not None
                and float(outstanding) > 0
                else None
            )

        sections.append(
            SummarySection(
                label="Payment",
                primary=payment_primary,
                secondary=payment_secondary,
            )
        )

        support = data.get(
            "support",
            {},
        )
        unresolved_count = support.get(
            "unresolved_count"
        )
        support_primary = (
            "Unresolved count unavailable"
            if unresolved_count is None
            else (
                "No unresolved tickets"
                if unresolved_count == 0
                else (
                    f"{_number(unresolved_count)} unresolved "
                    f"{'ticket' if unresolved_count == 1 else 'tickets'}"
                )
            )
        )
        important_ticket = support.get(
            "important_ticket"
        )
        if important_ticket is not None:
            support_secondary = (
                f"{important_ticket['ticket_id']} · "
                f"{_label(important_ticket['category'])} · "
                f"{_label(important_ticket['priority'])} · "
                f"{_label(important_ticket['status'])}"
            )
            link_parts: list[str] = []
            related_bill = important_ticket.get(
                "related_bill_id"
            )
            if related_bill:
                link_parts.append(
                    f"Linked bill {related_bill}"
                )
            related_payment = important_ticket.get(
                "related_payment_id"
            )
            if related_payment:
                link_parts.append(
                    f"Linked payment {related_payment}"
                )
            if link_parts:
                support_secondary = (
                    f"{support_secondary} · "
                    f"{'; '.join(link_parts)}"
                )
        else:
            support_secondary = None

        sections.append(
            SummarySection(
                label="Support",
                primary=support_primary,
                secondary=support_secondary,
            )
        )

        devices = data.get(
            "devices",
            {},
        )
        if not devices.get(
            "available"
        ):
            devices_primary = "No associated devices available"
            devices_secondary = None
        else:
            active_count = devices.get(
                "active_count",
                0,
            )
            devices_primary = (
                f"{_number(active_count)} active "
                f"{'device' if active_count == 1 else 'devices'}"
            )
            active_names = [
                device.get(
                    "device_name"
                )
                for device in devices.get(
                    "active_devices",
                    [],
                )[:3]
            ]
            devices_secondary = (
                ", ".join(active_names)
                if active_names
                else None
            )

        sections.append(
            SummarySection(
                label="Devices",
                primary=devices_primary,
                secondary=devices_secondary,
            )
        )

        attention = data.get(
            "attention",
            {},
        )
        attention_items = attention.get(
            "items",
            [],
        )
        attention_count = attention.get(
            "count"
        )
        attention_primary = (
            "Attention status unavailable"
            if attention_count is None
            else (
                "Nothing currently requires attention"
                if attention_count == 0
                else (
                    f"{_number(attention_count)} items need attention"
                )
            )
        )
        attention_secondary = (
            "\n".join(
                item["message"]
                for item in attention_items
            )
            if attention_items
            else None
        )

        sections.append(
            SummarySection(
                label="Attention",
                primary=attention_primary,
                secondary=attention_secondary,
            )
        )

        customer_360_record_keys = (
            "customer",
            "subscriptions",
            "plans",
            "usage",
            "payments",
            "support_tickets",
            "devices",
        )

        table_columns = {
            "customer": (
                ("customer_id", "Customer ID"),
                ("name", "Name"),
                ("email", "Email"),
                ("phone_number", "Phone"),
                ("city", "City"),
                ("account_status", "Account status"),
                ("registration_date", "Registration date"),
            ),
            "subscriptions": (
                ("subscription_id", "Subscription ID"),
                ("customer_id", "Customer ID"),
                ("plan_id", "Plan ID"),
                ("activation_date", "Activation date"),
                ("status", "Status"),
                ("renewal_date", "Renewal date"),
            ),
            "plans": (
                ("plan_id", "Plan ID"),
                ("plan_name", "Plan name"),
                ("monthly_price", "Monthly price"),
                ("data_limit_gb", "Data limit (GB)"),
                ("is_data_unlimited", "Unlimited data"),
                ("voice_limit_minutes", "Voice limit (minutes)"),
                ("sms_limit", "SMS limit"),
                ("plan_type", "Plan type"),
            ),
            "usage": (
                ("usage_id", "Usage ID"),
                ("customer_id", "Customer ID"),
                ("subscription_id", "Subscription ID"),
                ("usage_date", "Usage date"),
                ("data_used_gb", "Data used (GB)"),
                ("voice_minutes", "Voice minutes"),
                ("sms_count", "SMS count"),
            ),
            "bills": (
                ("bill_id", "Bill ID"),
                ("customer_id", "Customer ID"),
                ("billing_period_start", "Period start"),
                ("billing_period_end", "Period end"),
                ("amount", "Amount"),
                ("due_date", "Due date"),
                ("status", "Status"),
            ),
            "bill_items": (
                ("bill_item_id", "Bill item ID"),
                ("bill_id", "Bill ID"),
                ("description", "Description"),
                ("amount", "Amount"),
                ("item_type", "Type"),
            ),
            "payments": (
                ("payment_id", "Payment ID"),
                ("bill_id", "Bill ID"),
                ("customer_id", "Customer ID"),
                ("amount", "Amount"),
                ("payment_date", "Payment date"),
                ("payment_method", "Method"),
                ("status", "Status"),
                ("transaction_reference", "Transaction reference"),
            ),
            "support_tickets": (
                ("ticket_id", "Ticket ID"),
                ("customer_id", "Customer ID"),
                ("category", "Category"),
                ("description", "Description"),
                ("status", "Status"),
                ("priority", "Priority"),
                ("created_at", "Created at"),
                ("updated_at", "Updated at"),
            ),
            "devices": (
                ("device_id", "Device ID"),
                ("customer_id", "Customer ID"),
                ("device_name", "Device name"),
                ("device_type", "Device type"),
                ("purchase_date", "Purchase date"),
                ("status", "Status"),
            ),
        }

        tables = []
        records = data.get(
            "records",
            {},
        )

        for key in customer_360_record_keys:
            columns = table_columns[key]
            rows = records.get(
                key,
                [],
            )
            tables.append(
                Customer360Table(
                    title=(
                        f"{_label(key)} "
                        f"({len(rows)} {'record' if len(rows) == 1 else 'records'})"
                    ),
                    columns=[
                        TableColumn(
                            key=column_key,
                            label=label,
                        )
                        for column_key, label in columns
                    ],
                    rows=[
                        {
                            column_key: (
                                "—"
                                if row.get(column_key) is None
                                else str(row[column_key])
                            )
                            for column_key, _ in columns
                        }
                        for row in rows
                    ],
                )
            )

        return Customer360Presentation(
            type="customer_360",
            title="Your account at a glance",
            sections=sections,
            tables=tables,
        )