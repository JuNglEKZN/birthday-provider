from __future__ import annotations

from datetime import date

from custom_components.birthday_provider.core.birthdays import (
    active_birthday_events,
    birthday_occurrence,
    calculate_age,
    sort_birthdays,
)
from custom_components.birthday_provider.core.models import Birthday


def test_age_for_known_and_unknown_year() -> None:
    occurrence = date(2026, 8, 17)

    assert calculate_age(Birthday("known", "Ada", 17, 8, 1984), occurrence) == 42
    assert calculate_age(Birthday("unknown", "Ada", 17, 8, None), occurrence) is None


def test_february_29_uses_february_29_in_a_leap_year() -> None:
    birthday = Birthday("leap", "Leap", 29, 2, 2000)

    assert birthday_occurrence(birthday, date(2028, 2, 28)) == date(2028, 2, 29)


def test_february_29_uses_march_1_in_a_non_leap_year() -> None:
    birthday = Birthday("leap", "Leap", 29, 2, 2000)
    occurrence = birthday_occurrence(birthday, date(2029, 2, 28))

    assert occurrence == date(2029, 3, 1)
    assert calculate_age(birthday, occurrence) == 29


def test_occurrence_rolls_over_at_month_and_year_boundaries() -> None:
    month_boundary = birthday_occurrence(
        Birthday("month", "Month", 1, 9, None), date(2026, 8, 31)
    )
    year_boundary = birthday_occurrence(
        Birthday("year", "Year", 1, 1, None), date(2026, 12, 31)
    )

    assert month_boundary == date(2026, 9, 1)
    assert year_boundary == date(2027, 1, 1)


def test_active_window_includes_days_zero_through_three_and_excludes_day_four() -> None:
    as_of = date(2026, 8, 10)
    birthdays = [
        Birthday(str(offset), f"Person {offset}", 10 + offset, 8, None)
        for offset in range(5)
    ]

    events = active_birthday_events(birthdays, as_of)

    assert [event.date for event in events] == [
        date(2026, 8, day) for day in range(10, 14)
    ]


def test_active_window_crosses_month_and_year_boundaries() -> None:
    birthdays = [
        Birthday("dec-31", "December", 31, 12, None),
        Birthday("jan-1", "January", 1, 1, None),
        Birthday("jan-3", "Three", 3, 1, None),
        Birthday("jan-4", "Four", 4, 1, None),
    ]

    events = active_birthday_events(birthdays, date(2026, 12, 31))

    assert [event.id for event in events] == ["dec-31", "jan-1", "jan-3"]


def test_multiple_birthdays_on_one_day_have_deterministic_active_order() -> None:
    birthdays = [
        Birthday("z", "zoe", 10, 8, None),
        Birthday("a", "Álvaro", 10, 8, None),
        Birthday("b", "alex", 10, 8, None),
        Birthday("c", "Alex", 10, 8, None),
    ]

    events = active_birthday_events(birthdays, date(2026, 8, 10))

    assert [event.id for event in events] == ["b", "c", "z", "a"]


def test_normalized_birthdays_have_deterministic_canonical_order() -> None:
    birthdays = [
        Birthday("z", "zoe", 10, 8, None),
        Birthday("early", "Later", 9, 8, None),
        Birthday("b", "alex", 10, 8, None),
        Birthday("c", "Alex", 10, 8, None),
    ]

    assert [birthday.id for birthday in sort_birthdays(birthdays)] == [
        "early",
        "b",
        "c",
        "z",
    ]
