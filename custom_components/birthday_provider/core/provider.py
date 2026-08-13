"""Provider contract and a synthetic in-memory provider for tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import RawContact


class ContactProvider(Protocol):
    """Fetch the minimal contact fields needed by the provider-neutral core."""

    async def async_fetch_contacts(self) -> list[RawContact]:
        """Return a complete source snapshot of minimal raw contacts."""


@dataclass(frozen=True, slots=True)
class FixtureProvider:
    """A deterministic synthetic provider used only by unit tests."""

    contacts: tuple[RawContact, ...]

    def __init__(self, contacts: tuple[RawContact, ...] | list[RawContact]) -> None:
        object.__setattr__(self, "contacts", tuple(contacts))

    async def async_fetch_contacts(self) -> list[RawContact]:
        """Return a fresh list so callers cannot mutate this fixture."""
        return list(self.contacts)
