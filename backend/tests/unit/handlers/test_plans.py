from app.database.connection import create_connection
from app.handlers.plans import (
    get_current_plan,
    get_plan_renewal,
)
from app.models.domain import (
    CustomerContext,
    TruthStatus,
)


def test_get_current_plan_returns_verified_customer_plan():
    db = create_connection()

    try:
        result = get_current_plan(
            db,
            CustomerContext(customer_id="CUST001"),
        )

        assert result.status == TruthStatus.VERIFIED
        assert result.data["plan_name"] == "NexaMax 799"
        assert result.data["monthly_price"] == 799.0

    finally:
        db.close()


def test_get_plan_renewal_returns_verified_date():
    db = create_connection()

    try:
        result = get_plan_renewal(
            db,
            CustomerContext(customer_id="CUST001"),
        )

        assert result.status == TruthStatus.VERIFIED
        assert result.data["renewal_date"] == "2026-10-10"

    finally:
        db.close()