from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/intent/definitions.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    '            "month_count",\n        ),\n\n    _definition(\n        Intent.GET_PAYMENT_PROFILE,',
    '            "month_count",\n        ),\n    ),\n    _definition(\n        Intent.GET_PAYMENT_PROFILE,',
)
text = text.replace(
    '            "limit",\n        ),\n    ),\n\n    _definition(\n        Intent.GET_BILL_CHARGE_SUMMARY,',
    '            "limit",\n            *PLAN_TYPE,\n        ),\n    ),\n    _definition(\n        Intent.GET_BILL_CHARGE_SUMMARY,',
)
path.write_text(text, encoding="utf-8")
