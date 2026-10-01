from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
import sqlite3

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
MONTHS = [(2026, m) for m in range(4, 10)]

# Intentional manager-demo fixtures:
# CUST002: roaming bill increase + failed payment + billing ticket.
# CUST006: heavy mobile usage approaching allowance.
# CUST004: overdue/payment problem on a suspended account.
# CUST005: stable customer; BILL009/BILL010 retained for existing tests/evaluation.
# CUST003: unlimited fiber customer with router and broadband support history.

CUSTOMERS = [
    (
        "CUST001",
        "Aarav Sharma",
        "aarav.sharma@example.com",
        "+919000000001",
        "Mumbai",
        "ACTIVE",
        "2024-02-15",
    ),
    (
        "CUST002",
        "Diya Mehta",
        "diya.mehta@example.com",
        "+919000000002",
        "Pune",
        "ACTIVE",
        "2024-06-20",
    ),
    (
        "CUST003",
        "Rohan Kapoor",
        "rohan.kapoor@example.com",
        "+919000000003",
        "Bengaluru",
        "ACTIVE",
        "2023-11-10",
    ),
    (
        "CUST004",
        "Ananya Iyer",
        "ananya.iyer@example.com",
        "+919000000004",
        "Delhi",
        "SUSPENDED",
        "2023-05-03",
    ),
    (
        "CUST005",
        "Kabir Patel",
        "kabir.patel@example.com",
        "+919000000005",
        "Ahmedabad",
        "ACTIVE",
        "2025-01-18",
    ),
    (
        "CUST006",
        "Meera Nair",
        "meera.nair@example.com",
        "+919000000006",
        "Chennai",
        "ACTIVE",
        "2025-03-22",
    ),
    (
        "CUST007",
        "Vikram Singh",
        "vikram.singh@example.com",
        "+919000000007",
        "Jaipur",
        "CANCELLED",
        "2024-08-14",
    ),
    (
        "CUST008",
        "Ishita Rao",
        "ishita.rao@example.com",
        "+919000000008",
        "Hyderabad",
        "ACTIVE",
        "2025-07-09",
    ),
    (
        "CUST009",
        "Arjun Reddy",
        "arjun.reddy@example.com",
        "+919000000009",
        "Hyderabad",
        "ACTIVE",
        "2024-09-12",
    ),
    (
        "CUST010",
        "Sneha Banerjee",
        "sneha.banerjee@example.com",
        "+919000000010",
        "Kolkata",
        "ACTIVE",
        "2025-02-03",
    ),
    (
        "CUST011",
        "Aditya Deshmukh",
        "aditya.deshmukh@example.com",
        "+919000000011",
        "Pune",
        "ACTIVE",
        "2024-12-18",
    ),
    (
        "CUST012",
        "Nandini Menon",
        "nandini.menon@example.com",
        "+919000000012",
        "Kochi",
        "ACTIVE",
        "2023-08-27",
    ),
    (
        "CUST013",
        "Harpreet Kaur",
        "harpreet.kaur@example.com",
        "+919000000013",
        "Chandigarh",
        "ACTIVE",
        "2025-05-11",
    ),
    (
        "CUST014",
        "Siddharth Verma",
        "siddharth.verma@example.com",
        "+919000000014",
        "Lucknow",
        "ACTIVE",
        "2024-04-06",
    ),
    (
        "CUST015",
        "Priya Kulkarni",
        "priya.kulkarni@example.com",
        "+919000000015",
        "Indore",
        "SUSPENDED",
        "2024-10-19",
    ),
    (
        "CUST016",
        "Debashish Mohanty",
        "debashish.mohanty@example.com",
        "+919000000016",
        "Bhubaneswar",
        "ACTIVE",
        "2025-06-02",
    ),
    (
        "CUST017",
        "Neha Malhotra",
        "neha.malhotra@example.com",
        "+919000000017",
        "Gurugram",
        "ACTIVE",
        "2023-12-09",
    ),
    (
        "CUST018",
        "Karthik Subramanian",
        "karthik.subramanian@example.com",
        "+919000000018",
        "Chennai",
        "ACTIVE",
        "2024-07-21",
    ),
    (
        "CUST019",
        "Aditi Joshi",
        "aditi.joshi@example.com",
        "+919000000019",
        "Mumbai",
        "CANCELLED",
        "2023-09-14",
    ),
    (
        "CUST020",
        "Rahul Chatterjee",
        "rahul.chatterjee@example.com",
        "+919000000020",
        "Kolkata",
        "ACTIVE",
        "2025-01-30",
    ),
]

PLANS = [
    ("PLAN001", "NexaMax 499", 499, 50, 0, 1200, 100, "MOBILE"),
    ("PLAN002", "NexaMax 799", 799, 75, 0, 2000, 200, "MOBILE"),
    ("PLAN003", "NexaMax 999", 999, 100, 0, 3000, 300, "MOBILE"),
    ("PLAN004", "NexaMax 1499", 1499, 150, 0, 5000, 500, "MOBILE"),
    ("PLAN005", "NexaFiber 799", 799, 0, 1, 0, 0, "FIBER"),
    ("PLAN006", "NexaFiber 999", 999, 0, 1, 0, 0, "FIBER"),
    ("PLAN007", "NexaFiber 1499", 1499, 0, 1, 0, 0, "FIBER"),
    ("PLAN008", "NexaMax 649", 649, 60, 0, 1500, 150, "MOBILE"),
]

PLAN_BY_ID = {plan[0]: plan for plan in PLANS}

ASSIGN = [
    "PLAN002",
    "PLAN002",
    "PLAN005",
    "PLAN003",
    "PLAN001",
    "PLAN003",
    "PLAN001",
    "PLAN007",
    "PLAN008",
    "PLAN002",
    "PLAN001",
    "PLAN006",
    "PLAN002",
    "PLAN003",
    "PLAN001",
    "PLAN005",
    "PLAN004",
    "PLAN002",
    "PLAN001",
    "PLAN006",
]

PATTERNS = [
    "stable",
    "rising",
    "fiber",
    "stable",
    "low",
    "heavy",
    "cancelled",
    "fiber",
    "rising",
    "spike",
    "low",
    "fiber",
    "stable",
    "rising",
    "stable",
    "fiber",
    "heavy",
    "declining",
    "cancelled",
    "fiber",
]

DEVNAMES = [
    "Apple iPhone 15",
    "Samsung Galaxy S24",
    "TP-Link Archer AX55",
    "Google Pixel 9",
    "OnePlus 12",
    "Samsung Galaxy S24 Ultra",
    "Nothing Phone (2)",
    "Netgear Nighthawk AX5400",
    "OnePlus Nord 4",
    "Apple iPhone 16",
    "Samsung Galaxy A55 5G",
    "TP-Link Archer AX73",
    "Xiaomi 14",
    "Motorola Edge 50 Pro",
    "Apple iPhone 15",
    "D-Link DIR-X5460",
    "Apple iPhone 16 Pro",
    "Samsung Galaxy S24",
    "OnePlus Nord 4",
    "TP-Link Archer AX55",
]


def initialize_database(
    connection: sqlite3.Connection,
    reset: bool = False,
) -> None:
    if reset:
        _drop_tables(connection)

    connection.executescript(
        SCHEMA_PATH.read_text(encoding="utf-8")
    )
    connection.commit()


def _id(prefix: str, number: int) -> str:
    return f"{prefix}{number:03d}"


def _last(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def seed_database(
    connection: sqlite3.Connection,
    reset: bool = False,
) -> None:
    initialize_database(connection, reset=reset)

    connection.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?,?)",
        CUSTOMERS,
    )

    connection.executemany(
        """
        INSERT INTO plans (
            plan_id,
            plan_name,
            monthly_price,
            data_limit_gb,
            is_data_unlimited,
            voice_limit_minutes,
            sms_limit,
            plan_type
        )
        VALUES (?,?,?,?,?,?,?,?)
        """,
        PLANS,
    )

    subscriptions = []

    for index, customer in enumerate(CUSTOMERS, 1):
        if customer[5] == "CANCELLED":
            status = "CANCELLED"
        elif customer[5] == "SUSPENDED":
            status = "SUSPENDED"
        else:
            status = "ACTIVE"

        renewal_date = (
            "2026-08-14"
            if status == "CANCELLED"
            else "2026-10-15"
        )

        subscriptions.append(
            (
                _id("SUB", index),
                customer[0],
                ASSIGN[index - 1],
                customer[6],
                status,
                renewal_date,
            )
        )

    connection.executemany(
        "INSERT INTO subscriptions VALUES (?,?,?,?,?,?)",
        subscriptions,
    )

    _usage(connection, subscriptions)
    _billing(connection)
    _tickets(connection)
    _devices(connection)

    connection.commit()


def _usage(
    connection: sqlite3.Connection,
    subscriptions: list[tuple],
) -> None:
    rows = []
    usage_number = 1

    for customer_index, subscription in enumerate(
        subscriptions,
        1,
    ):
        plan = PLAN_BY_ID[subscription[2]]
        pattern = PATTERNS[customer_index - 1]

        for month_index, (year, month) in enumerate(MONTHS):
            if pattern == "cancelled" and month > 7:
                continue

            if pattern == "fiber":
                total = (
                    130
                    + month_index * 9
                    + customer_index % 4 * 7
                )
            else:
                total = {
                    "low": 12,
                    "stable": 34,
                    "rising": 24 + month_index * 6,
                    "heavy": 70 + month_index * 5,
                    "declining": 48 - month_index * 5,
                    "spike": (
                        35
                        if month != 8
                        else 68
                    ),
                    "cancelled": 26,
                }.get(pattern, 30)

            # Demo customer CUST006 has a deliberate
            # month-over-month heavy usage pattern.
            if customer_index == 6:
                total = [61, 68, 74, 81, 88, 94][
                    month_index
                ]

            for part_index, day in enumerate((5, 15, 25)):
                data = round(
                    total
                    * [0.28, 0.34, 0.38][part_index],
                    2,
                )

                if plan[7] == "FIBER":
                    voice = 0
                    sms = 0
                else:
                    voice = int(
                        (
                            220
                            + customer_index * 11
                            + month_index * 8
                        )
                        * [0.30, 0.35, 0.35][part_index]
                    )

                    sms = int(
                        (
                            24
                            + customer_index % 6 * 3
                            + month_index
                        )
                        * [0.30, 0.30, 0.40][part_index]
                    )

                rows.append(
                    (
                        _id("USE", usage_number),
                        subscription[1],
                        subscription[0],
                        (
                            f"{year}-{month:02d}-"
                            f"{day:02d}"
                        ),
                        data,
                        voice,
                        sms,
                    )
                )

                usage_number += 1

    connection.executemany(
        "INSERT INTO usage VALUES (?,?,?,?,?,?,?)",
        rows,
    )


def _billing(connection: sqlite3.Connection) -> None:
    bills = []
    items = []
    payments = []

    bill_number = 1
    item_number = 1
    payment_number = 1

    for customer_index, customer in enumerate(
        CUSTOMERS,
        1,
    ):
        if customer[5] == "CANCELLED":
            if customer_index == 7:
                months = MONTHS[:5]
            else:
                months = MONTHS[:4]
        else:
            months = MONTHS

        plan = PLAN_BY_ID[ASSIGN[customer_index - 1]]
        price = float(plan[2])

        for month_index, (year, month) in enumerate(months):
            # Retain IDs expected by existing CUST005
            # tests/evaluation.
            if customer_index == 5 and month_index == 4:
                bill_id = "BILL009"

            elif customer_index == 5 and month_index == 5:
                bill_id = "BILL010"

            else:
                while _id(
                    "BILL",
                    bill_number,
                ) in {"BILL009", "BILL010"}:
                    bill_number += 1

                bill_id = _id("BILL", bill_number)
                bill_number += 1

            charges = [
                (
                    "Monthly plan charge",
                    price,
                    "PLAN_CHARGE",
                )
            ]

            # Deliberate roaming bill-increase scenario.
            if customer_index == 2 and month == 9:
                charges += [
                    (
                        "International roaming",
                        301.0,
                        "ROAMING",
                    ),
                    (
                        "Roaming tax",
                        43.0,
                        "TAX",
                    ),
                ]

            # Deliberate data add-on scenario.
            if customer_index == 10 and month == 8:
                charges += [
                    (
                        "10 GB data add-on",
                        199.0,
                        "DATA_ADDON",
                    )
                ]

            # Deliberate additional-service scenario.
            if customer_index == 17 and month == 7:
                charges += [
                    (
                        "International calling service",
                        149.0,
                        "OTHER",
                    )
                ]

            total = round(
                sum(charge[1] for charge in charges),
                2,
            )

            status = "PAID"

            if customer_index == 2 and month == 9:
                status = "UNPAID"

            elif customer_index in (4, 15) and month == 9:
                status = "OVERDUE"

            elif customer_index == 6 and month == 9:
                status = "PARTIALLY_PAID"

            elif customer_index == 8 and month == 9:
                status = "UNPAID"

            period_start = f"{year}-{month:02d}-01"

            period_end = (
                f"{year}-{month:02d}-"
                f"{_last(year, month):02d}"
            )

            due_date = (
                date(
                    year,
                    month,
                    _last(year, month),
                )
                + timedelta(days=12)
            ).isoformat()

            bills.append(
                (
                    bill_id,
                    customer[0],
                    period_start,
                    period_end,
                    total,
                    due_date,
                    status,
                )
            )

            for description, amount, item_type in charges:
                items.append(
                    (
                        _id("ITEM", item_number),
                        bill_id,
                        description,
                        amount,
                        item_type,
                    )
                )
                item_number += 1

            payment_date = (
                (
                    date(
                        year,
                        month,
                        _last(year, month),
                    )
                    + timedelta(days=5)
                ).isoformat()
                + "T10:30:00"
            )

            if status == "PAID":
                payments.append(
                    (
                        _id("PAY", payment_number),
                        bill_id,
                        customer[0],
                        total,
                        payment_date,
                        "UPI",
                        "SUCCESS",
                        f"TXN2026{payment_number:06d}",
                    )
                )
                payment_number += 1

            elif customer_index == 2 and month == 9:
                payments.append(
                    (
                        _id("PAY", payment_number),
                        bill_id,
                        customer[0],
                        total,
                        payment_date,
                        "CREDIT_CARD",
                        "FAILED",
                        f"TXN2026{payment_number:06d}",
                    )
                )
                payment_number += 1

            elif customer_index == 6 and month == 9:
                payments.append(
                    (
                        _id("PAY", payment_number),
                        bill_id,
                        customer[0],
                        round(total * 0.45, 2),
                        payment_date,
                        "UPI",
                        "SUCCESS",
                        f"TXN2026{payment_number:06d}",
                    )
                )
                payment_number += 1

            elif customer_index == 8 and month == 9:
                payments.append(
                    (
                        _id("PAY", payment_number),
                        bill_id,
                        customer[0],
                        total,
                        payment_date,
                        "NET_BANKING",
                        "PENDING",
                        f"TXN2026{payment_number:06d}",
                    )
                )
                payment_number += 1

            elif customer_index == 15 and month == 9:
                payments.append(
                    (
                        _id("PAY", payment_number),
                        bill_id,
                        customer[0],
                        total,
                        payment_date,
                        "DEBIT_CARD",
                        "FAILED",
                        f"TXN2026{payment_number:06d}",
                    )
                )
                payment_number += 1

        # Failed-then-successful-retry scenario for
        # CUST009's June bill.
        if customer_index == 9:
            target = [
                bill
                for bill in bills
                if bill[1] == customer[0]
                and bill[2] == "2026-06-01"
            ][0]

            payments.append(
                (
                    _id("PAY", payment_number),
                    target[0],
                    customer[0],
                    target[4],
                    "2026-07-02T09:15:00",
                    "CREDIT_CARD",
                    "FAILED",
                    f"TXN2026{payment_number:06d}",
                )
            )

            payment_number += 1

    connection.executemany(
        "INSERT INTO bills VALUES (?,?,?,?,?,?,?)",
        bills,
    )

    connection.executemany(
        "INSERT INTO bill_items VALUES (?,?,?,?,?)",
        items,
    )

    connection.executemany(
        "INSERT INTO payments VALUES (?,?,?,?,?,?,?,?)",
        payments,
    )


def _tickets(connection: sqlite3.Connection) -> None:
    rows = []
    ticket_number = 1

    special = {
        2: [
            (
                "BILLING",
                (
                    "Customer reported unexpected "
                    "international roaming charges."
                ),
                "OPEN",
                "HIGH",
                "2026-09-18T10:00:00",
                "2026-09-18T12:30:00",
            ),
            (
                "NETWORK",
                (
                    "Intermittent mobile data reported "
                    "while travelling."
                ),
                "RESOLVED",
                "MEDIUM",
                "2026-06-11T09:00:00",
                "2026-06-12T16:00:00",
            ),
        ],
        3: [
            (
                "BROADBAND",
                (
                    "Wi-Fi speed lower than expected "
                    "in one room."
                ),
                "RESOLVED",
                "MEDIUM",
                "2026-05-08T11:00:00",
                "2026-05-09T15:00:00",
            ),
            (
                "BROADBAND",
                (
                    "Router required configuration "
                    "assistance after reset."
                ),
                "CLOSED",
                "LOW",
                "2026-08-03T13:00:00",
                "2026-08-03T16:30:00",
            ),
        ],
        4: [
            (
                "PAYMENT",
                "Payment failed and bill remains overdue.",
                "IN_PROGRESS",
                "HIGH",
                "2026-09-16T10:30:00",
                "2026-09-17T09:00:00",
            )
        ],
        6: [
            (
                "PLAN",
                (
                    "Customer asked about higher-data "
                    "plan options."
                ),
                "RESOLVED",
                "LOW",
                "2026-08-20T10:00:00",
                "2026-08-20T14:00:00",
            )
        ],
    }

    for customer_index, customer in enumerate(
        CUSTOMERS,
        1,
    ):
        entries = special.get(customer_index, [])

        if not entries:
            entries = [
                (
                    "NETWORK",
                    (
                        "Customer reported temporary "
                        "connectivity issue."
                    ),
                    "RESOLVED",
                    "MEDIUM",
                    (
                        f"2026-0{4 + (customer_index % 5)}"
                        "-12T10:00:00"
                    ),
                    (
                        f"2026-0{4 + (customer_index % 5)}"
                        "-13T11:00:00"
                    ),
                )
            ]

        if (
            customer_index % 2 == 0
            and len(entries) < 2
        ):
            entries.append(
                (
                    "PLAN",
                    (
                        "Customer requested clarification "
                        "about plan benefits."
                    ),
                    "CLOSED",
                    "LOW",
                    "2026-07-05T09:00:00",
                    "2026-07-05T12:00:00",
                )
            )

        if (
            customer_index in (1, 5, 9, 13, 17, 20)
            and len(entries) < 3
        ):
            entries.append(
                (
                    "OTHER",
                    (
                        "Customer requested general "
                        "account assistance."
                    ),
                    "CLOSED",
                    "LOW",
                    "2026-04-22T14:00:00",
                    "2026-04-22T16:00:00",
                )
            )

        for entry in entries:
            rows.append(
                (
                    _id("TKT", ticket_number),
                    customer[0],
                    *entry,
                )
            )
            ticket_number += 1

    connection.executemany(
        """
        INSERT INTO support_tickets
        VALUES (?,?,?,?,?,?,?,?)
        """,
        rows,
    )


def _devices(connection: sqlite3.Connection) -> None:
    rows = []
    device_number = 1

    for customer_index, customer in enumerate(
        CUSTOMERS,
        1,
    ):
        plan = PLAN_BY_ID[
            ASSIGN[customer_index - 1]
        ]

        device_type = (
            "ROUTER"
            if plan[7] == "FIBER"
            else "SMARTPHONE"
        )

        rows.append(
            (
                _id("DEV", device_number),
                customer[0],
                DEVNAMES[customer_index - 1],
                device_type,
                "2025-01-15",
                (
                    "ACTIVE"
                    if customer[5] != "CANCELLED"
                    else "INACTIVE"
                ),
            )
        )

        device_number += 1

        if customer_index in (
            1,
            2,
            5,
            6,
            10,
            17,
            18,
        ):
            old_device = (
                "Apple iPhone 15"
                if device_type == "SMARTPHONE"
                else "TP-Link Archer AX55"
            )

            rows.append(
                (
                    _id("DEV", device_number),
                    customer[0],
                    old_device,
                    device_type,
                    "2024-03-10",
                    "REPLACED",
                )
            )

            device_number += 1

        if customer_index in (2, 17):
            rows.append(
                (
                    _id("DEV", device_number),
                    customer[0],
                    "Samsung Galaxy A55 5G",
                    "SMARTPHONE",
                    "2025-11-20",
                    "INACTIVE",
                )
            )

            device_number += 1

    connection.executemany(
        "INSERT INTO devices VALUES (?,?,?,?,?,?)",
        rows,
    )


def _drop_tables(
    connection: sqlite3.Connection,
) -> None:
    tables = [
        "devices",
        "support_tickets",
        "payments",
        "bill_items",
        "bills",
        "usage",
        "subscriptions",
        "plans",
        "customers",
    ]

    for table in tables:
        connection.execute(
            f"DROP TABLE IF EXISTS {table}"
        )

    connection.commit()