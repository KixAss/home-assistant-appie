"""A Home Assistant to-do list backed directly by the Albert Heijn API."""

from __future__ import annotations

import logging

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import AppieApiError
from .const import DOMAIN
from .coordinator import AppieCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AppieCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([AppieTodoListEntity(coordinator, entry)])


def _to_todo_item(item: dict) -> TodoItem:
    return TodoItem(
        uid=item["id"],
        summary=item.get("name") or f"Product #{item.get('product_id')}",
        status=TodoItemStatus.COMPLETED if item.get("checked") else TodoItemStatus.NEEDS_ACTION,
    )


class AppieTodoListEntity(CoordinatorEntity[AppieCoordinator], TodoListEntity):
    """Boodschappenlijst backed by Albert Heijn."""

    _attr_has_entity_name = True
    _attr_name = "Boodschappenlijst"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator: AppieCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_shopping_list"

    @property
    def todo_items(self) -> list[TodoItem] | None:
        if self.coordinator.data is None:
            return None
        return [_to_todo_item(item) for item in self.coordinator.data]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        summary = item.summary.strip() if item.summary else ""
        try:
            if summary.isdigit():
                # Typed a bare number — treat it as a real AH product ID
                # and link it directly, skipping search/free-text entirely.
                await self.coordinator.client.add_item(product_id=int(summary), quantity=1)
            else:
                # Added as free text by default — see api.py's module
                # docstring and check_item/delete_items docstrings for why
                # product-linked items via search are currently less
                # reliable. Use the appie.add_item service with
                # free_text: false if you want search-based product
                # linking instead of typing a product ID directly.
                await self.coordinator.client.add_item(name=summary, quantity=1, free_text=True)
        except AppieApiError:
            _LOGGER.exception("Failed to add item '%s' to AH shopping list", summary)
            raise
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        checked = item.status == TodoItemStatus.COMPLETED
        try:
            await self.coordinator.client.check_item(item.uid, checked)
        except AppieApiError:
            _LOGGER.exception("Failed to update item %s on AH shopping list", item.uid)
            raise
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        try:
            await self.coordinator.client.delete_items(list(uids))
        except AppieApiError:
            _LOGGER.exception("Failed to delete items %s from AH shopping list", uids)
            raise
        await self.coordinator.async_request_refresh()
