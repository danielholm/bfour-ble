"""Delat tillstand per probe: maltemperatur, forvarning och larmlatchar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

# Proben annonserar var femte sekund sa lange den ar vaken. En lucka langre
# an sa har betyder att den legat i basstationen och somnat — det ar den
# handelsen som nollstaller larmet infor nasta tillagning. Tilltaget tilltaget
# for att tala tillfalliga hal i BLE-tackningen mitt i en langkok.
SLEEP_GAP = timedelta(minutes=5)

DEFAULT_PREWARN_C = 10.0


@dataclass
class BFourRuntime:
    """Tillstand som delas mellan plattformarna for en probe."""

    coordinator: Any
    address: str

    target_temp: float | None = None
    prewarn_offset: float = DEFAULT_PREWARN_C

    target_reached: bool = False
    prewarn_reached: bool = False

    _last_seen: datetime | None = field(default=None, repr=False)

    def note_temp(self, core_temp: float) -> None:
        """Registrera en ny karntemperatur och uppdatera latcharna."""
        now = datetime.now(timezone.utc)
        if self._last_seen is not None and now - self._last_seen > SLEEP_GAP:
            # Proben har sovit. Ny tillagning, nytt larm.
            self.reset_latches()
        self._last_seen = now

        if self.target_temp is None:
            return

        if core_temp >= self.target_temp:
            self.target_reached = True
        if core_temp >= self.target_temp - self.prewarn_offset:
            self.prewarn_reached = True

    def reset_latches(self) -> None:
        """Nollstall larmen."""
        self.target_reached = False
        self.prewarn_reached = False
