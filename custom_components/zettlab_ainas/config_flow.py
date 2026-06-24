"""Config flow for Zettlab AINAS.

Onboarding flow (per product requirement):
  1. discover  — native LAN discovery protocol
  2. manual    — if not discovered, enter the device IP
  3. remote_id — log in via the device's remote-access ID (cloud relay)
All paths end at the login step (RSA-encrypted username/password).
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import ZettosAuthError, ZettOSClient, ZettosError, async_probe_device
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_REMOTE_ID,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .coordinator import ZettlabAinasConfigEntry
from .discovery import async_discover

_LOGGER = logging.getLogger(__name__)

_LOGIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ZettlabAinasConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the Zettlab AINAS config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise transient flow state."""
        self._host: str | None = None
        self._info: dict[str, Any] = {}
        self._discovered: dict[str, dict] = {}

    # --- step 0: pick a method --------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user choose how to add the device."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["discover", "manual", "remote_id"],
        )

    # --- step 1: discovery ------------------------------------------------------

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Discover devices on the LAN; fall back to manual if none."""
        if not self._discovered:
            self._discovered = await async_discover(self.hass)
        if not self._discovered:
            return await self.async_step_manual()

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._info = self._discovered[self._host]
            return await self.async_step_login()

        choices = {
            host: f"{info.get('model_name', 'Zettlab')} ({host})"
            for host, info in self._discovered.items()
        }
        return self.async_show_form(
            step_id="discover",
            data_schema=vol.Schema({vol.Required(CONF_HOST): vol.In(choices)}),
        )

    # --- step 2: manual IP ------------------------------------------------------

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter a device IP/host directly."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            info = await async_probe_device(
                async_get_clientsession(self.hass), host, verify_ssl=DEFAULT_VERIFY_SSL
            )
            if info is None:
                errors["base"] = "cannot_connect"
            else:
                self._host = host
                self._info = info
                return await self.async_step_login()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    # --- step 3: remote ID ------------------------------------------------------

    async def async_step_remote_id(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add via the device's remote-access ID (Zettlab cloud relay).

        The cloud relay protocol (iot.zettlab.com) is not yet implemented; this
        step is scaffolded so the onboarding structure is in place. For now it
        aborts with guidance to use discovery or manual entry.
        """
        if user_input is not None:
            # TODO: resolve {remote_id} -> reachable endpoint via the cloud relay,
            # then chain into async_step_login().
            return self.async_abort(reason="remote_id_not_supported")
        return self.async_show_form(
            step_id="remote_id",
            data_schema=vol.Schema({vol.Required(CONF_REMOTE_ID): str}),
        )

    # --- final: login -----------------------------------------------------------

    async def async_step_login(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authenticate and create the entry."""
        assert self._host is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ZettOSClient(
                host=self._host,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
                verify_ssl=DEFAULT_VERIFY_SSL,
            )
            try:
                await client.async_login()
                device = await client.async_get_device()
            except ZettosAuthError:
                errors["base"] = "invalid_auth"
            except ZettosError:
                errors["base"] = "cannot_connect"
            else:
                sn = device.get("sn") or self._info.get("sn")
                await self.async_set_unique_id(sn)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=device.get("device_name")
                    or self._info.get("device_name")
                    or self._host,
                    data={
                        CONF_HOST: self._host,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
                    },
                )

        return self.async_show_form(
            step_id="login",
            data_schema=_LOGIN_SCHEMA,
            errors=errors,
            description_placeholders={
                "name": self._info.get("device_name", self._host)
            },
        )

    # --- reauth -----------------------------------------------------------------

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle re-authentication when the token/credentials become invalid."""
        self._host = entry_data[CONF_HOST]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm new credentials."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ZettOSClient(
                host=entry.data[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
                verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            )
            try:
                await client.async_login()
            except ZettosAuthError:
                errors["base"] = "invalid_auth"
            except ZettosError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_LOGIN_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ZettlabAinasConfigEntry,
    ) -> ZettlabAinasOptionsFlow:
        """Return the options flow."""
        return ZettlabAinasOptionsFlow()


class ZettlabAinasOptionsFlow(OptionsFlow):
    """Options: polling interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                    )
                }
            ),
        )
