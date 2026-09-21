# ADR 0001: Architektura warstwowa (ports & adapters) dla PASCO2_sensor

## Kontekst
Pierwotne skrypty (`pas_co2.py`, `PASCO2Monitor.py`) mieszaly w jednym
pliku: otwieranie portu szeregowego, protokol komend PASCO2, petle
pomiarowa i (zakomentowany) zapis do bazy danych. Utrudnia to testowanie
(wymaga fizycznego sensora) i rozwoj (zmiana jednej rzeczy ryzykuje
zepsucie innej).

## Rozwazane opcje
1. Zostawic jeden plik skryptowy, tylko posprzatac nazwy zmiennych.
2. Podzielic na moduly funkcyjne bez jasnych interfejsow miedzy nimi.
3. Architektura warstwowa z jawnymi interfejsami (ports & adapters):
   `transport` (port szeregowy), `protocol` (logika domenowa protokolu),
   `application` (orkiestracja), `storage` (persystencja), `cli` (wejscie).

## Decyzja
Wybrano opcje 3. Kazda warstwa komunikuje sie z sasiednimi przez interfejsy
(`SensorTransport`, `MeasurementRepository`), a konkretne implementacje
(`SerialTransport`, `PostgresMeasurementRepository`, `FakeSerialTransport`,
`InMemoryMeasurementRepository`) sa wstrzykiwane z zewnatrz - w
`cli/main.py` dla aplikacji, w testach dla weryfikacji logiki.

## Konsekwencje
- Logike protokolu (`protocol/`) i orkiestracji (`application/`) mozna
  testowac jednostkowo/integracyjnie bez fizycznego czujnika i bez bazy
  danych.
- Dodanie nowego typu transportu (np. I2C/SPI) albo bazy danych (np.
  SQLite, InfluxDB) nie wymaga zmian w `protocol/` ani `application/` -
  tylko nowej implementacji odpowiedniego interfejsu.
- Wiecej plikow/modulow niz w jednym skrypcie - akceptowalny koszt w
  zamian za testowalnosc i mozliwosc bezpiecznego rozwoju przez kilka
  osob rownolegle.
- Oryginalne skrypty zachowane w `legacy/` jako punkt odniesienia dla
  logiki protokolu, do czasu pelnego pokrycia ich funkcjonalnosci przez
  nowy kod.
