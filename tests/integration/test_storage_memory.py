from datetime import datetime, timezone

from pasco2.protocol.frames import Co2Reading
from pasco2.storage.memory_repository import InMemoryMeasurementRepository


def test_save_persists_measurement_with_timestamp():
    repo = InMemoryMeasurementRepository()
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)

    repo.save(Co2Reading(ppm=650), ts)

    assert len(repo.records) == 1
    assert repo.records[0].ppm == 650
    assert repo.records[0].timestamp == ts


def test_save_appends_multiple_measurements_in_order():
    repo = InMemoryMeasurementRepository()
    ts1 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)

    repo.save(Co2Reading(ppm=600), ts1)
    repo.save(Co2Reading(ppm=610), ts2)

    assert [r.ppm for r in repo.records] == [600, 610]
