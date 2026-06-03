from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace(",", "")
    if text.endswith("-"):
        text = "-" + text[:-1]
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def mask_account(account: str) -> str:
    digits = "".join(ch for ch in account if ch.isdigit())
    if len(digits) <= 4:
        return account
    return f"{digits[:3]}****{digits[-3:]}"


def pick(record: dict[str, Any], candidates: list[str]) -> Any:
    for key in candidates:
        if key in record and record[key] not in (None, ""):
            return record[key]
    lowered = {str(key).lower(): value for key, value in record.items()}
    for key in candidates:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return value
    return None
