from pasco2.protocol import commands


def test_build_write_command_format():
    assert commands.build_write_command("04", "00") == b"W,04,00\n"


def test_build_read_command_format():
    assert commands.build_read_command("05") == b"R,05\n"


def test_known_commands_match_original_protocol_bytes():
    # Wartosci potwierdzone wzgledem oryginalnego skryptu
    # legacy/PASCO2Monitor.py - nie zmieniaj bez sprawdzenia ze sprzetem.
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
