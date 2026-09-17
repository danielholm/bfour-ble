"""Statusflagga for BFOUR-probes."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BFourConfigEntry
from .parser import ProbeData

# Bit 7 i sista byten. Den vaxlar samtidigt pa bada proberna nar en session
# startas, sa "aktiv" ar en rimlig men inte bekraftad tolkning.
ACTIVE_DESCRIPTION = BinarySensorEntityDescription(
    key="active",
    name="Aktiv",
    entity_category=EntityCategory.DIAGNOSTIC,
)


def _key(key: str) -> PassiveBluetoothEntityKey:
    return PassiveBluetoothEntityKey(key=key, device_id=None)


def binary_sensor_update_to_bluetooth_data_update(
    data: ProbeData | None,
) -> PassiveBluetoothDataUpdate:
    """Oversatt statusbyten till en entitetsuppdatering."""
    if data is None:
        return PassiveBluetoothDataUpdate()

    return PassiveBluetoothDataUpdate(
        entity_descriptions={_key("active"): ACTIVE_DESCRIPTION},
        entity_data={_key("active"): data.active},
        entity_names={_key("active"): ACTIVE_DESCRIPTION.name},
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BFourConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in statusflaggan."""
    coordinator = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(
        binary_sensor_update_to_bluetooth_data_update
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(BFourBinarySensor, async_add_entities)
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, BinarySensorEntityDescription)
    )


class BFourBinarySensor(PassiveBluetoothProcessorEntity, BinarySensorEntity):
    """Statusflagga pa en BFOUR-probe."""

    _attr_has_entity_name = True

    @property
    def is_on(self) -> bool | None:
        """Senaste vardet."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Otillganglig tills ett giltigt paket kommit in."""
        return super().available and self.entity_key in self.processor.entity_data
