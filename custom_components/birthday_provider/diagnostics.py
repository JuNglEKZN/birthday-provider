"""Privacy-safe diagnostics for Birthday Provider."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import BirthdayProviderConfigEntry
from .const import STORAGE_VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BirthdayProviderConfigEntry
) -> dict[str, Any]:
    """Return aggregate-only diagnostics safe to attach to a public issue."""
    runtime_data = entry.runtime_data
    coordinator = runtime_data.coordinator
    return {
        "integration_version": "0.0.0",
        "provider_type": "fixture" if runtime_data.provider is not None else "none",
        "normalized_birthday_count": len(coordinator.birthdays),
        "active_event_count": len(coordinator.active_events),
        "last_successful_sync": (
            coordinator.last_successful_sync.isoformat()
            if coordinator.last_successful_sync is not None
            else None
        ),
        "last_sync_status": coordinator.last_sync_status,
        "ha_timezone": str(hass.config.time_zone),
        "snapshot_schema_version": STORAGE_VERSION,
    }
