from __future__ import annotations

import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from pasco2.application.measurement_service import MeasurementService
from pasco2.config import AppConfig
from pasco2.logging_config import configure_logging
from pasco2.protocol.frames import Co2Reading
from pasco2.storage.base import MeasurementRepository
from pasco2.storage.memory_repository import InMemoryMeasurementRepository
from pasco2.transport.serial_transport import SerialTransport

logger = logging.getLogger(__name__)


def build_repository(config: AppConfig) -> MeasurementRepository:
    """Wybiera implementacje repozytorium na podstawie konfiguracji.

    Jedyne miejsce w aplikacji, ktore decyduje, jaka implementacja
    MeasurementRepository jest uzywana.
    """
    if config.database_url:
        from pasco2.storage.postgres_repository import PostgresMeasurementRepository

        return PostgresMeasurementRepository(config.database_url)
    logger.warning("Brak DATABASE_URL - pomiary beda przechowywane tylko w pamieci.")
    return InMemoryMeasurementRepository()


def main() -> None:
    # Wczytuje plik .env (jesli istnieje) do zmiennych srodowiskowych
    # procesu, zanim AppConfig.from_env() je odczyta. AppConfig sam nie
    # dotyka plikow - to jedyne miejsce w aplikacji z ta odpowiedzialnoscia,
    # zeby config.py zostal latwy do testowania bez dotykania dysku.
    load_dotenv()

    config = AppConfig.from_env()
    configure_logging(config.log_level)

    repository = build_repository(config)

    rate_seconds = max(1, min(255, round(config.measurement_interval_s)))

    with SerialTransport(config.serial_port, config.baud_rate) as transport:
        service = MeasurementService(
            transport,
            max_wait_for_data_s=max(30.0, rate_seconds * 3),
        )
        service.initialize_continuous_mode(rate_seconds=rate_seconds)

        def on_reading(reading: Co2Reading) -> None:
            timestamp = datetime.now(timezone.utc)
            logger.info("CO2 = %s ppm", reading.ppm)
            repository.save(reading, timestamp)

        try:
            service.run_forever(on_reading)
        except KeyboardInterrupt:
            logger.info("Przerwano dzialanie programu przez uzytkownika.")


if __name__ == "__main__":
    main()
