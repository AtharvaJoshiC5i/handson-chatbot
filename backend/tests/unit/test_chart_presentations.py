from app.models.api import TablePresentation, TimeSeriesPresentation
from app.services.presentation_service import PresentationService
from app.truth.result import verified_result
from app.truth.sources import DATABASE_SOURCE


def _build_presentation(data):
    return PresentationService().build(
        verified_result(data, source=DATABASE_SOURCE)
    )


def test_usage_history_with_multiple_periods_builds_line_chart() -> None:
    presentation = _build_presentation(
        {
            "result_type": "USAGE_HISTORY",
            "usage_type": "DATA",
            "history": [
                {"period": "Jul 2026", "value": 20.5, "unit": "GB"},
                {"period": "Aug 2026", "value": 24.0, "unit": "GB"},
                {"period": "Sep 2026", "value": 34.0, "unit": "GB"},
            ],
        }
    )

    assert isinstance(presentation, TimeSeriesPresentation)
    assert presentation.chart_type == "line"
    assert presentation.unit == "GB"
    assert [point.value for point in presentation.points] == [20.5, 24.0, 34.0]


def test_short_usage_history_keeps_the_existing_table() -> None:
    presentation = _build_presentation(
        {
            "result_type": "USAGE_HISTORY",
            "usage_type": "VOICE",
            "history": [
                {"period": "Aug 2026", "value": 120, "unit": "minutes"},
                {"period": "Sep 2026", "value": 140, "unit": "minutes"},
            ],
        }
    )

    assert isinstance(presentation, TablePresentation)
    assert presentation.rows[0]["usage"] == "120 minutes"


def test_bill_history_builds_bar_chart_with_status_details() -> None:
    presentation = _build_presentation(
        {
            "result_type": "BILL_HISTORY",
            "bills": [
                {
                    "period": "Jul 2026",
                    "amount": "₹799",
                    "amount_value": 799,
                    "status": "PAID",
                },
                {
                    "period": "Aug 2026",
                    "amount": "₹899",
                    "amount_value": 899,
                    "status": "UNPAID",
                },
                {
                    "period": "Sep 2026",
                    "amount": "₹799",
                    "amount_value": 799,
                    "status": "PAID",
                },
            ],
        }
    )

    assert isinstance(presentation, TimeSeriesPresentation)
    assert presentation.chart_type == "bar"
    assert presentation.value_format == "inr"
    assert presentation.points[1].value == 899
    assert presentation.points[1].detail == "Unpaid"


def test_usage_and_bill_trends_build_line_charts() -> None:
    usage = _build_presentation(
        {
            "result_type": "USAGE_TREND",
            "usage_type": "DATA",
            "unit": "GB",
            "history": [
                {"period": "Aug 2026", "value": 24.0, "unit": "GB"},
                {"period": "Sep 2026", "value": 34.0, "unit": "GB"},
            ],
        }
    )
    billing = _build_presentation(
        {
            "result_type": "BILL_TREND",
            "bills": [
                {"period": "Aug 2026", "amount_value": 799, "status": "PAID"},
                {"period": "Sep 2026", "amount_value": 899, "status": "PAID"},
            ],
        }
    )

    assert isinstance(usage, TimeSeriesPresentation)
    assert usage.chart_type == "line"
    assert isinstance(billing, TimeSeriesPresentation)
    assert billing.chart_type == "line"


def test_plan_renewal_builds_key_value_presentation() -> None:
    presentation = _build_presentation(
        {
            "result_type": "PLAN_RENEWAL",
            "plan_name": "NexaMax 799",
            "plan_type": "MOBILE",
            "renewal_date": "2026-10-15",
            "subscription_status": "ACTIVE",
        }
    )

    assert presentation is not None
    assert presentation.type == "key_value"
    assert presentation.title == "Plan renewal"
    labels = [item.label for item in presentation.items]
    assert "Renewal date" in labels


def test_payment_history_splits_date_and_time_columns() -> None:
    presentation = _build_presentation(
        {
            "result_type": "PAYMENT_HISTORY",
            "payments": [
                {
                    "payment_date": "2026-11-05T10:30:00",
                    "amount": 801,
                    "payment_method": "debit_card",
                    "status": "SUCCESS",
                },
            ],
        }
    )

    assert isinstance(presentation, TablePresentation)
    assert [col.key for col in presentation.columns] == [
        "bill_period",
        "date",
        "time",
        "amount",
        "method",
        "status",
    ]
    assert presentation.rows[0]["date"] == "2026-11-05"
    assert presentation.rows[0]["time"] == "10:30:00"