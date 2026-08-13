"""Canonical, provider-neutral birthday models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

type BirthdayRawValue = str | date


class BirthdayValidationError(ValueError):
    """Raised when birthday-domain input is invalid."""


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        msg = f"{field_name} must be a non-empty string"
        raise BirthdayValidationError(msg)


def _validate_date_parts(day: int, month: int, year: int | None) -> None:
    if isinstance(day, bool) or isinstance(month, bool):
        raise BirthdayValidationError("day and month must be integers")
    if not isinstance(day, int) or not isinstance(month, int):
        raise BirthdayValidationError("day and month must be integers")
    if year is not None and (isinstance(year, bool) or not isinstance(year, int)):
        raise BirthdayValidationError("year must be an integer or None")
    if year in {0, 1900, 1970}:
        raise BirthdayValidationError("year is a forbidden placeholder")

    validation_year = year if year is not None else 2000
    try:
        date(validation_year, month, day)
    except ValueError as error:
        raise BirthdayValidationError("birthday has an invalid day or month") from error


@dataclass(frozen=True, slots=True)
class RawContact:
    """The only contact fields that may enter the birthday pipeline."""

    uid: str
    display_name: str
    birthday_raw: BirthdayRawValue

    def __post_init__(self) -> None:
        _require_text(self.uid, "uid")
        _require_text(self.display_name, "display_name")
        if not isinstance(self.birthday_raw, (str, date)):
            raise BirthdayValidationError("birthday_raw must be a string or date")


@dataclass(frozen=True, slots=True)
class Birthday:
    """Normalized birthday retained in the persistent catalog."""

    id: str
    name: str
    day: int
    month: int
    year: int | None

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.name, "name")
        _validate_date_parts(self.day, self.month, self.year)

    def to_storage(self) -> dict[str, Any]:
        """Return a JSON-compatible representation for a future storage layer."""
        return {
            "id": self.id,
            "name": self.name,
            "day": self.day,
            "month": self.month,
            "year": self.year,
        }

    @classmethod
    def from_storage(cls, value: dict[str, Any]) -> Birthday:
        """Restore a validated birthday from JSON-compatible storage data."""
        try:
            return cls(
                id=value["id"],
                name=value["name"],
                day=value["day"],
                month=value["month"],
                year=value["year"],
            )
        except (KeyError, TypeError) as error:
            message = "invalid birthday storage representation"
            raise BirthdayValidationError(message) from error


@dataclass(frozen=True, slots=True)
class ActiveBirthdayEvent:
    """A concrete birthday occurrence within the active date window."""

    id: str
    name: str
    date: date
    age: int | None

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.name, "name")
        if not isinstance(self.date, date):
            raise BirthdayValidationError("date must be a date")
        if self.age is not None and (
            isinstance(self.age, bool) or not isinstance(self.age, int)
        ):
            raise BirthdayValidationError("age must be an integer or None")
