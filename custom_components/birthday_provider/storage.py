"""Persistent storage for the minimal normalized birthday snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY_PREFIX, STORAGE_VERSION
from .core.models import Birthday, BirthdayValidationError


@dataclass(frozen=True, slots=True)
class BirthdaySnapshot:
    """A fully normalized source snapshot, never an active-event cache."""

    generated_at: datetime
    birthdays: tuple[Birthday, ...]


class BirthdayStore:
    """Read and write a versioned minimal birthday catalog."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._key = f"{STORAGE_KEY_PREFIX}.{entry_id}"
        self._store = self._new_store()

    def _new_store(self) -> Store[dict[str, Any]]:
        """Create a Store instance with no retained in-memory payload."""
        return Store[dict[str, Any]](
            self._hass,
            STORAGE_VERSION,
            self._key,
        )

    async def async_load(self) -> BirthdaySnapshot | None:
        """Load a valid snapshot, treating unavailable or malformed data as absent."""
        data = await self._store.async_load()
        if data is None:
            return None
        try:
            if data["schema_version"] != STORAGE_VERSION:
                return None
            generated_at = datetime.fromisoformat(data["generated_at"])
            if generated_at.tzinfo is None:
                return None
            birthdays = tuple(
                Birthday.from_storage(value) for value in data["birthdays"]
            )
        except (BirthdayValidationError, KeyError, TypeError, ValueError):
            return None
        return BirthdaySnapshot(generated_at=generated_at, birthdays=birthdays)

    async def async_save(self, snapshot: BirthdaySnapshot) -> None:
        """Persist the complete normalized catalog in JSON-compatible form."""
        await self._store.async_save(
            {
                "schema_version": STORAGE_VERSION,
                "generated_at": snapshot.generated_at.isoformat(),
                "birthdays": [birthday.to_storage() for birthday in snapshot.birthdays],
            }
        )

    async def async_remove(self) -> None:
        """Remove the integration-specific snapshot for this config entry."""
        await self._store.async_remove()
        self._store = self._new_store()
