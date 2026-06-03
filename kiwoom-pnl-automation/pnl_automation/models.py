from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class RealizedPnlRow:
    broker: str
    account: str
    account_alias: str
    trade_date: date
    market: str
    currency: str
    symbol: str
    name: str
    realized_pnl_krw: Decimal
    fees_taxes_krw: Decimal | None = None

    @property
    def month(self) -> str:
        return f"{self.trade_date.year:04d}-{self.trade_date.month:02d}"


@dataclass(frozen=True)
class AccountStatus:
    broker: str
    account: str
    alias: str
    status: str
    note: str = ""


@dataclass(frozen=True)
class CheckIssue:
    severity: str
    broker: str
    account: str
    message: str
