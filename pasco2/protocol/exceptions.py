class SensorProtocolError(Exception):
    """Blad protokolu PASCO2 - nieoczekiwana lub uszkodzona odpowiedz sensora.

    Rzucany zamiast po cichu zwracac wartosc domyslna (np. 0) - blad musi
    byc widoczny i diagnozowalny, nigdy ukryty.
    """


class SensorTimeoutError(SensorProtocolError):
    """Sensor nie odpowiedzial w oczekiwanym czasie (pusta odpowiedz)."""
