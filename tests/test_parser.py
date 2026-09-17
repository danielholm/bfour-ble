"""Tester mot verkliga paket fran en BF-80."""

import importlib.util
import sys
from pathlib import Path

# Ladda parsern direkt fran fil — paketets __init__ importerar Home Assistant,
# och parsern ska kunna testas utan det.
_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "bfour_ble"
    / "parser.py"
)
_spec = importlib.util.spec_from_file_location("bfour_parser", _PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["bfour_parser"] = _module
_spec.loader.exec_module(_module)
parse = _module.parse

BLACK = "A4:C3:4E:AC:ED:CE"
WHITE = "44:3E:8A:0F:36:D5"


def _payload(hexstr: str) -> bytes:
    return bytes.fromhex(hexstr)


def test_black_matchar_displayen():
    # Displayen visade 24.3 / Ambient 26, batteriet pa vag ner.
    data = parse(_payload("83CEEDAC4EC3A4F3000401630E80"), BLACK)
    assert data is not None
    assert data.core_temp == 24.3
    assert data.ambient_temp == 26.0
    assert data.ambient_valid is True
    assert data.battery_volts == 3.683
    assert data.active is True


def test_white_under_ambienttroskeln():
    # Displayen visade "Loo" pa ambient — 13.0 ligger under granstemperaturen.
    data = parse(_payload("83D5360F8A3E44960082008E0E80"), WHITE)
    assert data is not None
    assert data.core_temp == 15.0
    assert data.ambient_temp == 13.0
    assert data.ambient_valid is False


def test_statusflagga_avstangd():
    # Tidigare fangst, innan sessionen startades i appen.
    data = parse(_payload("83CEEDAC4EC3A4FD00F000B90F00"), BLACK)
    assert data is not None
    assert data.core_temp == 25.3
    assert data.battery_volts == 4.025
    assert data.active is False


def test_fel_mac_avvisas():
    # Samma paket, fel avsandare — MAC-spegeln stammer inte.
    assert parse(_payload("83CEEDAC4EC3A4F3000401630E80"), WHITE) is None


def test_skrap_avvisas():
    assert parse(b"", BLACK) is None
    assert parse(_payload("00" * 14), BLACK) is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nAlla tester gick igenom.")
