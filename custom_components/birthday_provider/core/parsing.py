"""Parsing for the minimal BDAY formats supported by the core."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from .models import BirthdayRawValue, BirthdayValidationError, _validate_date_parts

_DATED_BDAY = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})")
_YEARLESS_BDAY = re.compile(r"--(?P<month>\d{2})-(?P<day>\d{2})")


@dataclass(frozen=True, slots=True)
class ParsedBirthday:
    """Validated date components obtained from a BDAY value."""

    day: int
    month: int
    year: int | None

    def __post_init__(self) -> None:
        _validate_date_parts(self.day, self.month, self.year)


def parse_birthday(value: BirthdayRawValue) -> ParsedBirthday:
    """Parse a BDAY in ``YYYY-MM-DD`` or ``--MM-DD`` form.

    A ``date`` is accepted for standards-compliant provider libraries that expose
    a fully specified BDAY as a parsed Python date.
    """
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return ParsedBirthday(day=value.day, month=value.month, year=value.year)
    if not isinstance(value, str):
        raise BirthdayValidationError("BDAY must be a string or date")

    match = _DATED_BDAY.fullmatch(value)
    if match:
        return ParsedBirthday(
            day=int(match["day"]),
            month=int(match["month"]),
            year=int(match["year"]),
        )

    match = _YEARLESS_BDAY.fullmatch(value)
    if match:
        return ParsedBirthday(
            day=int(match["day"]), month=int(match["month"]), year=None
        )

    raise BirthdayValidationError("unsupported BDAY format")
