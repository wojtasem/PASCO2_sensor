from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SensorTransport(Protocol):
    """Interfejs komunikacji z czujnikiem PASCO2.

    Kazda implementacja (realny port szeregowy, fake do testow) musi
    dostarczac te metody. Warstwy protocol/ i application/ znaja tylko
    ten interfejs - nigdy konkretnej implementacji (np. pyserial).
    """

    def open(self) -> None:
        """Otwiera polaczenie z urzadzeniem."""
        ...

    def close(self) -> None:
        """Zamyka polaczenie."""
        ...

    def write(self, data: bytes) -> None:
        """Wysyla surowe bajty komendy do urzadzenia."""
        ...

    def read_line(self) -> bytes:
        """Czyta jedna linie odpowiedzi. Zwraca b"" gdy brak danych/timeout."""
        ...

    def reset_input_buffer(self) -> None:
        """Czysci bufor wejsciowy."""
        ...

    @property
    def is_open(self) -> bool:
        ...
