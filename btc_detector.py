from __future__ import annotations

from collections import deque

from market_data import Trade


class BTCDetector:
    def __init__(
        self,
        threshold_percent: float = 0.5,
        volume_ratio: float = 1.5,
        window_seconds: int = 60,
        reference_minutes: int = 60,
    ) -> None:
        if not 0.10 <= threshold_percent <= 2.50:
            raise ValueError("BTC threshold must be between 0.10 and 2.50 percent")
        self.threshold_percent = threshold_percent
        self.volume_ratio = volume_ratio
        self.window_seconds = window_seconds
        self.reference_minutes = reference_minutes
        self.window: deque[Trade] = deque()
        self.minute_history: deque[float] = deque(maxlen=reference_minutes)
        self.current_minute_bucket = None
        self.current_minute_volume = 0.0
        self.last_signal_ts = None

    def _bucket_key(self, exchange_ts: int) -> int:
        return exchange_ts // 60000

    def _rotate_bucket(self, trade: Trade) -> None:
        bucket_key = self._bucket_key(trade.exchange_ts)
        if self.current_minute_bucket is None:
            self.current_minute_bucket = bucket_key
            self.current_minute_volume = 0.0
        elif bucket_key != self.current_minute_bucket:
            self.minute_history.append(self.current_minute_volume)
            self.current_minute_bucket = bucket_key
            self.current_minute_volume = 0.0

    def _window_volume(self, now_ts: int) -> float:
        return sum(t.quote_volume for t in self.window if now_ts - t.exchange_ts <= self.window_seconds * 1000)

    def update(self, trade: Trade):
        if trade.symbol != "BTCUSDT":
            return None

        self._rotate_bucket(trade)
        self.current_minute_volume += trade.quote_volume
        self.window.append(trade)

        cutoff = trade.exchange_ts - self.window_seconds * 1000
        while self.window and self.window[0].exchange_ts < cutoff:
            self.window.popleft()

        if len(self.window) < 2:
            return None

        current_price = trade.price
        first_price = self.window[0].price
        move_percent = ((current_price - first_price) / first_price) * 100.0

        recent_volume = self._window_volume(trade.exchange_ts)
        if self.minute_history:
            reference_volume = sum(self.minute_history) / len(self.minute_history)
        else:
            reference_volume = 0.0

        if abs(move_percent) >= self.threshold_percent and reference_volume > 0 and (recent_volume / reference_volume) >= self.volume_ratio:
            if self.last_signal_ts is None or trade.exchange_ts - self.last_signal_ts >= 1000:
                self.last_signal_ts = trade.exchange_ts
                return {
                    "direction": "up" if move_percent > 0 else "down",
                    "move_percent": move_percent,
                    "volume_60s": recent_volume,
                    "reference_volume": reference_volume,
                    "volume_ratio": recent_volume / reference_volume,
                    "price": current_price,
                    "exchange_ts": trade.exchange_ts,
                    "threshold_percent": self.threshold_percent,
                }
        return None
