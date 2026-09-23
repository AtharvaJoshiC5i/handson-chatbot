"""Deterministic response generation for NexaTel."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.domain import TruthStatus
from app.truth.result import TruthResult


class ResponseService:
    """Convert TruthResult objects into user-facing responses."""

    def build_response(
        self,
        result: TruthResult,
    ) -> str:
        """Build a concise response from a verified backend result."""

        if result.status == TruthStatus.VERIFIED:
            return self._verified_response(result)

        if result.status == TruthStatus.NOT_FOUND:
            return result.message or (
                "I couldn't find matching information "
                "for your account."
            )

        if result.status == TruthStatus.AMBIGUOUS:
            return result.message or (
                "I need a little more information to answer that."
            )

        if result.status == TruthStatus.UNSUPPORTED:
            return result.message or (
                "That request isn't supported yet."
            )

        if result.status == TruthStatus.ACCESS_DENIED:
            return result.message or (
                "I can't access that information."
            )

        if result.status == TruthStatus.VALIDATION_ERROR:
            return result.message or (
                "The request contains invalid information."
            )

        if result.status == TruthStatus.DATABASE_ERROR:
            return result.message or (
                "I couldn't retrieve the information right now."
            )

        return (
            "I couldn't complete that request right now."
        )

    def _verified_response(
        self,
        result: TruthResult,
    ) -> str:
        """Format verified data based on its shape."""

        data = result.data

        if isinstance(data, list):
            return self._format_list(data)

        if isinstance(data, dict):
            return self._format_dict(data)

        return str(data)

    def _format_dict(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format common NexaTel dictionary responses."""

        if "plan_name" in data:
            return self._format_plan(data)

        if "account_status" in data:
            return self._format_account(data)

        if "total_usage" in data and "usage_type" in data:
            return self._format_usage(data)

        if "total_amount" in data and "bill_id" in data:
            return self._format_bill(data)

        if "total_spending" in data:
            return self._format_spending(data)

        if "percentage_change" in data and (
            "current_bill" in data
            and "previous_bill" in data
        ):
            return self._format_bill_comparison(data)

        if "payment_status" in data:
            return self._format_payment(data)

        if "renewal_date" in data:
            return self._format_renewal(data)

        return self._format_generic_dict(data)

    def _format_plan(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format current plan information."""

        plan_name = data.get("plan_name", "your plan")
        price = data.get("monthly_price")

        response = f"Your current plan is {plan_name}."

        if price is not None:
            response += f" The monthly price is ₹{self._money(price)}."

        if data.get("renewal_date"):
            response += (
                f" Your next renewal is on "
                f"{data['renewal_date']}."
            )

        return response

    def _format_account(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format account information."""

        name = data.get("name", "Customer")
        status = data.get("account_status", "UNKNOWN")

        return (
            f"Your account is currently {self._display(status)}. "
            f"Account holder: {name}."
        )

    def _format_usage(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format usage information."""

        usage_type = self._display(
            data.get("usage_type", "usage")
        )

        total = data.get("total_usage", 0)
        unit = data.get("unit", "")

        start_date = data.get("start_date")
        end_date = data.get("end_date")

        response = (
            f"Your {usage_type.lower()} usage for "
            f"{start_date} to {end_date} is "
            f"{total:g} {unit}."
        )

        return response

    def _format_bill(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format current bill information."""

        bill_id = data.get("bill_id", "the bill")
        total = data.get("total_amount", 0)
        outstanding = data.get("outstanding_amount")

        response = (
            f"Your bill {bill_id} is "
            f"₹{self._money(total)}."
        )

        if outstanding is not None:
            response += (
                f" The outstanding amount is "
                f"₹{self._money(outstanding)}."
            )

        status = data.get("derived_status")

        if status:
            response += (
                f" The bill status is "
                f"{self._display(status)}."
            )

        return response

    def _format_spending(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format total spending information."""

        total = data.get("total_spending", 0)
        count = data.get("bill_count", 0)

        return (
            f"Your total recorded spending across "
            f"{count} bill(s) is ₹{self._money(total)}."
        )

    def _format_bill_comparison(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format a bill comparison."""

        current_bill = data["current_bill"]
        previous_bill = data["previous_bill"]

        current_total = current_bill["total_amount"]
        previous_total = previous_bill["total_amount"]

        difference = data.get("difference", 0)
        percentage = data.get("percentage_change")

        response = (
            f"Bill {current_bill['bill_id']} is "
            f"₹{self._money(current_total)}, compared with "
            f"₹{self._money(previous_total)} for "
            f"bill {previous_bill['bill_id']}."
        )

        response += (
            f" The absolute difference is "
            f"₹{self._money(difference)}."
        )

        if percentage is not None:
            response += (
                f" That's a "
                f"{self._money(percentage)}% change."
            )

        return response

    def _format_payment(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format payment information."""

        status = data.get(
            "payment_status",
            data.get("status", "UNKNOWN"),
        )

        return (
            f"The latest payment status is "
            f"{self._display(status)}."
        )

    def _format_renewal(
        self,
        data: dict[str, Any],
    ) -> str:
        """Format renewal information."""

        renewal_date = data.get(
            "renewal_date",
            "unknown",
        )

        return (
            f"Your next plan renewal is on "
            f"{renewal_date}."
        )

    def _format_list(
        self,
        data: list[Any],
    ) -> str:
        """Format common list responses."""

        if not data:
            return "No records were found."

        first = data[0]

        if isinstance(first, dict):
            # Check payment records before bills because payment
            # records also contain bill_id.
            if "payment_id" in first:
                return self._format_payment_history(data)

            if (
                "bill_id" in first
                and "total_amount" in first
            ):
                return self._format_bill_history(data)

            if "ticket_id" in first:
                return self._format_ticket_history(data)

            if "device_id" in first:
                return self._format_device_history(data)

        return (
            f"I found {len(data)} record(s) "
            "for your account."
        )

    def _format_bill_history(
        self,
        bills: list[dict[str, Any]],
    ) -> str:
        """Format bill history."""

        lines = [
            f"Found {len(bills)} bill(s):"
        ]

        for bill in bills:
            lines.append(
                f"- {bill['bill_id']}: "
                f"₹{self._money(bill['total_amount'])} "
                f"({self._display(bill['status'])})"
            )

        return "\n".join(lines)

    def _format_payment_history(
        self,
        payments: list[dict[str, Any]],
    ) -> str:
        """Format payment history."""

        lines = [
            f"Found {len(payments)} payment(s):"
        ]

        for payment in payments:
            payment_id = payment.get(
                "payment_id",
                "unknown",
            )
            status = payment.get(
                "status",
                payment.get(
                    "payment_status",
                    "UNKNOWN",
                ),
            )
            amount = payment.get(
                "amount",
                0,
            )

            lines.append(
                f"- {payment_id}: "
                f"₹{self._money(amount)} "
                f"({self._display(status)})"
            )

        return "\n".join(lines)

    def _format_ticket_history(
        self,
        tickets: list[dict[str, Any]],
    ) -> str:
        """Format support-ticket history."""

        lines = [
            f"Found {len(tickets)} support ticket(s):"
        ]

        for ticket in tickets:
            ticket_id = ticket.get(
                "ticket_id",
                "unknown",
            )
            status = ticket.get(
                "status",
                "UNKNOWN",
            )

            lines.append(
                f"- {ticket_id}: "
                f"{self._display(status)}"
            )

        return "\n".join(lines)

    def _format_device_history(
        self,
        devices: list[dict[str, Any]],
    ) -> str:
        """Format device information."""

        lines = [
            f"Found {len(devices)} device(s):"
        ]

        for device in devices:
            device_name = device.get(
                "device_name",
                device.get(
                    "model",
                    device.get(
                        "device_id",
                        "Unknown device",
                    ),
                ),
            )

            status = device.get(
                "status",
                "UNKNOWN",
            )

            lines.append(
                f"- {device_name}: "
                f"{self._display(status)}"
            )

        return "\n".join(lines)

    def _format_generic_dict(
        self,
        data: dict[str, Any],
    ) -> str:
        """Fallback deterministic dictionary formatting."""

        parts: list[str] = []

        for key, value in data.items():
            if isinstance(value, (dict, list)):
                continue

            label = self._display(key)

            if isinstance(value, (int, float, Decimal)):
                if "amount" in key or "spending" in key:
                    value_text = f"₹{self._money(value)}"
                else:
                    value_text = str(value)
            else:
                value_text = str(value)

            parts.append(
                f"{label}: {value_text}"
            )

        if not parts:
            return "The requested information was verified."

        return "\n".join(parts)

    @staticmethod
    def _money(value: Any) -> str:
        """Format a monetary value."""

        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _display(value: Any) -> str:
        """Convert database enum-style strings into display text."""

        return str(value).replace(
            "_",
            " ",
        ).title()