"""BFOUR BLE — passiv avlasning av BF-70/BF-80-probes."""

from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .parser import MANUFACTURER_ID, ProbeData, parse

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]

BFourConfigEntry = ConfigEntry


def _build_update_method(
    address: str,
) -> Callable[[BluetoothServiceInfoBleak], ProbeData | None]:
    """Stang in adressen sa parsern kan validera MAC-spegeln."""

    def _update(service_info: BluetoothServiceInfoBleak) -> ProbeData | None:
        raw = service_info.manufacturer_data.get(MANUFACTURER_ID)
        if raw is None:
            return None
        return parse(bytes(raw), address)

    return _update


async def async_setup_entry(hass: HomeAssistant, entry: BFourConfigEntry) -> bool:
    """Satt upp en probe."""
    address = entry.unique_id
    if address is None:
        raise ConfigEntryNotReady("Konfigurationen saknar BLE-adress")

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        address=address,
        mode=BluetoothScanningMode.PASSIVE,
        update_method=_build_update_method(address),
    )
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # async_start returnerar en callback som avregistrerar lyssnaren.
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BFourConfigEntry) -> bool:
    """Ta bort en probe."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
