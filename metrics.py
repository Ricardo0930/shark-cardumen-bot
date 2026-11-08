from __future__ import annotations

from statistics import median


def summarize_events(events: list) -> dict:
    total = len(events)
    favorable = 0
    contrary = 0
    no_reaction = 0
    invalid_reference = 0
    latencies = []

    for event in events:
        for reaction in event.reactions.values():
            if reaction.status == "reacted" and reaction.direction_result == "favorable":
                favorable += 1
            elif reaction.status == "reacted" and reaction.direction_result == "contrary":
                contrary += 1
            elif reaction.status == "no_reaction":
                no_reaction += 1
            elif reaction.status == "invalid_reference":
                invalid_reference += 1
            if reaction.delay_ms is not None:
                latencies.append(reaction.delay_ms)

    return {
        "btc_signals": total,
        "reactions_favorable": favorable,
        "reactions_contrary": contrary,
        "absence_of_reaction": no_reaction,
        "invalid_reference": invalid_reference,
        "median_delay_ms": median(latencies) if latencies else None,
        "latencies_ms": sorted(latencies),
    }
