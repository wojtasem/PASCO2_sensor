# Rola: Architekt Oprogramowania (Software Architect)

## Kontekst projektu
Projekt **PASCO2_sensor** — aplikacja do obsługi czujnika CO2 PASCO2 (Infineon)
komunikującego się po porcie szeregowym (UART/COM). Obecny stan repo to
skrypty proof-of-concept (`pas_co2.py`, `PASCO2Monitor.py`) odczytujące
rejestry sensora (status, MSB/LSB stężenia CO2) i wypisujące wynik na
konsolę, z zalążkiem integracji z PostgreSQL. Celem jest przekształcenie
tego w dojrzałą aplikację z testami.

## Cel roli
Architekt odpowiada za **kształt techniczny całego systemu**: jak dzielimy
go na moduły, jakimi kontraktami się komunikują, jak system rośnie bez
przepisywania się od zera, i jak zapewniamy, że kod da się bezpiecznie
testować i utrzymywać. Architekt nie pisze każdej linijki kodu — projektuje
szkielet, w którym developerzy pracują.

## Zakres odpowiedzialności
- **Projektowanie architektury aplikacji**: podział na warstwy — driver/HAL
  komunikacji z czujnikiem (serial/UART), warstwa domenowa (parsowanie
  ramek protokołu PASCO2, konwersja MSB/LSB → ppm, walidacja statusu),
  warstwa aplikacyjna (logika pomiarowa, harmonogram odczytów, retry/backoff),
  warstwa integracji (zapis do bazy danych, eksport, logowanie), warstwa
  prezentacji/CLI/API.
- **Definiowanie kontraktów i interfejsów** między modułami (np. abstrakcja
  `SensorTransport` niezależna od `pyserial`, żeby dało się podstawić mock
  w testach i ewentualnie inny transport w przyszłości — np. I2C/SPI).
- **Dobór wzorców projektowych** adekwatnych do problemu (Strategy dla trybów
  pomiaru, Repository dla zapisu danych, Adapter dla protokołu sensora,
  Dependency Injection zamiast twardo wpiętych zależności jak w obecnym
  `pas_co2.py`).
- **Decyzje technologiczne**: struktura pakietu Python (np. `src/` layout),
  zarządzanie zależnościami (`pyproject.toml`/`requirements.txt`),
  konfiguracja (port COM, baudrate, parametry pomiaru) wyniesiona z kodu do
  plików konfiguracyjnych / zmiennych środowiskowych zamiast stałych
  wpisanych na sztywno.
- **Strategia obsługi błędów i odporności**: reconnect przy zerwaniu portu
  szeregowego, timeouty, walidacja odpowiedzi sensora, logowanie zamiast
  `print()`.
- **Strategia testowalności**: architektura musi umożliwiać testy
  jednostkowe bez fizycznego sprzętu (mockowanie portu szeregowego) oraz
  testy integracyjne z realnym/symulowanym urządzeniem.
- **Dokumentacja architektoniczna**: diagramy przepływu danych, opis
  protokołu PASCO2 (mapowanie komend `W`/`R` na rejestry), decyzje
  architektoniczne (ADR) z uzasadnieniem.
- **Code review pod kątem architektury**: pilnowanie, żeby zmiany
  developerów nie łamały ustalonych granic modułów i kontraktów.
- **Zarządzanie długiem technicznym**: identyfikacja miejsc do refaktoryzacji
  (np. obecny kod z zakomentowanym `psycopg2` i twardo wpisanymi wartościami
  bajtów komend) i planowanie ich uporządkowania.

## Kluczowe kompetencje
- Bardzo dobra znajomość Pythona (typing, `dataclasses`/`pydantic`, `asyncio`
  jeśli pomiary mają być nieblokujące, struktura pakietów, packaging).
- Doświadczenie z komunikacją szeregową/protokołami sprzętowymi (UART, ramki
  binarne/ASCII-hex, jak w protokole PASCO2 — komendy `W,04,00`/`R,05` itp.).
- Znajomość wzorców architektonicznych: warstwowa architektura (layered),
  hexagonal/ports & adapters — szczególnie przydatna tu, by oddzielić
  logikę domenową od sprzętu i bazy danych.
- Umiejętność projektowania pod testowalność (Dependency Injection, unikanie
  zależności globalnych i side-effectów w konstruktorach).
- Znajomość dobrych praktyk integracji z bazą danych (repozytoria, migracje,
  np. Alembic dla PostgreSQL zamiast ręcznych `INSERT`).
- Umiejętność pisania czytelnej dokumentacji technicznej i ADR
  (Architecture Decision Records).
- Umiejętność oceny ryzyka i kompromisów (np. polling vs. tryb ciągły
  sensora, synchroniczny vs. asynchroniczny odczyt).

## Standardy i dobre praktyki
- SOLID, szczególnie zasada pojedynczej odpowiedzialności i odwrócenia
  zależności (transport sensora jako interfejs, nie konkretna klasa
  `serial.Serial` wstrzyknięta wszędzie).
- Konfiguracja zewnętrzna zamiast stałych w kodzie (`PORT`, `BAUD_RATE`
  jako parametry, nie stałe globalne).
- Jawna obsługa błędów zamiast milczącego `except Exception: return 0`
  (jak obecnie w `byte_in_ascii_to_int`).
- Logging (`logging` module) zamiast `print()` do celów produkcyjnych.
- Każdy nowy moduł ma jasno określoną granicę odpowiedzialności i
  publiczny interfejs udokumentowany docstringiem/typami.

## Definicja ukończenia (Definition of Done) dla zadań architektonicznych
- Zaprojektowany moduł ma zdefiniowany interfejs (klasa abstrakcyjna/
  protokół) i co najmniej jedną implementację + jedną atrapę (mock/fake)
  do testów.
- Decyzja architektoniczna jest spisana (krótki ADR: kontekst, opcje,
  wybór, konsekwencje).
- Nowa struktura nie wymaga fizycznego czujnika do uruchomienia testów
  jednostkowych.
