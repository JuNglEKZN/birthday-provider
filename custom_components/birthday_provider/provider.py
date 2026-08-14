"""Stage 2 fixture-provider injection for Home Assistant tests."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DATA_FIXTURE_PROVIDERS
from .core.provider import ContactProvider


def async_set_fixture_provider(
    hass: HomeAssistant, entry_id: str, provider: ContactProvider
) -> None:
    """Register a synthetic provider for a config entry in tests.

    This hook exists solely until Stage 3 supplies the production provider.
    It does not persist source data or make network requests.
    """
    providers = hass.data.setdefault(DATA_FIXTURE_PROVIDERS, {})
    providers[entry_id] = provider


def async_get_fixture_provider(
    hass: HomeAssistant, entry_id: str
) -> ContactProvider | None:
    """Return the test-only fixture provider configured for an entry, if any."""
    return hass.data.get(DATA_FIXTURE_PROVIDERS, {}).get(entry_id)


def async_remove_fixture_provider(hass: HomeAssistant, entry_id: str) -> None:
    """Discard a test-only fixture provider during entry removal."""
    providers = hass.data.get(DATA_FIXTURE_PROVIDERS)
    if providers is not None:
        providers.pop(entry_id, None)
