import pytest

from pasco2.protocol.exceptions import SensorProtocolError
from pasco2.protocol.frames import Co2Reading, is_data_ready, parse_hex_byte


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


def test_is_data_ready_true_when_bit_set():
    # Wartosc zaobserwowana empirycznie na prawdziwym sensorze w probce,
    # w ktorej MSB/LSB mialy juz nowe dane.
    assert is_data_ready(b"10\n") is True


def test_is_data_ready_false_when_bit_not_set():
    # Wartosc zaobserwowana empirycznie miedzy pomiarami.
    assert is_data_ready(b"00\n") is False


def test_is_data_ready_false_for_unrelated_bit():
    # Bit 0x20 (zaobserwowany tuz przed 0x10) nie jest bitem DATA_RDY.
    assert is_data_ready(b"20\n") is False


def test_is_data_ready_true_when_combined_with_other_bits():
    # 0x30 = 0x20 | 0x10 - DATA_RDY nadal ustawiony mimo innego bitu.
    assert is_data_ready(b"30\n") is True
