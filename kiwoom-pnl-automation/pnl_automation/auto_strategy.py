from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal


@dataclass(frozen=True)
class Candle:
    symbol: str
    name: str
    open: Decimal
    close: Decimal
    volume: int

    @property
    def trading_value(self) -> Decimal:
        return self.close * Decimal(self.volume)


@dataclass(frozen=True)
class StockState:
    symbol: str
    name: str
    previous_open: Decimal
    previous_close: Decimal
    today_open: Decimal
    current_price: Decimal


@dataclass(frozen=True)
class Position:
    symbol: str
    buy_price: Decimal
    quantity: int
    bought_at: datetime


@dataclass(frozen=True)
class StrategySettings:
    top_trading_value_count: int = 30
    day_stop_loss_rate: Decimal = Decimal("-0.08")
    close_stop_loss_rate: Decimal = Decimal("-0.04")
    close_stop_start: time = time(15, 10)
    new_buy_cutoff: time = time(15, 0)
    min_hold_seconds_before_stop: int = 60


@dataclass(frozen=True)
class BuyDecision:
    should_buy: bool
    trigger_price: Decimal
    reason: str


@dataclass(frozen=True)
class SellDecision:
    should_sell: bool
    profit_rate: Decimal
    stop_loss_rate: Decimal
    reason: str


def top_by_trading_value(candles: list[Candle], limit: int = 30) -> list[Candle]:
    return sorted(candles, key=lambda candle: candle.trading_value, reverse=True)[:limit]


def buy_trigger_price(stock: StockState) -> Decimal:
    if stock.previous_close > stock.previous_open:
        return stock.previous_close
    return stock.previous_open


def stop_loss_rate(now: time, settings: StrategySettings) -> Decimal:
    if now >= settings.close_stop_start:
        return settings.close_stop_loss_rate
    return settings.day_stop_loss_rate


def decide_buy(
    stock: StockState,
    top_symbols: set[str],
    already_bought_symbols: set[str],
    now: datetime,
    settings: StrategySettings,
) -> BuyDecision:
    trigger = buy_trigger_price(stock)
    if stock.symbol not in top_symbols:
        return BuyDecision(False, trigger, "not_in_top_trading_value")
    if stock.symbol in already_bought_symbols:
        return BuyDecision(False, trigger, "already_bought_today")
    if now.time() >= settings.new_buy_cutoff:
        return BuyDecision(False, trigger, "after_new_buy_cutoff")
    if stock.current_price <= trigger:
        return BuyDecision(False, trigger, "not_breakout")
    return BuyDecision(True, trigger, "breakout")


def decide_sell(
    position: Position,
    current_price: Decimal,
    now: datetime,
    settings: StrategySettings,
) -> SellDecision:
    profit_rate = (current_price - position.buy_price) / position.buy_price
    active_stop = stop_loss_rate(now.time(), settings)
    held_seconds = (now - position.bought_at).total_seconds()
    if held_seconds < settings.min_hold_seconds_before_stop:
        return SellDecision(False, profit_rate, active_stop, "min_hold_time")
    if profit_rate <= active_stop:
        return SellDecision(True, profit_rate, active_stop, "stop_loss")
    return SellDecision(False, profit_rate, active_stop, "hold")
