from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class Trade:
    symbol: str
    price: float
    quantity: float
    exchange_ts: int
    local_received_ms: int
    latency_ms: int

    @property
    def quote_volume(self) -> float:
        return self.price * self.quantity


def normalize_trade(payload: dict) -> Trade:
    """Normalize Binance trade payload from stream."""
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise ValueError("Trade payload is not a dictionary")

    symbol = str(data.get("s", "")).upper()
    price = float(data.get("p", 0))
    quantity = float(data.get("q", 0))
    exchange_ts = int(data.get("E", data.get("T", 0)))

    if not symbol or price <= 0 or quantity <= 0:
        raise ValueError("Trade payload has invalid symbol, price or quantity")

    now_ms = time.time_ns() // 1_000_000
    return Trade(
        symbol=symbol,
        price=price,
        quantity=quantity,
        exchange_ts=exchange_ts,
        local_received_ms=now_ms,
        latency_ms=max(0, now_ms - exchange_ts),
    )
