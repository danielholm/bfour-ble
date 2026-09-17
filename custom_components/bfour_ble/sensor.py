"""Temperatur- och batterisensorer for BFOUR-probes."""

from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BFourConfigEntry
from .parser import ProbeData

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    "core_temp": SensorEntityDescription(
        key="core_temp",
        name="Kärntemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    "ambient_temp": SensorEntityDescription(
        key="ambient_temp",
        name="Omgivningstemperatur",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    "battery_volts": SensorEntityDescription(
        key="battery_volts",
        name="Batterispänning",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


def _key(key: str) -> PassiveBluetoothEntityKey:
    return PassiveBluetoothEntityKey(key=key, device_id=None)


def sensor_update_to_bluetooth_data_update(
    data: ProbeData | None,
) -> PassiveBluetoothDataUpdate:
    """Oversatt ett avkodat paket till en entitetsuppdatering."""
    if data is None:
        return PassiveBluetoothDataUpdate()

    values: dict[str, float | None] = {
        "core_temp": data.core_temp,
        # Under trosklen rapporterar sensorn skrap. Publicera None sa grafen
        # far ett hal istallet for en falsk linje.
        "ambient_temp": data.ambient_temp if data.ambient_valid else None,
        "battery_volts": data.battery_volts,
    }

    return PassiveBluetoothDataUpdate(
        entity_descriptions={
            _key(key): description for key, description in SENSOR_DESCRIPTIONS.items()
        },
        entity_data={_key(key): value for key, value in values.items()},
        entity_names={
            _key(key): description.name
            for key, description in SENSOR_DESCRIPTIONS.items()
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BFourConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Koppla in sensorerna."""
    coordinator = entry.runtime_data.coordinator
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    entry.async_on_unload(
        processor.async_add_entities_listener(BFourSensor, async_add_entities)
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class BFourSensor(PassiveBluetoothProcessorEntity, SensorEntity):
    """En sensor pa en BFOUR-probe."""

    _attr_has_entity_name = True

    @property
    def native_value(self) -> float | None:
        """Senaste vardet."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    def available(self) -> bool:
        """Sensorn ar otillganglig tills ett giltigt varde kommit in."""
        return super().available and self.entity_key in self.processor.entity_data
