from __future__ import annotations

from dataclasses import dataclass, field

MEMECOINS = ("DOGEUSDT", "PEPEUSDT", "SHIBUSDT")


@dataclass(slots=True)
class Reaction:
    symbol: str
    reference_price: float | None
    reference_exchange_ts: int | None
    status: str = "pending"
    reaction_price: float | None = None
    reaction_exchange_ts: int | None = None
    reaction_pct: float | None = None
    delay_ms: int | None = None
    direction_result: str | None = None


@dataclass(slots=True)
class BTCSignalEvent:
    event_id: str
    trigger_symbol: str
    trigger_exchange_ts: int
    trigger_price: float
    direction: str
    move_percent: float
    volume_60s: float
    reference_volume: float
    volume_ratio: float
    threshold_percent: float
    observation_seconds: int
    reactions: dict[str, Reaction] = field(default_factory=dict)
    btc_reverted: bool = False
    closed: bool = False


class ReactionEngine:
    def __init__(self, minimum_percent: float = 0.05) -> None:
        if minimum_percent < 0:
            raise ValueError("minimum percent cannot be negative")
        self.minimum_percent = minimum_percent

    def prepare_event(self, event: BTCSignalEvent, latest_trades: dict[str, object]) -> None:
        for symbol in MEMECOINS:
            trade = latest_trades.get(symbol)
            if trade is None:
                event.reactions[symbol] = Reaction(symbol=symbol, reference_price=None, reference_exchange_ts=None, status="invalid_reference")
                continue
            event.reactions[symbol] = Reaction(
                symbol=symbol,
                reference_price=trade.price,
                reference_exchange_ts=trade.exchange_ts,
                status="pending",
            )

    def observe_trade(self, event: BTCSignalEvent, trade) -> None:
        reaction = event.reactions.get(trade.symbol)
        if reaction is None or reaction.status != "pending" or reaction.reference_price is None:
            return
        pct = ((trade.price - reaction.reference_price) / reaction.reference_price) * 100.0
        if abs(pct) < self.minimum_percent:
            return
        reaction.reaction_price = trade.price
        reaction.reaction_exchange_ts = trade.exchange_ts
        reaction.reaction_pct = pct
        reaction.delay_ms = max(0, trade.local_received_ms - event.trigger_exchange_ts)
        direction_multiplier = 1 if event.direction == "up" else -1
        reaction.direction_result = "favorable" if pct * direction_multiplier > 0 else "contrary"
        reaction.status = "reacted"
