from __future__ import annotations

from datetime import date
from decimal import Decimal

from .models import RealizedPnlRow


def sample_rows() -> list[RealizedPnlRow]:
    return [
        RealizedPnlRow("키움증권", "123****890", "키움-국내", date(2026, 1, 8), "국내", "KRW", "005930", "삼성전자", Decimal("125000"), Decimal("1200")),
        RealizedPnlRow("키움증권", "123****890", "키움-국내", date(2026, 1, 22), "국내", "KRW", "000660", "SK하이닉스", Decimal("-43000"), Decimal("900")),
        RealizedPnlRow("키움증권", "987****210", "키움-해외", date(2026, 2, 14), "해외", "USD", "AAPL", "Apple", Decimal("72000"), Decimal("3000")),
        RealizedPnlRow("키움증권", "987****210", "키움-해외", date(2026, 3, 2), "해외", "USD", "MSFT", "Microsoft", Decimal("31000"), Decimal("2500")),
    ]
