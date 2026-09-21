---
name: pasco2-architekt
description: Użyj tego skilla, gdy projektujesz lub zmieniasz architekturę aplikacji PASCO2_sensor — podział na moduły/warstwy, interfejsy między transportem sensora a logiką domenową i bazą danych, wybór wzorców projektowych, decyzje technologiczne, strategię testowalności i obsługi błędów. Uruchamiaj PRZED pisaniem kodu implementacyjnego dla nowej funkcjonalności lub większej refaktoryzacji.
---

# Architekt Oprogramowania — PASCO2_sensor

Pełny opis roli: `roles/architekt-oprogramowania.md` w katalogu projektu —
przeczytaj go, jeśli potrzebujesz pełnego kontekstu kompetencji i standardów.
Ten skill mówi, co konkretnie zrobić, gdy pracujesz jako architekt nad tym
projektem.

## Kiedy używać
- Przed dodaniem nowego modułu lub większej zmianą struktury kodu.
- Gdy trzeba zdecydować, jak podłączyć nową zależność (np. bazę danych,
  nowy typ transportu, harmonogram pomiarów).
- Gdy kod zaczyna łączyć ze sobą rzeczy, które powinny być rozdzielone
  (np. logika parsowania protokołu wymieszana z kodem portu szeregowego).

## Docelowy podział na warstwy (obowiązujący w tym projekcie)
1. **`transport/`** — komunikacja fizyczna z sensorem. Definiuje interfejs
   `SensorTransport` (protokół/ABC) z metodami typu `write(bytes)`,
   `read_line() -> bytes`, `open()`, `close()`. Implementacja produkcyjna
   oparta o `pyserial`; implementacja testowa (`FakeSerialTransport`) do
   testów bez fizycznego sprzętu.
2. **`protocol/`** — znajomość protokołu PASCO2: budowanie ramek komend
   (`W,XX,YY` / `R,XX`), parsowanie surowych odpowiedzi na wartości (status,
   MSB, LSB → ppm). Czysta logika, zero I/O, w 100% testowalna bez mocków.
3. **`application/`** (domena/serwis) — sekwencja inicjalizacji sensora
   (idle → measurement rate → tryb ciągły), pętla pomiarowa, retry/backoff,
   walidacja statusu przed odczytem. Zależy od `transport` i `protocol`
   przez interfejsy, nie przez konkretne implementacje.
4. **`storage/`** — interfejs `MeasurementRepository` (np. `save(ppm,
   timestamp)`), implementacja PostgreSQL (`SQLAlchemy`/`psycopg2`) i
   implementacja w pamięci do testów.
5. **`cli/` / wejście aplikacji** — parsowanie konfiguracji (port, baudrate,
   connection string bazy) ze zmiennych środowiskowych/pliku config, spięcie
   powyższych warstw (dependency injection w jednym miejscu — `main.py`),
   logowanie.

Zasada: warstwy niższe (`protocol`) nie wiedzą nic o wyższych (`storage`).
Nic poza `cli`/`main` nie tworzy bezpośrednio `serial.Serial(...)` ani
połączenia z bazą — zawsze przez wstrzyknięty interfejs.

## Checklist przy projektowaniu zmiany architektonicznej
1. Zidentyfikuj, do której warstwy należy nowa funkcjonalność.
2. Zdefiniuj interfejs (protokół/ABC) zanim napiszesz implementację.
3. Sprawdź: czy dało by się to przetestować bez fizycznego czujnika i bez
   realnej bazy danych? Jeśli nie — zmień projekt.
4. Zapisz krótki ADR w `docs/adr/NNNN-tytul.md` (kontekst, rozważane
   opcje, decyzja, konsekwencje) dla decyzji, które trudno odkręcić
   (wybór biblioteki bazodanowej, format konfiguracji, sync vs async).
5. Przekaż developerowi: interfejs + gdzie ma trafić implementacja + jakie
   dwie implementacje są potrzebne (produkcyjna + testowa/fake).

## Twarde zasady tego projektu
- Zero stałych `PORT`/`BAUD_RATE`/connection stringów wpisanych na sztywno
  w logice — zawsze konfiguracja wstrzyknięta z zewnątrz.
- Zero `print()` poza ewentualnym prostym CLI-output — reszta przez
  `logging`.
- Każdy nowy publiczny interfejs ma type hints.
- Żadna klasa domenowa/serwisowa nie importuje `serial` ani sterownika
  bazy danych bezpośrednio — tylko przez zdefiniowany interfejs.
