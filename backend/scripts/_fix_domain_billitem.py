from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/models/domain.py"
text = path.read_text(encoding="utf-8")
if "class BillItemType" not in text:
    text = text.replace(
        "class BillSortOrder(str, Enum):",
        "class BillItemType(str, Enum):\n"
        '    PLAN_CHARGE = "PLAN_CHARGE"\n'
        '    ROAMING = "ROAMING"\n'
        '    DATA_ADDON = "DATA_ADDON"\n'
        '    TAX = "TAX"\n'
        '    OTHER = "OTHER"\n\n\n'
        "class BillSortOrder(str, Enum):",
    )
    path.write_text(text, encoding="utf-8")

client = Path(__file__).resolve().parents[1] / "app/llm/client.py"
ctext = client.read_text(encoding="utf-8")
if "PlanType," not in ctext.split("from app.models.domain import")[1].split(")")[0]:
    ctext = ctext.replace(
        "from app.models.domain import (\n    CustomerContext,",
        "from app.models.domain import (\n    CustomerContext,\n    PlanType,",
        1,
    )
    client.write_text(ctext, encoding="utf-8")
