from __future__ import annotations

import asyncio
import time
import uuid

from btc_detector import BTCSignalEvent
from market_data import Trade
from reaction_engine import ReactionEngine


class EventManager:
    def __init__(self, reaction_engine: ReactionEngine, observation_seconds: int, on_close, btc_reversion_percent: float = 0.10):
        self.reaction_engine = reaction_engine
        self.observation_seconds = observation_seconds
        self.on_close = on_close
        self.btc_reversion_percent = btc_reversion_percent
        self.latest_trades: dict[str, Trade] = {}
        self.active_event: BTCSignalEvent | None = None
        self._close_task: asyncio.Task | None = None

    async def handle_trade(self, trade: Trade, signal: dict | None = None) -> None:
        self.latest_trades[trade.symbol] = trade

        if signal and self.active_event is None:
            event = BTCSignalEvent(
                event_id=str(uuid.uuid4()),
                trigger_symbol="BTCUSDT",
                trigger_exchange_ts=signal["exchange_ts"],
                trigger_price=signal["price"],
                direction=signal["direction"],
                move_percent=signal["move_percent"],
                volume_60s=signal["volume_60s"],
                reference_volume=signal["reference_volume"],
                volume_ratio=signal["volume_ratio"],
                threshold_percent=signal["threshold_percent"],
                observation_seconds=self.observation_seconds,
            )
            self.reaction_engine.prepare_event(event, self.latest_trades)
            self.active_event = event
            self._close_task = asyncio.create_task(self._close_later(event))

        if self.active_event is not None and not self.active_event.closed:
            if trade.symbol in {"DOGEUSDT", "PEPEUSDT", "SHIBUSDT"}:
                self.reaction_engine.observe_trade(self.active_event, trade)
            if trade.symbol == "BTCUSDT" and signal is None:
                current_move = ((trade.price - self.active_event.trigger_price) / self.active_event.trigger_price) * 100.0
                if (self.active_event.direction == "up" and current_move < -self.btc_reversion_percent) or (
                    self.active_event.direction == "down" and current_move > self.btc_reversion_percent
                ):
                    self.active_event.btc_reverted = True

    async def _close_later(self, event: BTCSignalEvent) -> None:
        await asyncio.sleep(self.observation_seconds)
        self.close_event(event)

    def close_event(self, event: BTCSignalEvent) -> None:
        if event.closed:
            return
        event.closed = True
        for reaction in event.reactions.values():
            if reaction.status == "pending":
                reaction.status = "no_reaction"
        if self.active_event is event:
            self.active_event = None
        self.on_close(event)

    def shutdown(self) -> None:
        if self.active_event is not None:
            self.close_event(self.active_event)
        if self._close_task is not None and not self._close_task.done():
            self._close_task.cancel()
