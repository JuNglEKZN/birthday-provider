"""Conversion of minimal provider data into canonical birthdays."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .birthdays import sort_birthdays
from .models import Birthday, BirthdayValidationError, RawContact
from .parsing import parse_birthday


@dataclass(frozen=True, slots=True)
class DuplicateResolution:
    """Canonical values and duplicate information for safe diagnostics upstream."""

    birthdays: tuple[Birthday, ...]
    identical_duplicate_ids: frozenset[str]
    conflicting_duplicate_ids: frozenset[str]


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Result of normalizing one complete provider snapshot."""

    birthdays: tuple[Birthday, ...]
    invalid_contact_count: int
    identical_duplicate_ids: frozenset[str]
    conflicting_duplicate_ids: frozenset[str]


def normalize_contact(contact: RawContact) -> Birthday:
    """Reduce one raw contact immediately to the allowed persistent fields."""
    parsed = parse_birthday(contact.birthday_raw)
    return Birthday(
        id=contact.uid,
        name=contact.display_name,
        day=parsed.day,
        month=parsed.month,
        year=parsed.year,
    )


def resolve_duplicate_birthdays(birthdays: Iterable[Birthday]) -> DuplicateResolution:
    """Apply the v0.1 UID collision policy deterministically."""
    by_id: dict[str, list[Birthday]] = defaultdict(list)
    for birthday in birthdays:
        by_id[birthday.id].append(birthday)

    canonical: list[Birthday] = []
    identical_ids: set[str] = set()
    conflicting_ids: set[str] = set()
    for birthday_id, values in by_id.items():
        first = values[0]
        if len(values) == 1:
            canonical.append(first)
        elif all(value == first for value in values[1:]):
            canonical.append(first)
            identical_ids.add(birthday_id)
        else:
            conflicting_ids.add(birthday_id)

    return DuplicateResolution(
        birthdays=tuple(sort_birthdays(canonical)),
        identical_duplicate_ids=frozenset(identical_ids),
        conflicting_duplicate_ids=frozenset(conflicting_ids),
    )


def normalize_contacts(contacts: Iterable[RawContact]) -> NormalizationResult:
    """Normalize a complete snapshot, skipping malformed individual contacts."""
    normalized: list[Birthday] = []
    invalid_contact_count = 0
    for contact in contacts:
        try:
            normalized.append(normalize_contact(contact))
        except BirthdayValidationError:
            invalid_contact_count += 1

    duplicates = resolve_duplicate_birthdays(normalized)
    return NormalizationResult(
        birthdays=duplicates.birthdays,
        invalid_contact_count=invalid_contact_count,
        identical_duplicate_ids=duplicates.identical_duplicate_ids,
        conflicting_duplicate_ids=duplicates.conflicting_duplicate_ids,
    )
