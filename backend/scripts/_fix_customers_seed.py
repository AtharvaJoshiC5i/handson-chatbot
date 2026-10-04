from pathlib import Path

path = Path(__file__).resolve().parents[1] / "app/database/seed.py"
text = path.read_text(encoding="utf-8")
old = '''def _customers() -> list[tuple]:
    rows = []
    for customer in CUSTOMERS:
        rows.append(
            (
                *customer,
                "",
                "",
                "",
            )
        )
    rows[2] = (
        "CUST003",
        "Rohan Kapoor",
        "rohan.kapoor@example.com",
        "+919000000003",
        "Bengaluru",
        "42 MG Road, Indiranagar",
        "Karnataka",
        "560038",
        "ACTIVE",
        "2023-11-10",
    )
    return rows'''
new = '''def _customers() -> list[tuple]:
    rows = []
    for customer in CUSTOMERS:
        customer_id, name, email, phone, city, status, reg_date = customer
        rows.append(
            (
                customer_id,
                name,
                email,
                phone,
                city,
                "",
                "",
                "",
                status,
                reg_date,
            )
        )
    rows[2] = (
        "CUST003",
        "Rohan Kapoor",
        "rohan.kapoor@example.com",
        "+919000000003",
        "Bengaluru",
        "42 MG Road, Indiranagar",
        "Karnataka",
        "560038",
        "ACTIVE",
        "2023-11-10",
    )
    return rows'''
if old not in text:
    raise SystemExit("block not found")
path.write_text(text.replace(old, new), encoding="utf-8")
