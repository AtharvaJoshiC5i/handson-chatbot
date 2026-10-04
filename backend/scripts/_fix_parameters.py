from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/intent/parameters.py"
text = path.read_text(encoding="utf-8")
if '"plan_id"' in text:
    raise SystemExit(0)
text = text.replace(
    '        "device_id",\n    )',
    '        "device_id",\n        "plan_id",\n        "comparison_plan_id",\n    )',
)
path.write_text(text, encoding="utf-8")
