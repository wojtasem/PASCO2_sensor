from __future__ import annotations

import logging
from datetime import datetime

from pasco2.protocol.frames import Co2Reading

logger = logging.getLogger(__name__)


class PostgresMeasurementRepository:
    """Implementacja MeasurementRepository dla PostgreSQL.

    Wymaga dodatkowych zaleznosci: `pip install -e ".[postgres]"`
    (SQLAlchemy, psycopg2-binary). Import jest lazy (w __init__), zeby
    reszta aplikacji i testy dzialaly bez tych zaleznosci zainstalowanych.
    """

    def __init__(self, database_url: str) -> None:
        try:
            from sqlalchemy import create_engine, text
        except ImportError as exc:
            raise ImportError(
                "Zapis do PostgreSQL wymaga dodatkowych zaleznosci: "
                'pip install -e ".[postgres]"'
            ) from exc
        self._text = text
        self._engine = create_engine(database_url)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                self._text(
                    """
                    CREATE TABLE IF NOT EXISTS room_co2_ppm (
                        id SERIAL PRIMARY KEY,
                        ppm INTEGER NOT NULL,
                        measured_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
            )

    def save(self, reading: Co2Reading, timestamp: datetime) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                self._text("INSERT INTO room_co2_ppm (ppm, measured_at) VALUES (:ppm, :ts)"),
                {"ppm": reading.ppm, "ts": timestamp},
            )
        logger.debug("Zapisano pomiar %s ppm do bazy.", reading.ppm)
