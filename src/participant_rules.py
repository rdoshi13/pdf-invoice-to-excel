from __future__ import annotations

from datetime import date


ALL_PARTICIPANTS = ["Rakshit", "Ansh", "Rishabh", "Varun", "Anuj"]
ANUJ = "Anuj"

ANUJ_EXCLUDED_RANGES = [
    (date(2024, 6, 3), date(2024, 6, 19)),
    (date(2024, 7, 10), date(2024, 8, 17)),
    (date(2024, 10, 24), date(2024, 10, 27)),
    (date(2024, 12, 16), date(2025, 1, 6)),
    (date(2025, 4, 1), date(2025, 5, 10)),
    (date(2025, 5, 31), date.max),
]

WALMART_ANUJ_EXCLUDED_FROM = date(2024, 11, 8)


def is_anuj_excluded(order_date: date) -> bool:
    if order_date >= WALMART_ANUJ_EXCLUDED_FROM:
        return True

    return any(start <= order_date <= end for start, end in ANUJ_EXCLUDED_RANGES)


def active_participants(order_date: date) -> list[str]:
    if not is_anuj_excluded(order_date):
        return list(ALL_PARTICIPANTS)

    return [participant for participant in ALL_PARTICIPANTS if participant != ANUJ]
