from datetime import date
from decimal import Decimal
from unittest import TestCase

from pnl_automation.models import AccountStatus, RealizedPnlRow
from pnl_automation.report import build_report_payload


class ReportTest(TestCase):
    def test_monthly_totals_match_raw_sum(self):
        rows = [
            RealizedPnlRow("키움증권", "123****890", "키움-국내", date(2026, 1, 1), "국내", "KRW", "A", "A", Decimal("100")),
            RealizedPnlRow("키움증권", "123****890", "키움-국내", date(2026, 1, 2), "국내", "KRW", "B", "B", Decimal("-40")),
            RealizedPnlRow("키움증권", "987****210", "키움-해외", date(2026, 2, 1), "해외", "USD", "C", "C", Decimal("70")),
        ]
        payload = build_report_payload(rows, [AccountStatus("삼성증권", "", "삼성증권", "미연동")], [])
        monthly = payload["Monthly"]
        self.assertIn(["2026-01", "키움증권", "키움-국내", "국내", 60], monthly)
        self.assertIn(["2026-02", "키움증권", "키움-해외", "해외", 70], monthly)
        self.assertEqual(sum(row[9] for row in payload["Raw"][1:]), 130)
