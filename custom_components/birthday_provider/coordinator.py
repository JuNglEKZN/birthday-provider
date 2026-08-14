"""Orchestrate stored birthdays and their active Home Assistant view."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .core.birthdays import active_birthday_events
from .core.models import ActiveBirthdayEvent, Birthday
from .core.normalization import normalize_contacts
from .storage import BirthdaySnapshot, BirthdayStore

if TYPE_CHECKING:
    from .core.provider import ContactProvider


UpdateListener = Callable[[], None]


class BirthdayProviderCoordinator:
    """Keep the full internal catalog and derived active events consistent."""

    def __init__(
        self,
        hass: HomeAssistant,
        storage: BirthdayStore,
        provider: ContactProvider | None,
    ) -> None:
        self.hass = hass
        self.storage = storage
        self.provider = provider
        self.birthdays: tuple[Birthday, ...] = ()
        self.active_events: tuple[ActiveBirthdayEvent, ...] = ()
        self.as_of: date = self._local_today()
        self.last_successful_sync: datetime | None = None
        self.last_sync_status = "not_started"
        self._listeners: set[UpdateListener] = set()

    async def async_initialize(self) -> None:
        """Restore the catalog, or use an injected synthetic fixture in tests."""
        snapshot = await self.storage.async_load()
        if snapshot is not None:
            self._apply_snapshot(snapshot)
            self.last_sync_status = "restored"
        elif self.provider is not None:
            await self.async_load_fixture()
        else:
            self.async_recalculate_active_events()

    async def async_load_fixture(self) -> None:
        """Normalize and store the complete synthetic fixture snapshot.

        Stage 2 intentionally uses this only through the test fixture hook. It is
        not a remote synchronization mechanism.
        """
        if self.provider is None:
            return
        contacts = await self.provider.async_fetch_contacts()
        result = normalize_contacts(contacts)
        generated_at = dt_util.utcnow()
        snapshot = BirthdaySnapshot(generated_at, result.birthdays)
        await self.storage.async_save(snapshot)
        self._apply_snapshot(snapshot)
        self.last_sync_status = "fixture_loaded"

    def async_recalculate_active_events(self) -> None:
        """Recalculate the derived active view without mutating stored birthdays."""
        self.as_of = self._local_today()
        self.active_events = tuple(active_birthday_events(self.birthdays, self.as_of))
        self._notify_listeners()

    def async_add_listener(self, listener: UpdateListener) -> Callable[[], None]:
        """Register an entity callback for active-view changes."""
        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    async def async_shutdown(self) -> None:
        """Release all entity listeners owned by this coordinator."""
        self._listeners.clear()

    def _apply_snapshot(self, snapshot: BirthdaySnapshot) -> None:
        self.birthdays = snapshot.birthdays
        self.last_successful_sync = snapshot.generated_at
        self.async_recalculate_active_events()

    def _local_today(self) -> date:
        return dt_util.now(self.hass.config.time_zone).date()

    def _notify_listeners(self) -> None:
        for listener in tuple(self._listeners):
            listener()
