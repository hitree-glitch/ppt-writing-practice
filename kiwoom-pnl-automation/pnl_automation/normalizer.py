from __future__ import annotations

from decimal import Decimal
from typing import Any

from .config import AppConfig
from .models import CheckIssue, RealizedPnlRow
from .utils import mask_account, parse_date, parse_decimal, pick


def normalize_kiwoom_records(
    records: list[dict[str, Any]], config: AppConfig
) -> tuple[list[RealizedPnlRow], list[CheckIssue]]:
    rows: list[RealizedPnlRow] = []
    checks: list[CheckIssue] = []
    fields = config.kiwoom.field_map

    for index, record in enumerate(records, start=1):
        account_raw = str(pick(record, fields.get("account_number", [])) or "").strip()
        account_display = mask_account(account_raw) if config.report.mask_accounts else account_raw
        account_alias = config.kiwoom.account_aliases.get(account_raw, account_display or "키움 계좌")
        parsed_date = parse_date(pick(record, fields.get("date", [])))
        pnl = parse_decimal(pick(record, fields.get("realized_pnl_krw", [])))

        if not parsed_date:
            checks.append(CheckIssue("error", "키움증권", account_display, f"{index}행 날짜 누락/파싱 실패"))
            continue
        if pnl is None:
            checks.append(CheckIssue("error", "키움증권", account_display, f"{index}행 원화 실현손익 누락"))
            continue

        fees_taxes = parse_decimal(pick(record, fields.get("fees_taxes_krw", [])))
        market = str(pick(record, fields.get("market", [])) or "국내").strip()
        currency = str(pick(record, fields.get("currency", [])) or config.report.default_currency).strip()
        symbol = str(pick(record, fields.get("symbol", [])) or "").strip()
        name = str(pick(record, fields.get("name", [])) or "").strip()

        if market in ("", "KRX", "KOSPI", "KOSDAQ"):
            market = "국내"
        if currency.upper() != "KRW" and pnl == Decimal("0"):
            checks.append(CheckIssue("warn", "키움증권", account_display, f"{index}행 해외 원화 손익 0원 확인 필요"))

        rows.append(
            RealizedPnlRow(
                broker="키움증권",
                account=account_display,
                account_alias=account_alias,
                trade_date=parsed_date,
                market=market,
                currency=currency.upper(),
                symbol=symbol,
                name=name,
                realized_pnl_krw=pnl,
                fees_taxes_krw=fees_taxes,
            )
        )

    return rows, checks
