import pytest

from pasco2.application.measurement_service import MeasurementService
from pasco2.protocol import commands
from pasco2.protocol.exceptions import SensorProtocolError
from tests.fakes.fake_transport import FakeSerialTransport


def _make_service_with_ready_sensor():
    transport = FakeSerialTransport()
    for cmd in commands.INIT_CONTINUOUS_MODE_SEQUENCE:
        transport.queue_response(cmd, b"OK\n")
    return MeasurementService(transport), transport


def test_initialize_continuous_mode_sends_expected_sequence():
    service, transport = _make_service_with_ready_sensor()

    service.initialize_continuous_mode()

    assert transport.sent_commands == list(commands.INIT_CONTINUOUS_MODE_SEQUENCE)


def test_read_measurement_happy_path_returns_ppm():
    service, transport = _make_service_with_ready_sensor()
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"02\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"58\n")

    reading = service.read_measurement()

    assert reading.ppm == (0x02 << 8) + 0x58


def test_read_measurement_retries_on_timeout_then_succeeds():
    service, transport = _make_service_with_ready_sensor()
    # Kazda proba odczytu zawsze wysyla STATUS -> MSB -> LSB (tak jak
    # oryginalny protokol), wiec fake musi miec zakolejkowane odpowiedzi
    # na wszystkie trzy komendy w kazdej probie, nawet jesli proba ostatecznie
    # i tak zawiedzie na etapie parsowania.
    #
    # 1. proba: brak odpowiedzi na MSB (timeout) -> caly odczyt odrzucony
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"00\n")
    # 2. proba: poprawne dane
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"01\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"00\n")

    reading = service.read_measurement()

    assert reading.ppm == 0x0100


def test_read_measurement_raises_after_exhausting_retries():
    service, transport = _make_service_with_ready_sensor()
    for _ in range(3):
        transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
        transport.queue_response(commands.CMD_READ_CO2_MSB, b"")  # zawsze brak danych

    with pytest.raises(SensorProtocolError):
        service.read_measurement()


def test_run_forever_stops_when_should_continue_returns_false():
    service, transport = _make_service_with_ready_sensor()
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"01\n")

    readings = []
    calls = {"n": 0}

    def should_continue():
        calls["n"] += 1
        return calls["n"] <= 1  # pozwol na dokladnie jedna iteracje

    service.run_forever(interval_s=0, on_reading=readings.append, should_continue=should_continue)

    assert len(readings) == 1
    assert readings[0].ppm == 1
