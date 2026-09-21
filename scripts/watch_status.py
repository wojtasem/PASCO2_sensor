"""Obserwuje rejestr statusu (R,07) w czasie, zeby zweryfikowac empirycznie
kiedy i jak sensor sygnalizuje "dane gotowe" (DATA_RDY), zamiast zgadywac
uklad bitow z pamieci/dokumentacji.

Uzycie:
    python scripts/watch_status.py [PORT] [BAUDRATE] [CZAS_S]

Domyslnie: COM6, 9600, 60s.
"""

from __future__ import annotations

import sys
import time

from pasco2.protocol import commands
from pasco2.protocol.frames import Co2Reading, parse_hex_byte
from pasco2.transport.serial_transport import SerialTransport, SerialTransportError


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "COM6"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
    duration_s = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0

    transport = SerialTransport(port, baud, timeout=2.0)
    try:
        transport.open()
    except SerialTransportError as exc:
        print(f"[BLAD] {exc}")
        sys.exit(1)

    time.sleep(1.5)
    print(f"Port {port} otwarty. Inicjalizuje tryb ciagly...")

    for cmd in commands.INIT_CONTINUOUS_MODE_SEQUENCE:
        transport.write(cmd)
        transport.read_line()
    transport.reset_input_buffer()

    print(f"Zainicjalizowano. Obserwuje status przez {duration_s:.0f}s, co 1s...\n")
    print(f"{'t[s]':>6}  {'status_raw':<12} {'status_int':<12} {'MSB':<8} {'LSB':<8} {'ppm':<8}")
    print("-" * 70)

    start = time.monotonic()
    last_status_int = None
    while time.monotonic() - start < duration_s:
        t = time.monotonic() - start

        transport.write(commands.CMD_READ_STATUS)
        status_raw = transport.read_line()

        try:
            status_int = parse_hex_byte(status_raw)
            status_str = f"0x{status_int:02X} (bin={status_int:08b})"
        except Exception:
            status_int = None
            status_str = "PARSE_ERR"

        # Zawsze czytamy tez MSB/LSB, zeby zobaczyc czy/jak zmieniaja sie
        # niezaleznie od statusu.
        transport.write(commands.CMD_READ_CO2_MSB)
        msb_raw = transport.read_line()
        transport.write(commands.CMD_READ_CO2_LSB)
        lsb_raw = transport.read_line()

        try:
            reading = Co2Reading.from_msb_lsb(msb_raw, lsb_raw)
            ppm_str = str(reading.ppm)
        except Exception:
            ppm_str = "ERR"

        marker = ""
        if status_int is not None and status_int != last_status_int:
            marker = "  <-- ZMIANA STATUSU"
            last_status_int = status_int

        print(
            f"{t:6.1f}  {status_raw!r:<12} {status_str:<20} "
            f"{msb_raw!r:<8} {lsb_raw!r:<8} {ppm_str:<8}{marker}"
        )

        time.sleep(1.0)

    transport.close()
    print("\nZakonczono. Wklej cala tabele do rozmowy z Claude.")


if __name__ == "__main__":
    main()
