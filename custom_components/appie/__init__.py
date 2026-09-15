"""The Albert Heijn boodschappenlijst integration (no external service)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AppieClient
from .const import (
    ATTR_FREE_TEXT,
    ATTR_NAME,
    ATTR_QUANTITY,
    DOMAIN,
    SERVICE_ADD_ITEM,
    SERVICE_CHECKOUT,
    SERVICE_CLEAR_LIST,
)
from .coordinator import AppieCoordinator

PLATFORMS = ["todo"]

ADD_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): str,
        vol.Optional(ATTR_QUANTITY, default=1): int,
        vol.Optional(ATTR_FREE_TEXT, default=True): bool,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)

    async def _on_tokens_updated(tokens: dict) -> None:
        hass.config_entries.async_update_entry(entry, data={**entry.data, **tokens})

    client = AppieClient(session, tokens=dict(entry.data), on_tokens_updated=_on_tokens_updated)

    coordinator = AppieCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"client": client, "coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            for service in (SERVICE_ADD_ITEM, SERVICE_CHECKOUT, SERVICE_CLEAR_LIST):
                hass.services.async_remove(DOMAIN, service)
    return unload_ok


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_ADD_ITEM):
        return

    def _first_client() -> AppieClient:
        entry_data = next(iter(hass.data[DOMAIN].values()))
        return entry_data["client"]

    async def _refresh_all() -> None:
        for entry_data in hass.data[DOMAIN].values():
            await entry_data["coordinator"].async_request_refresh()

    async def handle_add_item(call: ServiceCall) -> None:
        client = _first_client()
        try:
            await client.add_item(
                name=call.data[ATTR_NAME],
                quantity=call.data.get(ATTR_QUANTITY, 1),
                free_text=call.data.get(ATTR_FREE_TEXT, True),
            )
        finally:
            await _refresh_all()

    async def handle_checkout(call: ServiceCall) -> None:
        await _first_client().shopping_list_to_order()

    async def handle_clear_list(call: ServiceCall) -> None:
        try:
            await _first_client().clear_list()
        finally:
            await _refresh_all()

    hass.services.async_register(DOMAIN, SERVICE_ADD_ITEM, handle_add_item, schema=ADD_ITEM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CHECKOUT, handle_checkout)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_LIST, handle_clear_list)
