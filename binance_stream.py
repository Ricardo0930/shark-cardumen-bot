from __future__ import annotations

import asyncio
import json
import logging

import websockets

from market_data import normalize_trade, Trade

LOGGER = logging.getLogger(__name__)


class BinanceStream:
    def __init__(
        self,
        base_url: str,
        symbols: list[str],
        on_trade,
        reconnect_initial_delay: float = 1.0,
        reconnect_max_delay: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.symbols = [s.upper() for s in symbols]
        self.on_trade = on_trade
        self.reconnect_initial_delay = reconnect_initial_delay
        self.reconnect_max_delay = reconnect_max_delay

    @property
    def stream_url(self) -> str:
        stream_names = "/".join(f"{symbol.lower()}@trade" for symbol in self.symbols)
        return f"{self.base_url}/stream?streams={stream_names}"

    async def run_forever(self) -> None:
        delay = self.reconnect_initial_delay
        while True:
            try:
                LOGGER.info("Connecting to Binance public stream: %s", self.stream_url)
                async with websockets.connect(self.stream_url, ping_interval=20, ping_timeout=20) as ws:
                    LOGGER.info("Connected to Binance public stream for %s", ", ".join(self.symbols))
                    delay = self.reconnect_initial_delay
                    async for raw in ws:
                        try:
                            payload = json.loads(raw)
                            if "data" not in payload:
                                continue
                            trade = normalize_trade(payload)
                            await self.on_trade(trade)
                        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
                            LOGGER.exception("Malformed trade payload ignored")
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("Stream connection lost. Reconnecting in %.1f seconds", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, self.reconnect_max_delay)
