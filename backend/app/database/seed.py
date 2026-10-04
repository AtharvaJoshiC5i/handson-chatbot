from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
import sqlite3

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
MONTHS = (
    [(2025, month) for month in range(10, 13)]
    + [(2026, month) for month in range(1, 11)]
)

# Demo customers with more than one subscription (mobile + fiber).
MULTI_SUBSCRIPTION_CUSTOMERS = {
    "CUST003": (
        "PLAN003",
        "2023-12-01",
    ),
}

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

# Populated during _usage for bill_shock / heavy linkage.
USAGE_MONTH_DATA_GB: dict[
    tuple[str, int, int],
    float,
] = {}

BILLING_PERSONA_BY_INDEX = {
    1: "autopay_steady",
    2: "roaming_story",
    3: "fiber_stable",
    4: "chronic_late",
    5: "autopay_steady",
    6: "bill_shock",
    7: "churned",
    8: "fiber_stable",
    9: "addon_heavy",
    10: "addon_heavy",
    11: "autopay_steady",
    12: "fiber_stable",
    13: "autopay_steady",
    14: "addon_heavy",
    15: "chronic_late",
    16: "fiber_stable",
    17: "bill_shock",
    18: "autopay_steady",
    19: "churned",
    20: "fiber_stable",
}

RESERVED_BILL_IDS = frozenset(
    {"BILL009", "BILL010", "BILL027"},
)


def _billing_persona(
    customer_index: int,
    plan: tuple,
) -> str:
    if plan[7] == "FIBER":
        return "fiber_stable"
    return BILLING_PERSONA_BY_INDEX.get(
        customer_index,
        "autopay_steady",
    )


def _month_seed(
    customer_index: int,
    year: int,
    month: int,
) -> int:
    return (
        customer_index * 37
        + year * 13
        + month * 11
    ) % 97


def _payment_method_for_bill(
    customer_index: int,
    year: int,
    month: int,
    persona: str,
) -> str:
    if persona == "fiber_stable":
        return "NET_BANKING"
    methods = (
        "UPI",
        "UPI",
        "UPI",
        "CREDIT_CARD",
        "DEBIT_CARD",
        "NET_BANKING",
    )
    pick = _month_seed(
        customer_index,
        year,
        month,
    )
    return methods[pick % len(methods)]


def _bill_amount_and_lines(
    customer_index: int,
    customer_id: str,
    plan: tuple,
    year: int,
    month: int,
    subscription_index: int,
    bill_id: str,
) -> tuple[float, list[tuple[str, float, str]]]:
    price = float(plan[2])
    persona = _billing_persona(
        customer_index,
        plan,
    )
    seed = _month_seed(
        customer_index,
        year,
        month,
    )

    charges: list[tuple[str, float, str]] = []

    if (
        customer_index == 2
        and month == 9
        and plan[7] == "MOBILE"
    ):
        charges = [
            (
                "Monthly plan charge",
                price,
                "PLAN_CHARGE",
            ),
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
        return (
            round(sum(c[1] for c in charges), 2),
            charges,
        )

    if (
        customer_index == 10
        and month == 8
        and plan[7] == "MOBILE"
    ):
        charges = [
            (
                "Monthly plan charge",
                price,
                "PLAN_CHARGE",
            ),
            (
                "10 GB data add-on",
                199.0,
                "DATA_ADDON",
            ),
        ]
        return (
            round(sum(c[1] for c in charges), 2),
            charges,
        )

    if (
        customer_index == 17
        and month == 7
        and plan[7] == "MOBILE"
    ):
        charges = [
            (
                "Monthly plan charge",
                price,
                "PLAN_CHARGE",
            ),
            (
                "International calling service",
                149.0,
                "OTHER",
            ),
        ]
        return (
            round(sum(c[1] for c in charges), 2),
            charges,
        )

    if bill_id == "BILL009":
        amount = round(price + 2.0, 2)
        return (
            amount,
            [
                (
                    "Plan rental (incl. GST)",
                    amount,
                    "PLAN_CHARGE",
                ),
            ],
        )

    if bill_id == "BILL010":
        amount = round(price + 149.0, 2)
        return (
            amount,
            [
                (
                    "Monthly charges + 2GB data booster",
                    amount,
                    "PLAN_CHARGE",
                ),
            ],
        )

    if (
        customer_index == 6
        and month == 9
        and plan[7] == "MOBILE"
        and subscription_index == 0
    ):
        amount = 999.0
        return (
            amount,
            [
                (
                    "Plan rental + excess data usage",
                    amount,
                    "PLAN_CHARGE",
                ),
            ],
        )

    amount = price
    description = "Monthly plan charge"

    if persona == "autopay_steady":
        noise = (seed % 5) - 2
        amount = round(price + noise, 2)
        if seed % 11 == 0:
            amount = round(price + 49.0, 2)
            description = "Plan rental + SMS pack (incl. GST)"
        else:
            description = "Plan rental (incl. GST)"

    elif persona == "addon_heavy":
        addons = (0, 99, 149, 199, 249)
        addon = addons[seed % len(addons)]
        amount = round(price + addon, 2)
        if addon:
            description = (
                f"Monthly charges + booster pack (₹{addon:.0f})"
            )
        else:
            description = "Plan rental (incl. GST)"

    elif persona == "fiber_stable":
        amount = price
        if seed % 9 == 0:
            amount = round(price + 99.0, 2)
            description = "Fiber rent + static IP add-on"
        elif seed % 5 == 0:
            description = "Broadband monthly rental (incl. GST)"
        else:
            description = "Fiber plan rental (incl. GST)"

    elif persona == "chronic_late":
        amount = round(price + (seed % 3), 2)
        description = "Plan rental (incl. GST)"

    elif persona == "bill_shock":
        amount = price
        description = "Plan rental (incl. GST)"
        usage_total = USAGE_MONTH_DATA_GB.get(
            (customer_id, year, month),
        )
        if usage_total is not None and usage_total >= 70:
            surcharge = round(
                price * 0.12
                + (seed % 4) * 5,
                2,
            )
            amount = round(price + surcharge, 2)
            description = (
                "Plan rental + excess data usage"
            )
        elif usage_total is not None and usage_total >= 55:
            surcharge = round(price * 0.08, 2)
            amount = round(price + surcharge, 2)
            description = (
                "Monthly charges incl. fair-usage excess"
            )

    elif persona == "churned":
        amount = round(price + (seed % 2), 2)
        description = "Final cycle plan charges"

    elif persona == "roaming_story":
        amount = round(price + (seed % 4), 2)
        description = "Plan rental (incl. GST)"

    total = round(amount, 2)
    return (
        total,
        [
            (
                description,
                total,
                "PLAN_CHARGE",
            ),
        ],
    )


def _bill_status(
    customer_index: int,
    year: int,
    month: int,
    plan: tuple,
    subscription_index: int,
    customer_account_status: str,
) -> str:
    if (
        customer_index == 2
        and month == 9
        and plan[7] == "MOBILE"
    ):
        return "UNPAID"

    if (
        customer_index in (4, 15)
        and month == 9
        and subscription_index == 0
    ):
        return "OVERDUE"

    if (
        customer_index == 6
        and month == 9
        and subscription_index == 0
    ):
        return "PARTIALLY_PAID"

    if (
        customer_index == 8
        and month == 9
        and subscription_index == 0
    ):
        return "UNPAID"

    persona = _billing_persona(
        customer_index,
        plan,
    )
    seed = _month_seed(
        customer_index,
        year,
        month,
    )

    if persona == "chronic_late" and subscription_index == 0:
        if (year, month) in {
            (2026, 3),
            (2026, 7),
            (2025, 12),
        }:
            return "OVERDUE"
        if (year, month) == (2026, 1):
            return "UNPAID"

    if persona == "addon_heavy" and plan[7] == "MOBILE":
        if (year, month) in {
            (2026, 2),
            (2025, 11),
        }:
            return "UNPAID"

    if persona == "churned" and subscription_index == 0:
        months = MONTHS
        if customer_index == 7:
            tail = months[4:5]
        else:
            tail = months[3:4]
        if (year, month) in tail:
            return "UNPAID"

    if persona == "autopay_steady" and seed % 29 == 0:
        return "UNPAID"

    return "PAID"


def _append_payment_for_bill(
    payments: list,
    payment_number: int,
    bill_id: str,
    customer_id: str,
    customer_index: int,
    total: float,
    status: str,
    year: int,
    month: int,
    due_date: str,
    plan: tuple,
) -> int:
    persona = _billing_persona(
        customer_index,
        plan,
    )
    period_end = date(
        year,
        month,
        _last(year, month),
    )
    on_time = (
        period_end + timedelta(days=5)
    ).isoformat() + "T10:30:00"
    late = (
        date.fromisoformat(due_date)
        + timedelta(days=4)
    ).isoformat() + "T18:45:00"

    payment_date = on_time
    if (
        status == "PAID"
        and persona in ("chronic_late", "addon_heavy")
        and _month_seed(customer_index, year, month) % 7 == 0
    ):
        payment_date = late

    if status == "PAID":
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                total,
                payment_date,
                _payment_method_for_bill(
                    customer_index,
                    year,
                    month,
                    persona,
                ),
                "SUCCESS",
                f"TXN2026{payment_number:06d}",
                None,
            )
        )
        return payment_number + 1

    if (
        customer_index == 2
        and month == 9
        and plan[7] == "MOBILE"
    ):
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                total,
                payment_date,
                "CREDIT_CARD",
                "FAILED",
                f"TXN2026{payment_number:06d}",
                "INSUFFICIENT_FUNDS",
            )
        )
        return payment_number + 1

    if (
        customer_index == 6
        and month == 9
    ):
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                round(total * 0.45, 2),
                payment_date,
                "UPI",
                "SUCCESS",
                f"TXN2026{payment_number:06d}",
                None,
            )
        )
        return payment_number + 1

    if (
        customer_index == 8
        and month == 9
    ):
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                total,
                payment_date,
                "NET_BANKING",
                "PENDING",
                f"TXN2026{payment_number:06d}",
                None,
            )
        )
        return payment_number + 1

    if (
        customer_index == 15
        and month == 9
    ):
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                total,
                payment_date,
                "DEBIT_CARD",
                "FAILED",
                f"TXN2026{payment_number:06d}",
                "CARD_DECLINED",
            )
        )
        return payment_number + 1

    if status in ("UNPAID", "OVERDUE"):
        payments.append(
            (
                _id("PAY", payment_number),
                bill_id,
                customer_id,
                total,
                payment_date,
                _payment_method_for_bill(
                    customer_index,
                    year,
                    month,
                    persona,
                ),
                "FAILED",
                f"TXN2026{payment_number:06d}",
                (
                    "INSUFFICIENT_FUNDS"
                    if status == "UNPAID"
                    else "CARD_DECLINED"
                ),
            )
        )
        return payment_number + 1

    return payment_number


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




def _customers() -> list[tuple]:
    rows = []
    for customer in CUSTOMERS:
        customer_id, name, email, phone, city, status, reg_date = customer
        rows.append(
            (
                customer_id,
                name,
                email,
                phone,
                city,
                "",
                "",
                "",
                status,
                reg_date,
            )
        )
    rows[2] = (
        "CUST003",
        "Rohan Kapoor",
        "rohan.kapoor@example.com",
        "+919000000003",
        "Bengaluru",
        "42 MG Road, Indiranagar",
        "Karnataka",
        "560038",
        "ACTIVE",
        "2023-11-10",
    )
    rows[0] = (
        *rows[0][:5],
        "Flat 12B, Andheri West",
        "Maharashtra",
        "400053",
        *rows[0][8:],
    )
    rows[4] = (
        *rows[4][:5],
        "14 Satellite Road",
        "Gujarat",
        "380015",
        *rows[4][8:],
    )
    rows[8] = (
        *rows[8][:5],
        "HITEC City, Phase 2",
        "Telangana",
        "500081",
        *rows[8][8:],
    )
    return rows


def _customer_extensions(connection: sqlite3.Connection) -> None:
    profiles = [
        ("CUST001", 1, "UPI", "Paytm UPI •••• 8821"),
        ("CUST002", 0, "CREDIT_CARD", "Visa credit •••• 4242"),
        ("CUST003", 1, "NET_BANKING", "HDFC NetBanking (autopay)"),
        ("CUST005", 1, "DEBIT_CARD", "SBI debit •••• 9911"),
    ]
    connection.executemany(
        """
        INSERT INTO customer_payment_profiles
        VALUES (?,?,?,?)
        """,
        profiles,
    )
    credits = [
        (
            "CRD001",
            "CUST002",
            150.0,
            "SR#NX-2026-0918 goodwill — roaming dispute",
            "2026-09-20",
            "AVAILABLE",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO account_credits
        VALUES (?,?,?,?,?,?)
        """,
        credits,
    )


def _id(prefix: str, number: int) -> str:
    return f"{prefix}{number:03d}"


def _last(year: int, month: int) -> int:
    return monthrange(year, month)[1]


def seed_database(
    connection: sqlite3.Connection,
    reset: bool = False,
) -> None:
    USAGE_MONTH_DATA_GB.clear()
    initialize_database(connection, reset=reset)

    connection.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?)",
        _customers(),
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

    for customer_id, (
        mobile_plan_id,
        activation_date,
    ) in MULTI_SUBSCRIPTION_CUSTOMERS.items():
        subscriptions.append(
            (
                f"{customer_id}M",
                customer_id,
                mobile_plan_id,
                activation_date,
                "ACTIVE",
                "2026-10-15",
            )
        )

    connection.executemany(
        "INSERT INTO subscriptions VALUES (?,?,?,?,?,?)",
        subscriptions,
    )

    _usage(connection, subscriptions)
    _billing(connection, subscriptions)
    _tickets(connection)
    _ticket_updates(connection)
    _devices(connection)
    _customer_extensions(connection)

    connection.commit()


def _usage(
    connection: sqlite3.Connection,
    subscriptions: list[tuple],
) -> None:
    rows = []
    usage_number = 1

    customer_index_by_id = {
        customer[0]: index
        for index, customer in enumerate(
            CUSTOMERS,
            1,
        )
    }

    for subscription in subscriptions:
        customer_index = customer_index_by_id[
            subscription[1]
        ]
        plan = PLAN_BY_ID[subscription[2]]
        pattern = PATTERNS[customer_index - 1]

        if plan[7] == "FIBER":
            pattern = "fiber"

        for month_index, (year, month) in enumerate(MONTHS):
            if pattern == "cancelled" and month_index >= 5:
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
                    "declining": max(
                        12,
                        48 - month_index * 3,
                    ),
                    "spike": (
                        35
                        if month != 8
                        else 68
                    ),
                    "cancelled": 26,
                }.get(pattern, 30)

            # Demo customer CUST006 has a deliberate
            # month-over-month heavy usage pattern.
            if (
                customer_index == 6
                and plan[7] == "MOBILE"
            ):
                canonical_month_totals = {
                    (2026, 4): 61,
                    (2026, 5): 68,
                    (2026, 6): 74,
                    (2026, 7): 81,
                    (2026, 8): 88,
                    (2026, 9): 94,
                    (2026, 10): 97,
                }

                total = canonical_month_totals.get(
                    (year, month),
                    [
                        45,
                        52,
                        58,
                        61,
                        68,
                        74,
                        81,
                        88,
                        90,
                        92,
                        93,
                        95,
                        97,
                    ][month_index],
                )

            USAGE_MONTH_DATA_GB[
                (subscription[1], year, month)
            ] = float(total)

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


def _billing(
    connection: sqlite3.Connection,
    subscriptions: list[tuple],
) -> None:
    bills = []
    items = []
    payments = []

    bill_number = 1
    item_number = 1
    payment_number = 1

    subscriptions_by_customer: dict[
        str,
        list[tuple],
    ] = {}

    for subscription in subscriptions:
        subscriptions_by_customer.setdefault(
            subscription[1],
            [],
        ).append(subscription)

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

        customer_subscriptions = (
            subscriptions_by_customer.get(
                customer[0],
                [],
            )
        )

        for subscription_index, subscription in enumerate(
            customer_subscriptions,
        ):
            subscription_id = subscription[0]
            plan = PLAN_BY_ID[subscription[2]]

            for month_index, (year, month) in enumerate(
                months,
            ):
                if (
                    customer_index in (2, 5, 6)
                    and (year, month) == (2026, 10)
                    and plan[7] == "MOBILE"
                    and subscription_index == 0
                ):
                    continue

                if (
                    customer_index == 5
                    and subscription_index == 0
                    and month_index == 10
                ):
                    bill_id = "BILL009"

                elif (
                    customer_index == 5
                    and subscription_index == 0
                    and month_index == 11
                ):
                    bill_id = "BILL010"

                elif (
                    customer_index == 2
                    and subscription_index == 0
                    and (year, month) == (2026, 9)
                    and plan[7] == "MOBILE"
                ):
                    bill_id = "BILL027"

                else:
                    while _id(
                        "BILL",
                        bill_number,
                    ) in RESERVED_BILL_IDS:
                        bill_number += 1

                    bill_id = _id("BILL", bill_number)
                    bill_number += 1

                total, charges = _bill_amount_and_lines(
                    customer_index,
                    customer[0],
                    plan,
                    year,
                    month,
                    subscription_index,
                    bill_id,
                )

                status = _bill_status(
                    customer_index,
                    year,
                    month,
                    plan,
                    subscription_index,
                    customer[5],
                )

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
                        subscription_id,
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

                payment_number = _append_payment_for_bill(
                    payments,
                    payment_number,
                    bill_id,
                    customer[0],
                    customer_index,
                    total,
                    status,
                    year,
                    month,
                    due_date,
                    plan,
                )

        if customer_index == 9:
            target = [
                bill
                for bill in bills
                if bill[1] == customer[0]
                and bill[3] == "2026-06-01"
            ][0]

            payments.append(
                (
                    _id("PAY", payment_number),
                    target[0],
                    customer[0],
                    target[5],
                    "2026-07-02T09:15:00",
                    "CREDIT_CARD",
                    "FAILED",
                    f"TXN2026{payment_number:06d}",
                    "BANK_TIMEOUT",
                )
            )

            payment_number += 1

    connection.executemany(
        "INSERT INTO bills VALUES (?,?,?,?,?,?,?,?)",
        bills,
    )

    connection.executemany(
        "INSERT INTO bill_items VALUES (?,?,?,?,?)",
        items,
    )

    connection.executemany(
        "INSERT INTO payments VALUES (?,?,?,?,?,?,?,?,?)",
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
                    "SR#NX-2026-4412: Bill dispute — "
                    "unexpected international roaming on "
                    "September invoice."
                ),
                "OPEN",
                "HIGH",
                "2026-09-18T10:00:00",
                "2026-09-18T12:30:00",
            ),
            (
                "NETWORK",
                (
                    "SR#NX-2026-2287: Mobile data drops "
                    "while travelling (4G handoff)."
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
                (
                    "SR#NX-2026-5103: Auto-debit failed; "
                    "September bill overdue on suspended line."
                ),
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
            related_bill = None
            related_payment = None
            if (
                customer_index == 2
                and entry[0] == "BILLING"
            ):
                related_bill = "BILL027"
                related_payment = "PAY025"
            rows.append(
                (
                    _id("TKT", ticket_number),
                    customer[0],
                    *entry,
                    related_bill,
                    related_payment,
                )
            )
            ticket_number += 1

    connection.executemany(
        """
        INSERT INTO support_tickets
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )


def _ticket_updates(
    connection: sqlite3.Connection,
) -> None:
    rows = [
        (
            "UPD001",
            "TKT003",
            "CUST002",
            "2026-06-11T09:00:00",
            "OPEN",
            "Ticket opened for intermittent mobile data.",
        ),
        (
            "UPD002",
            "TKT003",
            "CUST002",
            "2026-06-11T14:30:00",
            "IN_PROGRESS",
            "Network team investigating tower handoff.",
        ),
        (
            "UPD003",
            "TKT003",
            "CUST002",
            "2026-06-12T16:00:00",
            "RESOLVED",
            "Roaming profile refreshed; data restored.",
        ),
    ]

    connection.executemany(
        """
        INSERT INTO support_ticket_updates
        VALUES (?,?,?,?,?,?)
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
        "support_ticket_updates",
        "support_tickets",
        "payments",
        "bill_items",
        "bills",
        "usage",
        "subscriptions",
        "plans",
        "customer_payment_profiles",
        "account_credits",
        "customers",
    ]

    for table in tables:
        connection.execute(
            f"DROP TABLE IF EXISTS {table}"
        )

    connection.commit()