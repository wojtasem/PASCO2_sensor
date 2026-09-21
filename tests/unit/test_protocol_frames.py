import pytest

from pasco2.protocol.exceptions import SensorProtocolError
from pasco2.protocol.frames import Co2Reading, parse_hex_byte


def test_parse_hex_byte_valid():
    assert parse_hex_byte(b"1A\n") == 0x1A


def test_parse_hex_byte_empty_raises_protocol_error():
    with pytest.raises(SensorProtocolError):
        parse_hex_byte(b"")


def test_parse_hex_byte_garbage_raises_protocol_error():
    with pytest.raises(SensorProtocolError):
        parse_hex_byte(b"not-hex\n")


def test_co2_reading_from_msb_lsb_computes_ppm():
    reading = Co2Reading.from_msb_lsb(b"02\n", b"58\n")
    assert reading.ppm == (0x02 << 8) + 0x58


def test_co2_reading_from_msb_lsb_zero():
    reading = Co2Reading.from_msb_lsb(b"00\n", b"00\n")
    assert reading.ppm == 0


def test_co2_reading_from_msb_lsb_raises_on_garbage_lsb():
    with pytest.raises(SensorProtocolError):
        Co2Reading.from_msb_lsb(b"02\n", b"zz\n")
