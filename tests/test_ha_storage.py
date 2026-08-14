"""Home Assistant Store tests using synthetic normalized birthday data."""

from __future__ import annotations

from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.birthday_provider.core.models import Birthday
from custom_components.birthday_provider.storage import BirthdaySnapshot, BirthdayStore


async def test_store_round_trip_and_removal(hass: HomeAssistant) -> None:
    store = BirthdayStore(hass, "synthetic-entry")
    snapshot = BirthdaySnapshot(
        generated_at=dt_util.utcnow(),
        birthdays=(Birthday("synthetic-1", "Ada", 10, 8, 1984),),
    )

    await store.async_save(snapshot)

    assert await store.async_load() == snapshot

    await store.async_remove()

    assert await store.async_load() is None


async def test_store_rejects_snapshot_with_naive_timestamp(hass: HomeAssistant) -> None:
    store = BirthdayStore(hass, "synthetic-entry")
    await store._store.async_save(  # noqa: SLF001 - malformed storage regression test
        {
            "schema_version": 1,
            "generated_at": datetime(2026, 8, 10).isoformat(),
            "birthdays": [],
        }
    )

    assert await store.async_load() is None
