from __future__ import annotations

import csv
import os
from pathlib import Path


class CSVStorage:
    def __init__(self, filepath: str) -> None:
        self.path = Path(filepath)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_event(self, event) -> None:
        fieldnames = [
            "event_id",
            "trigger_symbol",
            "trigger_exchange_ts",
            "trigger_price",
            "direction",
            "move_percent",
            "volume_60s",
            "reference_volume",
            "volume_ratio",
            "threshold_percent",
            "symbol",
            "reference_price",
            "reference_exchange_ts",
            "reaction_price",
            "reaction_exchange_ts",
            "reaction_pct",
            "delay_ms",
            "status",
            "direction_result",
            "btc_reverted",
        ]

        file_exists = self.path.exists() and self.path.stat().st_size > 0
        with self.path.open("a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for reaction in event.reactions.values():
                writer.writerow({
                    "event_id": event.event_id,
                    "trigger_symbol": event.trigger_symbol,
                    "trigger_exchange_ts": event.trigger_exchange_ts,
                    "trigger_price": event.trigger_price,
                    "direction": event.direction,
                    "move_percent": event.move_percent,
                    "volume_60s": event.volume_60s,
                    "reference_volume": event.reference_volume,
                    "volume_ratio": event.volume_ratio,
                    "threshold_percent": event.threshold_percent,
                    "symbol": reaction.symbol,
                    "reference_price": reaction.reference_price,
                    "reference_exchange_ts": reaction.reference_exchange_ts,
                    "reaction_price": reaction.reaction_price,
                    "reaction_exchange_ts": reaction.reaction_exchange_ts,
                    "reaction_pct": reaction.reaction_pct,
                    "delay_ms": reaction.delay_ms,
                    "status": reaction.status,
                    "direction_result": reaction.direction_result,
                    "btc_reverted": event.btc_reverted,
                })
            csvfile.flush()
            os.fsync(csvfile.fileno())
