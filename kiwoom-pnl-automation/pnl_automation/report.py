from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .models import AccountStatus, CheckIssue, RealizedPnlRow


SheetPayload = dict[str, list[list[Any]]]


def build_report_payload(
    rows: list[RealizedPnlRow],
    accounts: list[AccountStatus],
    checks: list[CheckIssue],
) -> SheetPayload:
    return {
        "Dashboard": _dashboard(rows),
        "Monthly": _monthly(rows),
        "Raw": _raw(rows),
        "Accounts": _accounts(accounts),
        "Checks": _checks(checks),
    }


def _dashboard(rows: list[RealizedPnlRow]) -> list[list[Any]]:
    by_month: dict[str, Decimal] = defaultdict(Decimal)
    by_broker: dict[str, Decimal] = defaultdict(Decimal)
    by_account: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
    by_market: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        by_month[row.month] += row.realized_pnl_krw
        by_broker[row.broker] += row.realized_pnl_krw
        by_account[(row.broker, row.account_alias)] += row.realized_pnl_krw
        by_market[row.market] += row.realized_pnl_krw

    out: list[list[Any]] = [["월별 실현손익 리포트"], []]
    out.append(["전체 순손익", _money(sum((row.realized_pnl_krw for row in rows), Decimal()))])
    out.append(["거래 건수", len(rows)])
    out.append([])
    out.append(["월", "순손익(KRW)"])
    for month, amount in sorted(by_month.items()):
        out.append([month, _money(amount)])
    out.append([])
    out.append(["증권사", "순손익(KRW)"])
    for broker, amount in sorted(by_broker.items()):
        out.append([broker, _money(amount)])
    out.append([])
    out.append(["계좌", "순손익(KRW)"])
    for (_, account), amount in sorted(by_account.items()):
        out.append([account, _money(amount)])
    out.append([])
    out.append(["시장", "순손익(KRW)"])
    for market, amount in sorted(by_market.items()):
        out.append([market, _money(amount)])
    return out


def _monthly(rows: list[RealizedPnlRow]) -> list[list[Any]]:
    grouped: dict[tuple[str, str, str, str], Decimal] = defaultdict(Decimal)
    for row in rows:
        grouped[(row.month, row.broker, row.account_alias, row.market)] += row.realized_pnl_krw
    out = [["Month", "Broker", "Account", "Market", "RealizedPnL(KRW)"]]
    for key, amount in sorted(grouped.items()):
        out.append([*key, _money(amount)])
    return out


def _raw(rows: list[RealizedPnlRow]) -> list[list[Any]]:
    out = [[
        "Broker",
        "Account",
        "AccountAlias",
        "TradeDate",
        "Month",
        "Market",
        "Currency",
        "Symbol",
        "Name",
        "RealizedPnL(KRW)",
        "FeesTaxes(KRW)",
    ]]
    for row in sorted(rows, key=lambda item: (item.trade_date, item.broker, item.account_alias)):
        out.append([
            row.broker,
            row.account,
            row.account_alias,
            row.trade_date.isoformat(),
            row.month,
            row.market,
            row.currency,
            row.symbol,
            row.name,
            _money(row.realized_pnl_krw),
            _money(row.fees_taxes_krw) if row.fees_taxes_krw is not None else "",
        ])
    return out


def _accounts(accounts: list[AccountStatus]) -> list[list[Any]]:
    out = [["Broker", "Account", "Alias", "Status", "Note"]]
    for account in accounts:
        out.append([account.broker, account.account, account.alias, account.status, account.note])
    return out


def _checks(checks: list[CheckIssue]) -> list[list[Any]]:
    out = [["Severity", "Broker", "Account", "Message"]]
    for check in checks:
        out.append([check.severity, check.broker, check.account, check.message])
    return out


def _money(value: Decimal | None) -> int:
    if value is None:
        return 0
    return int(value.quantize(Decimal("1")))
