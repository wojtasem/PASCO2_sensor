from __future__ import annotations

import logging
from datetime import datetime, timezone

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
    config = AppConfig.from_env()
    configure_logging(config.log_level)

    repository = build_repository(config)

    with SerialTransport(config.serial_port, config.baud_rate) as transport:
        service = MeasurementService(transport)
        service.initialize_continuous_mode()

        def on_reading(reading: Co2Reading) -> None:
            timestamp = datetime.now(timezone.utc)
            logger.info("CO2 = %s ppm", reading.ppm)
            repository.save(reading, timestamp)

        try:
            service.run_forever(config.measurement_interval_s, on_reading)
        except KeyboardInterrupt:
            logger.info("Przerwano dzialanie programu przez uzytkownika.")


if __name__ == "__main__":
    main()
