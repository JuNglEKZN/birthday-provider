from __future__ import annotations

from custom_components.birthday_provider.core.models import RawContact
from custom_components.birthday_provider.core.normalization import normalize_contacts


def test_same_name_with_different_uids_are_distinct_birthdays() -> None:
    result = normalize_contacts(
        [
            RawContact("first", "Alex", "--08-17"),
            RawContact("second", "Alex", "--08-17"),
        ]
    )

    assert [birthday.id for birthday in result.birthdays] == ["first", "second"]


def test_identical_duplicate_uid_is_deduplicated() -> None:
    result = normalize_contacts(
        [
            RawContact("same", "Alex", "--08-17"),
            RawContact("same", "Alex", "--08-17"),
        ]
    )

    assert [birthday.id for birthday in result.birthdays] == ["same"]
    assert result.identical_duplicate_ids == {"same"}
    assert not result.conflicting_duplicate_ids


def test_conflicting_duplicate_uid_is_removed_from_candidate_catalog() -> None:
    result = normalize_contacts(
        [
            RawContact("same", "Alex", "--08-17"),
            RawContact("same", "Alexandra", "--08-17"),
            RawContact("other", "Boris", "--08-18"),
        ]
    )

    assert [birthday.id for birthday in result.birthdays] == ["other"]
    assert result.conflicting_duplicate_ids == {"same"}
