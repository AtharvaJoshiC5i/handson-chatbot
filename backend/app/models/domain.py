from datetime import date, datetime
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class BillStatus(str, Enum):
    PAID = "PAID"
    UNPAID = "UNPAID"
    OVERDUE = "OVERDUE"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class PaymentAggregateType(str, Enum):
    TOTAL_SUCCESSFUL_AMOUNT = "TOTAL_SUCCESSFUL_AMOUNT"
    AVERAGE_SUCCESSFUL_AMOUNT = "AVERAGE_SUCCESSFUL_AMOUNT"
    COUNT_ALL = "COUNT_ALL"
    COUNT_SUCCESSFUL = "COUNT_SUCCESSFUL"
    COUNT_FAILED = "COUNT_FAILED"
    COUNT_PENDING = "COUNT_PENDING"


class SupportTicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SupportTicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SupportTicketCategory(str, Enum):
    BILLING = "BILLING"
    NETWORK = "NETWORK"
    BROADBAND = "BROADBAND"
    PAYMENT = "PAYMENT"
    PLAN = "PLAN"
    OTHER = "OTHER"


class SupportSortOrder(str, Enum):
    NEWEST = "NEWEST"
    OLDEST = "OLDEST"


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REPLACED = "REPLACED"
    LOST = "LOST"


class DeviceType(str, Enum):
    SMARTPHONE = "SMARTPHONE"
    ROUTER = "ROUTER"
    TABLET = "TABLET"
    MODEM = "MODEM"
    OTHER = "OTHER"


class DeviceSortOrder(str, Enum):
    NEWEST = "NEWEST"
    OLDEST = "OLDEST"


class DeviceExtremeType(str, Enum):
    NEWEST = "NEWEST"
    OLDEST = "OLDEST"


class TruthStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    DATABASE_ERROR = "DATABASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ACCESS_DENIED = "ACCESS_DENIED"


class SourceType(str, Enum):
    SQLITE = "SQLITE"


class Intent(str, Enum):
    # Account / plan
    GET_CURRENT_PLAN = "GET_CURRENT_PLAN"
    GET_ACCOUNT_STATUS = "GET_ACCOUNT_STATUS"
    GET_PLAN_RENEWAL = "GET_PLAN_RENEWAL"
    GET_LIST_SUBSCRIPTIONS = "GET_LIST_SUBSCRIPTIONS"
    GET_PLAN_CATALOG = "GET_PLAN_CATALOG"
    GET_PLAN_COMPARISON = "GET_PLAN_COMPARISON"
    GET_PLAN_DETAILS = "GET_PLAN_DETAILS"

    # Explorer parity — granular records
    LIST_USAGE_RECORDS = "LIST_USAGE_RECORDS"
    LIST_BILL_ITEMS = "LIST_BILL_ITEMS"
    LIST_TICKET_UPDATES = "LIST_TICKET_UPDATES"

    # Phase 1 — usage
    GET_DATA_USAGE = "GET_DATA_USAGE"
    GET_VOICE_USAGE = "GET_VOICE_USAGE"
    GET_SMS_USAGE = "GET_SMS_USAGE"
    GET_USAGE_REMAINING = "GET_USAGE_REMAINING"
    GET_USAGE_PERCENTAGE = "GET_USAGE_PERCENTAGE"
    GET_USAGE_SUMMARY = "GET_USAGE_SUMMARY"
    GET_USAGE_HISTORY = "GET_USAGE_HISTORY"
    GET_USAGE_COMPARISON = "GET_USAGE_COMPARISON"
    GET_USAGE_AVERAGE = "GET_USAGE_AVERAGE"
    GET_USAGE_EXTREME = "GET_USAGE_EXTREME"
    GET_USAGE_TREND = "GET_USAGE_TREND"

    # Phase 2 — billing
    GET_CURRENT_BILL = "GET_CURRENT_BILL"
    GET_BILL_HISTORY = "GET_BILL_HISTORY"
    GET_TOTAL_SPENDING = "GET_TOTAL_SPENDING"
    GET_BILL_COMPARISON = "GET_BILL_COMPARISON"
    GET_SPECIFIC_BILL = "GET_SPECIFIC_BILL"
    GET_BILL_BREAKDOWN = "GET_BILL_BREAKDOWN"
    EXPLAIN_BILL_CHANGE = "EXPLAIN_BILL_CHANGE"
    GET_AVERAGE_BILL = "GET_AVERAGE_BILL"
    GET_BILL_EXTREME = "GET_BILL_EXTREME"
    GET_BILL_TREND = "GET_BILL_TREND"
    FILTER_BILLS = "FILTER_BILLS"
    GET_BILL_CHARGE_SUMMARY = "GET_BILL_CHARGE_SUMMARY"
    GET_PROJECTED_BILL = "GET_PROJECTED_BILL"

    # Phase 3 — payments
    GET_PAYMENT_STATUS = "GET_PAYMENT_STATUS"
    GET_PAYMENT_HISTORY = "GET_PAYMENT_HISTORY"
    FILTER_PAYMENTS = "FILTER_PAYMENTS"
    GET_LAST_SUCCESSFUL_PAYMENT = "GET_LAST_SUCCESSFUL_PAYMENT"
    GET_LAST_FAILED_PAYMENT = "GET_LAST_FAILED_PAYMENT"
    GET_PAYMENT_BY_REFERENCE = "GET_PAYMENT_BY_REFERENCE"
    RECONCILE_BILL_PAYMENT = "RECONCILE_BILL_PAYMENT"
    GET_PAYMENT_OUTSTANDING = "GET_PAYMENT_OUTSTANDING"
    GET_PAYMENT_SUMMARY = "GET_PAYMENT_SUMMARY"
    GET_PAYMENT_AGGREGATE = "GET_PAYMENT_AGGREGATE"
    GET_PAYMENT_PROFILE = "GET_PAYMENT_PROFILE"
    GET_ACCOUNT_CREDITS = "GET_ACCOUNT_CREDITS"

    # Phase 4 — support
    GET_SUPPORT_TICKETS = "GET_SUPPORT_TICKETS"
    GET_LATEST_SUPPORT_TICKET = "GET_LATEST_SUPPORT_TICKET"
    GET_SPECIFIC_SUPPORT_TICKET = "GET_SPECIFIC_SUPPORT_TICKET"
    FILTER_SUPPORT_TICKETS = "FILTER_SUPPORT_TICKETS"
    GET_SUPPORT_TICKET_COUNT = "GET_SUPPORT_TICKET_COUNT"
    GET_SUPPORT_COMMON_CATEGORY = "GET_SUPPORT_COMMON_CATEGORY"
    GET_SUPPORT_SUMMARY = "GET_SUPPORT_SUMMARY"
    GET_SUPPORT_LAST_UPDATED = "GET_SUPPORT_LAST_UPDATED"
    GET_SUPPORT_TICKET_UPDATES = "GET_SUPPORT_TICKET_UPDATES"

    # Phase 4 — devices
    GET_DEVICE_INFORMATION = "GET_DEVICE_INFORMATION"
    GET_SPECIFIC_DEVICE = "GET_SPECIFIC_DEVICE"
    FILTER_DEVICES = "FILTER_DEVICES"
    GET_DEVICE_COUNT = "GET_DEVICE_COUNT"
    GET_DEVICE_EXTREME = "GET_DEVICE_EXTREME"
    GET_DEVICE_SUMMARY = "GET_DEVICE_SUMMARY"
    GET_DEVICE_DIAGNOSTIC_LIMITATION = (
        "GET_DEVICE_DIAGNOSTIC_LIMITATION"
    )

    # Phase 5 — cross-domain
    GET_PLAN_USAGE_STATUS = "GET_PLAN_USAGE_STATUS"
    GET_BILL_PAYMENT_STATUS = "GET_BILL_PAYMENT_STATUS"
    GET_BILL_PAYMENT_EXPLANATION = (
        "GET_BILL_PAYMENT_EXPLANATION"
    )
    GET_BILLING_SUPPORT_STATUS = "GET_BILLING_SUPPORT_STATUS"
    GET_PAYMENT_SUPPORT_STATUS = "GET_PAYMENT_SUPPORT_STATUS"
    GET_ACCOUNT_PLAN_STATUS = "GET_ACCOUNT_PLAN_STATUS"
    GET_ACCOUNT_ATTENTION_SUMMARY = (
        "GET_ACCOUNT_ATTENTION_SUMMARY"
    )

    # Smart features
    GET_BILL_ANOMALY_DETECTION = "GET_BILL_ANOMALY_DETECTION"
    GET_PLAN_RECOMMENDATION = "GET_PLAN_RECOMMENDATION"

    # Phase 6 — customer 360
    GET_CUSTOMER_360 = "GET_CUSTOMER_360"

    UNSUPPORTED = "UNSUPPORTED"


class TimeRange(str, Enum):
    CURRENT_MONTH = "CURRENT_MONTH"
    LAST_MONTH = "LAST_MONTH"
    CURRENT_YEAR = "CURRENT_YEAR"


class UsageType(str, Enum):
    DATA = "DATA"
    VOICE = "VOICE"
    SMS = "SMS"


class PlanType(str, Enum):
    MOBILE = "MOBILE"
    FIBER = "FIBER"


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class UsagePercentageType(str, Enum):
    CONSUMED = "CONSUMED"
    REMAINING = "REMAINING"


class UsageExtremeType(str, Enum):
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"


class BillExtremeType(str, Enum):
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"


class BillItemType(str, Enum):
    PLAN_CHARGE = "PLAN_CHARGE"
    ROAMING = "ROAMING"
    DATA_ADDON = "DATA_ADDON"
    TAX = "TAX"
    OTHER = "OTHER"


class BillSortOrder(str, Enum):
    NEWEST = "NEWEST"
    OLDEST = "OLDEST"
    AMOUNT_HIGH_TO_LOW = "AMOUNT_HIGH_TO_LOW"
    AMOUNT_LOW_TO_HIGH = "AMOUNT_LOW_TO_HIGH"


class CustomerContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    customer_id: str = Field(
        min_length=1,
        max_length=64,
    )

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Customer ID cannot be empty."
            )

        return value


class TruthSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: SourceType
    source_name: str = Field(
        min_length=1,
        max_length=128,
    )


class DateRange(BaseModel):
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_order(
        cls,
        value: date,
        info,
    ) -> date:
        start_date = info.data.get(
            "start_date"
        )

        if (
            start_date is not None
            and value < start_date
        ):
            raise ValueError(
                "End date cannot be before start date."
            )

        return value


class CustomerRecord(BaseModel):
    customer_id: str
    name: str
    email: str
    phone_number: str
    city: str
    account_status: AccountStatus
    registration_date: date


class PlanRecord(BaseModel):
    plan_id: str
    plan_name: str
    monthly_price: float
    data_limit_gb: float
    is_data_unlimited: bool = False
    voice_limit_minutes: int
    sms_limit: int
    plan_type: str


class SubscriptionRecord(BaseModel):
    subscription_id: str
    customer_id: str
    plan_id: str
    activation_date: date
    status: str
    renewal_date: date


class UsageRecord(BaseModel):
    usage_id: str
    customer_id: str
    subscription_id: str
    usage_date: date
    data_used_gb: float
    voice_minutes: int
    sms_count: int


class BillRecord(BaseModel):
    bill_id: str
    customer_id: str
    billing_period_start: date
    billing_period_end: date
    amount: float
    due_date: date
    status: BillStatus


class BillItemRecord(BaseModel):
    bill_item_id: str
    bill_id: str
    description: str
    amount: float
    item_type: str


class PaymentRecord(BaseModel):
    payment_id: str
    bill_id: str
    customer_id: str
    amount: float
    payment_date: datetime
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_reference: str


class SupportTicketRecord(BaseModel):
    ticket_id: str
    customer_id: str
    category: SupportTicketCategory
    description: str
    status: SupportTicketStatus
    priority: SupportTicketPriority
    created_at: datetime
    updated_at: datetime


class DeviceRecord(BaseModel):
    device_id: str
    customer_id: str
    device_name: str
    device_type: str
    purchase_date: date
    status: DeviceStatus