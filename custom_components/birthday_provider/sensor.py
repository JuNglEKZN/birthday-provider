"""Aggregated sensors for Birthday Provider."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BirthdayProviderConfigEntry
from .const import DOMAIN
from .core.birthdays import ACTIVE_WINDOW_DAYS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BirthdayProviderConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the aggregated birthday sensors."""
    async_add_entities(
        [
            BirthdayProviderActiveSensor(entry),
            BirthdayProviderLastSyncSensor(entry),
        ]
    )


class _BirthdayProviderSensor(SensorEntity):
    """Common setup for sensors backed by one runtime coordinator."""

    _attr_has_entity_name = True

    def __init__(self, entry: BirthdayProviderConfigEntry, suffix: str) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._remove_listener: Callable[[], None] | None = None

    @property
    def _coordinator(self):
        return self._entry.runtime_data.coordinator

    async def async_added_to_hass(self) -> None:
        """Subscribe to active-view updates after entity registration."""
        self._remove_listener = self._coordinator.async_add_listener(
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from the runtime coordinator."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None


class BirthdayProviderActiveSensor(_BirthdayProviderSensor):
    """Expose only the short active birthday window."""

    _attr_translation_key = "active_birthdays"
    _attr_icon = "mdi:cake-variant"

    def __init__(self, entry: BirthdayProviderConfigEntry) -> None:
        super().__init__(entry, "active_birthdays")
        self.entity_id = f"sensor.{DOMAIN}"

    @property
    def native_value(self) -> int:
        """Return the number of active birthday events."""
        return len(self._coordinator.active_events)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose only active events; the complete catalog remains internal."""
        return {
            "as_of": self._coordinator.as_of.isoformat(),
            "window_days": ACTIVE_WINDOW_DAYS,
            "events": [
                {
                    "id": event.id,
                    "name": event.name,
                    "date": event.date.isoformat(),
                    "age": event.age,
                }
                for event in self._coordinator.active_events
            ],
        }


class BirthdayProviderLastSyncSensor(_BirthdayProviderSensor):
    """Expose the timestamp of the last successful catalog snapshot."""

    _attr_translation_key = "last_sync"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, entry: BirthdayProviderConfigEntry) -> None:
        super().__init__(entry, "last_sync")
        self.entity_id = f"sensor.{DOMAIN}_last_sync"

    @property
    def native_value(self):
        """Return the snapshot timestamp, if a fixture or cache was loaded."""
        return self._coordinator.last_successful_sync

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose category-level status without personal data."""
        provider = (
            "fixture"
            if type(self._entry.runtime_data.provider).__name__ == "FixtureProvider"
            else "icloud_carddav"
        )
        return {"status": self._coordinator.last_sync_status, "provider": provider}
