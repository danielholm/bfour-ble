"""Larm och status for BFOUR-probes."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
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
from .runtime import BFourRuntime

DESCRIPTIONS: dict[str, BinarySensorEntityDescription] = {
    "target_reached": BinarySensorEntityDescription(
        key="target_reached",
        name="Måltemp nådd",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    "prewarn_reached": BinarySensorEntityDescription(
        key="prewarn_reached",
        name="Snart klar",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    # Bit 7 i sista byten. Vaxlar samtidigt pa bada proberna nar en session
    # startas — "aktiv" ar en rimlig men obekraftad tolkning.
    "active": BinarySensorEntityDescription(
        key="active",
        name="Aktiv",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


def _key(key: str) -> PassiveBluetoothEntityKey:
    return PassiveBluetoothEntityKey(key=key, device_id=None)


def _build_update(runtime: BFourRuntime):
    """Latcharna uppdateras i takt med annonseringarna."""

    def _update(data: ProbeData | None) -> PassiveBluetoothDataUpdate:
        if data is None:
            return PassiveBluetoothDataUpdate()

        runtime.note_temp(data.core_temp)

        values = {
            "target_reached": runtime.target_reached,
            "prewarn_reached": runtime.prewarn_reached,
            "active": data.active,
        }
        return PassiveBluetoothDataUpdate(
            entity_descriptions={_key(k): DESCRIPTIONS[k] for k in values},
            entity_data={_key(k): v for k, v in values.items()},
            entity_names={_key(k): DESCRIPTIONS[k].name for k in values},
        )

    return _update


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BFourConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in larmen."""
    runtime: BFourRuntime = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(_build_update(runtime))
    entry.async_on_unload(
        processor.async_add_entities_listener(BFourBinarySensor, async_add_entities)
    )
    entry.async_on_unload(
        runtime.coordinator.async_register_processor(
            processor, BinarySensorEntityDescription
        )
    )


class BFourBinarySensor(PassiveBluetoothProcessorEntity, BinarySensorEntity):
    """Ett larm eller en statusflagga pa en probe."""

    _attr_has_entity_name = True

    @property
    def is_on(self) -> bool | None:
        """Senaste vardet."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Otillganglig tills ett giltigt paket kommit in."""
        return super().available and self.entity_key in self.processor.entity_data
