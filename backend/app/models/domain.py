from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccountStatus(str, Enum):
    """Valid NexaTel customer account states."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class BillStatus(str, Enum):
    """Valid NexaTel bill states."""

    PAID = "PAID"
    UNPAID = "UNPAID"
    OVERDUE = "OVERDUE"
    PARTIALLY_PAID = "PARTIALLY_PAID"


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"


class PaymentStatus(str, Enum):
    """Supported payment states."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class SupportTicketStatus(str, Enum):
    """Valid support-ticket states."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class SupportTicketPriority(str, Enum):
    """Valid support-ticket priorities."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SupportTicketCategory(str, Enum):
    """Valid support-ticket categories."""

    BILLING = "BILLING"
    NETWORK = "NETWORK"
    BROADBAND = "BROADBAND"
    PAYMENT = "PAYMENT"
    PLAN = "PLAN"
    OTHER = "OTHER"


class DeviceStatus(str, Enum):
    """Valid customer-device states."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REPLACED = "REPLACED"
    LOST = "LOST"


class TruthStatus(str, Enum):
    """
    Status of an authoritative backend result.

    These values are intentionally broader than HTTP status codes.
    They represent the semantic state of the information returned
    by the application's data/verification layer.
    """

    VERIFIED = "VERIFIED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    DATABASE_ERROR = "DATABASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ACCESS_DENIED = "ACCESS_DENIED"


class SourceType(str, Enum):
    """Authoritative source categories."""

    SQLITE = "SQLITE"


class Intent(str, Enum):
    """
    Complete Phase 1 supported intent set.

    The LLM may only return one of these values. UNSUPPORTED is used
    when the user's request cannot be handled by the Phase 1 system.
    """

    GET_CURRENT_PLAN = "GET_CURRENT_PLAN"
    GET_ACCOUNT_STATUS = "GET_ACCOUNT_STATUS"
    GET_PLAN_RENEWAL = "GET_PLAN_RENEWAL"

    GET_DATA_USAGE = "GET_DATA_USAGE"
    GET_VOICE_USAGE = "GET_VOICE_USAGE"

    GET_CURRENT_BILL = "GET_CURRENT_BILL"
    GET_BILL_HISTORY = "GET_BILL_HISTORY"
    GET_TOTAL_SPENDING = "GET_TOTAL_SPENDING"
    GET_BILL_COMPARISON = "GET_BILL_COMPARISON"

    GET_PAYMENT_STATUS = "GET_PAYMENT_STATUS"
    GET_PAYMENT_HISTORY = "GET_PAYMENT_HISTORY"

    GET_SUPPORT_TICKETS = "GET_SUPPORT_TICKETS"
    GET_DEVICE_INFORMATION = "GET_DEVICE_INFORMATION"

    UNSUPPORTED = "UNSUPPORTED"


class TimeRange(str, Enum):
    """Supported relative time ranges."""

    CURRENT_MONTH = "CURRENT_MONTH"
    LAST_MONTH = "LAST_MONTH"
    CURRENT_YEAR = "CURRENT_YEAR"


class CustomerContext(BaseModel):
    """
    Authenticated customer context.

    This object represents identity established by the backend,
    not identity inferred from a user message.
    """

    model_config = ConfigDict(frozen=True)

    customer_id: str = Field(min_length=1, max_length=64)

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Customer ID cannot be empty.")

        return value


class TruthSource(BaseModel):
    """Metadata describing where verified facts originated."""

    model_config = ConfigDict(frozen=True)

    source_type: SourceType
    source_name: str = Field(min_length=1, max_length=128)


class DateRange(BaseModel):
    """Resolved concrete date range used by backend logic."""

    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_order(
        cls,
        value: date,
        info,
    ) -> date:
        start_date = info.data.get("start_date")

        if start_date is not None and value < start_date:
            raise ValueError("End date cannot be before start date.")

        return value


class CustomerRecord(BaseModel):
    """Domain representation of a customer."""

    customer_id: str
    name: str
    email: str
    phone_number: str
    city: str
    account_status: AccountStatus
    registration_date: date


class PlanRecord(BaseModel):
    """Domain representation of a NexaTel plan."""

    plan_id: str
    plan_name: str
    monthly_price: float
    data_limit_gb: float
    voice_limit_minutes: int
    sms_limit: int
    plan_type: str


class SubscriptionRecord(BaseModel):
    """Domain representation of a customer subscription."""

    subscription_id: str
    customer_id: str
    plan_id: str
    activation_date: date
    status: str
    renewal_date: date


class UsageRecord(BaseModel):
    """Domain representation of one usage record."""

    usage_id: str
    customer_id: str
    subscription_id: str
    usage_date: date
    data_used_gb: float
    voice_minutes: int
    sms_count: int


class BillRecord(BaseModel):
    """Domain representation of a bill."""

    bill_id: str
    customer_id: str
    billing_period_start: date
    billing_period_end: date
    amount: float
    due_date: date
    status: BillStatus


class BillItemRecord(BaseModel):
    """Domain representation of an individual bill item."""

    bill_item_id: str
    bill_id: str
    description: str
    amount: float
    item_type: str


class PaymentRecord(BaseModel):
    """Domain representation of a payment."""

    payment_id: str
    bill_id: str
    customer_id: str
    amount: float
    payment_date: datetime
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_reference: str


class SupportTicketRecord(BaseModel):
    """Domain representation of a support ticket."""

    ticket_id: str
    customer_id: str
    category: SupportTicketCategory
    description: str
    status: SupportTicketStatus
    priority: SupportTicketPriority
    created_at: datetime
    updated_at: datetime


class DeviceRecord(BaseModel):
    """Domain representation of a customer device."""

    device_id: str
    customer_id: str
    device_name: str
    device_type: str
    purchase_date: date
    status: DeviceStatus