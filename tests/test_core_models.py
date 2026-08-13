from __future__ import annotations

from datetime import date

import pytest

from custom_components.birthday_provider.core.models import (
    ActiveBirthdayEvent,
    Birthday,
    BirthdayValidationError,
    RawContact,
)
from custom_components.birthday_provider.core.provider import FixtureProvider


def test_birthday_storage_round_trip() -> None:
    birthday = Birthday("person-1", "Ada", 10, 12, 1985)

    assert Birthday.from_storage(birthday.to_storage()) == birthday


@pytest.mark.parametrize("uid", ["", "   "])
def test_raw_contact_requires_uid(uid: str) -> None:
    with pytest.raises(BirthdayValidationError, match="uid"):
        RawContact(uid, "Ada", "1985-12-10")


def test_raw_contact_has_no_unrelated_contact_fields() -> None:
    contact = RawContact("person-1", "Ada", "1985-12-10")

    assert contact == RawContact("person-1", "Ada", "1985-12-10")
    with pytest.raises(AttributeError):
        _ = contact.email


def test_active_event_uses_concrete_date_not_days_until() -> None:
    event = ActiveBirthdayEvent("person-1", "Ada", date(2026, 8, 10), None)

    with pytest.raises(AttributeError):
        _ = event.days_until


@pytest.mark.asyncio
async def test_fixture_provider_returns_a_fresh_synthetic_snapshot() -> None:
    provider = FixtureProvider((RawContact("person-1", "Ada", date(1985, 12, 10)),))

    first = await provider.async_fetch_contacts()
    second = await provider.async_fetch_contacts()

    assert first == second
    assert first is not second
