from __future__ import annotations

import logging
import time
from typing import Callable

from pasco2.protocol import commands
from pasco2.protocol.exceptions import SensorProtocolError, SensorTimeoutError
from pasco2.protocol.frames import Co2Reading, is_data_ready
from pasco2.transport.base import SensorTransport

logger = logging.getLogger(__name__)


class MeasurementService:
    """Orkiestruje inicjalizacje sensora PASCO2 i petle pomiarowa.

    Zalezy tylko od interfejsu SensorTransport - nie wie nic o pyserial
    ani o bazie danych. Dzieki temu jest w pelni testowalna z
    FakeSerialTransport (patrz tests/fakes/fake_transport.py).

    Tempo pomiarow wyznacza sam sensor: read_measurement() poluje rejestr
    statusu (R,07) az bit DATA_RDY (0x10) sie zapali, zamiast (tak jak w
    poprzedniej wersji i w legacy skryptach) czytac MSB/LSB na slepo zaraz
    po odczycie statusu bez sprawdzania jego wartosci. Zachowanie
    zweryfikowane empirycznie na prawdziwym sensorze - patrz
    docs/protocol-notes.md.
    """

    def __init__(
        self,
        transport: SensorTransport,
        max_retries: int = 3,
        status_poll_interval_s: float = 1.0,
        max_wait_for_data_s: float = 30.0,
    ) -> None:
        self._transport = transport
        self._max_retries = max_retries
        self._status_poll_interval_s = status_poll_interval_s
        self._max_wait_for_data_s = max_wait_for_data_s

    def initialize_continuous_mode(self, rate_seconds: int = 10) -> None:
        """Sekwencja inicjalizacji: idle -> measurement rate -> tryb ciagly."""
        for cmd in commands.build_init_continuous_mode_sequence(rate_seconds):
            self._transport.write(cmd)
            self._transport.read_line()
        self._transport.reset_input_buffer()
        logger.info("Sensor zainicjalizowany w trybie ciaglym (rate=%ss).", rate_seconds)

    def _wait_until_data_ready(self) -> None:
        """Poluje status (R,07), az bit DATA_RDY sie zapali, z limitem czasu.

        Rzuca SensorTimeoutError, jesli sensor nie zglosi gotowych danych
        w ciagu max_wait_for_data_s - to sygnal, ze cos jest nie tak
        (rozlaczony port, zawieszony sensor), a nie normalna sytuacja do
        cichego zignorowania.
        """
        elapsed = 0.0
        while elapsed < self._max_wait_for_data_s:
            self._transport.write(commands.CMD_READ_STATUS)
            status_raw = self._transport.read_line()
            if status_raw and is_data_ready(status_raw):
                return
            time.sleep(self._status_poll_interval_s)
            elapsed += self._status_poll_interval_s
        raise SensorTimeoutError(
            f"Sensor nie zglosil gotowych danych (DATA_RDY) w ciagu "
            f"{self._max_wait_for_data_s}s."
        )

    def read_measurement(self) -> Co2Reading:
        """Czeka na DATA_RDY i odczytuje jeden pomiar (MSB -> LSB).

        Retry obejmuje cala probe (czekanie + odczyt) - jesli sensor
        zglosi gotowosc, ale odpowiedz MSB/LSB okaze sie uszkodzona, albo
        jesli czekanie na DATA_RDY przekroczy limit czasu, probujemy
        ponownie do max_retries razy zanim poddamy sie z bledem.
        """
        last_error: SensorProtocolError | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                self._wait_until_data_ready()

                self._transport.write(commands.CMD_READ_CO2_MSB)
                msb_raw = self._transport.read_line()

                self._transport.write(commands.CMD_READ_CO2_LSB)
                lsb_raw = self._transport.read_line()

                return Co2Reading.from_msb_lsb(msb_raw, lsb_raw)
            except SensorProtocolError as exc:
                last_error = exc
                logger.warning(
                    "Blad odczytu pomiaru (proba %s/%s): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
        assert last_error is not None
        raise last_error

    def run_forever(
        self,
        on_reading: Callable[[Co2Reading], None],
        should_continue: Callable[[], bool] = lambda: True,
    ) -> None:
        """Petla pomiarowa - wywoluje on_reading(reading) dla kazdego nowego pomiaru.

        Bez dodatkowego time.sleep() na zewnatrz - tempo wyznacza sam
        sensor przez DATA_RDY wewnatrz read_measurement(). Wczesniejsza
        wersja dodawala tu osobny sleep(interval_s), co bylo bledem:
        podwajalo efektywny odstep miedzy pomiarami zamiast po prostu
        poczekac na sensor.
        """
        while should_continue():
            reading = self.read_measurement()
            on_reading(reading)
