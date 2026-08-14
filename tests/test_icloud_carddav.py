"""Synthetic CardDAV protocol tests for the iCloud provider."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest

from custom_components.birthday_provider.icloud import (
    ADDRESSBOOK_QUERY_REQUEST,
    ICloudAuthenticationError,
    ICloudCardDAVProvider,
    ICloudConnectionError,
    extract_raw_contacts,
)

DAV = "DAV:"
CARD = "urn:ietf:params:xml:ns:carddav"


def _multistatus(property_xml: str, href: str = "/") -> str:
    return f"""<?xml version="1.0"?>
<D:multistatus xmlns:D="{DAV}" xmlns:C="{CARD}">
  <D:response>
    <D:href>{href}</D:href>
    <D:propstat><D:prop>{property_xml}</D:prop>
    <D:status>HTTP/1.1 200 OK</D:status></D:propstat>
  </D:response>
</D:multistatus>"""


def _discovery_responses() -> list[str]:
    return [
        _multistatus(
            "<D:current-user-principal>"
            "<D:href>/principal/</D:href>"
            "</D:current-user-principal>"
        ),
        _multistatus(
            "<C:addressbook-home-set><D:href>/home/</D:href>"
            "</C:addressbook-home-set>",
            "/principal/",
        ),
        _multistatus(
            "<D:resourcetype><D:collection/><C:addressbook/></D:resourcetype>",
            "/home/contacts/",
        ),
    ]


@dataclass
class _Response:
    status: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)

    async def __aenter__(self) -> _Response:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def text(self) -> str:
        return self.body


class _Session:
    def __init__(self, responses: list[_Response]) -> None:
        self._responses: Iterator[_Response] = iter(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        return next(self._responses)


def test_extract_raw_contacts_discards_unrelated_vcard_properties() -> None:
    contacts = extract_raw_contacts(
        """BEGIN:VCARD
VERSION:3.0
UID:synthetic-uid
ITEM1.FN:Synthetic\\, Person
ITEM2.BDAY;VALUE=date:19840817
TEL:+1-555-0100
EMAIL:synthetic@example.invalid
NOTE:must not reach Core
END:VCARD
BEGIN:VCARD
UID:no-birthday
FN:Ignored Contact
END:VCARD
"""
    )

    contact_values = [
        (contact.uid, contact.display_name, contact.birthday_raw)
        for contact in contacts
    ]
    assert contact_values == [("synthetic-uid", "Synthetic, Person", "1984-08-17")]


def test_extract_raw_contacts_accepts_group_prefixes_for_all_retained_fields() -> None:
    contacts = extract_raw_contacts(
        """BEGIN:VCARD
ITEM0.UID:grouped-synthetic-uid
ITEM1.FN:Synthetic Person
ITEM2.BDAY:--0817
END:VCARD
"""
    )

    assert contacts[0].uid == "grouped-synthetic-uid"
    assert contacts[0].display_name == "Synthetic Person"
    assert contacts[0].birthday_raw == "--08-17"


async def test_provider_discovers_and_fetches_only_minimal_carddav_fields() -> None:
    vcard = """BEGIN:VCARD
VERSION:3.0
UID:synthetic-uid
FN:Synthetic Person
BDAY:--0817
TEL:+1-555-0100
END:VCARD"""
    report = _multistatus(
        f"<C:address-data><![CDATA[{vcard}]]></C:address-data>",
        "/home/contacts/synthetic.vcf",
    )
    session = _Session(
        [
            *(_Response(207, item) for item in _discovery_responses()),
            _Response(207, report),
        ]
    )
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    contacts = await provider.async_fetch_contacts()

    contact_values = [
        (contact.uid, contact.display_name, contact.birthday_raw)
        for contact in contacts
    ]
    assert contact_values == [("synthetic-uid", "Synthetic Person", "--08-17")]
    assert [call["method"] for call in session.calls] == [
        "PROPFIND",
        "PROPFIND",
        "PROPFIND",
        "REPORT",
    ]
    report_payload = session.calls[-1]["data"]
    assert report_payload == ADDRESSBOOK_QUERY_REQUEST
    assert b'"UID"' in report_payload
    assert b'"FN"' in report_payload
    assert b'"BDAY"' in report_payload
    assert b"TEL" not in report_payload
    assert b"EMAIL" not in report_payload


async def test_provider_classifies_credential_rejection() -> None:
    session = _Session([_Response(401, "")])
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudAuthenticationError):
        await provider.async_validate_credentials()


async def test_provider_preserves_credentials_across_icloud_redirect() -> None:
    principal = _discovery_responses()[0]
    session = _Session(
        [
            _Response(302, "", {"Location": "https://p01-contacts.icloud.com/"}),
            _Response(207, principal),
        ]
    )
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    response = await provider._async_xml_request(  # noqa: SLF001 - protocol regression test
        "PROPFIND", "https://contacts.icloud.com/", b"<request/>", depth="0"
    )

    assert response.tag == f"{{{DAV}}}multistatus"
    assert session.calls[1]["url"] == "https://p01-contacts.icloud.com/"
    assert session.calls[1]["allow_redirects"] is False


async def test_provider_rejects_untrusted_redirect_before_sending_credentials() -> None:
    session = _Session([_Response(302, "", {"Location": "https://example.com/"})])
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudConnectionError):
        await provider.async_validate_credentials()

    assert len(session.calls) == 1


async def test_provider_rejects_untrusted_dav_href_before_sending_credentials() -> None:
    principal = _multistatus(
        "<D:current-user-principal>"
        "<D:href>https://example.com/principal/</D:href>"
        "</D:current-user-principal>"
    )
    session = _Session([_Response(207, principal)])
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudConnectionError):
        await provider.async_validate_credentials()

    assert len(session.calls) == 1


async def test_provider_rejects_empty_addressbook_discovery() -> None:
    no_addressbooks = _multistatus(
        "<D:resourcetype><D:collection/></D:resourcetype>", "/home/"
    )
    session = _Session(
        [
            *(_Response(207, item) for item in _discovery_responses()[:2]),
            _Response(207, no_addressbooks),
        ]
    )
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudConnectionError):
        await provider.async_validate_credentials()


async def test_provider_classifies_unauthenticated_principal() -> None:
    unauthenticated = _multistatus(
        "<D:current-user-principal><D:unauthenticated/>"
        "</D:current-user-principal>"
    )
    session = _Session([_Response(207, unauthenticated)])
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudAuthenticationError):
        await provider.async_validate_credentials()


async def test_provider_rejects_partial_addressbook_response() -> None:
    incomplete_report = """<?xml version="1.0"?>
<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:response><D:href>/home/contacts/missing.vcf</D:href>
  <D:propstat><D:prop/><D:status>HTTP/1.1 404 Not Found</D:status></D:propstat>
  </D:response>
</D:multistatus>"""
    session = _Session(
        [
            *(_Response(207, item) for item in _discovery_responses()),
            _Response(207, incomplete_report),
        ]
    )
    provider = ICloudCardDAVProvider(
        "synthetic@example.invalid", "synthetic-app-password", session  # type: ignore[arg-type]
    )

    with pytest.raises(ICloudConnectionError):
        await provider.async_fetch_contacts()
