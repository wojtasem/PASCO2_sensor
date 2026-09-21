import pytest

from pasco2.protocol import commands


def test_build_write_command_format():
    assert commands.build_write_command("04", "00") == b"W,04,00\n"


def test_build_read_command_format():
    assert commands.build_read_command("05") == b"R,05\n"


def test_known_commands_match_original_protocol_bytes():
    # Wartosci potwierdzone wzgledem oryginalnego skryptu
    # legacy/PASCO2Monitor.py ORAZ empirycznie na prawdziwym sensorze
    # (docs/protocol-notes.md) - nie zmieniaj bez ponownej weryfikacji.
    assert commands.CMD_SET_IDLE == bytes([0x57, 0x2C, 0x30, 0x34, 0x2C, 0x30, 0x30, 0x0A])
    assert commands.CMD_SET_MEASUREMENT_RATE_LSB == bytes(
        [0x57, 0x2C, 0x30, 0x32, 0x2C, 0x30, 0x30, 0x0A]
    )
    assert commands.CMD_SET_MEASUREMENT_RATE_MSB == bytes(
        [0x57, 0x2C, 0x30, 0x33, 0x2C, 0x30, 0x41, 0x0A]
    )
    assert commands.CMD_SET_CONTINUOUS == bytes([0x57, 0x2C, 0x30, 0x34, 0x2C, 0x30, 0x32, 0x0A])
    assert commands.CMD_READ_STATUS == bytes([0x52, 0x2C, 0x30, 0x37, 0x0A])
    assert commands.CMD_READ_CO2_MSB == bytes([0x52, 0x2C, 0x30, 0x35, 0x0A])
    assert commands.CMD_READ_CO2_LSB == bytes([0x52, 0x2C, 0x30, 0x36, 0x0A])


def test_init_sequence_order():
    assert commands.INIT_CONTINUOUS_MODE_SEQUENCE == (
        commands.CMD_SET_IDLE,
        commands.CMD_SET_MEASUREMENT_RATE_LSB,
        commands.CMD_SET_MEASUREMENT_RATE_MSB,
        commands.CMD_SET_CONTINUOUS,
    )


def test_build_measurement_rate_commands_encodes_seconds_as_hex_msb():
    lsb_cmd, msb_cmd = commands.build_measurement_rate_commands(10)
    assert lsb_cmd == b"W,02,00\n"
    assert msb_cmd == b"W,03,0A\n"


def test_build_measurement_rate_commands_rejects_out_of_range():
    with pytest.raises(ValueError):
        commands.build_measurement_rate_commands(0)
    with pytest.raises(ValueError):
        commands.build_measurement_rate_commands(256)


def test_build_init_continuous_mode_sequence_default_matches_legacy_constant():
    # rate=10 to domyslna, zweryfikowana empirycznie wartosc - sekwencja
    # zbudowana dynamicznie musi dawac te same bajty co stala legacy.
    assert commands.build_init_continuous_mode_sequence(10) == commands.INIT_CONTINUOUS_MODE_SEQUENCE


def test_build_init_continuous_mode_sequence_custom_rate():
    seq = commands.build_init_continuous_mode_sequence(30)
    assert seq[0] == commands.CMD_SET_IDLE
    assert seq[1] == b"W,02,00\n"
    assert seq[2] == b"W,03,1E\n"  # 30 dec = 0x1E
    assert seq[3] == commands.CMD_SET_CONTINUOUS


def test_status_data_ready_bit_value():
    # Zweryfikowane empirycznie na prawdziwym sensorze - docs/protocol-notes.md.
    assert commands.STATUS_DATA_READY_BIT == 0x10
