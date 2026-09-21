from __future__ import annotations

import logging
from typing import Optional

import serial

from pasco2.transport.base import SensorTransport

logger = logging.getLogger(__name__)


class SerialTransportError(RuntimeError):
    """Blad komunikacji z portem szeregowym."""


class SerialTransport(SensorTransport):
    """Implementacja SensorTransport oparta o pyserial.

    Jedyne miejsce w aplikacji (poza cli/main.py), ktore importuje pyserial.
    """

    def __init__(self, port: str, baud_rate: int, timeout: float = 1.0) -> None:
        self._port = port
        self._baud_rate = baud_rate
        self._timeout = timeout
        self._serial: Optional[serial.Serial] = None

    def open(self) -> None:
        try:
            self._serial = serial.Serial(self._port, self._baud_rate, timeout=self._timeout)
        except serial.SerialException as exc:
            raise SerialTransportError(
                f"Nie udalo sie otworzyc portu {self._port}: {exc}"
            ) from exc
        if not self._serial.is_open:
            raise SerialTransportError(f"Port {self._port} nie zostal otwarty.")
        logger.info("Otwarto port %s (baudrate=%s)", self._port, self._baud_rate)

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Zamknieto port %s", self._port)

    def write(self, data: bytes) -> None:
        if not self._serial:
            raise SerialTransportError("Port nie jest otwarty - wywolaj open() przed write().")
        self._serial.write(data)

    def read_line(self) -> bytes:
        if not self._serial:
            raise SerialTransportError("Port nie jest otwarty - wywolaj open() przed read_line().")
        return self._serial.readline()

    def reset_input_buffer(self) -> None:
        if self._serial:
            self._serial.reset_input_buffer()

    @property
    def is_open(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def __enter__(self) -> "SerialTransport":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
