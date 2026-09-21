from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional


class FakeSerialTransport:
    """Implementacja SensorTransport do testow - bez fizycznego portu COM.

    Uzycie:
        fake = FakeSerialTransport()
        fake.queue_response(commands.CMD_READ_STATUS, b"00\\n")
        ...
        service = MeasurementService(fake)

    Odpowiedzi sa kolejkowane per-komenda (FIFO): read_line() zwraca
    odpowiedz zakolejkowana dla ostatnio wyslanej komendy. Brak
    zakolejkowanej odpowiedzi -> pusty b"" (symulacja timeoutu pyserial).
    """

    def __init__(self) -> None:
        self._responses: Dict[bytes, deque] = {}
        self.sent_commands: List[bytes] = []
        self.raise_on_write: Optional[Exception] = None
        self._is_open = False

    def queue_response(self, command: bytes, response: bytes) -> None:
        self._responses.setdefault(command, deque()).append(response)

    def open(self) -> None:
        self._is_open = True

    def close(self) -> None:
        self._is_open = False

    def write(self, data: bytes) -> None:
        if self.raise_on_write is not None:
            raise self.raise_on_write
        self.sent_commands.append(data)

    def read_line(self) -> bytes:
        last_command = self.sent_commands[-1] if self.sent_commands else None
        queue = self._responses.get(last_command)
        if not queue:
            return b""
        return queue.popleft()

    def reset_input_buffer(self) -> None:
        pass

    @property
    def is_open(self) -> bool:
        return self._is_open
