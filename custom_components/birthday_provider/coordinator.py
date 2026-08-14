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
from .icloud import ICloudAuthenticationError, ICloudConnectionError
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
        provider: ContactProvider,
        on_authentication_error: Callable[[], None] | None = None,
    ) -> None:
        self.hass = hass
        self.storage = storage
        self.provider = provider
        self._on_authentication_error = on_authentication_error
        self.birthdays: tuple[Birthday, ...] = ()
        self.active_events: tuple[ActiveBirthdayEvent, ...] = ()
        self.as_of: date = self._local_today()
        self.last_successful_sync: datetime | None = None
        self.last_sync_status = "not_started"
        self._listeners: set[UpdateListener] = set()

    async def async_initialize(self) -> None:
        """Restore a catalog, or synchronously create the first snapshot."""
        snapshot = await self.storage.async_load()
        if snapshot is not None:
            self._apply_snapshot(snapshot)
            self.last_sync_status = "restored"
        else:
            await self.async_sync()

    async def async_sync(self) -> None:
        """Atomically replace the snapshot only after a complete provider fetch."""
        try:
            contacts = await self.provider.async_fetch_contacts()
        except ICloudAuthenticationError:
            self.last_sync_status = "authentication_failed"
            self._notify_listeners()
            if self._on_authentication_error is not None:
                self._on_authentication_error()
            raise
        except ICloudConnectionError:
            self.last_sync_status = "connection_failed"
            self._notify_listeners()
            raise

        result = normalize_contacts(contacts)
        snapshot = BirthdaySnapshot(dt_util.utcnow(), result.birthdays)
        await self.storage.async_save(snapshot)
        self._apply_snapshot(snapshot)
        self.last_sync_status = "success"

    def async_set_authentication_error_handler(
        self, handler: Callable[[], None]
    ) -> None:
        """Register the runtime reauth trigger after setup has succeeded."""
        self._on_authentication_error = handler

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
        time_zone = dt_util.get_time_zone(self.hass.config.time_zone)
        if time_zone is None:
            return dt_util.now().date()
        return dt_util.now(time_zone).date()

    def _notify_listeners(self) -> None:
        for listener in tuple(self._listeners):
            listener()
