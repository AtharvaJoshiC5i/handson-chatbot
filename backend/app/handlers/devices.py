"""Deterministic device intelligence handlers for NexaTel."""

from __future__ import annotations

import sqlite3

from app.database.queries.devices import (
    get_device_by_id,
    get_device_counts,
    get_device_type_counts,
    get_devices,
    get_newest_device,
    get_oldest_device,
)
from app.models.domain import (
    CustomerContext,
    DeviceExtremeType,
    DeviceSortOrder,
    DeviceStatus,
    DeviceType,
)
from app.truth.result import (
    TruthResult,
    database_error_result,
    not_found_result,
    verified_result,
)
from app.truth.sources import source_for_table


def _device_dict(
    device,
) -> dict:
    return {
        "device_id": device[
            "device_id"
        ],
        "device_name": device[
            "device_name"
        ],
        "device_type": device[
            "device_type"
        ],
        "purchase_date": device[
            "purchase_date"
        ],
        "status": device[
            "status"
        ],
    }


def get_device_information(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """Return all devices associated with the customer."""

    try:
        devices = get_devices(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your devices."
            ),
        )

    if not devices:
        return not_found_result(
            source=source_for_table(
                "devices"
            ),
            message=(
                "I don't have any devices associated "
                "with your account in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "DEVICE_LIST",
            "devices": [
                _device_dict(
                    device
                )
                for device in devices
            ],
        },
        source=source_for_table(
            "devices"
        ),
    )


def get_specific_device(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    device_id: str,
) -> TruthResult[dict]:
    try:
        device = get_device_by_id(
            db,
            customer.customer_id,
            device_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve that device."
            ),
        )

    if device is None:
        return not_found_result(
            source=source_for_table(
                "devices"
            ),
            message=(
                "I don't have that device in the "
                "records available for your account."
            ),
        )

    return verified_result(
        {
            "result_type": "DEVICE_SPECIFIC",
            "device": _device_dict(
                device
            ),
        },
        source=source_for_table(
            "devices"
        ),
    )


def filter_devices(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    device_status: DeviceStatus | None = None,
    device_type: DeviceType | None = None,
    device_sort_order: DeviceSortOrder | None = None,
    limit: int | None = None,
) -> TruthResult[dict]:
    statuses = (
        (
            device_status.value,
        )
        if device_status
        is not None
        else None
    )

    types = (
        (
            device_type.value,
        )
        if device_type
        is not None
        else None
    )

    try:
        devices = get_devices(
            db,
            customer.customer_id,
            statuses=statuses,
            device_types=types,
            sort_order=(
                device_sort_order.value
                if device_sort_order
                is not None
                else "NEWEST"
            ),
            limit=limit,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to filter your devices."
            ),
        )

    if not devices:
        return not_found_result(
            source=source_for_table(
                "devices"
            ),
            message=(
                "I don't have any devices matching "
                "those criteria in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "DEVICE_FILTER",
            "devices": [
                _device_dict(
                    device
                )
                for device in devices
            ],
        },
        source=source_for_table(
            "devices"
        ),
    )


def get_device_count(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    device_status: DeviceStatus | None = None,
    device_type: DeviceType | None = None,
) -> TruthResult[dict]:
    statuses = (
        (
            device_status.value,
        )
        if device_status
        is not None
        else None
    )

    types = (
        (
            device_type.value,
        )
        if device_type
        is not None
        else None
    )

    try:
        devices = get_devices(
            db,
            customer.customer_id,
            statuses=statuses,
            device_types=types,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to count your devices."
            ),
        )

    return verified_result(
        {
            "result_type": "DEVICE_COUNT",
            "count": len(
                devices
            ),
            "device_status": (
                device_status.value
                if device_status
                is not None
                else None
            ),
            "device_type": (
                device_type.value
                if device_type
                is not None
                else None
            ),
        },
        source=source_for_table(
            "devices"
        ),
    )


def get_device_extreme(
    db: sqlite3.Connection,
    customer: CustomerContext,
    *,
    device_extreme_type: DeviceExtremeType,
) -> TruthResult[dict]:
    try:
        if (
            device_extreme_type
            == DeviceExtremeType.NEWEST
        ):
            device = get_newest_device(
                db,
                customer.customer_id,
            )

        else:
            device = get_oldest_device(
                db,
                customer.customer_id,
            )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to analyze your device history."
            ),
        )

    if device is None:
        return not_found_result(
            source=source_for_table(
                "devices"
            ),
            message=(
                "I don't have any devices associated "
                "with your account in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": "DEVICE_EXTREME",
            "extreme_type": (
                device_extreme_type.value
            ),
            "device": _device_dict(
                device
            ),
        },
        source=source_for_table(
            "devices"
        ),
    )


def get_device_summary(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    try:
        counts = get_device_counts(
            db,
            customer.customer_id,
        )

        type_counts = (
            get_device_type_counts(
                db,
                customer.customer_id,
            )
        )

        devices = get_devices(
            db,
            customer.customer_id,
        )

        newest = get_newest_device(
            db,
            customer.customer_id,
        )

    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to summarize your devices."
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
                "devices"
            ),
            message=(
                "I don't have any devices associated "
                "with your account in the available records."
            ),
        )

    active_devices = [
        _device_dict(
            device
        )
        for device in devices
        if device["status"]
        == DeviceStatus.ACTIVE.value
    ]

    return verified_result(
        {
            "result_type": "DEVICE_SUMMARY",
            "total_devices": total,
            "active_count": int(
                counts[
                    "active_count"
                ]
                or 0
            ),
            "inactive_count": int(
                counts[
                    "inactive_count"
                ]
                or 0
            ),
            "replaced_count": int(
                counts[
                    "replaced_count"
                ]
                or 0
            ),
            "lost_count": int(
                counts[
                    "lost_count"
                ]
                or 0
            ),
            "type_counts": [
                {
                    "device_type": row[
                        "device_type"
                    ],
                    "count": int(
                        row[
                            "device_count"
                        ]
                    ),
                }
                for row in type_counts
            ],
            "active_devices": (
                active_devices
            ),
            "newest_device": (
                _device_dict(
                    newest
                )
                if newest
                is not None
                else None
            ),
        },
        source=source_for_table(
            "devices"
        ),
    )


def get_device_diagnostic_limitation(
    db: sqlite3.Connection,
    customer: CustomerContext,
) -> TruthResult[dict]:
    """
    Return recorded device information while explicitly stating
    that diagnostic information is unavailable.
    """

    try:
        devices = get_devices(
            db,
            customer.customer_id,
        )
    except sqlite3.Error:
        return database_error_result(
            message=(
                "Unable to retrieve your devices."
            ),
        )

    if not devices:
        return not_found_result(
            source=source_for_table(
                "devices"
            ),
            message=(
                "I don't have any devices associated "
                "with your account in the available records."
            ),
        )

    return verified_result(
        {
            "result_type": (
                "DEVICE_DIAGNOSTIC_LIMITATION"
            ),
            "devices": [
                _device_dict(
                    device
                )
                for device in devices
            ],
            "diagnostic_data_available": False,
        },
        source=source_for_table(
            "devices"
        ),
    )