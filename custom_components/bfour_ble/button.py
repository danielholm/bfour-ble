"""Manuell aterstallning av larmen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BFourConfigEntry, probe_device_info
from .runtime import BFourRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BFourConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in knappen."""
    async_add_entities([BFourResetButton(entry.runtime_data)])


class BFourResetButton(ButtonEntity):
    """Nollstall larmen utan att lagga tillbaka proben i basen."""

    _attr_has_entity_name = True
    _attr_name = "Återställ larm"
    _attr_icon = "mdi:restart"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, runtime: BFourRuntime) -> None:
        """Initiera."""
        self._runtime = runtime
        self._attr_unique_id = f"{runtime.address}_reset"
        self._attr_device_info = probe_device_info(runtime.address)

    async def async_press(self) -> None:
        """Nollstall."""
        self._runtime.reset_latches()
