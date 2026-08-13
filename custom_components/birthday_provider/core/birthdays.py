"""Pure calendar calculations for normalized birthdays."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from .models import ActiveBirthdayEvent, Birthday

ACTIVE_WINDOW_DAYS = 3


def _date_in_year(birthday: Birthday, year: int) -> date:
    """Return the policy-compliant occurrence of a birthday in ``year``."""
    if birthday.month == 2 and birthday.day == 29:
        try:
            return date(year, 2, 29)
        except ValueError:
            return date(year, 3, 1)
    return date(year, birthday.month, birthday.day)


def birthday_occurrence(birthday: Birthday, as_of: date) -> date:
    """Return the next concrete occurrence on or after ``as_of``."""
    occurrence = _date_in_year(birthday, as_of.year)
    if occurrence < as_of:
        occurrence = _date_in_year(birthday, as_of.year + 1)
    return occurrence


def calculate_age(birthday: Birthday, occurrence: date) -> int | None:
    """Calculate age for one concrete occurrence without inventing a birth year."""
    if birthday.year is None:
        return None
    return occurrence.year - birthday.year


def sort_birthdays(birthdays: Iterable[Birthday]) -> list[Birthday]:
    """Sort normalized birthdays in the canonical deterministic order."""
    return sorted(
        birthdays,
        key=lambda birthday: (
            birthday.month,
            birthday.day,
            birthday.name.casefold(),
            birthday.id,
        ),
    )


def sort_active_events(
    events: Iterable[ActiveBirthdayEvent],
) -> list[ActiveBirthdayEvent]:
    """Sort active events in the canonical deterministic order."""
    return sorted(
        events,
        key=lambda event: (event.date, event.name.casefold(), event.id),
    )


def active_birthday_events(
    birthdays: Iterable[Birthday], as_of: date
) -> list[ActiveBirthdayEvent]:
    """Return events in the fixed inclusive active window from 0 through +3 days."""
    window_end = as_of + timedelta(days=ACTIVE_WINDOW_DAYS)
    events = []
    for birthday in birthdays:
        occurrence = birthday_occurrence(birthday, as_of)
        if occurrence <= window_end:
            events.append(
                ActiveBirthdayEvent(
                    id=birthday.id,
                    name=birthday.name,
                    date=occurrence,
                    age=calculate_age(birthday, occurrence),
                )
            )
    return sort_active_events(events)
