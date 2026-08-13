from __future__ import annotations

from datetime import date

import pytest

from custom_components.birthday_provider.core.models import (
    BirthdayValidationError,
    RawContact,
)
from custom_components.birthday_provider.core.normalization import normalize_contact
from custom_components.birthday_provider.core.parsing import parse_birthday


def test_parses_bday_with_year() -> None:
    assert parse_birthday("1985-12-10").year == 1985
    assert normalize_contact(RawContact("ada", "Ada", "1985-12-10")).to_storage() == {
        "id": "ada",
        "name": "Ada",
        "day": 10,
        "month": 12,
        "year": 1985,
    }


def test_parses_bday_without_year() -> None:
    parsed = parse_birthday("--08-17")

    assert (parsed.day, parsed.month, parsed.year) == (17, 8, None)


def test_accepts_a_parsed_date_value() -> None:
    assert parse_birthday(date(1985, 12, 10)).year == 1985


@pytest.mark.parametrize(
    "value", ["1985-13-10", "1985-02-30", "--00-01", "--04-31", "10-12-1985"]
)
def test_rejects_invalid_month_day_and_format(value: str) -> None:
    with pytest.raises(BirthdayValidationError):
        parse_birthday(value)


@pytest.mark.parametrize("value", ["0000-01-01", "1900-01-01", "1970-01-01"])
def test_rejects_placeholder_years(value: str) -> None:
    with pytest.raises(BirthdayValidationError, match="placeholder"):
        parse_birthday(value)
