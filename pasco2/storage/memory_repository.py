from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pasco2.protocol.frames import Co2Reading


@dataclass(frozen=True)
class StoredMeasurement:
    ppm: int
    timestamp: datetime


class InMemoryMeasurementRepository:
    """Implementacja MeasurementRepository w pamieci.

    Uzywana w testach integracyjnych oraz jako domyslny tryb aplikacji,
    gdy nie skonfigurowano DATABASE_URL (tryb dev/demo bez persystencji
    po zamknieciu procesu).
    """

    def __init__(self) -> None:
        self._records: list[StoredMeasurement] = []

    def save(self, reading: Co2Reading, timestamp: datetime) -> None:
        self._records.append(StoredMeasurement(ppm=reading.ppm, timestamp=timestamp))

    @property
    def records(self) -> list[StoredMeasurement]:
        return list(self._records)
