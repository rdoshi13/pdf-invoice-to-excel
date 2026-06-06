from datetime import date

from src.participant_rules import active_participants, is_anuj_excluded


def test_anuj_included_before_exclusion_periods():
    assert not is_anuj_excluded(date(2024, 6, 2))
    assert active_participants(date(2024, 6, 2)) == ["Rakshit", "Ansh", "Rishabh", "Varun", "Anuj"]


def test_anuj_exclusion_ranges_are_inclusive():
    excluded_dates = [
        date(2024, 6, 3),
        date(2024, 6, 19),
        date(2024, 7, 10),
        date(2024, 8, 17),
        date(2024, 10, 24),
        date(2024, 10, 27),
        date(2025, 4, 1),
        date(2025, 5, 10),
    ]
    for order_date in excluded_dates:
        assert is_anuj_excluded(order_date)
        assert active_participants(order_date) == ["Rakshit", "Ansh", "Rishabh", "Varun"]


def test_anuj_excluded_on_and_after_november_8_2024():
    assert not is_anuj_excluded(date(2024, 11, 7))
    assert is_anuj_excluded(date(2024, 11, 8))
    assert is_anuj_excluded(date(2025, 5, 31))
