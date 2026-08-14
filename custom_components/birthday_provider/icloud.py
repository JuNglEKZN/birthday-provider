"""iCloud CardDAV provider with minimal, non-persistent vCard extraction."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from contextlib import suppress
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from aiohttp import BasicAuth, ClientError

from .core.models import BirthdayValidationError, RawContact

if TYPE_CHECKING:
    from aiohttp import ClientSession


ICLOUD_CARDDAV_URL = "https://contacts.icloud.com/"

DAV_NAMESPACE = "DAV:"
CARDDAV_NAMESPACE = "urn:ietf:params:xml:ns:carddav"
TRUSTED_ICLOUD_HOST = "icloud.com"


class ICloudCardDAVError(Exception):
    """Base error for iCloud CardDAV operations without sensitive details."""


class ICloudAuthenticationError(ICloudCardDAVError):
    """The Apple Account or app-specific password was rejected."""


class ICloudConnectionError(ICloudCardDAVError):
    """A temporary network, server, or protocol failure occurred."""


def resolve_icloud_url(base_url: str, target: str) -> str:
    """Resolve a DAV or redirect target without widening the credential scope."""
    resolved = urljoin(base_url, target)
    parsed = urlparse(resolved)
    hostname = parsed.hostname.casefold() if parsed.hostname else ""
    if (
        parsed.scheme != "https"
        or not hostname
        or not hostname.endswith(f".{TRUSTED_ICLOUD_HOST}")
    ):
        raise ICloudConnectionError("CardDAV target is outside iCloud")
    if parsed.username is not None or parsed.password is not None:
        raise ICloudConnectionError("CardDAV target must not contain credentials")
    return resolved


def _qname(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _xml_request(*property_names: tuple[str, str]) -> bytes:
    """Build a DAV PROPFIND payload for the requested properties."""
    root = ET.Element(_qname(DAV_NAMESPACE, "propfind"))
    prop = ET.SubElement(root, _qname(DAV_NAMESPACE, "prop"))
    for namespace, name in property_names:
        ET.SubElement(prop, _qname(namespace, name))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


DISCOVER_PRINCIPAL_REQUEST = _xml_request((DAV_NAMESPACE, "current-user-principal"))
DISCOVER_HOME_SET_REQUEST = _xml_request((CARDDAV_NAMESPACE, "addressbook-home-set"))
DISCOVER_ADDRESS_BOOKS_REQUEST = _xml_request((DAV_NAMESPACE, "resourcetype"))


def _addressbook_query_request() -> bytes:
    root = ET.Element(_qname(CARDDAV_NAMESPACE, "addressbook-query"))
    prop = ET.SubElement(root, _qname(DAV_NAMESPACE, "prop"))
    address_data = ET.SubElement(prop, _qname(CARDDAV_NAMESPACE, "address-data"))
    for name in ("UID", "FN", "BDAY"):
        ET.SubElement(
            address_data, _qname(CARDDAV_NAMESPACE, "prop"), {"name": name}
        )
    ET.SubElement(root, _qname(CARDDAV_NAMESPACE, "filter"))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


ADDRESSBOOK_QUERY_REQUEST = _addressbook_query_request()


def _success_status(status: str | None) -> bool:
    """Return whether a DAV status line reports a 2xx response."""
    if status is None:
        return False
    parts = status.split()
    return len(parts) >= 2 and parts[1].startswith("2")


def _property_hrefs(xml: ET.Element, property_name: tuple[str, str]) -> list[str]:
    """Read successful href values for one DAV property."""
    property_qname = _qname(*property_name)
    href_qname = _qname(DAV_NAMESPACE, "href")
    values: list[str] = []
    for response in xml.findall(f".//{_qname(DAV_NAMESPACE, 'response')}"):
        for propstat in response.findall(_qname(DAV_NAMESPACE, "propstat")):
            if not _success_status(propstat.findtext(_qname(DAV_NAMESPACE, "status"))):
                continue
            property_value = propstat.find(
                f"{_qname(DAV_NAMESPACE, 'prop')}/{property_qname}"
            )
            if property_value is None:
                continue
            values.extend(
                href.text.strip()
                for href in property_value.findall(href_qname)
                if href.text and href.text.strip()
            )
    return values


def _property_contains_unauthenticated(xml: ET.Element) -> bool:
    """Return whether DAV explicitly reports an unauthenticated principal."""
    current_principal = _qname(DAV_NAMESPACE, "current-user-principal")
    unauthenticated = _qname(DAV_NAMESPACE, "unauthenticated")
    for response in xml.findall(f".//{_qname(DAV_NAMESPACE, 'response')}"):
        for propstat in response.findall(_qname(DAV_NAMESPACE, "propstat")):
            if not _success_status(propstat.findtext(_qname(DAV_NAMESPACE, "status"))):
                continue
            property_value = propstat.find(
                f"{_qname(DAV_NAMESPACE, 'prop')}/{current_principal}"
            )
            if (
                property_value is not None
                and property_value.find(unauthenticated) is not None
            ):
                return True
    return False


def _addressbook_hrefs(xml: ET.Element) -> list[str]:
    """Return collection hrefs whose successful resource type is CardDAV."""
    href_qname = _qname(DAV_NAMESPACE, "href")
    addressbook_qname = _qname(CARDDAV_NAMESPACE, "addressbook")
    result: list[str] = []
    for response in xml.findall(f".//{_qname(DAV_NAMESPACE, 'response')}"):
        href = response.findtext(href_qname)
        if not href:
            continue
        for propstat in response.findall(_qname(DAV_NAMESPACE, "propstat")):
            if not _success_status(propstat.findtext(_qname(DAV_NAMESPACE, "status"))):
                continue
            resource_type = propstat.find(
                f"{_qname(DAV_NAMESPACE, 'prop')}/"
                f"{_qname(DAV_NAMESPACE, 'resourcetype')}"
            )
            if (
                resource_type is not None
                and resource_type.find(addressbook_qname) is not None
            ):
                result.append(href.strip())
    return result


def _successful_address_data(xml: ET.Element) -> list[str]:
    """Return all vCards or fail if any reported resource did not succeed."""
    response_qname = _qname(DAV_NAMESPACE, "response")
    data_qname = _qname(CARDDAV_NAMESPACE, "address-data")
    values: list[str] = []
    for response in xml.findall(f".//{response_qname}"):
        success_values: list[str] = []
        for propstat in response.findall(_qname(DAV_NAMESPACE, "propstat")):
            if not _success_status(propstat.findtext(_qname(DAV_NAMESPACE, "status"))):
                continue
            value = propstat.findtext(
                f"{_qname(DAV_NAMESPACE, 'prop')}/{data_qname}"
            )
            if value is not None:
                success_values.append(value)
        if not success_values:
            raise ICloudConnectionError("CardDAV returned an incomplete address book")
        values.extend(success_values)
    return values


def _unfold_vcard_lines(vcard: str) -> Iterable[str]:
    """Yield vCard content lines after RFC-style continuation unfolding."""
    current: str | None = None
    for line in vcard.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith((" ", "\t")) and current is not None:
            current += line[1:]
        else:
            if current is not None:
                yield current
            current = line
    if current is not None:
        yield current


def _unescape_vcard_text(value: str) -> str:
    """Decode the limited vCard text escapes relevant to a display name."""
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
    )


def _canonical_bday(value: str) -> str:
    """Map common vCard DATE compact forms to the Core BDAY contract."""
    value = value.strip()
    if len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    if len(value) == 6 and value.startswith("--") and value[2:].isdigit():
        return f"--{value[2:4]}-{value[4:]}"
    return value


def extract_raw_contacts(vcard_data: str) -> list[RawContact]:
    """Immediately reduce a CardDAV response to UID, FN, and BDAY only.

    The input is intentionally local to this function. It is neither returned
    nor retained after the resulting minimal ``RawContact`` values are built.
    """
    contacts: list[RawContact] = []
    fields: dict[str, str] | None = None
    for line in _unfold_vcard_lines(vcard_data):
        if line.upper() == "BEGIN:VCARD":
            fields = {}
            continue
        if line.upper() == "END:VCARD":
            if fields is not None:
                with suppress(BirthdayValidationError, KeyError):
                    contacts.append(
                        RawContact(
                            uid=fields["UID"],
                            display_name=_unescape_vcard_text(fields["FN"]),
                            birthday_raw=_canonical_bday(fields["BDAY"]),
                        )
                    )
            fields = None
            continue
        if fields is None or ":" not in line:
            continue
        descriptor, value = line.split(":", 1)
        property_name = descriptor.split(";", 1)[0].rsplit(".", 1)[-1].upper()
        if property_name in {"UID", "FN", "BDAY"} and property_name not in fields:
            fields[property_name] = value
    return contacts


class ICloudCardDAVProvider:
    """Fetch a complete, minimal iCloud Contacts snapshot through CardDAV."""

    def __init__(
        self,
        username: str,
        app_specific_password: str,
        session: ClientSession,
        base_url: str = ICLOUD_CARDDAV_URL,
    ) -> None:
        self._username = username
        self._password = app_specific_password
        self._session = session
        self._base_url = resolve_icloud_url(ICLOUD_CARDDAV_URL, base_url)

    async def async_validate_credentials(self) -> None:
        """Authenticate and discover address books without reading contacts."""
        await self.async_discover_address_books()

    async def async_fetch_contacts(self) -> list[RawContact]:
        """Return a complete source snapshot reduced before it reaches Core."""
        contacts: list[RawContact] = []
        for addressbook_url in await self.async_discover_address_books():
            report = await self._async_xml_request(
                "REPORT",
                addressbook_url,
                ADDRESSBOOK_QUERY_REQUEST,
                depth="1",
            )
            for vcard in _successful_address_data(report):
                contacts.extend(extract_raw_contacts(vcard))
        return contacts

    async def async_discover_address_books(self) -> list[str]:
        """Discover the authenticated principal, home set, and address books."""
        principal_response = await self._async_xml_request(
            "PROPFIND", self._base_url, DISCOVER_PRINCIPAL_REQUEST, depth="0"
        )
        principal_hrefs = _property_hrefs(
            principal_response, (DAV_NAMESPACE, "current-user-principal")
        )
        if _property_contains_unauthenticated(principal_response):
            raise ICloudAuthenticationError("iCloud rejected app credentials")
        if len(principal_hrefs) != 1:
            raise ICloudConnectionError("CardDAV principal discovery was incomplete")
        principal_url = resolve_icloud_url(self._base_url, principal_hrefs[0])

        home_response = await self._async_xml_request(
            "PROPFIND", principal_url, DISCOVER_HOME_SET_REQUEST, depth="0"
        )
        home_hrefs = _property_hrefs(
            home_response, (CARDDAV_NAMESPACE, "addressbook-home-set")
        )
        if len(home_hrefs) != 1:
            raise ICloudConnectionError("CardDAV address book discovery was incomplete")
        home_url = resolve_icloud_url(principal_url, home_hrefs[0])

        collections = await self._async_xml_request(
            "PROPFIND", home_url, DISCOVER_ADDRESS_BOOKS_REQUEST, depth="1"
        )
        addressbooks = [
            resolve_icloud_url(home_url, href)
            for href in _addressbook_hrefs(collections)
        ]
        if not addressbooks:
            raise ICloudConnectionError("CardDAV address book discovery was empty")
        return addressbooks

    async def _async_xml_request(
        self, method: str, url: str, payload: bytes, *, depth: str
    ) -> ET.Element:
        """Make a CardDAV XML request without logging its response content."""
        request_url = resolve_icloud_url(self._base_url, url)
        try:
            for _ in range(5):
                async with self._session.request(
                    method,
                    request_url,
                    allow_redirects=False,
                    auth=BasicAuth(self._username, self._password),
                    data=payload,
                    headers={
                        "Content-Type": "application/xml; charset=utf-8",
                        "Depth": depth,
                    },
                ) as response:
                    if response.status in {301, 302, 307, 308}:
                        location = response.headers.get("Location")
                        if not location:
                            message = "iCloud CardDAV redirect was invalid"
                            raise ICloudConnectionError(message)
                        request_url = resolve_icloud_url(request_url, location)
                        continue
                    if response.status in {401, 403}:
                        raise ICloudAuthenticationError(
                            "iCloud rejected app credentials"
                        )
                    if response.status != 207:
                        raise ICloudConnectionError("iCloud CardDAV request failed")
                    response_body = await response.text()
                    break
            else:
                raise ICloudConnectionError("iCloud CardDAV redirect limit exceeded")
        except ICloudCardDAVError:
            raise
        except (ClientError, TimeoutError) as error:
            raise ICloudConnectionError("iCloud CardDAV connection failed") from error

        try:
            return ET.fromstring(response_body)
        except ET.ParseError as error:
            message = "iCloud CardDAV response was invalid"
            raise ICloudConnectionError(message) from error
