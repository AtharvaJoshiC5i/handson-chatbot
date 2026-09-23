PRAGMA foreign_keys = ON;


-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone_number TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    account_status TEXT NOT NULL
        CHECK (account_status IN (
            'ACTIVE',
            'SUSPENDED',
            'CANCELLED'
        )),
    registration_date TEXT NOT NULL
);


-- ============================================================
-- PLANS
-- ============================================================

CREATE TABLE IF NOT EXISTS plans (
    plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL UNIQUE,
    monthly_price REAL NOT NULL CHECK (monthly_price >= 0),
    data_limit_gb REAL NOT NULL CHECK (data_limit_gb >= 0),
    voice_limit_minutes INTEGER NOT NULL CHECK (voice_limit_minutes >= 0),
    sms_limit INTEGER NOT NULL CHECK (sms_limit >= 0),
    plan_type TEXT NOT NULL
);


-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    activation_date TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'ACTIVE',
            'INACTIVE',
            'CANCELLED',
            'SUSPENDED'
        )),
    renewal_date TEXT NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id)
);


-- ============================================================
-- USAGE
-- ============================================================

CREATE TABLE IF NOT EXISTS usage (
    usage_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    subscription_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    data_used_gb REAL NOT NULL CHECK (data_used_gb >= 0),
    voice_minutes INTEGER NOT NULL CHECK (voice_minutes >= 0),
    sms_count INTEGER NOT NULL CHECK (sms_count >= 0),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id)
);


-- ============================================================
-- BILLS
-- ============================================================

CREATE TABLE IF NOT EXISTS bills (
    bill_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    billing_period_start TEXT NOT NULL,
    billing_period_end TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    due_date TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'PAID',
            'UNPAID',
            'OVERDUE',
            'PARTIALLY_PAID'
        )),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CHECK (billing_period_end >= billing_period_start)
);


-- ============================================================
-- BILL ITEMS
-- ============================================================

CREATE TABLE IF NOT EXISTS bill_items (
    bill_item_id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    item_type TEXT NOT NULL
        CHECK (item_type IN (
            'PLAN_CHARGE',
            'ROAMING',
            'DATA_ADDON',
            'TAX',
            'OTHER'
        )),

    FOREIGN KEY (bill_id)
        REFERENCES bills(bill_id)
        ON DELETE CASCADE
);


-- ============================================================
-- PAYMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount >= 0),
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL
        CHECK (payment_method IN (
            'UPI',
            'CREDIT_CARD',
            'DEBIT_CARD',
            'NET_BANKING'
        )),
    status TEXT NOT NULL
        CHECK (status IN (
            'SUCCESS',
            'FAILED',
            'PENDING'
        )),
    transaction_reference TEXT NOT NULL UNIQUE,

    FOREIGN KEY (bill_id)
        REFERENCES bills(bill_id),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


-- ============================================================
-- SUPPORT TICKETS
-- ============================================================

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    category TEXT NOT NULL
        CHECK (category IN (
            'BILLING',
            'NETWORK',
            'BROADBAND',
            'PAYMENT',
            'PLAN',
            'OTHER'
        )),
    description TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'OPEN',
            'IN_PROGRESS',
            'RESOLVED',
            'CLOSED'
        )),
    priority TEXT NOT NULL
        CHECK (priority IN (
            'LOW',
            'MEDIUM',
            'HIGH',
            'CRITICAL'
        )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


-- ============================================================
-- DEVICES
-- ============================================================

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    purchase_date TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'ACTIVE',
            'INACTIVE',
            'REPLACED',
            'LOST'
        )),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
    ON subscriptions(customer_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_plan
    ON subscriptions(plan_id);

CREATE INDEX IF NOT EXISTS idx_usage_customer_date
    ON usage(customer_id, usage_date);

CREATE INDEX IF NOT EXISTS idx_usage_subscription
    ON usage(subscription_id);

CREATE INDEX IF NOT EXISTS idx_bills_customer_period
    ON bills(customer_id, billing_period_end);

CREATE INDEX IF NOT EXISTS idx_bill_items_bill
    ON bill_items(bill_id);

CREATE INDEX IF NOT EXISTS idx_payments_customer_date
    ON payments(customer_id, payment_date);

CREATE INDEX IF NOT EXISTS idx_payments_bill
    ON payments(bill_id);

CREATE INDEX IF NOT EXISTS idx_support_tickets_customer_status
    ON support_tickets(customer_id, status);

CREATE INDEX IF NOT EXISTS idx_devices_customer
    ON devices(customer_id);