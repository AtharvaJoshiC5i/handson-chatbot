from app.llm.client import (
    classify_deterministic_request,
    classify_prompt_guard_request,
)
from app.models.domain import (
    CustomerContext,
    Intent,
    TimeRange,
)
from app.services.chat_service import ChatService


def test_classifier_recognizes_current_year_usage() -> None:
    response = classify_prompt_guard_request(
        "How much data have I used this year?"
    )

    assert response.intent == Intent.GET_DATA_USAGE
    assert response.parameters.time_range == TimeRange.CURRENT_YEAR


def test_classifier_leaves_billing_phrases_for_structured_llm() -> None:
    owed = classify_prompt_guard_request("What do I currently owe?")

    assert owed.intent == Intent.UNSUPPORTED


def test_classifier_routes_phone_bill_to_current_mobile_bill() -> None:
    phone_bill = classify_prompt_guard_request("Show me my phone bill")

    assert phone_bill.intent == Intent.GET_CURRENT_BILL
    assert phone_bill.parameters.plan_type is not None


def test_classifier_leaves_subscription_questions_for_structured_llm() -> None:
    plan_response = classify_deterministic_request(
        "What subscription am I using?"
    )

    assert plan_response is None


def test_classifier_recognizes_sms_usage_this_month() -> None:
    response = classify_deterministic_request(
        "Show my SMS usage this month."
    )

    assert response is not None
    assert response.intent == Intent.GET_SMS_USAGE


def test_classifier_clarifies_unspecified_usage_type() -> None:
    response = classify_deterministic_request(
        "How much have I used?"
    )

    assert response is not None
    assert response.intent == Intent.UNSUPPORTED
    assert response.clarification is not None
    assert "data" in response.clarification
    assert "voice" in response.clarification


def test_classifier_leaves_general_information_for_structured_llm() -> None:
    response = classify_deterministic_request(
        "Show me my information."
    )

    assert response is None


def test_classifier_leaves_payment_status_synonyms_for_structured_llm() -> None:
    response = classify_deterministic_request(
        "Has my latest payment gone through?"
    )

    assert response is None


def test_classifier_clarifies_general_payment_help() -> None:
    class DeterministicClient:
        def extract_intent(self, user_message: str):
            return classify_deterministic_request(
                user_message
            )

    service = ChatService(
        DeterministicClient()
    )
    response = service.respond(
        db=None,
        customer=CustomerContext(
            customer_id="CUST001"
        ),
        user_message="Help with a payment",
    )

    assert response.status == "AMBIGUOUS"
    assert "What would you like help with?" in response.message
    assert {option.label for option in response.options} == {
        "Latest payment status",
        "Payment history",
        "Bill and payment status",
        "Payment support tickets",
    }


def test_prompt_guard_keeps_unrelated_requests_unsupported() -> None:
    response = classify_prompt_guard_request(
        "What is the weather today?"
    )

    assert response.intent == Intent.UNSUPPORTED
    assert response.clarification is None
