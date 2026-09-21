from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pasco2.protocol.frames import Co2Reading


class MeasurementRepository(Protocol):
    """Interfejs zapisu pomiarow.

    Warstwa application/ zna tylko ten interfejs - nigdy konkretnej
    implementacji (PostgreSQL, w pamieci, ...).
    """

    def save(self, reading: Co2Reading, timestamp: datetime) -> None:
        ...
