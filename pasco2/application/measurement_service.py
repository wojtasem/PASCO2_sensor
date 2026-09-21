from __future__ import annotations

import logging
import time
from typing import Callable

from pasco2.protocol import commands
from pasco2.protocol.exceptions import SensorProtocolError
from pasco2.protocol.frames import Co2Reading
from pasco2.transport.base import SensorTransport

logger = logging.getLogger(__name__)


class MeasurementService:
    """Orkiestruje inicjalizacje sensora PASCO2 i petle pomiarowa.

    Zalezy tylko od interfejsu SensorTransport - nie wie nic o pyserial
    ani o bazie danych. Dzieki temu jest w pelni testowalna z
    FakeSerialTransport (patrz tests/fakes/fake_transport.py).
    """

    def __init__(self, transport: SensorTransport, max_retries: int = 3) -> None:
        self._transport = transport
        self._max_retries = max_retries

    def initialize_continuous_mode(self) -> None:
        """Sekwencja inicjalizacji: idle -> measurement rate -> tryb ciagly."""
        for cmd in commands.INIT_CONTINUOUS_MODE_SEQUENCE:
            self._transport.write(cmd)
            self._transport.read_line()
        self._transport.reset_input_buffer()
        logger.info("Sensor zainicjalizowany w trybie ciaglym.")

    def read_measurement(self) -> Co2Reading:
        """Odczytuje jeden pomiar: status -> MSB -> LSB, z retry przy bledzie."""
        last_error: SensorProtocolError | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                self._transport.write(commands.CMD_READ_STATUS)
                self._transport.read_line()

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
        interval_s: float,
        on_reading: Callable[[Co2Reading], None],
        should_continue: Callable[[], bool] = lambda: True,
    ) -> None:
        """Petla pomiarowa - wywoluje on_reading(reading) co interval_s sekund.

        `should_continue` pozwala testom/wywolujacemu zatrzymac petle bez
        polegania na KeyboardInterrupt.
        """
        while should_continue():
            reading = self.read_measurement()
            on_reading(reading)
            time.sleep(interval_s)
