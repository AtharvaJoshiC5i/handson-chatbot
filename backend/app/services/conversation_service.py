"""Compact, customer-bound conversation context for chat follow-ups."""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import date
import re
from threading import RLock
from typing import Any

from app.config.settings import get_settings
from app.llm.client import classify_deterministic_request
from app.services.conversation_turn import ConversationTurn
from app.services.conversation_turn_summary import (
    summarize_turn_facts,
    truncate_user_message,
)
from app.models.domain import (
    CustomerContext,
    Intent,
    PaymentStatus,
    SupportTicketPriority,
    SupportTicketStatus,
    TimeRange,
    TruthStatus,
    UsageType,
)
from app.models.llm import (
    IntentOption,
    IntentParameters,
    LLMIntentResponse,
)
from app.truth.result import TruthResult


_MONTHS = {
    month.lower(): index
    for index, month in enumerate(
        (
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        )
    )
    if month
}

_BILL_ID_PATTERN = re.compile(
    r"\bBILL\d+\b",
    re.IGNORECASE,
)


def _turn_deque() -> deque[ConversationTurn]:
    return deque(
        maxlen=get_settings().conversation_turn_window,
    )


def _month_and_year(
    text: str,
    *,
    default_year: int | None = None,
) -> tuple[int | None, int | None]:
    lowered = text.lower()
    month = next(
        (
            number
            for name, number in _MONTHS.items()
            if re.search(
                rf"\b{name}\b",
                lowered,
            )
        ),
        None,
    )

    if month is None:
        numeric_month = re.search(
            r"\bmonth\s+(1[0-2]|[1-9])\b",
            lowered,
        )
        if numeric_month is not None:
            month = int(
                numeric_month.group(1)
            )

    year_match = re.search(
        r"\b(20\d{2})\b",
        lowered,
    )
    year = (
        int(year_match.group(1))
        if year_match is not None
        else default_year
    )

    return month, year


def _period_key(
    value: Any,
) -> str | None:
    if not isinstance(
        value,
        str,
    ):
        return None

    match = re.search(
        r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b",
        value,
    )
    if match is not None:
        return (
            f"{int(match.group(1)):04d}-"
            f"{int(match.group(2)):02d}"
        )

    month, year = _month_and_year(
        value
    )
    if month is not None and year is not None:
        return f"{year:04d}-{month:02d}"

    return None


def _shift_month(
    year: int,
    month: int,
    amount: int,
) -> tuple[int, int]:
    index = year * 12 + month - 1 + amount
    return index // 12, index % 12 + 1


@dataclass
class ConversationContext:
    """Small structured state for one customer conversation."""

    customer_id: str
    last_intent: str | None = None
    active_domain: str | None = None
    referenced_bill_id: str | None = None
    referenced_payment_id: str | None = None
    referenced_payment_reference: str | None = None
    referenced_ticket_id: str | None = None
    referenced_device_id: str | None = None
    referenced_subscription_id: str | None = None
    referenced_period: str | None = None
    comparison_period: str | None = None
    usage_type: str | None = None
    support_unresolved_only: bool = False
    support_ticket_status: str | None = None
    turns: deque[ConversationTurn] = field(
        default_factory=_turn_deque,
    )

    def compact_hint(self) -> str:
        """Return bounded structured state, never a message transcript."""

        fields = (
            "last_intent",
            "active_domain",
            "referenced_bill_id",
            "referenced_payment_id",
            "referenced_payment_reference",
            "referenced_ticket_id",
            "referenced_device_id",
            "referenced_subscription_id",
            "referenced_period",
            "comparison_period",
            "usage_type",
            "support_unresolved_only",
            "support_ticket_status",
        )
        return "; ".join(
            f"{name}={getattr(self, name)}"
            for name in fields
            if getattr(self, name) is not None
            and getattr(self, name) is not False
        )

    def build_intent_context(self) -> str:
        """Snapshot plus bounded recent turn summaries for intent LLM."""

        parts: list[str] = []
        snapshot = self.compact_hint()
        if snapshot:
            parts.append(f"Snapshot: {snapshot}")
        if self.turns:
            lines = [
                turn.format_line(index)
                for index, turn in enumerate(
                    self.turns,
                    start=1,
                )
            ]
            parts.append(
                "Recent turns (oldest→newest):\n"
                + "\n".join(lines)
            )
        return "\n".join(parts)

    def record_turn(
        self,
        user_message: str,
        intent_response: LLMIntentResponse,
        result: TruthResult[Any],
    ) -> None:
        data = result.data
        result_type: str | None = None
        if isinstance(data, dict):
            raw_type = data.get("result_type")
            if isinstance(raw_type, str):
                result_type = raw_type

        self.turns.append(
            ConversationTurn(
                user_message=truncate_user_message(
                    user_message,
                ),
                intent=intent_response.intent.value,
                status=result.status.value,
                result_type=result_type,
                domain=self.active_domain,
                facts=summarize_turn_facts(result),
            )
        )

    def recent_turns(
        self,
        limit: int = 3,
    ) -> list[ConversationTurn]:
        if limit <= 0:
            return []
        return list(self.turns)[-limit:]

    def referenced_period_from_history(
        self,
        limit: int = 3,
    ) -> str | None:
        for turn in reversed(
            self.recent_turns(limit)
        ):
            period = _period_key(turn.facts)
            if period is not None:
                return period
        return None

    def referenced_bill_id_from_history(
        self,
        limit: int = 3,
    ) -> str | None:
        for turn in reversed(
            self.recent_turns(limit)
        ):
            match = _BILL_ID_PATTERN.search(
                turn.facts,
            )
            if match is not None:
                return match.group(0).upper()
        return None

    def referenced_ticket_id_from_history(
        self,
        limit: int = 3,
    ) -> str | None:
        for turn in reversed(
            self.recent_turns(limit)
        ):
            match = re.search(
                r"\bTKT\d+\b",
                turn.facts,
                re.IGNORECASE,
            )
            if match is not None:
                return match.group(0).upper()
        return None

    def update(
        self,
        intent_response: LLMIntentResponse,
        result: TruthResult[Any],
    ) -> None:
        if result.status in {
            TruthStatus.AMBIGUOUS,
            TruthStatus.UNSUPPORTED,
            TruthStatus.DATABASE_ERROR,
            TruthStatus.VALIDATION_ERROR,
        }:
            return

        intent = intent_response.intent
        self.last_intent = intent.value
        self.active_domain = _domain_for_intent(
            intent
        ) or self.active_domain

        parameters = intent_response.parameters
        next_domain = _domain_for_intent(
            intent
        )

        if (
            explicit_period := _period_from_parameters(
                parameters.month,
                parameters.year,
                parameters.time_range,
            )
        ) is not None:
            if (
                self.active_domain == "usage"
                and next_domain == "usage"
                and self.referenced_period is not None
                and explicit_period != self.referenced_period
            ):
                self.comparison_period = (
                    self.referenced_period
                )
            self.referenced_period = explicit_period

        if parameters.usage_type is not None:
            self.usage_type = parameters.usage_type.value

        if parameters.unresolved_only is not None:
            self.support_unresolved_only = (
                parameters.unresolved_only
            )
        elif intent in {
            Intent.GET_SUPPORT_TICKETS,
            Intent.GET_LATEST_SUPPORT_TICKET,
        }:
            self.support_unresolved_only = False

        if parameters.ticket_status is not None:
            self.support_ticket_status = (
                parameters.ticket_status.value
            )
        elif intent in {
            Intent.GET_SUPPORT_TICKETS,
            Intent.GET_LATEST_SUPPORT_TICKET,
        }:
            self.support_ticket_status = None

        comparison_period = _period_from_parameters(
            parameters.comparison_month,
            parameters.comparison_year,
            None,
        )
        if comparison_period is not None:
            self.comparison_period = comparison_period

        data = result.data
        if isinstance(data, dict):
            self._capture_entities(data)

        if parameters.ticket_id is not None:
            self.referenced_ticket_id = parameters.ticket_id

    def _capture_entities(
        self,
        data: dict[str, Any],
    ) -> None:
        bill = (
            data.get("bill")
            or data.get("current_bill")
            or data.get("billing")
        )
        if bill is None and "bill_id" in data:
            bill = data
        if bill is None and data.get("bills"):
            bill = data["bills"][0]

        if isinstance(bill, dict):
            self.referenced_bill_id = bill.get(
                "bill_id",
                self.referenced_bill_id,
            )
            self.referenced_period = (
                _period_key(
                    bill.get("billing_period_start")
                )
                or _period_key(
                    bill.get("period")
                )
                or self.referenced_period
            )

        payment = data.get("payment")
        if payment is None and data.get(
            "payment_attempts"
        ):
            payment = data[
                "payment_attempts"
            ][-1]
        if isinstance(payment, dict):
            payment = (
                payment.get("latest_attempt")
                or payment.get("payment")
                or payment
            )
        if isinstance(payment, dict):
            self.referenced_payment_id = payment.get(
                "payment_id",
                self.referenced_payment_id,
            )
            self.referenced_payment_reference = payment.get(
                "transaction_reference",
                self.referenced_payment_reference,
            )

        ticket = data.get("ticket")
        if ticket is None and isinstance(
            data.get("support"),
            dict,
        ):
            ticket = data["support"].get(
                "important_ticket"
            )
        if ticket is None:
            ticket_list = next(
                (
                    data[key]
                    for key in (
                        "tickets",
                        "billing_tickets",
                        "payment_tickets",
                    )
                    if isinstance(
                        data.get(key),
                        list,
                    )
                    and data[key]
                ),
                None,
            )
            if ticket_list is not None:
                ticket = ticket_list[0]
        if isinstance(ticket, dict):
            self.referenced_ticket_id = ticket.get(
                "ticket_id",
                self.referenced_ticket_id,
            )

        device = data.get("device")
        if device is None and isinstance(
            data.get("devices"),
            dict,
        ):
            active_devices = data["devices"].get(
                "active_devices",
                [],
            )
            if active_devices:
                device = active_devices[0]
        if device is None and data.get("devices"):
            devices = data["devices"]
            if isinstance(
                devices,
                list,
            ):
                device = devices[0]
        if isinstance(device, dict):
            self.referenced_device_id = device.get(
                "device_id",
                self.referenced_device_id,
            )

        subscription = data.get("subscription")
        if isinstance(subscription, dict):
            self.referenced_subscription_id = subscription.get(
                "subscription_id",
                self.referenced_subscription_id,
            )
        elif data.get("subscription_id") is not None:
            self.referenced_subscription_id = data[
                "subscription_id"
            ]

        period = _period_key(
            data.get("period")
        )
        self.referenced_period = (
            period
            or self.referenced_period
        )

        usage = data.get("usage")
        if isinstance(usage, dict):
            usage_period = _period_key(
                usage.get("period")
            )
            if usage_period is not None:
                self.referenced_period = usage_period
            usage_type = usage.get(
                "usage_type"
            )
            if usage_type is not None:
                self.usage_type = usage_type
        elif data.get("usage_type") is not None:
            self.usage_type = data[
                "usage_type"
            ]


def _period_from_parameters(
    month: int | None,
    year: int | None,
    time_range: TimeRange | None,
) -> str | None:
    today = date.today()

    if month is not None:
        return f"{year or today.year:04d}-{month:02d}"

    if time_range == TimeRange.CURRENT_MONTH:
        return f"{today.year:04d}-{today.month:02d}"

    if time_range == TimeRange.LAST_MONTH:
        previous_year, previous_month = _shift_month(
            today.year,
            today.month,
            -1,
        )
        return f"{previous_year:04d}-{previous_month:02d}"

    return None


def _domain_for_intent(
    intent: Intent,
) -> str | None:
    if intent in {
        Intent.GET_BILLING_SUPPORT_STATUS,
        Intent.GET_PAYMENT_SUPPORT_STATUS,
    }:
        return "support"

    name = intent.value

    if "USAGE" in name:
        return "usage"
    if "BILL" in name:
        return "billing"
    if "PAYMENT" in name:
        return "payment"
    if "SUPPORT" in name or "TICKET" in name:
        return "support"
    if "DEVICE" in name:
        return "devices"
    if intent in {
        Intent.GET_CURRENT_PLAN,
        Intent.GET_PLAN_RENEWAL,
    }:
        return "subscription"
    if intent == Intent.GET_ACCOUNT_PLAN_STATUS:
        return "account_summary"
    if intent == Intent.GET_ACCOUNT_ATTENTION_SUMMARY:
        return "attention"
    if intent == Intent.GET_ACCOUNT_STATUS:
        return "account"
    return None


class ConversationService:
    """Own ephemeral context by conversation ID and trusted customer."""

    MAX_CONVERSATIONS = 500

    def __init__(self) -> None:
        self._contexts: OrderedDict[
            str,
            ConversationContext,
        ] = OrderedDict()
        self._lock = RLock()

    def get_context(
        self,
        conversation_id: str,
        customer: CustomerContext,
    ) -> ConversationContext:
        with self._lock:
            context = self._contexts.get(
                conversation_id
            )
            if (
                context is None
                or context.customer_id
                != customer.customer_id
            ):
                context = ConversationContext(
                    customer_id=customer.customer_id
                )
                self._contexts[
                    conversation_id
                ] = context

            self._contexts.move_to_end(
                conversation_id
            )

            while len(
                self._contexts
            ) > self.MAX_CONVERSATIONS:
                self._contexts.popitem(
                    last=False
                )

            return context

    def clear(
        self,
        conversation_id: str,
        customer: CustomerContext,
    ) -> None:
        with self._lock:
            context = self._contexts.get(
                conversation_id
            )
            if (
                context is not None
                and context.customer_id
                == customer.customer_id
            ):
                del self._contexts[
                    conversation_id
                ]

    def resolve_followup(
        self,
        message: str,
        context: ConversationContext,
    ) -> LLMIntentResponse | None:
        text = message.lower().strip()
        params = IntentParameters()
        active = context.active_domain

        direct = classify_deterministic_request(
            message
        )

        is_reference = any(
            phrase in text
            for phrase in (
                " it",
                "that ",
                " this",
                "those ",
                "which one",
                "which ones",
                "what about",
                "the previous one",
                "newest one",
                "last month",
                "this month",
            )
        ) or text in {
            "it",
            "that",
            "this",
        }

        def _bill_id_for_followup() -> str | None:
            if context.referenced_bill_id:
                return context.referenced_bill_id
            if is_reference:
                return context.referenced_bill_id_from_history()
            return None

        def _period_for_followup() -> str | None:
            if context.referenced_period:
                return context.referenced_period
            if is_reference or any(
                phrase in text
                for phrase in (
                    "same period",
                    "that month",
                    "same month",
                )
            ):
                return context.referenced_period_from_history()
            return None

        def _ticket_id_for_followup() -> str | None:
            if context.referenced_ticket_id:
                return context.referenced_ticket_id
            if is_reference:
                return context.referenced_ticket_id_from_history()
            return None

        explicit_domain = self._explicit_domain(
            text
        )

        if (
            explicit_domain is not None
            and active is not None
            and explicit_domain != active
            and not {
                explicit_domain,
                active,
            }.issubset(
                {
                    "billing",
                    "payment",
                }
            )
        ):
            return direct

        if active == "usage" and any(
            phrase in text
            for phrase in (
                "how much is left",
                "how much do i have left",
                "what is left",
                "what's left",
            )
        ):
            params.usage_type = UsageType(
                context.usage_type
                or UsageType.DATA.value
            )
            if "last month" in text:
                params.time_range = TimeRange.LAST_MONTH
            return LLMIntentResponse(
                intent=Intent.GET_USAGE_REMAINING,
                parameters=params,
            )

        if direct is not None and not (
            context.last_intent is not None
            and is_reference
        ):
            return direct

        if self._asks_status(text):
            if active == "billing":
                return LLMIntentResponse(
                    intent=Intent.GET_CURRENT_BILL,
                    parameters=params,
                )
            if active == "payment":
                return LLMIntentResponse(
                    intent=Intent.GET_PAYMENT_STATUS,
                    parameters=params,
                )
            if active == "subscription":
                return LLMIntentResponse(
                    intent=Intent.GET_ACCOUNT_PLAN_STATUS,
                    parameters=params,
                )
            if active == "support":
                ticket_id = _ticket_id_for_followup()
                if ticket_id:
                    params.ticket_id = ticket_id
                return LLMIntentResponse(
                    intent=Intent.GET_LATEST_SUPPORT_TICKET,
                    parameters=params,
                )
            if active in {
                "account_summary",
                "attention",
            }:
                return self._status_clarification()
            if active is None:
                resolved = self._status_intent_from_message(
                    text,
                    params,
                )
                if resolved is not None:
                    return resolved
            return self._status_clarification()

        effective_period = _period_for_followup()
        month, year = _month_and_year(
            text,
            default_year=(
                int(effective_period[:4])
                if effective_period
                else date.today().year
            ),
        )
        if (
            month is None
            and is_reference
            and any(
                phrase in text
                for phrase in (
                    "that month",
                    "same month",
                    "same period",
                )
            )
            and effective_period is not None
        ):
            month = int(effective_period[5:7])
            year = int(effective_period[:4])
        is_last_month = "last month" in text
        is_this_month = "this month" in text
        has_comparison = any(
            phrase in text
            for phrase in (
                "more than",
                "less than",
                "compared with",
                "compared to",
                "compare",
            )
        )

        if (
            active == "usage"
            and has_comparison
            and (month is not None or is_last_month)
        ):
            primary_month, primary_year = self._context_month(
                context
            )
            comparison_month = month
            comparison_year = year
            if is_last_month:
                comparison_year, comparison_month = _shift_month(
                    date.today().year,
                    date.today().month,
                    -1,
                )
            elif (
                "that" in text
                and context.comparison_period is not None
                and context.referenced_period
                == f"{year or date.today().year:04d}-{month:02d}"
            ):
                primary_year, primary_month = (
                    int(context.comparison_period[:4]),
                    int(context.comparison_period[5:7]),
                )
            if primary_month is not None:
                params.month = primary_month
                params.year = primary_year
            params.comparison_month = comparison_month
            params.comparison_year = comparison_year
            params.usage_type = UsageType(
                context.usage_type or UsageType.DATA.value
            )
            return LLMIntentResponse(
                intent=Intent.GET_USAGE_COMPARISON,
                parameters=params,
            )

        if (
            active == "usage"
            and "previous one" in text
            and context.comparison_period is not None
        ):
            params.usage_type = UsageType(
                context.usage_type or UsageType.DATA.value
            )
            params.month_count = 2
            return LLMIntentResponse(
                intent=Intent.GET_USAGE_HISTORY,
                parameters=params,
            )

        if (
            active in {"usage", "billing"}
            and (
                month is not None
                or is_last_month
                or is_this_month
            )
            and any(
                phrase in text
                for phrase in (
                    "what about",
                    "last month",
                    "this month",
                    "previous one",
                )
            )
        ):
            if active == "usage":
                if is_last_month:
                    params.time_range = TimeRange.LAST_MONTH
                elif is_this_month:
                    params.time_range = TimeRange.CURRENT_MONTH
                else:
                    params.month = month
                    params.year = year
                followup_usage_intent = Intent.GET_DATA_USAGE
                if context.usage_type == UsageType.VOICE.value:
                    followup_usage_intent = Intent.GET_VOICE_USAGE
                elif context.usage_type == UsageType.SMS.value:
                    followup_usage_intent = Intent.GET_SMS_USAGE
                return LLMIntentResponse(
                    intent=followup_usage_intent,
                    parameters=params,
                )

            params.month = (
                month
                if month is not None
                else date.today().month
            )
            params.year = (
                year
                if year is not None
                else date.today().year
            )
            if is_last_month and month is None:
                params.time_range = TimeRange.LAST_MONTH
            params.limit = 1
            return LLMIntentResponse(
                intent=Intent.GET_BILL_HISTORY,
                parameters=params,
            )

        if active in {"billing", "payment"}:
            if "previous one" in text:
                if context.comparison_period is not None:
                    params.month = int(
                        context.comparison_period[5:7]
                    )
                    params.year = int(
                        context.comparison_period[:4]
                    )
                elif context.referenced_period is not None:
                    previous_year, previous_month = _shift_month(
                        int(context.referenced_period[:4]),
                        int(context.referenced_period[5:7]),
                        -1,
                    )
                    params.month = previous_month
                    params.year = previous_year
                else:
                    return None
                return LLMIntentResponse(
                    intent=Intent.GET_BILL_COMPARISON,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "why is it higher",
                    "why is that higher",
                    "why did it increase",
                    "why did that increase",
                    "why is it more",
                )
            ):
                bill_id = _bill_id_for_followup()
                if bill_id:
                    params.current_bill_id = bill_id
                return LLMIntentResponse(
                    intent=Intent.GET_BILL_ANOMALY_DETECTION,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "break it down",
                    "break that down",
                    "what extra charges",
                    "those charges",
                    "what are the charges",
                )
            ):
                bill_id = _bill_id_for_followup()
                if bill_id:
                    params.current_bill_id = bill_id
                return LLMIntentResponse(
                    intent=Intent.GET_BILL_BREAKDOWN,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "did i pay it",
                    "did i try paying it",
                    "did i try to pay it",
                    "have i paid it",
                    "did i pay that bill",
                )
            ):
                period = _period_for_followup()
                if period:
                    params.month = int(period[5:7])
                    params.year = int(period[:4])
                    return LLMIntentResponse(
                        intent=Intent.RECONCILE_BILL_PAYMENT,
                        parameters=params,
                    )
                return LLMIntentResponse(
                    intent=Intent.GET_BILL_PAYMENT_STATUS,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "did that payment succeed",
                    "did the payment succeed",
                    "was that payment successful",
                    "did it go through",
                )
            ):
                return LLMIntentResponse(
                    intent=Intent.GET_PAYMENT_STATUS,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "complaint about this",
                    "complaint about it",
                    "complaints about this",
                    "support about this",
                )
            ):
                if _bill_id_for_followup():
                    return LLMIntentResponse(
                        intent=Intent.GET_BILLING_SUPPORT_STATUS,
                        parameters=params,
                    )
                return LLMIntentResponse(
                    intent=Intent.GET_PAYMENT_SUPPORT_STATUS,
                    parameters=params,
                )

        if active == "usage" and any(
            phrase in text
            for phrase in (
                "how much is left",
                "how much do i have left",
                "what is left",
                "what's left",
            )
        ):
            params.usage_type = UsageType(
                context.usage_type or UsageType.DATA.value
            )
            if "last month" in text:
                params.time_range = TimeRange.LAST_MONTH
            return LLMIntentResponse(
                intent=Intent.GET_USAGE_REMAINING,
                parameters=params,
            )

        if active == "support":
            if any(
                phrase in text
                for phrase in (
                    "which one is high priority",
                    "which ones are high priority",
                    "which is high priority",
                    "which one is critical",
                    "which ticket is high priority",
                )
            ):
                params.ticket_priority = (
                    SupportTicketPriority.HIGH
                )
                if context.support_unresolved_only:
                    params.unresolved_only = True
                elif context.support_ticket_status:
                    params.ticket_status = (
                        SupportTicketStatus(
                            context.support_ticket_status
                        )
                    )
                return LLMIntentResponse(
                    intent=Intent.GET_SUPPORT_TICKETS,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "when was it last updated",
                    "when was that last updated",
                    "when was the ticket last updated",
                    "when was the previous one updated",
                )
            ):
                ticket_id = _ticket_id_for_followup()
                if ticket_id:
                    params.ticket_id = ticket_id
                return LLMIntentResponse(
                    intent=Intent.GET_SUPPORT_LAST_UPDATED,
                    parameters=params,
                )

        if active == "devices":
            if any(
                phrase in text
                for phrase in (
                    "which ones are active",
                    "which are active",
                    "which ones active",
                )
            ):
                return LLMIntentResponse(
                    intent=Intent.GET_DEVICE_INFORMATION,
                    parameters=params,
                )

            if any(
                phrase in text
                for phrase in (
                    "which is the newest",
                    "which one is newest",
                    "newest one",
                    "which is newest",
                )
            ):
                return LLMIntentResponse(
                    intent=Intent.GET_DEVICE_INFORMATION,
                    parameters=params,
                )

        if active in {"account_summary", "attention"} and any(
            phrase in text
            for phrase in (
                "what needs my attention",
                "what should i take care of",
                "what needs attention",
                "anything i need to take care of",
            )
        ):
            return LLMIntentResponse(
                intent=Intent.GET_ACCOUNT_ATTENTION_SUMMARY,
                parameters=params,
            )

        if active is None and self._asks_status(text):
            resolved = self._status_intent_from_message(
                text,
                params,
            )
            if resolved is not None:
                return resolved
            return self._status_clarification()

        return None

    @staticmethod
    def _status_intent_from_message(
        text: str,
        params: IntentParameters,
    ) -> LLMIntentResponse | None:
        if any(
            phrase in text
            for phrase in (
                "payment",
                "paid",
                "transaction",
            )
        ) and not any(
            word in text
            for word in ("ticket", "support", "case")
        ):
            return LLMIntentResponse(
                intent=Intent.GET_PAYMENT_STATUS,
                parameters=params,
            )
        if "bill" in text and "payment" not in text:
            return LLMIntentResponse(
                intent=Intent.GET_CURRENT_BILL,
                parameters=params,
            )
        if any(
            word in text
            for word in (
                "ticket",
                "support",
                "case",
            )
        ):
            return LLMIntentResponse(
                intent=Intent.GET_LATEST_SUPPORT_TICKET,
                parameters=params,
            )
        if "subscription" in text or "plan" in text:
            return LLMIntentResponse(
                intent=Intent.GET_ACCOUNT_PLAN_STATUS,
                parameters=params,
            )
        return None

    @staticmethod
    def _asks_status(
        text: str,
    ) -> bool:
        return any(
            phrase in text
            for phrase in (
                "what's the status",
                "what is the status",
                "what's status",
                "what is status",
                "the status?",
                "status of it",
            )
        )

    @staticmethod
    def _explicit_domain(
        text: str,
    ) -> str | None:
        if any(
            word in text
            for word in (
                "bill",
                "billing",
                "charge",
            )
        ):
            return "billing"

        if "payment" in text:
            return "payment"

        if any(
            word in text
            for word in (
                "usage",
                "data",
                "voice minutes",
                "sms",
                "consumption",
            )
        ):
            return "usage"

        if any(
            word in text
            for word in (
                "ticket",
                "tickets",
                "support",
                "case",
                "cases",
            )
        ):
            return "support"

        if any(
            word in text
            for word in (
                "device",
                "devices",
                "phone",
                "router",
                "tablet",
                "modem",
            )
        ):
            return "devices"

        if "plan" in text or "subscription" in text:
            return "subscription"

        if any(
            phrase in text
            for phrase in (
                "customer 360",
                "account overview",
                "account summary",
                "entire account",
                "everything about my account",
                "full profile",
                "all my account details",
                "at a glance",
            )
        ):
            return "account_summary"

        return None

    @staticmethod
    def _status_clarification() -> LLMIntentResponse:
        return LLMIntentResponse(
            intent=Intent.UNSUPPORTED,
            clarification=(
                "Which status would you like to check — "
                "your bill, payment, subscription, or support ticket?"
            ),
            options=[
                IntentOption(
                    label="Bill",
                    message="What's my current bill?",
                ),
                IntentOption(
                    label="Payment",
                    message="What's my latest payment status?",
                ),
                IntentOption(
                    label="Subscription",
                    message="What's my subscription status?",
                ),
                IntentOption(
                    label="Support ticket",
                    message="What's the status of my latest support ticket?",
                ),
            ],
        )

    @staticmethod
    def _context_month(
        context: ConversationContext,
    ) -> tuple[int | None, int | None]:
        if context.referenced_period is None:
            today = date.today()
            return today.month, today.year

        year_text, month_text = context.referenced_period.split(
            "-",
            maxsplit=1,
        )
        return int(month_text), int(year_text)