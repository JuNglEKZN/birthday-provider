"""Birthday Provider Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import BirthdayProviderCoordinator
    from .core.provider import ContactProvider
    from .storage import BirthdayStore


type BirthdayProviderConfigEntry = Any


@dataclass(slots=True)
class BirthdayProviderRuntimeData:
    """Runtime objects owned by one Birthday Provider config entry."""

    coordinator: BirthdayProviderCoordinator
    storage: BirthdayStore
    provider: ContactProvider | None


async def async_setup_entry(
    hass: HomeAssistant, entry: BirthdayProviderConfigEntry
) -> bool:
    """Set up Birthday Provider from a config entry."""
    from homeassistant.const import Platform

    from .coordinator import BirthdayProviderCoordinator
    from .provider import async_get_fixture_provider
    from .storage import BirthdayStore

    storage = BirthdayStore(hass, entry.entry_id)
    provider = async_get_fixture_provider(hass, entry.entry_id)
    coordinator = BirthdayProviderCoordinator(hass, storage, provider)
    await coordinator.async_initialize()

    entry.runtime_data = BirthdayProviderRuntimeData(
        coordinator=coordinator,
        storage=storage,
        provider=provider,
    )
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BirthdayProviderConfigEntry
) -> bool:
    """Unload a Birthday Provider config entry."""
    from homeassistant.const import Platform

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    ):
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok


async def async_remove_entry(
    hass: HomeAssistant, entry: BirthdayProviderConfigEntry
) -> None:
    """Remove the entry's normalized birthday snapshot."""
    from .provider import async_remove_fixture_provider
    from .storage import BirthdayStore

    await BirthdayStore(hass, entry.entry_id).async_remove()
    async_remove_fixture_provider(hass, entry.entry_id)
