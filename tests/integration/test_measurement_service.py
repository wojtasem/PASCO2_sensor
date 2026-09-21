import pytest

from pasco2.application.measurement_service import MeasurementService
from pasco2.protocol import commands
from pasco2.protocol.exceptions import SensorProtocolError, SensorTimeoutError
from tests.fakes.fake_transport import FakeSerialTransport


def _make_service_with_ready_sensor(**service_kwargs):
    transport = FakeSerialTransport()
    for cmd in commands.INIT_CONTINUOUS_MODE_SEQUENCE:
        transport.queue_response(cmd, b"OK\n")
    # Male, ale > 0 wartosci - testy nie czekaja realnie na zegar (rzedu
    # milisekund), ale petla polling w _wait_until_data_ready() faktycznie
    # postepuje (poll_interval_s=0 zapetlilby sie w nieskonczonosc, bo
    # "elapsed" nigdy by nie wzroslo).
    service = MeasurementService(
        transport,
        status_poll_interval_s=0.001,
        max_wait_for_data_s=0.005,
        **service_kwargs,
    )
    return service, transport


def test_initialize_continuous_mode_sends_expected_sequence():
    service, transport = _make_service_with_ready_sensor()

    service.initialize_continuous_mode()

    assert transport.sent_commands == list(commands.INIT_CONTINUOUS_MODE_SEQUENCE)


def test_initialize_continuous_mode_uses_custom_rate():
    service, transport = _make_service_with_ready_sensor()
    for cmd in commands.build_init_continuous_mode_sequence(30):
        transport.queue_response(cmd, b"OK\n")

    service.initialize_continuous_mode(rate_seconds=30)

    assert transport.sent_commands == list(commands.build_init_continuous_mode_sequence(30))


def test_read_measurement_waits_for_data_ready_then_returns_ppm():
    service, transport = _make_service_with_ready_sensor()
    # Dwie probki statusu "nie gotowe", trzecia "gotowe" - tak jak
    # zaobserwowalismy na prawdziwym sensorze (0x00 ... 0x00, 0x10).
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_STATUS, b"00\n")
    transport.queue_response(commands.CMD_READ_STATUS, b"10\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"02\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"58\n")

    reading = service.read_measurement()

    assert reading.ppm == (0x02 << 8) + 0x58
    # Nie czytamy MSB/LSB, dopoki status nie zglosi DATA_RDY.
    assert transport.sent_commands == [
        commands.CMD_READ_STATUS,
        commands.CMD_READ_STATUS,
        commands.CMD_READ_STATUS,
        commands.CMD_READ_CO2_MSB,
        commands.CMD_READ_CO2_LSB,
    ]


def test_read_measurement_times_out_when_never_ready():
    service, transport = _make_service_with_ready_sensor()
    # Status nigdy nie zglasza DATA_RDY - kazda z max_retries probek
    # ma skonczyc sie SensorTimeoutError.
    for _ in range(50):
        transport.queue_response(commands.CMD_READ_STATUS, b"00\n")

    with pytest.raises(SensorTimeoutError):
        service.read_measurement()


def test_read_measurement_retries_when_msb_lsb_garbled_after_ready():
    service, transport = _make_service_with_ready_sensor()
    # Kod zawsze czyta LSB zaraz po MSB (nawet gdy MSB jest bledny) -
    # zanim cokolwiek sparsuje - wiec fake musi miec zakolejkowana
    # odpowiedz LSB rowniez dla "zepsutej" proby, inaczej zuzyje
    # odpowiedz przeznaczona dla proby 2.
    #
    # 1. proba: status gotowy, ale MSB uszkodzony -> blad parsowania
    # (LSB i tak zostanie przeczytany, ale nigdy sparsowany).
    transport.queue_response(commands.CMD_READ_STATUS, b"10\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"zz\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"00\n")
    # 2. proba: status znow gotowy, tym razem poprawne dane.
    transport.queue_response(commands.CMD_READ_STATUS, b"10\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"01\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"00\n")

    reading = service.read_measurement()

    assert reading.ppm == 0x0100


def test_read_measurement_raises_after_exhausting_retries():
    service, transport = _make_service_with_ready_sensor(max_retries=2)
    for _ in range(50):
        transport.queue_response(commands.CMD_READ_STATUS, b"00\n")

    with pytest.raises(SensorProtocolError):
        service.read_measurement()


def test_run_forever_stops_when_should_continue_returns_false():
    service, transport = _make_service_with_ready_sensor()
    transport.queue_response(commands.CMD_READ_STATUS, b"10\n")
    transport.queue_response(commands.CMD_READ_CO2_MSB, b"00\n")
    transport.queue_response(commands.CMD_READ_CO2_LSB, b"01\n")

    readings = []
    calls = {"n": 0}

    def should_continue():
        calls["n"] += 1
        return calls["n"] <= 1  # pozwol na dokladnie jedna iteracje

    service.run_forever(on_reading=readings.append, should_continue=should_continue)

    assert len(readings) == 1
    assert readings[0].ppm == 1
