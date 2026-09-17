"""Konfigurationsflode for BFOUR BLE."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN
from .parser import MANUFACTURER_ID, parse, short_id


def _is_bfour_probe(service_info: BluetoothServiceInfoBleak) -> bool:
    """0x1002 anvands av manga enheter — MAC-spegeln avgor."""
    raw = service_info.manufacturer_data.get(MANUFACTURER_ID)
    if raw is None:
        return False
    return parse(bytes(raw), service_info.address) is not None


def _title(service_info: BluetoothServiceInfoBleak) -> str:
    """Bada proberna heter "Probe" — lagg till MAC-svansen."""
    return f"BFOUR Probe {short_id(service_info.address)}"


class BFourConfigFlow(ConfigFlow, domain=DOMAIN):
    """Hantera upptackt och manuellt val av probes."""

    VERSION = 1

    def __init__(self) -> None:
        """Initiera flodet."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Probe upptackt via en proxy eller den lokala adaptern."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        if not _is_bfour_probe(discovery_info):
            return self.async_abort(reason="not_supported")

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": _title(discovery_info)}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Bekrafta en upptackt probe."""
        assert self._discovery_info is not None
        title = _title(self._discovery_info)

        if user_input is not None:
            return self.async_create_entry(title=title, data={})

        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"name": title},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Valj bland probes som syns just nu."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_title(self._discovered[address]), data={}
            )

        current = self._async_current_ids()
        for service_info in async_discovered_service_info(self.hass, False):
            if service_info.address in current:
                continue
            if not _is_bfour_probe(service_info):
                continue
            self._discovered[service_info.address] = service_info

        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: _title(service_info)
                            for address, service_info in self._discovered.items()
                        }
                    )
                }
            ),
        )
