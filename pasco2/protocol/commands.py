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

# Bit "dane gotowe" (DATA_RDY) w rejestrze statusu (R,07).
#
# ZWERYFIKOWANE EMPIRYCZNIE na prawdziwym sensorze (Infineon PASCO2 na
# plytce Sensor2Go, USB Serial Device, 2026-09-21, skrypt
# scripts/watch_status.py): status = 0x10 dokladnie w tej probce, w ktorej
# MSB/LSB pokazuja juz nowa wartosc pomiaru; miedzy pomiarami status = 0x00.
# Bit 0x20 pojawia sie na jedna probke tuz przed 0x10 (prawdopodobnie
# "pomiar w toku") - nie jest tu wykorzystywany.
# Szczegoly: docs/protocol-notes.md.
STATUS_DATA_READY_BIT = 0x10


def build_write_command(register: str, value: str) -> bytes:
    """Buduje ramke komendy zapisu: W,<rejestr>,<wartosc>\\n."""
    return f"W,{register},{value}\n".encode("ascii")


def build_read_command(register: str) -> bytes:
    """Buduje ramke komendy odczytu: R,<rejestr>\\n."""
    return f"R,{register}\n".encode("ascii")


def build_measurement_rate_commands(rate_seconds: int) -> tuple[bytes, bytes]:
    """Buduje komendy ustawiajace okres pomiaru sensora (LSB, MSB).

    Zachowuje dokladnie ten sam uklad rejestrow co oryginalny legacy skrypt
    (LSB zawsze "00", MSB = wartosc w sekundach jako bajt ASCII-hex).
    Wartosc 10 zostala zweryfikowana empirycznie - dala okres pomiaru
    ~10s (patrz docs/protocol-notes.md). Nie mamy potwierdzenia semantyki
    dla innych wartosci niz domyslna z datasheetu - zmieniaj ostroznie
    i zweryfikuj scripts/watch_status.py po kazdej zmianie.
    """
    if not 1 <= rate_seconds <= 255:
        raise ValueError("rate_seconds musi byc w zakresie 1-255 (pojedynczy bajt ASCII-hex).")
    lsb_cmd = build_write_command(REG_MEASUREMENT_RATE_LSB, "00")
    msb_cmd = build_write_command(REG_MEASUREMENT_RATE_MSB, f"{rate_seconds:02X}")
    return lsb_cmd, msb_cmd


def build_init_continuous_mode_sequence(rate_seconds: int = 10) -> tuple[bytes, ...]:
    """Buduje pelna sekwencje inicjalizacji trybu ciaglego pomiaru.

    Kolejnosc (idle -> measurement rate -> tryb ciagly) zweryfikowana
    empirycznie na prawdziwym sensorze - kazda komenda dostaje ACK (0x06).
    """
    rate_lsb_cmd, rate_msb_cmd = build_measurement_rate_commands(rate_seconds)
    return (
        build_write_command(REG_MEAS_CFG, MODE_IDLE),
        rate_lsb_cmd,
        rate_msb_cmd,
        build_write_command(REG_MEAS_CFG, MODE_CONTINUOUS),
    )


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

# Domyslna (rate=10s) sekwencja inicjalizacji - zachowana jako stala dla
# wstecznej zgodnosci i testow; rownowazna
# build_init_continuous_mode_sequence(10).
INIT_CONTINUOUS_MODE_SEQUENCE = (
    CMD_SET_IDLE,
    CMD_SET_MEASUREMENT_RATE_LSB,
    CMD_SET_MEASUREMENT_RATE_MSB,
    CMD_SET_CONTINUOUS,
)
