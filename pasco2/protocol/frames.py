from __future__ import annotations

from dataclasses import dataclass

from pasco2.protocol.exceptions import SensorProtocolError


def parse_hex_byte(raw: bytes) -> int:
    """Parsuje surowa odpowiedz sensora (ASCII-hex) na wartosc calkowita.

    Rzuca SensorProtocolError zamiast po cichu zwracac 0 (tak jak robil to
    legacy `byte_in_ascii_to_int`) - blad ma byc widoczny, nie ukryty.
    """
    if not raw:
        raise SensorProtocolError("Pusta odpowiedz od sensora (brak danych/timeout).")
    try:
        text = raw.decode("ascii").strip()
        return int(text, 16)
    except (UnicodeDecodeError, ValueError) as exc:
        raise SensorProtocolError(
            f"Nie mozna sparsowac odpowiedzi sensora jako liczby hex: {raw!r}"
        ) from exc


@dataclass(frozen=True)
class Co2Reading:
    """Wynik pojedynczego pomiaru stezenia CO2."""

    ppm: int

    @staticmethod
    def from_msb_lsb(msb_raw: bytes, lsb_raw: bytes) -> "Co2Reading":
        """Buduje odczyt z surowych odpowiedzi na komendy MSB/LSB.

        ppm = (msb << 8) + lsb, tak samo jak w legacy/PASCO2Monitor.py.
        """
        msb = parse_hex_byte(msb_raw)
        lsb = parse_hex_byte(lsb_raw)
        return Co2Reading(ppm=(msb << 8) + lsb)
