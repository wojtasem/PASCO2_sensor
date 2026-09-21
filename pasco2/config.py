from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class AppConfig:
    """Konfiguracja aplikacji, wczytywana ze zmiennych srodowiskowych.

    Zadna warstwa domenowa (protocol/, application/, storage/) nie powinna
    czytac zmiennych srodowiskowych bezposrednio - zawsze przez ten obiekt,
    wstrzykiwany z cli/main.py. Dzieki temu logike da sie testowac bez
    dotykania prawdziwego srodowiska.
    """

    serial_port: str
    baud_rate: int
    measurement_interval_s: float
    log_level: str
    database_url: Optional[str] = None

    @staticmethod
    def from_env(env: Optional[Mapping[str, str]] = None) -> "AppConfig":
        env = env if env is not None else os.environ
        return AppConfig(
            serial_port=env.get("PASCO2_PORT", "COM3"),
            baud_rate=int(env.get("PASCO2_BAUDRATE", "9600")),
            # Domyslnie 10s - jedyna wartosc rate zweryfikowana empirycznie
            # na prawdziwym sensorze (patrz docs/protocol-notes.md). Inne
            # wartosci moga dzialac inaczej niz oczekujesz - zweryfikuj
            # scripts/watch_status.py po zmianie.
            measurement_interval_s=float(env.get("PASCO2_MEASUREMENT_INTERVAL_S", "10")),
            log_level=env.get("PASCO2_LOG_LEVEL", "INFO"),
            database_url=env.get("DATABASE_URL") or None,
        )
