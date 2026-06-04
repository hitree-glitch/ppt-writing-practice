from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest import TestCase

from pnl_automation.auto_strategy import (
    Candle,
    Position,
    StockState,
    StrategySettings,
    buy_trigger_price,
    decide_buy,
    decide_sell,
    stop_loss_rate,
    top_by_trading_value,
)


class AutoStrategyTest(TestCase):
    def test_bullish_previous_day_breaks_previous_close(self):
        stock = StockState("A", "Alpha", Decimal("100"), Decimal("110"), Decimal("111"), Decimal("112"))
        self.assertEqual(buy_trigger_price(stock), Decimal("110"))

    def test_bearish_previous_day_breaks_previous_open(self):
        stock = StockState("A", "Alpha", Decimal("110"), Decimal("100"), Decimal("101"), Decimal("111"))
        self.assertEqual(buy_trigger_price(stock), Decimal("110"))

    def test_buy_requires_top_trading_value_and_breakout(self):
        stock = StockState("A", "Alpha", Decimal("110"), Decimal("100"), Decimal("101"), Decimal("111"))
        decision = decide_buy(stock, {"A"}, set(), datetime(2026, 6, 5, 10, 0), StrategySettings())
        self.assertTrue(decision.should_buy)
        self.assertEqual(decision.reason, "breakout")

    def test_buy_blocks_symbols_outside_top_trading_value(self):
        stock = StockState("A", "Alpha", Decimal("110"), Decimal("100"), Decimal("101"), Decimal("111"))
        decision = decide_buy(stock, set(), set(), datetime(2026, 6, 5, 10, 0), StrategySettings())
        self.assertFalse(decision.should_buy)
        self.assertEqual(decision.reason, "not_in_top_trading_value")

    def test_close_stop_loss_is_tighter(self):
        settings = StrategySettings()
        self.assertEqual(stop_loss_rate(time(10, 0), settings), Decimal("-0.08"))
        self.assertEqual(stop_loss_rate(time(15, 10), settings), Decimal("-0.04"))

    def test_sell_uses_close_stop_loss_near_close(self):
        now = datetime(2026, 6, 5, 15, 11)
        position = Position("A", Decimal("100"), 1, now - timedelta(minutes=10))
        decision = decide_sell(position, Decimal("95"), now, StrategySettings())
        self.assertTrue(decision.should_sell)
        self.assertEqual(decision.stop_loss_rate, Decimal("-0.04"))

    def test_top_by_trading_value_uses_close_times_volume(self):
        candles = [
            Candle("A", "Alpha", Decimal("10"), Decimal("10"), 10),
            Candle("B", "Beta", Decimal("5"), Decimal("5"), 100),
        ]
        self.assertEqual(top_by_trading_value(candles, 1)[0].symbol, "B")
