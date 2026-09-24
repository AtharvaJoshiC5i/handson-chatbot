from app.llm.client import (
    classify_deterministic_request,
    classify_prompt_guard_request,
)
from app.models.domain import Intent, TimeRange


def test_classifier_recognizes_current_year_usage() -> None:
    response = classify_prompt_guard_request(
        "How much data have I used this year?"
    )

    assert response.intent == Intent.GET_DATA_USAGE
    assert response.parameters.time_range == TimeRange.CURRENT_YEAR


def test_classifier_recognizes_amount_owed_as_current_bill() -> None:
    response = classify_prompt_guard_request("What do I currently owe?")

    assert response.intent == Intent.GET_CURRENT_BILL


def test_classifier_does_not_treat_phone_bill_as_device_request() -> None:
    response = classify_prompt_guard_request("Show me my phone bill")

    assert response.intent == Intent.GET_CURRENT_BILL


def test_classifier_recognizes_ticket_and_subscription_aliases() -> None:
    ticket_response = classify_prompt_guard_request(
        "Show my open support cases"
    )
    plan_response = classify_prompt_guard_request(
        "What subscription am I using?"
    )

    assert ticket_response.intent == Intent.GET_SUPPORT_TICKETS
    assert plan_response.intent == Intent.GET_CURRENT_PLAN


def test_classifier_clarifies_unspecified_usage_type() -> None:
    response = classify_deterministic_request(
        "How much have I used?"
    )

    assert response is not None
    assert response.intent == Intent.UNSUPPORTED
    assert response.clarification is not None
    assert "data usage" in response.clarification
    assert "voice" in response.clarification


def test_classifier_provides_choices_for_general_information_request() -> None:
    response = classify_deterministic_request(
        "Show me my information."
    )

    assert response is not None
    assert response.clarification is not None
    assert response.options
    assert {option.label for option in response.options} >= {
        "Account status",
        "Current plan",
        "Usage",
        "Current bill",
        "Payment status",
        "Support tickets",
        "Devices",
    }


def test_classifier_recognizes_payment_status_synonyms() -> None:
    response = classify_deterministic_request(
        "Has my latest payment gone through?"
    )

    assert response is not None
    assert response.intent == Intent.GET_PAYMENT_STATUS


def test_prompt_guard_keeps_unrelated_requests_unsupported() -> None:
    response = classify_prompt_guard_request(
        "What is the weather today?"
    )

    assert response.intent == Intent.UNSUPPORTED
    assert response.clarification is None