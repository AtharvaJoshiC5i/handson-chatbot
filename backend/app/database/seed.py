from pathlib import Path
import sqlite3


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _insert_customers(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO customers (
            customer_id,
            name,
            email,
            phone_number,
            city,
            account_status,
            registration_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "CUST001",
                "Aarav Sharma",
                "aarav.sharma@nexatel.example",
                "+919810000001",
                "Mumbai",
                "ACTIVE",
                "2024-02-15",
            ),
            (
                "CUST002",
                "Diya Mehta",
                "diya.mehta@nexatel.example",
                "+919810000002",
                "Pune",
                "ACTIVE",
                "2024-06-20",
            ),
            (
                "CUST003",
                "Rohan Kapoor",
                "rohan.kapoor@nexatel.example",
                "+919810000003",
                "Bengaluru",
                "ACTIVE",
                "2023-11-10",
            ),
            (
                "CUST004",
                "Ananya Iyer",
                "ananya.iyer@nexatel.example",
                "+919810000004",
                "Delhi",
                "SUSPENDED",
                "2023-05-03",
            ),
            (
                "CUST005",
                "Kabir Patel",
                "kabir.patel@nexatel.example",
                "+919810000005",
                "Ahmedabad",
                "ACTIVE",
                "2025-01-18",
            ),
            (
                "CUST006",
                "Meera Nair",
                "meera.nair@nexatel.example",
                "+919810000006",
                "Chennai",
                "ACTIVE",
                "2025-03-22",
            ),
            (
                "CUST007",
                "Vikram Singh",
                "vikram.singh@nexatel.example",
                "+919810000007",
                "Jaipur",
                "CANCELLED",
                "2024-08-14",
            ),
            (
                "CUST008",
                "Ishita Rao",
                "ishita.rao@nexatel.example",
                "+919810000008",
                "Hyderabad",
                "ACTIVE",
                "2025-07-09",
            ),
        ],
    )


def _insert_plans(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO plans (
            plan_id,
            plan_name,
            monthly_price,
            data_limit_gb,
            voice_limit_minutes,
            sms_limit,
            plan_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "PLAN001",
                "NexaMax 499",
                499.00,
                40.0,
                1000,
                100,
                "MOBILE",
            ),
            (
                "PLAN002",
                "NexaMax 799",
                799.00,
                75.0,
                2000,
                200,
                "MOBILE",
            ),
            (
                "PLAN003",
                "NexaMax 999",
                999.00,
                100.0,
                3000,
                300,
                "MOBILE",
            ),
            (
                "PLAN004",
                "NexaFiber 699",
                699.00,
                0.0,
                0,
                0,
                "FIBER",
            ),
            (
                "PLAN005",
                "NexaFiber 999",
                999.00,
                0.0,
                0,
                0,
                "FIBER",
            ),
            (
                "PLAN006",
                "NexaMax 1499",
                1499.00,
                200.0,
                5000,
                500,
                "MOBILE",
            ),
            (
                "PLAN007",
                "NexaFiber 1299",
                1299.00,
                0.0,
                0,
                0,
                "FIBER",
            ),
        ],
    )


def _insert_subscriptions(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO subscriptions (
            subscription_id,
            customer_id,
            plan_id,
            activation_date,
            status,
            renewal_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "SUB001",
                "CUST001",
                "PLAN002",
                "2025-08-10",
                "ACTIVE",
                "2026-10-10",
            ),
            (
                "SUB002",
                "CUST002",
                "PLAN002",
                "2025-11-05",
                "ACTIVE",
                "2026-10-05",
            ),
            (
                "SUB003",
                "CUST003",
                "PLAN005",
                "2024-12-01",
                "ACTIVE",
                "2026-10-01",
            ),
            (
                "SUB004",
                "CUST004",
                "PLAN003",
                "2024-01-15",
                "SUSPENDED",
                "2026-10-15",
            ),
            (
                "SUB005",
                "CUST005",
                "PLAN001",
                "2025-02-01",
                "ACTIVE",
                "2026-10-01",
            ),
            (
                "SUB006",
                "CUST006",
                "PLAN006",
                "2025-04-01",
                "ACTIVE",
                "2026-10-01",
            ),
            (
                "SUB007",
                "CUST007",
                "PLAN001",
                "2024-08-14",
                "CANCELLED",
                "2025-09-14",
            ),
            (
                "SUB008",
                "CUST008",
                "PLAN007",
                "2025-07-09",
                "ACTIVE",
                "2026-10-09",
            ),
        ],
    )


def _insert_usage(connection: sqlite3.Connection) -> None:
    usage_rows = [
        # ------------------------------------------------------
        # CUST001 - Normal usage
        # ------------------------------------------------------
        (
            "USE001",
            "CUST001",
            "SUB001",
            "2026-09-01",
            1.8,
            42,
            4,
        ),
        (
            "USE002",
            "CUST001",
            "SUB001",
            "2026-09-05",
            2.1,
            55,
            7,
        ),
        (
            "USE003",
            "CUST001",
            "SUB001",
            "2026-09-10",
            1.4,
            38,
            3,
        ),
        (
            "USE004",
            "CUST001",
            "SUB001",
            "2026-09-15",
            2.7,
            62,
            6,
        ),
        (
            "USE005",
            "CUST001",
            "SUB001",
            "2026-09-20",
            3.2,
            71,
            5,
        ),
        (
            "USE006",
            "CUST001",
            "SUB001",
            "2026-08-05",
            2.0,
            44,
            4,
        ),
        (
            "USE007",
            "CUST001",
            "SUB001",
            "2026-08-12",
            1.7,
            51,
            5,
        ),
        (
            "USE008",
            "CUST001",
            "SUB001",
            "2026-08-20",
            2.4,
            48,
            6,
        ),

        # ------------------------------------------------------
        # CUST002 - High usage
        # ------------------------------------------------------
        (
            "USE009",
            "CUST002",
            "SUB002",
            "2026-09-01",
            6.5,
            85,
            8,
        ),
        (
            "USE010",
            "CUST002",
            "SUB002",
            "2026-09-04",
            7.2,
            91,
            9,
        ),
        (
            "USE011",
            "CUST002",
            "SUB002",
            "2026-09-08",
            8.1,
            73,
            7,
        ),
        (
            "USE012",
            "CUST002",
            "SUB002",
            "2026-09-12",
            6.8,
            88,
            11,
        ),
        (
            "USE013",
            "CUST002",
            "SUB002",
            "2026-09-16",
            7.9,
            96,
            10,
        ),
        (
            "USE014",
            "CUST002",
            "SUB002",
            "2026-09-20",
            9.3,
            105,
            12,
        ),
        (
            "USE015",
            "CUST002",
            "SUB002",
            "2026-08-05",
            5.8,
            70,
            8,
        ),
        (
            "USE016",
            "CUST002",
            "SUB002",
            "2026-08-15",
            6.4,
            76,
            9,
        ),

        # ------------------------------------------------------
        # CUST003 - Fiber customer
        # ------------------------------------------------------
        (
            "USE017",
            "CUST003",
            "SUB003",
            "2026-09-01",
            3.4,
            0,
            0,
        ),
        (
            "USE018",
            "CUST003",
            "SUB003",
            "2026-09-10",
            4.1,
            0,
            0,
        ),
        (
            "USE019",
            "CUST003",
            "SUB003",
            "2026-09-20",
            5.0,
            0,
            0,
        ),

        # ------------------------------------------------------
        # CUST004 - Suspended customer
        # ------------------------------------------------------
        (
            "USE020",
            "CUST004",
            "SUB004",
            "2026-08-01",
            4.8,
            82,
            7,
        ),
        (
            "USE021",
            "CUST004",
            "SUB004",
            "2026-08-10",
            5.1,
            90,
            8,
        ),

        # ------------------------------------------------------
        # CUST005 - Multiple-history customer
        # ------------------------------------------------------
        (
            "USE022",
            "CUST005",
            "SUB005",
            "2026-09-03",
            1.2,
            31,
            2,
        ),
        (
            "USE023",
            "CUST005",
            "SUB005",
            "2026-09-09",
            1.8,
            45,
            4,
        ),
        (
            "USE024",
            "CUST005",
            "SUB005",
            "2026-09-17",
            2.1,
            52,
            5,
        ),
        (
            "USE025",
            "CUST005",
            "SUB005",
            "2026-08-03",
            1.5,
            39,
            3,
        ),
        (
            "USE026",
            "CUST005",
            "SUB005",
            "2026-07-08",
            1.1,
            34,
            2,
        ),

        # ------------------------------------------------------
        # CUST006 - Premium mobile customer with high current usage
        # ------------------------------------------------------
        (
            "USE027",
            "CUST006",
            "SUB006",
            "2026-09-02",
            18.5,
            210,
            24,
        ),
        (
            "USE028",
            "CUST006",
            "SUB006",
            "2026-09-12",
            22.0,
            265,
            31,
        ),
        (
            "USE029",
            "CUST006",
            "SUB006",
            "2026-09-22",
            20.4,
            198,
            27,
        ),
        (
            "USE030",
            "CUST006",
            "SUB006",
            "2026-08-08",
            16.2,
            240,
            25,
        ),
        (
            "USE031",
            "CUST006",
            "SUB006",
            "2026-08-18",
            19.1,
            230,
            29,
        ),

        # ------------------------------------------------------
        # CUST007 - Cancelled account history
        # ------------------------------------------------------
        (
            "USE032",
            "CUST007",
            "SUB007",
            "2025-08-10",
            3.2,
            64,
            5,
        ),

        # ------------------------------------------------------
        # CUST008 - Fiber customer with no mobile usage
        # ------------------------------------------------------
        (
            "USE033",
            "CUST008",
            "SUB008",
            "2026-09-03",
            8.0,
            0,
            0,
        ),
        (
            "USE034",
            "CUST008",
            "SUB008",
            "2026-09-15",
            9.4,
            0,
            0,
        ),
        (
            "USE035",
            "CUST008",
            "SUB008",
            "2026-08-12",
            7.7,
            0,
            0,
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO usage (
            usage_id,
            customer_id,
            subscription_id,
            usage_date,
            data_used_gb,
            voice_minutes,
            sms_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        usage_rows,
    )


def _insert_bills(connection: sqlite3.Connection) -> None:
    bills = [
        # CUST001 - paid current bill
        (
            "BILL001",
            "CUST001",
            "2026-09-01",
            "2026-09-30",
            799.00,
            "2026-10-05",
            "PAID",
        ),
        (
            "BILL002",
            "CUST001",
            "2026-08-01",
            "2026-08-31",
            799.00,
            "2026-09-05",
            "PAID",
        ),

        # CUST002 - unpaid current bill with roaming
        (
            "BILL003",
            "CUST002",
            "2026-09-01",
            "2026-09-30",
            1143.00,
            "2026-09-25",
            "UNPAID",
        ),
        (
            "BILL004",
            "CUST002",
            "2026-08-01",
            "2026-08-31",
            799.00,
            "2026-09-05",
            "PAID",
        ),

        # CUST003 - fiber bill
        (
            "BILL005",
            "CUST003",
            "2026-09-01",
            "2026-09-30",
            1042.00,
            "2026-10-01",
            "UNPAID",
        ),
        (
            "BILL006",
            "CUST003",
            "2026-08-01",
            "2026-08-31",
            999.00,
            "2026-09-01",
            "PAID",
        ),

        # CUST004 - overdue
        (
            "BILL007",
            "CUST004",
            "2026-08-01",
            "2026-08-31",
            1199.00,
            "2026-08-20",
            "OVERDUE",
        ),
        (
            "BILL008",
            "CUST004",
            "2026-07-01",
            "2026-07-31",
            999.00,
            "2026-08-05",
            "PAID",
        ),

        # CUST005 - multiple history records
        (
            "BILL009",
            "CUST005",
            "2026-09-01",
            "2026-09-30",
            499.00,
            "2026-10-01",
            "PAID",
        ),
        (
            "BILL010",
            "CUST005",
            "2026-08-01",
            "2026-08-31",
            499.00,
            "2026-09-01",
            "PAID",
        ),
        (
            "BILL011",
            "CUST005",
            "2026-07-01",
            "2026-07-31",
            649.00,
            "2026-08-01",
            "PAID",
        ),
        (
            "BILL012",
            "CUST005",
            "2026-06-01",
            "2026-06-30",
            499.00,
            "2026-07-01",
            "PAID",
        ),
        # CUST006 - partially paid current bill
        (
            "BILL013",
            "CUST006",
            "2026-09-01",
            "2026-09-30",
            1749.00,
            "2026-10-01",
            "PARTIALLY_PAID",
        ),
        (
            "BILL014",
            "CUST006",
            "2026-08-01",
            "2026-08-31",
            1499.00,
            "2026-09-01",
            "PAID",
        ),
        # CUST007 - final historical bill
        (
            "BILL015",
            "CUST007",
            "2025-08-01",
            "2025-08-31",
            499.00,
            "2025-09-01",
            "PAID",
        ),
        # CUST008 - current unpaid fiber bill
        (
            "BILL016",
            "CUST008",
            "2026-09-01",
            "2026-09-30",
            1342.00,
            "2026-10-09",
            "UNPAID",
        ),
        (
            "BILL017",
            "CUST008",
            "2026-08-01",
            "2026-08-31",
            1299.00,
            "2026-09-09",
            "PAID",
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO bills (
            bill_id,
            customer_id,
            billing_period_start,
            billing_period_end,
            amount,
            due_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        bills,
    )


def _insert_bill_items(connection: sqlite3.Connection) -> None:
    bill_items = [
        # CUST001
        (
            "ITEM001",
            "BILL001",
            "NexaMax 799 monthly plan",
            799.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM002",
            "BILL002",
            "NexaMax 799 monthly plan",
            799.00,
            "PLAN_CHARGE",
        ),

        # CUST002 - intentionally explainable ₹1,143 bill
        (
            "ITEM003",
            "BILL003",
            "NexaMax 799 monthly plan",
            799.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM004",
            "BILL003",
            "International roaming usage",
            301.00,
            "ROAMING",
        ),
        (
            "ITEM005",
            "BILL003",
            "Applicable taxes",
            43.00,
            "TAX",
        ),
        (
            "ITEM006",
            "BILL004",
            "NexaMax 799 monthly plan",
            799.00,
            "PLAN_CHARGE",
        ),

        # CUST003
        (
            "ITEM007",
            "BILL005",
            "NexaFiber 999 monthly plan",
            999.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM008",
            "BILL005",
            "Applicable taxes",
            43.00,
            "TAX",
        ),
        (
            "ITEM009",
            "BILL006",
            "NexaFiber 999 monthly plan",
            999.00,
            "PLAN_CHARGE",
        ),

        # CUST004
        (
            "ITEM010",
            "BILL007",
            "NexaMax 999 monthly plan",
            999.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM011",
            "BILL007",
            "Additional service charge",
            200.00,
            "OTHER",
        ),
        (
            "ITEM012",
            "BILL008",
            "NexaMax 999 monthly plan",
            999.00,
            "PLAN_CHARGE",
        ),

        # CUST005
        (
            "ITEM013",
            "BILL009",
            "NexaMax 499 monthly plan",
            499.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM014",
            "BILL010",
            "NexaMax 499 monthly plan",
            499.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM015",
            "BILL011",
            "NexaMax 499 monthly plan",
            499.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM016",
            "BILL011",
            "Data add-on",
            150.00,
            "DATA_ADDON",
        ),
        (
            "ITEM017",
            "BILL012",
            "NexaMax 499 monthly plan",
            499.00,
            "PLAN_CHARGE",
        ),
        # CUST006
        (
            "ITEM018",
            "BILL013",
            "NexaMax 1499 monthly plan",
            1499.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM019",
            "BILL013",
            "International roaming usage",
            200.00,
            "ROAMING",
        ),
        (
            "ITEM020",
            "BILL013",
            "Applicable taxes",
            50.00,
            "TAX",
        ),
        (
            "ITEM021",
            "BILL014",
            "NexaMax 1499 monthly plan",
            1499.00,
            "PLAN_CHARGE",
        ),
        # CUST007
        (
            "ITEM022",
            "BILL015",
            "NexaMax 499 monthly plan",
            499.00,
            "PLAN_CHARGE",
        ),
        # CUST008
        (
            "ITEM023",
            "BILL016",
            "NexaFiber 1299 monthly plan",
            1299.00,
            "PLAN_CHARGE",
        ),
        (
            "ITEM024",
            "BILL016",
            "Applicable taxes",
            43.00,
            "TAX",
        ),
        (
            "ITEM025",
            "BILL017",
            "NexaFiber 1299 monthly plan",
            1299.00,
            "PLAN_CHARGE",
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO bill_items (
            bill_item_id,
            bill_id,
            description,
            amount,
            item_type
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        bill_items,
    )


def _insert_payments(connection: sqlite3.Connection) -> None:
    payments = [
        # CUST001
        (
            "PAY001",
            "BILL001",
            "CUST001",
            799.00,
            "2026-09-03T10:15:00",
            "UPI",
            "SUCCESS",
            "TXN-C001-0001",
        ),
        (
            "PAY002",
            "BILL002",
            "CUST001",
            799.00,
            "2026-08-04T09:30:00",
            "CREDIT_CARD",
            "SUCCESS",
            "TXN-C001-0002",
        ),

        # CUST002
        (
            "PAY003",
            "BILL004",
            "CUST002",
            799.00,
            "2026-08-28T14:20:00",
            "UPI",
            "SUCCESS",
            "TXN-C002-0001",
        ),
        (
            "PAY004",
            "BILL003",
            "CUST002",
            1143.00,
            "2026-09-22T11:45:00",
            "UPI",
            "FAILED",
            "TXN-C002-0002",
        ),

        # CUST003
        (
            "PAY005",
            "BILL006",
            "CUST003",
            999.00,
            "2026-08-30T16:00:00",
            "NET_BANKING",
            "SUCCESS",
            "TXN-C003-0001",
        ),

        # CUST004
        (
            "PAY006",
            "BILL008",
            "CUST004",
            999.00,
            "2026-08-04T10:00:00",
            "DEBIT_CARD",
            "SUCCESS",
            "TXN-C004-0001",
        ),
        (
            "PAY007",
            "BILL007",
            "CUST004",
            500.00,
            "2026-08-21T12:00:00",
            "DEBIT_CARD",
            "SUCCESS",
            "TXN-C004-0002",
        ),

        # CUST005 - deliberately multiple payment history
        (
            "PAY008",
            "BILL009",
            "CUST005",
            499.00,
            "2026-09-02T09:10:00",
            "UPI",
            "SUCCESS",
            "TXN-C005-0001",
        ),
        (
            "PAY009",
            "BILL010",
            "CUST005",
            499.00,
            "2026-08-02T09:30:00",
            "CREDIT_CARD",
            "SUCCESS",
            "TXN-C005-0002",
        ),
        (
            "PAY010",
            "BILL011",
            "CUST005",
            649.00,
            "2026-07-03T13:20:00",
            "UPI",
            "SUCCESS",
            "TXN-C005-0003",
        ),
        (
            "PAY011",
            "BILL012",
            "CUST005",
            499.00,
            "2026-06-04T15:40:00",
            "NET_BANKING",
            "SUCCESS",
            "TXN-C005-0004",
        ),
        (
            "PAY012",
            "BILL011",
            "CUST005",
            100.00,
            "2026-07-02T11:00:00",
            "UPI",
            "FAILED",
            "TXN-C005-0005",
        ),
        # CUST006
        (
            "PAY013",
            "BILL014",
            "CUST006",
            1499.00,
            "2026-08-28T10:20:00",
            "CREDIT_CARD",
            "SUCCESS",
            "TXN-C006-0001",
        ),
        (
            "PAY014",
            "BILL013",
            "CUST006",
            1000.00,
            "2026-09-25T17:05:00",
            "UPI",
            "PENDING",
            "TXN-C006-0002",
        ),
        # CUST007
        (
            "PAY015",
            "BILL015",
            "CUST007",
            499.00,
            "2025-08-30T13:00:00",
            "NET_BANKING",
            "SUCCESS",
            "TXN-C007-0001",
        ),
        # CUST008
        (
            "PAY016",
            "BILL017",
            "CUST008",
            1299.00,
            "2026-09-07T11:45:00",
            "DEBIT_CARD",
            "SUCCESS",
            "TXN-C008-0001",
        ),
    ]

    connection.executemany(
        """
        INSERT OR IGNORE INTO payments (
            payment_id,
            bill_id,
            customer_id,
            amount,
            payment_date,
            payment_method,
            status,
            transaction_reference
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payments,
    )


def _insert_support_tickets(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO support_tickets (
            ticket_id,
            customer_id,
            category,
            description,
            status,
            priority,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "TICKET001",
                "CUST001",
                "PLAN",
                "Customer requested information about plan benefits.",
                "RESOLVED",
                "LOW",
                "2026-08-10T10:00:00",
                "2026-08-11T15:30:00",
            ),
            (
                "TICKET002",
                "CUST002",
                "BILLING",
                "Customer asked about unexpected roaming charges.",
                "IN_PROGRESS",
                "HIGH",
                "2026-09-21T09:15:00",
                "2026-09-22T10:30:00",
            ),
            (
                "TICKET003",
                "CUST003",
                "BROADBAND",
                "Intermittent broadband connectivity reported.",
                "OPEN",
                "HIGH",
                "2026-09-20T08:45:00",
                "2026-09-21T14:10:00",
            ),
            (
                "TICKET004",
                "CUST004",
                "PAYMENT",
                "Customer reported an issue with an overdue payment.",
                "OPEN",
                "CRITICAL",
                "2026-08-21T12:30:00",
                "2026-08-22T09:00:00",
            ),
            (
                "TICKET005",
                "CUST005",
                "PLAN",
                "Customer asked about upgrading the current plan.",
                "CLOSED",
                "LOW",
                "2026-07-12T11:00:00",
                "2026-07-13T16:00:00",
            ),
            (
                "TICKET006",
                "CUST006",
                "NETWORK",
                "Customer reported intermittent 5G connectivity while travelling.",
                "OPEN",
                "MEDIUM",
                "2026-09-23T09:00:00",
                "2026-09-23T09:00:00",
            ),
            (
                "TICKET007",
                "CUST007",
                "OTHER",
                "Customer requested account closure confirmation.",
                "RESOLVED",
                "MEDIUM",
                "2025-09-02T10:00:00",
                "2025-09-03T12:00:00",
            ),
            (
                "TICKET008",
                "CUST008",
                "BROADBAND",
                "Customer asked about a brief evening service interruption.",
                "IN_PROGRESS",
                "HIGH",
                "2026-09-22T18:30:00",
                "2026-09-23T08:15:00",
            ),
        ],
    )


def _insert_devices(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO devices (
            device_id,
            customer_id,
            device_name,
            device_type,
            purchase_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "DEV001",
                "CUST001",
                "NexaPhone X1",
                "SMARTPHONE",
                "2025-09-12",
                "ACTIVE",
            ),
            (
                "DEV002",
                "CUST002",
                "NexaPhone Pro 5G",
                "SMARTPHONE",
                "2025-12-03",
                "ACTIVE",
            ),
            (
                "DEV003",
                "CUST003",
                "NexaFiber Router AX",
                "ROUTER",
                "2024-12-01",
                "ACTIVE",
            ),
            (
                "DEV004",
                "CUST004",
                "NexaPhone Z",
                "SMARTPHONE",
                "2024-02-15",
                "INACTIVE",
            ),
            (
                "DEV005",
                "CUST005",
                "NexaPhone Lite",
                "SMARTPHONE",
                "2025-03-10",
                "ACTIVE",
            ),
            (
                "DEV006",
                "CUST005",
                "NexaFiber Mini Router",
                "ROUTER",
                "2025-04-01",
                "ACTIVE",
            ),
            (
                "DEV007",
                "CUST006",
                "NexaPhone Ultra 5G",
                "SMARTPHONE",
                "2025-04-02",
                "ACTIVE",
            ),
            (
                "DEV008",
                "CUST007",
                "NexaPhone S",
                "SMARTPHONE",
                "2024-08-15",
                "REPLACED",
            ),
            (
                "DEV009",
                "CUST008",
                "NexaFiber Router Pro",
                "ROUTER",
                "2025-07-10",
                "ACTIVE",
            ),
        ],
    )


def initialize_database(
    connection: sqlite3.Connection,
    *,
    reset: bool = False,
) -> None:
    """
    Create the NexaTel schema and optionally seed the database.

    reset=True removes existing application tables before recreating
    the database. This is intended for deterministic development and
    testing only.
    """

    if reset:
        _drop_tables(connection)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)

    connection.commit()


def seed_database(
    connection: sqlite3.Connection,
    *,
    reset: bool = False,
) -> None:
    """
    Initialize and populate the deterministic NexaTel dataset.
    """

    initialize_database(
        connection,
        reset=reset,
    )

    try:
        _insert_customers(connection)
        _insert_plans(connection)
        _insert_subscriptions(connection)
        _insert_usage(connection)
        _insert_bills(connection)
        _insert_bill_items(connection)
        _insert_payments(connection)
        _insert_support_tickets(connection)
        _insert_devices(connection)

        connection.commit()

    except Exception:
        connection.rollback()
        raise


def _drop_tables(connection: sqlite3.Connection) -> None:
    """
    Drop all NexaTel application tables.

    This is intentionally restricted to the known application tables.
    """

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
        connection.execute(f"DROP TABLE IF EXISTS {table}")

    connection.commit()