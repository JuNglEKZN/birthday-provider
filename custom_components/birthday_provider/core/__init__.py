"""Provider-neutral birthday domain logic."""

from .birthdays import (
    active_birthday_events,
    birthday_occurrence,
    calculate_age,
    sort_active_events,
    sort_birthdays,
)
from .models import (
    ActiveBirthdayEvent,
    Birthday,
    BirthdayValidationError,
    RawContact,
)
from .normalization import (
    DuplicateResolution,
    NormalizationResult,
    normalize_contact,
    normalize_contacts,
    resolve_duplicate_birthdays,
)
from .parsing import ParsedBirthday, parse_birthday
from .provider import ContactProvider, FixtureProvider

__all__ = [
    "ActiveBirthdayEvent",
    "Birthday",
    "BirthdayValidationError",
    "ContactProvider",
    "DuplicateResolution",
    "FixtureProvider",
    "NormalizationResult",
    "ParsedBirthday",
    "RawContact",
    "active_birthday_events",
    "birthday_occurrence",
    "calculate_age",
    "normalize_contact",
    "normalize_contacts",
    "parse_birthday",
    "resolve_duplicate_birthdays",
    "sort_active_events",
    "sort_birthdays",
]
