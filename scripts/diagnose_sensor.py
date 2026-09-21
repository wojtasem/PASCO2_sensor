"""Diagnostyka polaczenia z czujnikiem PASCO2 (Sensor2Go / eval board na COM).

Ten skrypt CELOWO nie ufa protokolowi zaimplementowanemu w pasco2/protocol/
- wypisuje surowe bajty (repr + hex) na kazdym kroku wymiany z sensorem,
zebysmy mogli zweryfikowac, czy odtworzony z legacy skryptow protokol
faktycznie pasuje do Twojego konkretnego modulu, zanim zaufamy pelnej
aplikacji (cli/main.py) dzialajacej w petli bez nadzoru.

Uzycie:
    python scripts/diagnose_sensor.py [PORT] [BAUDRATE]

Domyslnie: COM3, 9600 (tak jak w legacy/PASCO2Monitor.py).
"""

from __future__ import annotations

import sys
import time

from pasco2.protocol import commands
from pasco2.protocol.frames import Co2Reading
from pasco2.transport.serial_transport import SerialTransport, SerialTransportError


def hexdump(label: str, data: bytes) -> None:
    print(f"{label}: raw={data!r}  hex=[{data.hex(' ')}]  len={len(data)}")


def send_and_read(transport: SerialTransport, label: str, cmd: bytes) -> bytes:
    print(f"\n>>> Wysylam {label}: {cmd!r}  hex=[{cmd.hex(' ')}]")
    transport.write(cmd)
    time.sleep(0.05)
    response = transport.read_line()
    hexdump(f"<<< Odpowiedz na {label}", response)
    if response == b"":
        print("    [UWAGA] Pusta odpowiedz - albo timeout, albo sensor nie odpowiada na ta komende.")
    return response


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else "COM3"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600

    print(f"Otwieram port {port} @ {baud} baud (timeout=2s)...")
    transport = SerialTransport(port, baud, timeout=2.0)
    try:
        transport.open()
    except SerialTransportError as exc:
        print(f"[BLAD] Nie udalo sie otworzyc portu: {exc}")
        print("Sprawdz: czy port to na pewno COM3, czy nic innego go nie trzyma (np. Arduino IDE / inny skrypt).")
        sys.exit(1)

    print("[OK] Port otwarty. Czekam 1.5s (reset mikrokontrolera przy otwarciu portu bywa czesty)...")
    time.sleep(1.5)
    print()
    print("=" * 70)
    print("KROK 1: Sekwencja inicjalizacji trybu ciaglego (idle -> rate -> continuous)")
    print("=" * 70)
    try:
        send_and_read(transport, "SET_IDLE", commands.CMD_SET_IDLE)
        send_and_read(
            transport, "SET_MEASUREMENT_RATE_LSB", commands.CMD_SET_MEASUREMENT_RATE_LSB
        )
        send_and_read(
            transport, "SET_MEASUREMENT_RATE_MSB", commands.CMD_SET_MEASUREMENT_RATE_MSB
        )
        send_and_read(transport, "SET_CONTINUOUS", commands.CMD_SET_CONTINUOUS)
        transport.reset_input_buffer()

        print("\n" + "=" * 70)
        print("KROK 2: 5x odczyt pomiaru (surowe dane + probka parsowania)")
        print("=" * 70)
        for i in range(1, 6):
            print(f"\n--- Probka {i}/5 ---")
            send_and_read(transport, "READ_STATUS", commands.CMD_READ_STATUS)
            msb = send_and_read(transport, "READ_CO2_MSB", commands.CMD_READ_CO2_MSB)
            lsb = send_and_read(transport, "READ_CO2_LSB", commands.CMD_READ_CO2_LSB)

            try:
                reading = Co2Reading.from_msb_lsb(msb, lsb)
                print(f"    -> Sparsowane jako: {reading.ppm} ppm")
            except Exception as exc:  # celowo szeroko - to diagnostyka, nie produkcja
                print(f"    -> [BLAD PARSOWANIA] {exc}")

            time.sleep(2)

        print("\n" + "=" * 70)
        print("KONIEC. Wklej cala powyzsza sekcje (KROK 1 + KROK 2) do rozmowy z Claude.")
        print("=" * 70)
    finally:
        transport.close()
        print("\nPolaczenie zamkniete.")


if __name__ == "__main__":
    main()
