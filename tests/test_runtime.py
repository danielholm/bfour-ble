"""Tester for maltemp-latcharna."""

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "bfour_ble"
    / "runtime.py"
)
_spec = importlib.util.spec_from_file_location("bfour_runtime", _PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["bfour_runtime"] = _module
_spec.loader.exec_module(_module)

BFourRuntime = _module.BFourRuntime
SLEEP_GAP = _module.SLEEP_GAP


def _runtime(target=62.0, prewarn=10.0):
    return BFourRuntime(
        coordinator=None,
        address="A4:C3:4E:AC:ED:CE",
        target_temp=target,
        prewarn_offset=prewarn,
    )


def test_latchar_vid_malet():
    rt = _runtime()
    rt.note_temp(61.9)
    assert rt.target_reached is False
    rt.note_temp(62.0)
    assert rt.target_reached is True


def test_latchen_haller_vid_dipp():
    # Karntemperaturen vaggar alltid nagot. Larmet ska inte flimra.
    rt = _runtime()
    rt.note_temp(62.4)
    rt.note_temp(61.6)
    assert rt.target_reached is True


def test_forvarning_gar_forst():
    rt = _runtime(target=62.0, prewarn=10.0)
    rt.note_temp(52.5)
    assert rt.prewarn_reached is True
    assert rt.target_reached is False


def test_somn_nollstaller():
    # Proben lades i basstationen och slutade annonsera.
    rt = _runtime()
    rt.note_temp(70.0)
    assert rt.target_reached is True
    rt._last_seen = datetime.now(timezone.utc) - SLEEP_GAP - timedelta(seconds=1)
    rt.note_temp(20.0)
    assert rt.target_reached is False


def test_kort_lucka_nollstaller_inte():
    # Tillfalligt hal i BLE-tackningen mitt i en langkok.
    rt = _runtime()
    rt.note_temp(70.0)
    rt._last_seen = datetime.now(timezone.utc) - timedelta(minutes=2)
    rt.note_temp(71.0)
    assert rt.target_reached is True


def test_utan_mal_hander_inget():
    rt = _runtime(target=None)
    rt.note_temp(95.0)
    assert rt.target_reached is False
    assert rt.prewarn_reached is False


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nAlla tester gick igenom.")
