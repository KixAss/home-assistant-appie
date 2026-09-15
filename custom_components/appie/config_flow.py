"""Config flow for the Albert Heijn boodschappenlijst integration.

Login is manual: we show the plain AH login URL, the user logs in in
their own browser, and pastes back the resulting `appie://login-exit?
code=...` URL (captured via the browser's DevTools, since the browser
itself can't follow a custom URL scheme) or just the bare code. We then
exchange that code for tokens.

This replaces an earlier version that tried to automate this with a local
reverse-proxy server; that turned out to be unreliable, so this manual
step is simpler and more robust.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import unquote

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CLIENT_ID, AppieApiError, AppieClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

LOGIN_URL = (
    f"https://login.ah.nl/login?client_id={CLIENT_ID}"
    "&response_type=code&redirect_uri=appie://login-exit"
)

CONF_CALLBACK = "callback"

_CODE_RE = re.compile(r"(?:^|[?&])code=([^&\s]+)")


def _extract_code(raw: str) -> str | None:
    """Pull the authorization code out of whatever the user pasted.

    Accepts a full `appie://login-exit?code=...` URL, a URL-encoded
    variant, or just the bare code value.
    """
    raw = raw.strip()
    if not raw:
        return None
    match = _CODE_RE.search(raw)
    if match:
        return unquote(match.group(1))
    if raw.startswith(("http", "appie")):
        return None  # looks like a URL but we couldn't find a code= param
    return raw


class AppieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Albert Heijn integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            code = _extract_code(user_input[CONF_CALLBACK])
            if not code:
                errors["base"] = "invalid_code"
            else:
                session = async_get_clientsession(self.hass)
                client = AppieClient(session)
                try:
                    tokens = await client.exchange_code(code)
                except AppieApiError:
                    _LOGGER.exception("Failed to exchange AH login code for tokens")
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title="Albert Heijn boodschappenlijst", data=tokens
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_CALLBACK): str}),
            description_placeholders={"login_url": LOGIN_URL},
            errors=errors,
        )
