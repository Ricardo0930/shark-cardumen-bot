from __future__ import annotations

import asyncio
import json
import logging

from binance_stream import BinanceStream
from btc_detector import BTCDetector
from event_manager import EventManager
from market_data import Trade
from metrics import summarize_events
from reaction_engine import ReactionEngine
from storage import CSVStorage

LOGGER = logging.getLogger(__name__)


def load_config(path: str = "config.json") -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


async def run_bot(config: dict) -> None:
    detector = BTCDetector(
        threshold_percent=config["btc_threshold_percent"],
        volume_ratio=config["btc_volume_ratio"],
        window_seconds=config["btc_window_seconds"],
        reference_minutes=config["reference_minutes"],
    )
    engine = ReactionEngine(minimum_percent=config["min_reaction_percent"])
    storage = CSVStorage(config["output_csv"])
    closed_events = []

    def on_close(event) -> None:
        storage.save_event(event)
        closed_events.append(event)
        LOGGER.info("Event closed: %s | summary=%s", event.event_id, summarize_events(closed_events))

    event_manager = EventManager(engine, config["observation_seconds"], on_close, config["btc_reversion_percent"])

    async def handle_trade(trade: Trade) -> None:
        signal = None
        if trade.symbol == "BTCUSDT":
            signal = detector.update(trade)
            if signal:
                LOGGER.warning("BTC signal triggered: %s | move_pct=%.4f | ratio=%.3f", signal["direction"], signal["move_percent"], signal["volume_ratio"])
        await event_manager.handle_trade(trade, signal)

    stream = BinanceStream(
        base_url=config["websocket_url"].replace("/stream", ""),
        symbols=config["symbols"],
        on_trade=handle_trade,
        reconnect_initial_delay=config["reconnect_initial_seconds"],
        reconnect_max_delay=config["reconnect_max_seconds"],
    )

    try:
        await stream.run_forever()
    finally:
        event_manager.shutdown()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    if config.get("demo_trading_enabled"):
        raise RuntimeError("Trade execution is disabled by design. Use read-only market data only.")
    asyncio.run(run_bot(config))


if __name__ == "__main__":
    main()
