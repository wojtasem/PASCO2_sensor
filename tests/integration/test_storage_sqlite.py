from datetime import datetime, timezone

from pasco2.protocol.frames import Co2Reading
from pasco2.storage.sqlite_repository import SqliteMeasurementRepository


def test_save_persists_measurement_across_reconnect(tmp_path):
    db_path = tmp_path / "measurements.db"
    ts = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    repo = SqliteMeasurementRepository(str(db_path))
    repo.save(Co2Reading(ppm=650), ts)
    repo.close()

    assert db_path.exists()

    # Otwieramy nowa instancje wskazujaca na ten sam plik - dane musza
    # przetrwac zamkniecie polaczenia (to jest cel repozytorium plikowego).
    reopened = SqliteMeasurementRepository(str(db_path))
    rows = reopened.fetch_all()
    reopened.close()

    assert rows == [(650, ts.isoformat())]


def test_save_appends_multiple_measurements_in_order(tmp_path):
    db_path = tmp_path / "measurements2.db"
    repo = SqliteMeasurementRepository(str(db_path))
    ts1 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)

    repo.save(Co2Reading(ppm=600), ts1)
    repo.save(Co2Reading(ppm=610), ts2)
    rows = repo.fetch_all()
    repo.close()

    assert [ppm for ppm, _ in rows] == [600, 610]


def test_creates_parent_directory_if_missing(tmp_path):
    db_path = tmp_path / "nested" / "dir" / "measurements.db"

    repo = SqliteMeasurementRepository(str(db_path))
    repo.save(Co2Reading(ppm=500), datetime(2026, 1, 1, tzinfo=timezone.utc))
    repo.close()

    assert db_path.exists()
