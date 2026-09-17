"""Avkodning av BFOUR BF-70/BF-80 trådlösa probes.

Proben annonserar passivt, utan anslutning. Manufacturer data ser ut så här
(14 bytes efter company-ID 0x1002):

    83 CE ED AC 4E C3 A4  F3 00  04 01  63 0E  80
    |  |                  |      |      |      |
    |  |                  |      |      |      status, bit 7 = aktiv
    |  |                  |      |      batteri, mV, little-endian
    |  |                  |      omgivningstemp, 0.1 C, little-endian
    |  |                  karntemp, 0.1 C, little-endian
    |  probens egen MAC, omvand byteordning
    header, alltid 0x83

Company-ID 0x1002 ar en reserverad, ej tilldelad ID som anvands av manga
billiga BLE-moduler. MAC-spegeln i byte 1-6 anvands darfor som validering:
stammer den inte mot avsandaradressen ar paketet inte vart.
"""

from __future__ import annotations

from dataclasses import dataclass

MANUFACTURER_ID = 0x1002
HEADER = 0x83
PAYLOAD_LEN = 14

# Omgivningssensorn ar gjord for grill och ugn. Under den har gransen ar
# varderna inte meningsfulla, och basstationen visar "Loo" istallet.
AMBIENT_MIN_C = 20.0


@dataclass(frozen=True)
class ProbeData:
    """Ett avkodat matvarde fran en probe."""

    core_temp: float
    ambient_temp: float
    ambient_valid: bool
    battery_volts: float
    active: bool


def _u16_le(data: bytes, index: int) -> int:
    return data[index] | (data[index + 1] << 8)


def _mac_from_payload(data: bytes) -> str:
    return ":".join(f"{b:02X}" for b in reversed(data[1:7]))


def parse(data: bytes, address: str) -> ProbeData | None:
    """Avkoda manufacturer data. Returnerar None om paketet inte ar vart."""
    if len(data) < PAYLOAD_LEN:
        return None
    if data[0] != HEADER:
        return None
    if _mac_from_payload(data) != address.upper():
        return None

    ambient = _u16_le(data, 9) / 10.0
    return ProbeData(
        core_temp=_u16_le(data, 7) / 10.0,
        ambient_temp=ambient,
        ambient_valid=ambient >= AMBIENT_MIN_C,
        battery_volts=_u16_le(data, 11) / 1000.0,
        active=bool(data[13] & 0x80),
    )


def short_id(address: str) -> str:
    """Sista tva hex-siffrorna, for att skilja proberna at i UI."""
    return address.replace(":", "")[-2:].upper()
