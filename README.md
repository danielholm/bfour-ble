# BFOUR BLE

[![Tests](https://github.com/danielholm/bfour-ble/actions/workflows/tests.yml/badge.svg)](https://github.com/danielholm/bfour-ble/actions/workflows/tests.yml)
[![Validate](https://github.com/danielholm/bfour-ble/actions/workflows/validate.yml/badge.svg)](https://github.com/danielholm/bfour-ble/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/danielholm/bfour-ble)](https://github.com/danielholm/bfour-ble/blob/main/LICENSE)
[![Release](https://img.shields.io/github/v/release/danielholm/bfour-ble)](https://github.com/danielholm/bfour-ble/releases)
[![Stars](https://img.shields.io/github/stars/danielholm/bfour-ble)](https://github.com/danielholm/bfour-ble/stargazers)
[![Issues](https://img.shields.io/github/issues/danielholm/bfour-ble)](https://github.com/danielholm/bfour-ble/issues)
[![Downloads](https://img.shields.io/github/downloads/danielholm/bfour-ble/total)](https://github.com/danielholm/bfour-ble/releases)

Home Assistant integration for BFOUR wireless meat thermometers (BF-70, BF-80).

The probes are read **passively** from their advertisements. No connection, no
dedicated ESP32, no cloud. Every Bluetooth proxy in your home feeds the same
integration, so coverage is as good as your BLE coverage generally — and the
base station can be used alongside it, or left in a drawer.

[Svenska](README.sv.md)

## Installation

[![Add integration](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=danielholm&repository=bfour-ble&category=integration)

Add this repository as a custom repository in HACS, or copy
`custom_components/bfour_ble/` into your `config/custom_components/`. Restart
Home Assistant.

Take the probes out of the base station so they wake up. They should appear as
discovered devices within a minute or so. One config entry per probe.

## Entities

Per probe:

| Entity | Type | Description |
|---|---|---|
| Core temperature | sensor | The sensor in the tip |
| Ambient temperature | sensor | The sensor near the handle |
| Battery voltage | sensor | Diagnostic |
| Target temperature | number | Your target, 40–100 °C |
| Pre-warning | number | Degrees before the target, default 10 |
| Target reached | binary_sensor | Latched alarm |
| Almost done | binary_sensor | Pre-warning |
| Active | binary_sensor | Status flag, see below |
| Reset alarm | button | Clears the latches |

### Target temperature

The target is stored in Home Assistant and is **not** written to the probe or
the base station — this integration only reads advertisements and cannot write.
The base station's own alarm is therefore independent and may sit at a
different value.

The alarm is latched: `Target reached` turns `on` when the core temperature
passes the target and stays on even if the temperature dips back down. It
resets when

- the probe stops advertising for more than five minutes (it was put back in
the base station),
- the target temperature is changed, or
- you press `Reset alarm`.

## Protocol

The probe sends connectable legacy advertisements with service UUID `0xFFA0`
and manufacturer data under company ID `0x1002`. The payload is 14 bytes:

```
83 CE ED AC 4E C3 A4  F3 00  04 01  63 0E  80
|  \_______________/  \___/  \___/  \___/  |
|   MAC, reversed      24.3   26.0   3.683  status
header
```

All three values are little-endian uint16. Temperatures in tenths of a degree,
battery in millivolts.

`0x1002` is a **reserved, unassigned** company ID used freely by many cheap BLE
modules. The integration therefore validates that bytes 1–6 mirror the sender's
MAC address before accepting a packet. Without that check the matcher picks up
unrelated devices.

The consequence is that other devices broadcasting under the same company ID
may appear as discoveries and then be aborted with *"This device is not a BFOUR
probe"*. That is expected behaviour, not a bug: the matcher in `manifest.json`
works on company ID, and validation happens afterwards on packet content. The
alternative would be to also require the local name `Probe`, but that lives in
the scan response and is absent under passive scanning — no probes would be
found at all.

## Known quirks

**The ambient sensor has a lower cutoff** around 20 °C. The base station shows
`Loo` below it; this integration publishes `None` so history gets a gap rather
than a false line. The sensor is built for grill and oven temperatures and
should not be used as a room thermometer.

**The status flag** is bit 7 of the last byte. It flipped on both probes at
once when a cooking session was started in the app, but the interpretation is
unconfirmed — it may just as well mean "out of the charger" or "awake". Put a
probe in the base station and see whether the bit clears.

**Battery voltage** is raw cell voltage, not a percentage. Cold lowers it
temporarily, so a probe that has been in the fridge reads lower than it really
is. Mapping to a percentage needs a discharge curve that nobody has measured
yet.

## Tests

```
python3 tests/test_parser.py
```

The parser tests run against real packets captured from a BF-80, verified
against both the base station display and the manufacturer's app. The runtime
tests cover the latching logic, including that a brief gap in BLE coverage does
not reset an alarm mid-cook.

## Acknowledgements

The protocol structure of the older, connection-based generation (BF-60,
service `0xFFB0`, `0x55`-prefixed commands over a GATT notify characteristic)
is documented in
[wizbowes/BFour-ESPHome](https://github.com/wizbowes/BFour-ESPHome). None of
that code is used here — the BF-70/BF-80 probes advertise passively under
`0xFFA0` with a different layout and byte order — but knowing that the wireless
generation was readable at all is what made this worth attempting. Thanks.

Earlier work on the iBBQ / "Grill BT5.0" family of thermometers, including
[Fractvival/bfour](https://github.com/Fractvival/bfour), was useful background
on how this class of device tends to be built. The integration follows the
passive Bluetooth patterns established by `inkbird-ble`, `xiaomi-ble` and their
siblings in Home Assistant core.

## A note on how this was built

The protocol was reverse engineered in a single evening from nRF Connect
captures, cross-checked against the base station display and the BFOUR+ app. The
analysis and the code were produced in conversation with **Claude
(Anthropic)**, an LLM.

Every decoded field was verified against real readings before being committed —
the exact match on ambient temperature against the base station display is what
confirmed the field layout — and the tests in `tests/` run against those same
captures. The parts that remain guesses are marked as such above.

Treat this the way you would any reverse-engineered protocol implementation: it
works on the two probes it was developed against, and corrections are welcome.

## License

MIT
