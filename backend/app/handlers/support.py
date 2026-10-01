"""Deterministic support intelligence handlers for NexaTel."""

from __future__ import annotations

from datetime import date
import sqlite3

from app.database.queries.support_tickets import (
    get_latest_support_ticket,
    get_support_category_counts,
    get_support_ticket_by_id,
    get_support_ticket_counts,
    get_support_tickets,
)
from app.models.domain import (
    CustomerContext,
    SupportSortOrder,
    SupportTicketCategory,
    SupportTicketPriority,
    SupportTicketStatus,
    TimeRange,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


UNRESOLVED_STATUSES = (
    SupportTicketStatus.OPEN.value,
    SupportTicketStatus.IN_PROGRESS.value,
)

RESOLVED_STATUSES = (
    SupportTicketStatus.RESOLVED.value,
    SupportTicketStatus.CLOSED.value,
)


def _ticket_dict(
    ticket,
) -> dict:
    return {
        "ticket_id": ticket[
            "ticket_id"
        ],
        "category": ticket[
            "category"
        ],
        "description": ticket[
            "description"
        ],
        "status": ticket[
            "status"
        ],
        "priority": ticket[
            "priority"
        ],
        "created_at": ticket[
            "created_at"
        ],
        "updated_at": ticket[
            "updated_at"
        ],
        "is_unresolved": (
            ticket["status"]
            in UNRESOLVED_STATUSES
        ),
    }


def _period_bounds(
    *,
    time_range: TimeRange | None = None,
    month_count: int | None = None,
) -> tuple[
    str | None,
    str | None,
]:
    today = date.today()

    if (
        time_range
        == TimeRange.CURRENT_MONTH
    ):
        return (
            date(
                today.year,
                today.month,
                1,
            ).isoformat(),
            today.isoformat(),
        )

    if (
        time_range
        == TimeRange.CURRENT_YEAR
    ):
        return (
            date(
                today.year,
                1,
                1,
            ).isoformat(),
            today.isoformat(),
        )

    if (
        time_range
        == TimeRange.LAST_MONTH
    ):
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1

        start = date(
            year,
            month,
            1,
        )

        if month == 12:
            next_month = date(
                year + 1,
                1,
                1,
            )
        else:
            next_month = date(
                year,
                month + 1,
                1,
            )

        from datetime import timedelta

        return (
            start.isoformat(),
            (
                next_month
                - timedelta(days=1)
            ).isoformat(),
        )

    if month_count is not None:
        month_index = (
            today.year * 12
            + today.month
            - 1
            - (
                month_count
                - 1
            )
        )

        start_year = (
            month_index // 12
        )

        start_month = (
            month_index % 12
            + 1
        )

        return (
            date(
                start_year,
                start_month,
                1,
            ).isoformat(),
            today.isoformat(),
        )

    return (
        None,
        None,
    )


def get_latest_support_ticket_for_customer(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        ticket = (
            get_latest_support_ticket(
                db,
                customer.customer_id,
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your latest "
                "support ticket."
            ),
        )

    if ticket is None:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "You don't have any support tickets "
                "in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_LATEST",
            "ticket": _ticket_dict(
                ticket
            ),
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_specific_support_ticket(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    ticket_id: str,
) -> TruthResult[dict]:
    try:
        ticket = (
            get_support_ticket_by_id(
                db,
                customer.customer_id,
                ticket_id,
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve that "
                "support ticket."
            ),
        )

    if ticket is None:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "I don't have that support ticket "
                "in the records available for your account."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_SPECIFIC",
            "ticket": _ticket_dict(
                ticket
            ),
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_customer_support_tickets(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    limit: int | None = None,
    time_range: TimeRange | None = None,
    month_count: int | None = None,
) -> TruthResult[dict]:
    start_date, end_date = (
        _period_bounds(
            time_range=time_range,
            month_count=month_count,
        )
    )

    try:
        tickets = get_support_tickets(
            db,
            customer.customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=(
                limit
                if limit is not None
                else 10
            ),
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your "
                "support history."
            ),
        )

    if not tickets:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "You don't have any support tickets "
                "in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_HISTORY",
            "tickets": [
                _ticket_dict(
                    ticket
                )
                for ticket in tickets
            ],
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def filter_support_tickets(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    ticket_status: SupportTicketStatus | None = None,
    ticket_priority: SupportTicketPriority | None = None,
    ticket_category: SupportTicketCategory | None = None,
    unresolved_only: bool | None = None,
    time_range: TimeRange | None = None,
    month_count: int | None = None,
    limit: int | None = None,
    support_sort_order: SupportSortOrder | None = None,
) -> TruthResult[dict]:
    statuses = None

    if unresolved_only:
        statuses = UNRESOLVED_STATUSES

    elif ticket_status is not None:
        statuses = (
            ticket_status.value,
        )

    priorities = (
        (
            ticket_priority.value,
        )
        if ticket_priority
        is not None
        else None
    )

    categories = (
        (
            ticket_category.value,
        )
        if ticket_category
        is not None
        else None
    )

    start_date, end_date = (
        _period_bounds(
            time_range=time_range,
            month_count=month_count,
        )
    )

    try:
        tickets = get_support_tickets(
            db,
            customer.customer_id,
            statuses=statuses,
            priorities=priorities,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            sort_order=(
                support_sort_order.value
                if support_sort_order
                is not None
                else "NEWEST"
            ),
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to filter your "
                "support tickets."
            ),
        )

    if not tickets:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "I don't have any support tickets "
                "matching those criteria."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_FILTER",
            "tickets": [
                _ticket_dict(
                    ticket
                )
                for ticket in tickets
            ],
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_support_ticket_count(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    ticket_status: SupportTicketStatus | None = None,
    ticket_priority: SupportTicketPriority | None = None,
    ticket_category: SupportTicketCategory | None = None,
    unresolved_only: bool | None = None,
    time_range: TimeRange | None = None,
    month_count: int | None = None,
) -> TruthResult[dict]:
    statuses = None

    if unresolved_only:
        statuses = UNRESOLVED_STATUSES

    elif ticket_status is not None:
        statuses = (
            ticket_status.value,
        )

    priorities = (
        (
            ticket_priority.value,
        )
        if ticket_priority
        is not None
        else None
    )

    categories = (
        (
            ticket_category.value,
        )
        if ticket_category
        is not None
        else None
    )

    start_date, end_date = (
        _period_bounds(
            time_range=time_range,
            month_count=month_count,
        )
    )

    try:
        tickets = get_support_tickets(
            db,
            customer.customer_id,
            statuses=statuses,
            priorities=priorities,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to count your support tickets."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_COUNT",
            "count": len(
                tickets
            ),
            "unresolved_only": bool(
                unresolved_only
            ),
            "ticket_status": (
                ticket_status.value
                if ticket_status
                is not None
                else None
            ),
            "ticket_priority": (
                ticket_priority.value
                if ticket_priority
                is not None
                else None
            ),
            "ticket_category": (
                ticket_category.value
                if ticket_category
                is not None
                else None
            ),
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_most_common_support_category(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        rows = (
            get_support_category_counts(
                db,
                customer.customer_id,
            )
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to analyze your "
                "support history."
            ),
        )

    if not rows:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "You don't have any support tickets "
                "in the available records."
            ),
        )

    highest_count = int(
        rows[0][
            "ticket_count"
        ]
    )

    categories = [
        row["category"]
        for row in rows
        if int(
            row["ticket_count"]
        )
        == highest_count
    ]

    return verified_result(
        {
            "result_type": (
                "SUPPORT_COMMON_CATEGORY"
            ),
            "categories": categories,
            "ticket_count": (
                highest_count
            ),
            "is_tie": (
                len(categories) > 1
            ),
            "category_counts": [
                {
                    "category": row[
                        "category"
                    ],
                    "count": int(
                        row[
                            "ticket_count"
                        ]
                    ),
                }
                for row in rows
            ],
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_support_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        counts = (
            get_support_ticket_counts(
                db,
                customer.customer_id,
            )
        )

        latest = (
            get_latest_support_ticket(
                db,
                customer.customer_id,
            )
        )

        category_rows = (
            get_support_category_counts(
                db,
                customer.customer_id,
            )
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to summarize your "
                "support history."
            ),
        )

    total = int(
        counts[
            "total_count"
        ]
        or 0
    )

    if total == 0:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "You don't have any support tickets "
                "in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "SUPPORT_SUMMARY",
            "total_tickets": total,
            "unresolved_count": int(
                counts[
                    "unresolved_count"
                ]
                or 0
            ),
            "resolved_count": int(
                counts[
                    "resolved_count"
                ]
                or 0
            ),
            "high_count": int(
                counts[
                    "high_count"
                ]
                or 0
            ),
            "critical_count": int(
                counts[
                    "critical_count"
                ]
                or 0
            ),
            "latest_ticket": (
                _ticket_dict(
                    latest
                )
                if latest
                is not None
                else None
            ),
            "category_counts": [
                {
                    "category": row[
                        "category"
                    ],
                    "count": int(
                        row[
                            "ticket_count"
                        ]
                    ),
                }
                for row in category_rows
            ],
        },
        source=source_for_table(
            "support_tickets"
        ),
    )


def get_latest_ticket_update(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    ticket_id: str | None = None,
) -> TruthResult[dict]:
    try:
        if ticket_id is not None:
            ticket = (
                get_support_ticket_by_id(
                    db,
                    customer.customer_id,
                    ticket_id,
                )
            )

        else:
            ticket = (
                get_latest_support_ticket(
                    db,
                    customer.customer_id,
                )
            )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve the ticket update."
            ),
        )

    if ticket is None:
        return not_found_result(
            source=source_for_table(
                "support_tickets"
            ),
            message=(
                "I don't have that support ticket "
                "in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "SUPPORT_LAST_UPDATED"
            ),
            "ticket": _ticket_dict(
                ticket
            ),
            "update_content_available": False,
        },
        source=source_for_table(
            "support_tickets"
        ),
    )