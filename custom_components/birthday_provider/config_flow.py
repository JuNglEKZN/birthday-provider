"""Config flow scaffold for Birthday Provider."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN


class BirthdayProviderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create an entry for the Stage 2 fixture-driven integration skeleton."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial form without performing Stage 3 authentication."""
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            await self.async_set_unique_id(username.casefold())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Birthday Provider", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
        )
