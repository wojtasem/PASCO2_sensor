from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pasco2.protocol.frames import Co2Reading

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS room_co2_ppm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ppm INTEGER NOT NULL,
    measured_at TEXT NOT NULL
)
"""


class SqliteMeasurementRepository:
    """Implementacja MeasurementRepository dla SQLite (plik lokalny).

    Zero setupu - nie wymaga osobnego serwera bazy danych, uzywa modulu
    sqlite3 z biblioteki standardowej (brak dodatkowych zaleznosci).
    Dobra domyslna opcja dla jednego czujnika logujacego dane lokalnie.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(_CREATE_TABLE_SQL)

    def save(self, reading: Co2Reading, timestamp: datetime) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO room_co2_ppm (ppm, measured_at) VALUES (?, ?)",
                (reading.ppm, timestamp.astimezone(timezone.utc).isoformat()),
            )
        logger.debug("Zapisano pomiar %s ppm do %s.", reading.ppm, self._db_path)

    def fetch_all(self) -> list[tuple[int, str]]:
        """Zwraca wszystkie zapisane pomiary jako (ppm, measured_at_iso).

        Nie jest czescia interfejsu MeasurementRepository (ktory ma tylko
        save()) - to dodatkowa wygoda do testow i podgladu danych.
        """
        cur = self._conn.execute("SELECT ppm, measured_at FROM room_co2_ppm ORDER BY id")
        return cur.fetchall()

    def close(self) -> None:
        self._conn.close()
