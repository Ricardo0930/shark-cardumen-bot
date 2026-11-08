import asyncio

from btc_detector import BTCDetector
from event_manager import EventManager
from market_data import Trade
from reaction_engine import ReactionEngine


def make_trade(symbol, price, qty, exchange_ts, local_received_ms=None):
    if local_received_ms is None:
        local_received_ms = exchange_ts
    return Trade(symbol=symbol, price=price, quantity=qty, exchange_ts=exchange_ts, local_received_ms=local_received_ms, latency_ms=max(0, local_received_ms - exchange_ts))


def test_btc_signal_detection():
    detector = BTCDetector(threshold_percent=0.5, volume_ratio=1.5, window_seconds=60, reference_minutes=2)

    # Build reference history with stable BTC values.
    for ts in [0, 10_000, 20_000, 30_000, 40_000, 50_000]:
        detector.update(make_trade("BTCUSDT", 100.0, 1.0, ts))

    # Strong recent movement + volume spike in the last 60 seconds.
    signal = detector.update(make_trade("BTCUSDT", 100.80, 10.0, 60_000))
    assert signal is not None
    assert signal["direction"] == "up"
    assert signal["move_percent"] > 0


def test_reaction_engine_marks_favorable_reaction():
    engine = ReactionEngine(minimum_percent=0.05)
    event = __import__("btc_detector").BTCSignalEvent(
        event_id="evt-1",
        trigger_symbol="BTCUSDT",
        trigger_exchange_ts=10_000,
        trigger_price=100.0,
        direction="up",
        move_percent=1.0,
        volume_60s=10.0,
        reference_volume=5.0,
        volume_ratio=2.0,
        threshold_percent=0.5,
        observation_seconds=300,
    )
    event.reactions["DOGEUSDT"] = __import__("btc_detector").Reaction(symbol="DOGEUSDT", reference_price=1.0, reference_exchange_ts=9_000, status="pending")
    trade = make_trade("DOGEUSDT", 1.10, 1.0, 12_000, local_received_ms=12_100)
    engine.observe_trade(event, trade)
    assert event.reactions["DOGEUSDT"].status == "reacted"
    assert event.reactions["DOGEUSDT"].direction_result == "favorable"


def test_event_manager_closes_without_reaction():
    async def run():
        engine = ReactionEngine(minimum_percent=0.05)
        closed = []
        manager = EventManager(engine, observation_seconds=1, on_close=lambda event: closed.append(event), btc_reversion_percent=0.10)
        await manager.handle_trade(make_trade("BTCUSDT", 100.0, 1.0, 1000), {"direction": "up", "move_percent": 1.0, "volume_60s": 10, "reference_volume": 5, "volume_ratio": 2.0, "price": 100.0, "exchange_ts": 1000, "threshold_percent": 0.5})
        await asyncio.sleep(1.1)
        assert len(closed) >= 1
        assert closed[0].reactions["DOGEUSDT"].status == "invalid_reference" or closed[0].reactions["DOGEUSDT"].status == "no_reaction"

    asyncio.run(run())
