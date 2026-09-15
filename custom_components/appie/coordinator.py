"""Coordinator that polls the AH shopping list directly (no bridge)."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AppieApiError, AppieClient
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AppieCoordinator(DataUpdateCoordinator[list[dict]]):
    """Polls AH's shopping list on an interval.

    Polling (instead of only reacting to Home Assistant actions) is what
    makes this a two-way sync: if you add or check off something directly
    in the AH app while shopping, it shows up here too on the next refresh.
    """

    def __init__(self, hass: HomeAssistant, client: AppieClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="appie shopping list",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> list[dict]:
        try:
            return await self.client.get_shopping_list_items()
        except AppieApiError as err:
            raise UpdateFailed(f"Albert Heijn API unreachable: {err}") from err
