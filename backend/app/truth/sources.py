"""Source metadata for verified NexaTel data."""

from __future__ import annotations

from app.models.domain import SourceType, TruthSource


DATABASE_SOURCE = TruthSource(
    source_type=SourceType.SQLITE,
    source_name="nexatel.db",
)


_TABLE_SOURCES: dict[str, TruthSource] = {
    "customers": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.customers",
    ),
    "plans": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.plans",
    ),
    "subscriptions": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.subscriptions",
    ),
    "usage": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.usage",
    ),
    "bills": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.bills",
    ),
    "bill_items": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.bill_items",
    ),
    "payments": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.payments",
    ),
    "support_tickets": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.support_tickets",
    ),
    "devices": TruthSource(
        source_type=SourceType.SQLITE,
        source_name="sqlite.devices",
    ),
}


def source_for_table(table_name: str) -> TruthSource:
    """Return source metadata for a known database table."""

    try:
        return _TABLE_SOURCES[table_name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown NexaTel source table: {table_name}"
        ) from exc