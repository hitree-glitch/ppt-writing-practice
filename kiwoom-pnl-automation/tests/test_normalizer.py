from unittest import TestCase

from pnl_automation.config import load_config
from pnl_automation.normalizer import normalize_kiwoom_records


class NormalizerTest(TestCase):
    def test_normalizer_masks_account_and_parses_values(self):
        config = load_config("config.example.json")
        rows, checks = normalize_kiwoom_records(
            [
                {
                    "account_no": "1234567890",
                    "dt": "20260103",
                    "market": "KOSPI",
                    "currency": "krw",
                    "stk_cd": "005930",
                    "stk_nm": "삼성전자",
                    "rlzt_pl": "12,345",
                    "fee_tax": "100",
                }
            ],
            config,
        )
        self.assertEqual(checks, [])
        self.assertEqual(rows[0].account, "123****890")
        self.assertEqual(rows[0].account_alias, "키움-국내")
        self.assertEqual(rows[0].market, "국내")
        self.assertEqual(rows[0].realized_pnl_krw, 12345)
