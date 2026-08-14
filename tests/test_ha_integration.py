"""Fixture-driven Home Assistant integration tests."""

from __future__ import annotations

import json

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.birthday_provider.const import DOMAIN
from custom_components.birthday_provider.core.models import Birthday, RawContact
from custom_components.birthday_provider.core.provider import FixtureProvider
from custom_components.birthday_provider.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.birthday_provider.icloud import (
    ICloudAuthenticationError,
    ICloudConnectionError,
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


async def test_config_flow_validates_app_specific_password(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    validated: list[tuple[str, str]] = []

    async def validate(_hass: HomeAssistant, username: str, password: str) -> None:
        validated.append((username, password))

    monkeypatch.setattr(
        "custom_components.birthday_provider.config_flow.async_validate_icloud_credentials",
        validate,
    )
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
    assert validated == [("synthetic@example.invalid", "synthetic-secret")]


async def test_config_flow_distinguishes_invalid_credentials(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def reject(_hass: HomeAssistant, _username: str, _password: str) -> None:
        raise ICloudAuthenticationError("synthetic rejection")

    monkeypatch.setattr(
        "custom_components.birthday_provider.config_flow.async_validate_icloud_credentials",
        reject,
    )
    form = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    result = await hass.config_entries.flow.async_configure(
        form["flow_id"],
        {"username": "synthetic@example.invalid", "password": "wrong-password"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_replaces_only_the_app_specific_password(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="synthetic-entry",
        data={
            "username": "synthetic@example.invalid",
            "password": "synthetic-secret",
            "preserved_setting": "synthetic-value",
        },
        title="Birthday Provider",
    )
    entry.add_to_hass(hass)
    validated: list[tuple[str, str]] = []
    scheduled_reloads: list[str] = []

    async def validate(_hass: HomeAssistant, username: str, password: str) -> None:
        validated.append((username, password))

    def schedule_reload(entry_id: str) -> None:
        scheduled_reloads.append(entry_id)

    monkeypatch.setattr(
        "custom_components.birthday_provider.config_flow.async_validate_icloud_credentials",
        validate,
    )
    monkeypatch.setattr(hass.config_entries, "async_schedule_reload", schedule_reload)
    form = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reauth", "entry_id": entry.entry_id},
        data=entry.data,
    )

    assert form["type"] is FlowResultType.FORM
    assert form["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(
        form["flow_id"], {"password": "replacement-app-password"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert validated == [("synthetic@example.invalid", "replacement-app-password")]
    assert entry.data == {
        "username": "synthetic@example.invalid",
        "password": "replacement-app-password",
        "preserved_setting": "synthetic-value",
    }
    assert scheduled_reloads == [entry.entry_id]
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


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
    assert type(entry.runtime_data.provider).__name__ == "ICloudCardDAVProvider"


async def test_connection_failure_keeps_last_successful_snapshot(
    hass: HomeAssistant,
) -> None:
    today = _local_today(hass)
    entry = await _async_setup_fixture_entry(
        hass,
        FixtureProvider(
            (
                RawContact(
                    "cached-id",
                    "Cached Example",
                    f"--{today.month:02d}-{today.day:02d}",
                ),
            )
        ),
    )

    class UnavailableProvider:
        async def async_fetch_contacts(self) -> list[RawContact]:
            raise ICloudConnectionError("synthetic failure")

    coordinator = entry.runtime_data.coordinator
    coordinator.provider = UnavailableProvider()
    original_birthdays = coordinator.birthdays
    original_sync = coordinator.last_successful_sync

    with pytest.raises(ICloudConnectionError):
        await coordinator.async_sync()

    assert coordinator.birthdays == original_birthdays
    assert coordinator.last_successful_sync == original_sync
    assert coordinator.last_sync_status == "connection_failed"


async def test_authentication_failure_keeps_snapshot_and_starts_reauth(
    hass: HomeAssistant,
) -> None:
    entry = await _async_setup_fixture_entry(hass, FixtureProvider(()))

    class RejectedProvider:
        async def async_fetch_contacts(self) -> list[RawContact]:
            raise ICloudAuthenticationError("synthetic rejection")

    coordinator = entry.runtime_data.coordinator
    original_birthdays = coordinator.birthdays
    coordinator.provider = RejectedProvider()

    with pytest.raises(ICloudAuthenticationError):
        await coordinator.async_sync()
    await hass.async_block_till_done()

    assert coordinator.birthdays == original_birthdays
    assert coordinator.last_sync_status == "authentication_failed"
    assert hass.config_entries.flow.async_progress_by_handler(DOMAIN)


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

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED

    active_state = hass.states.get("sensor.birthday_provider")
    assert active_state is not None
    assert active_state.state == STATE_UNAVAILABLE
    assert active_state.attributes["restored"] is True

    entity_registry = er.async_get(hass)
    assert [
        entity
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    ]

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.config_entries.async_get_entry(entry.entry_id) is None
    assert await BirthdayStore(hass, entry.entry_id).async_load() is None
    assert not [
        entity
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    ]
    assert hass.states.get("sensor.birthday_provider") is None
    assert hass.states.get("sensor.birthday_provider_last_sync") is None
