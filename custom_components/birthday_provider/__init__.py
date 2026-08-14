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
    provider: ContactProvider


async def async_setup_entry(
    hass: HomeAssistant, entry: BirthdayProviderConfigEntry
) -> bool:
    """Set up Birthday Provider from a config entry."""
    from homeassistant.const import Platform
    from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

    from .coordinator import BirthdayProviderCoordinator
    from .icloud import ICloudAuthenticationError, ICloudConnectionError
    from .provider import async_create_provider
    from .storage import BirthdayStore

    storage = BirthdayStore(hass, entry.entry_id)
    provider = async_create_provider(hass, entry.entry_id, entry.data)
    coordinator = BirthdayProviderCoordinator(
        hass,
        storage,
        provider,
    )
    try:
        await coordinator.async_initialize()
    except ICloudAuthenticationError as error:
        raise ConfigEntryAuthFailed from error
    except ICloudConnectionError as error:
        raise ConfigEntryNotReady from error

    coordinator.async_set_authentication_error_handler(
        lambda: entry.async_start_reauth_if_available(hass)
    )

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
