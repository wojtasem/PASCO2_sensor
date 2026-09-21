import logging

from pasco2.cli.main import build_repository
from pasco2.config import AppConfig
from pasco2.storage.memory_repository import InMemoryMeasurementRepository
from pasco2.storage.sqlite_repository import SqliteMeasurementRepository


def _config(database_url):
    return AppConfig(
        serial_port="COM_TEST",
        baud_rate=9600,
        measurement_interval_s=10,
        log_level="INFO",
        database_url=database_url,
    )


def test_build_repository_defaults_to_memory_when_no_database_url():
    repo = build_repository(_config(None))
    assert isinstance(repo, InMemoryMeasurementRepository)


def test_build_repository_uses_sqlite_for_sqlite_url(tmp_path):
    db_path = tmp_path / "measurements.db"

    repo = build_repository(_config(f"sqlite:///{db_path}"))
    try:
        assert isinstance(repo, SqliteMeasurementRepository)
    finally:
        repo.close()

    assert db_path.exists()


def test_build_repository_falls_back_to_memory_for_unknown_scheme(caplog):
    with caplog.at_level(logging.WARNING):
        repo = build_repository(_config("mysql://user:pass@host/db"))

    assert isinstance(repo, InMemoryMeasurementRepository)
    assert "Nierozpoznany format" in caplog.text
