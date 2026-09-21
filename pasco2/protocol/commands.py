from __future__ import annotations

# Adresy rejestrow PASCO2 uzywane przez ta aplikacje (protokol tekstowy
# ASCII: komendy maja postac "W,<rejestr>,<wartosc>\n" / "R,<rejestr>\n").
# Zrodlo: dokumentacja PASCO2 / noty aplikacyjne Infineon oraz oryginalne
# skrypty proof-of-concept w legacy/.
REG_MEASUREMENT_RATE_LSB = "02"
REG_MEASUREMENT_RATE_MSB = "03"
REG_MEAS_CFG = "04"  # tryb pracy sensora: idle / tryb ciagly
REG_CO2_PPM_MSB = "05"
REG_CO2_PPM_LSB = "06"
REG_MEAS_STATUS = "07"

MODE_IDLE = "00"
MODE_CONTINUOUS = "02"


def build_write_command(register: str, value: str) -> bytes:
    """Buduje ramke komendy zapisu: W,<rejestr>,<wartosc>\\n."""
    return f"W,{register},{value}\n".encode("ascii")


def build_read_command(register: str) -> bytes:
    """Buduje ramke komendy odczytu: R,<rejestr>\\n."""
    return f"R,{register}\n".encode("ascii")


# Gotowe, nazwane komendy - odpowiadaja bajtom uzywanym wprost w
# legacy/PASCO2Monitor.py. Nie kopiuj surowych bytes([...]) w nowym kodzie,
# uzywaj tych stalych albo build_write_command/build_read_command.
CMD_SET_IDLE = build_write_command(REG_MEAS_CFG, MODE_IDLE)
CMD_SET_MEASUREMENT_RATE_LSB = build_write_command(REG_MEASUREMENT_RATE_LSB, "00")
CMD_SET_MEASUREMENT_RATE_MSB = build_write_command(REG_MEASUREMENT_RATE_MSB, "0A")
CMD_SET_CONTINUOUS = build_write_command(REG_MEAS_CFG, MODE_CONTINUOUS)

CMD_READ_STATUS = build_read_command(REG_MEAS_STATUS)
CMD_READ_CO2_MSB = build_read_command(REG_CO2_PPM_MSB)
CMD_READ_CO2_LSB = build_read_command(REG_CO2_PPM_LSB)

# Kolejnosc komend inicjalizujacych tryb ciagly pomiaru - w tej kolejnosci.
INIT_CONTINUOUS_MODE_SEQUENCE = (
    CMD_SET_IDLE,
    CMD_SET_MEASUREMENT_RATE_LSB,
    CMD_SET_MEASUREMENT_RATE_MSB,
    CMD_SET_CONTINUOUS,
)
