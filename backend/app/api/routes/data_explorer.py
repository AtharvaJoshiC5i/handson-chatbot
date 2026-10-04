"""Read-only database explorer API for demos."""

from __future__ import annotations

import sqlite3

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.database.connection import get_db
from app.services.data_explorer_service import (
    DEFAULT_PAGE_SIZE,
    query_table,
    list_tables,
)


router = APIRouter(
    prefix="/data",
    tags=["data"],
)


@router.get("/tables")
def get_data_tables(
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, object]:
    try:
        tables = list_tables(db)
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database tables are unavailable.",
        ) from exc

    return {"tables": tables}


@router.get("/tables/{table_name}")
def get_table_rows(
    table_name: str,
    db: sqlite3.Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=100,
    ),
    q: str | None = Query(None),
    customer_id: str | None = Query(None),
    status: str | None = Query(None),
    account_status: str | None = Query(None),
    city: str | None = Query(None),
    plan_type: str | None = Query(None),
    subscription_id: str | None = Query(None),
    bill_id: str | None = Query(None),
    item_type: str | None = Query(None),
    payment_method: str | None = Query(None),
    category: str | None = Query(None),
    priority: str | None = Query(None),
    ticket_id: str | None = Query(None),
) -> dict[str, object]:
    filters = {
        "customer_id": customer_id or "",
        "status": status or "",
        "account_status": account_status or "",
        "city": city or "",
        "plan_type": plan_type or "",
        "subscription_id": subscription_id or "",
        "bill_id": bill_id or "",
        "item_type": item_type or "",
        "payment_method": payment_method or "",
        "category": category or "",
        "priority": priority or "",
        "ticket_id": ticket_id or "",
    }

    try:
        return query_table(
            db,
            table_name,
            page=page,
            page_size=page_size,
            filters=filters,
            search=q,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown table.",
        ) from None
    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database query failed.",
        ) from exc
