"""Maltemperatur och forvarning — lagras i Home Assistant, inte i proben."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BFourConfigEntry, probe_device_info
from .runtime import DEFAULT_PREWARN_C, BFourRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BFourConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in installningarna."""
    runtime: BFourRuntime = entry.runtime_data
    async_add_entities([BFourTargetNumber(runtime), BFourPrewarnNumber(runtime)])


class _BFourNumberBase(RestoreNumber, NumberEntity):
    """Gemensamt for de lagrade talen."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    def __init__(self, runtime: BFourRuntime) -> None:
        """Initiera."""
        self._runtime = runtime
        self._attr_device_info = probe_device_info(runtime.address)
        self._attr_unique_id = f"{runtime.address}_{self.entity_description_key}"

    @property
    def entity_description_key(self) -> str:
        """Nyckel for unique_id."""
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Aterstall vardet efter omstart."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            if last.native_value is not None:
                self._attr_native_value = last.native_value
        self._push()

    def _push(self) -> None:
        """Skriv vardet till det delade tillstandet."""
        raise NotImplementedError


class BFourTargetNumber(_BFourNumberBase):
    """Maltemperatur for karnan."""

    _attr_name = "Måltemperatur"
    _attr_icon = "mdi:target"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 40
    _attr_native_max_value = 100
    _attr_native_value = 62.0

    entity_description_key = "target"

    def _push(self) -> None:
        self._runtime.target_temp = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        """Satt nytt mal och nollstall larmet."""
        self._attr_native_value = value
        self._push()
        # Ett andrat mal gor det gamla larmet irrelevant.
        self._runtime.reset_latches()
        self.async_write_ha_state()


class BFourPrewarnNumber(_BFourNumberBase):
    """Hur manga grader innan malet forvarningen ska ga."""

    _attr_name = "Förvarning"
    _attr_icon = "mdi:bell-outline"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 0
    _attr_native_max_value = 30
    _attr_native_value = DEFAULT_PREWARN_C
    _attr_entity_category = EntityCategory.CONFIG

    entity_description_key = "prewarn"

    def _push(self) -> None:
        self._runtime.prewarn_offset = self._attr_native_value or 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Satt ny forvarningsmarginal."""
        self._attr_native_value = value
        self._push()
        self._runtime.prewarn_reached = False
        self.async_write_ha_state()
