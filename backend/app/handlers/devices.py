"""Handlers for NexaTel device-information intents."""

from __future__ import annotations

import sqlite3

from app.database.queries.devices import (
    get_customer_devices,
)
from app.models.domain import CustomerContext
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def get_device_information(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[list[dict]]:
    """Return devices belonging to the authenticated customer."""

    try:
        devices = get_customer_devices(
            db,
            customer_id=customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message="Unable to retrieve your device information.",
        )

    if not devices:
        return not_found_result(
            source=source_for_table("devices"),
            message="No devices were found for your account.",
        )

    return verified_result(
        [dict(device) for device in devices],
        source=source_for_table("devices"),
    )