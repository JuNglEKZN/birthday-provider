"""Credential-validation and reauthentication flow for iCloud CardDAV."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .icloud import (
    ICloudAuthenticationError,
    ICloudCardDAVProvider,
    ICloudConnectionError,
)


async def async_validate_icloud_credentials(
    hass: HomeAssistant, username: str, password: str
) -> None:
    """Validate app-specific credentials without downloading contact records."""
    provider = ICloudCardDAVProvider(
        username=username,
        app_specific_password=password,
        session=async_get_clientsession(hass),
    )
    await provider.async_validate_credentials()


class BirthdayProviderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create and reauthenticate the Apple iCloud config entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial Apple Account setup with a credential check."""
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            try:
                await async_validate_icloud_credentials(self.hass, username, password)
            except ICloudAuthenticationError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._user_schema(),
                    errors={"base": "invalid_auth"},
                )
            except ICloudConnectionError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._user_schema(),
                    errors={"base": "cannot_connect"},
                )

            await self.async_set_unique_id(username.casefold())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Birthday Provider",
                data={CONF_USERNAME: username, CONF_PASSWORD: password},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Start a password-only repair flow for an existing entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate the replacement app-specific password and reload the entry."""
        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            entry = self._get_reauth_entry()
            username = entry.data[CONF_USERNAME]
            try:
                await async_validate_icloud_credentials(self.hass, username, password)
            except ICloudAuthenticationError:
                return self.async_show_form(
                    step_id="reauth_confirm",
                    data_schema=self._reauth_schema(),
                    errors={"base": "invalid_auth"},
                )
            except ICloudConnectionError:
                return self.async_show_form(
                    step_id="reauth_confirm",
                    data_schema=self._reauth_schema(),
                    errors={"base": "cannot_connect"},
                )

            return self.async_update_reload_and_abort(
                entry,
                data_updates={CONF_PASSWORD: password},
            )

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=self._reauth_schema()
        )

    @staticmethod
    def _user_schema() -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

    @staticmethod
    def _reauth_schema() -> vol.Schema:
        return vol.Schema({vol.Required(CONF_PASSWORD): str})
