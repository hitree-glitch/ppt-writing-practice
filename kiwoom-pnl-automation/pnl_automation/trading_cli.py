from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from decimal import Decimal

from .auto_strategy import (
    Candle,
    Position,
    StockState,
    StrategySettings,
    decide_buy,
    decide_sell,
    top_by_trading_value,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiwoom breakout strategy dry-run")
    parser.add_argument("--sample-data", action="store_true", help="Run with built-in sample data")
    parser.add_argument("--dry-run", action="store_true", help="Print decisions without orders")
    args = parser.parse_args(argv)

    if not args.sample_data:
        print("Live Kiwoom trading is intentionally disabled in this first version.")
        print("Run with: python -m pnl_automation.trading_cli --sample-data --dry-run")
        return 2

    settings = StrategySettings()
    now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    previous_candles, states = _sample_market()
    top_symbols = {item.symbol for item in top_by_trading_value(previous_candles, settings.top_trading_value_count)}
    already_bought: set[str] = set()
    decisions: list[dict[str, object]] = []

    for state in states:
        decision = decide_buy(state, top_symbols, already_bought, now, settings)
        decisions.append(
            {
                "symbol": state.symbol,
                "name": state.name,
                "action": "BUY" if decision.should_buy else "SKIP",
                "reason": decision.reason,
                "trigger_price": str(decision.trigger_price),
                "current_price": str(state.current_price),
            }
        )
        if decision.should_buy:
            already_bought.add(state.symbol)

    example_position = Position("005930", Decimal("76000"), 10, now - timedelta(minutes=10))
    sell = decide_sell(example_position, Decimal("72800"), now.replace(hour=15, minute=11), settings)
    decisions.append(
        {
            "symbol": example_position.symbol,
            "action": "SELL" if sell.should_sell else "HOLD",
            "reason": sell.reason,
            "profit_rate": f"{sell.profit_rate:.4f}",
            "stop_loss_rate": f"{sell.stop_loss_rate:.4f}",
        }
    )

    print(json.dumps(decisions, ensure_ascii=False, indent=2))
    return 0


def _sample_market() -> tuple[list[Candle], list[StockState]]:
    previous_candles = [
        Candle("005930", "Samsung Electronics", Decimal("74000"), Decimal("76000"), 30_000_000),
        Candle("000660", "SK hynix", Decimal("210000"), Decimal("205000"), 8_000_000),
        Candle("035420", "NAVER", Decimal("180000"), Decimal("184000"), 2_000_000),
    ]
    states = [
        StockState("005930", "Samsung Electronics", Decimal("74000"), Decimal("76000"), Decimal("76200"), Decimal("76400")),
        StockState("000660", "SK hynix", Decimal("210000"), Decimal("205000"), Decimal("207000"), Decimal("211000")),
        StockState("035420", "NAVER", Decimal("180000"), Decimal("184000"), Decimal("183000"), Decimal("183500")),
    ]
    return previous_candles, states


if __name__ == "__main__":
    raise SystemExit(main())
