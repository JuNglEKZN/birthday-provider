"""Fixture-driven Home Assistant integration tests."""

from __future__ import annotations

import json

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.birthday_provider import (
    async_remove_entry,
    async_unload_entry,
)
from custom_components.birthday_provider.const import DOMAIN
from custom_components.birthday_provider.core.models import Birthday, RawContact
from custom_components.birthday_provider.core.provider import FixtureProvider
from custom_components.birthday_provider.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.birthday_provider.provider import async_set_fixture_provider
from custom_components.birthday_provider.storage import BirthdaySnapshot, BirthdayStore

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


def _local_today(hass: HomeAssistant):
    time_zone = dt_util.get_time_zone(hass.config.time_zone)
    assert time_zone is not None
    return dt_util.now(time_zone).date()


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="synthetic-entry",
        data={"username": "synthetic@example.invalid", "password": "synthetic-secret"},
        title="Birthday Provider",
    )


async def _async_setup_fixture_entry(
    hass: HomeAssistant, provider: FixtureProvider
) -> MockConfigEntry:
    entry = _entry()
    entry.add_to_hass(hass)
    async_set_fixture_provider(hass, entry.entry_id, provider)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_fixture_provider_exposes_only_active_aggregated_events(
    hass: HomeAssistant,
) -> None:
    today = _local_today(hass)
    provider = FixtureProvider(
        (
            RawContact(
                "active-id",
                "Active Example",
                f"--{today.month:02d}-{today.day:02d}",
            ),
            RawContact("internal-id", "Internal Example", "--12-31"),
        )
    )

    await _async_setup_fixture_entry(hass, provider)

    active_state = hass.states.get("sensor.birthday_provider")
    last_sync_state = hass.states.get("sensor.birthday_provider_last_sync")

    assert active_state is not None
    assert active_state.state == "1"
    assert active_state.attributes["as_of"] == today.isoformat()
    assert active_state.attributes["window_days"] == 3
    assert active_state.attributes["events"] == [
        {
            "id": "active-id",
            "name": "Active Example",
            "date": today.isoformat(),
            "age": None,
        }
    ]
    assert "days_until" not in active_state.attributes
    assert "Internal Example" not in json.dumps(active_state.attributes)
    assert last_sync_state is not None
    assert last_sync_state.state != "unknown"


async def test_config_flow_scaffolds_apple_fields_without_network_access(
    hass: HomeAssistant,
) -> None:
    form = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert form["type"] is FlowResultType.FORM
    assert form["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {"username": "synthetic@example.invalid", "password": "synthetic-secret"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_cached_snapshot_restores_without_a_fixture_provider(
    hass: HomeAssistant,
) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    today = _local_today(hass)
    snapshot = BirthdaySnapshot(
        generated_at=dt_util.utcnow(),
        birthdays=(
            Birthday("cached-id", "Cached Example", today.day, today.month, None),
        ),
    )
    await BirthdayStore(hass, entry.entry_id).async_save(snapshot)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    active_state = hass.states.get("sensor.birthday_provider")
    assert active_state is not None
    assert active_state.state == "1"
    assert entry.runtime_data.coordinator.last_sync_status == "restored"
    assert entry.runtime_data.provider is None


async def test_diagnostics_exclude_all_contact_and_credential_data(
    hass: HomeAssistant,
) -> None:
    today = _local_today(hass)
    entry = await _async_setup_fixture_entry(
        hass,
        FixtureProvider(
            (
                RawContact(
                    "private-uid",
                    "Private Person",
                    f"1984-{today.month:02d}-{today.day:02d}",
                ),
            )
        ),
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    serialized = json.dumps(diagnostics)

    assert diagnostics["normalized_birthday_count"] == 1
    assert diagnostics["active_event_count"] == 1
    for forbidden_value in (
        "synthetic@example.invalid",
        "synthetic-secret",
        "private-uid",
        "Private Person",
        "1984-",
        "events",
    ):
        assert forbidden_value not in serialized


async def test_unload_and_removal_clean_up_entities_and_storage(
    hass: HomeAssistant,
) -> None:
    entry = await _async_setup_fixture_entry(hass, FixtureProvider(()))

    assert await async_unload_entry(hass, entry)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.birthday_provider") is None
    assert hass.states.get("sensor.birthday_provider_last_sync") is None

    await async_remove_entry(hass, entry)

    assert await BirthdayStore(hass, entry.entry_id).async_load() is None
