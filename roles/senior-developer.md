# Rola: Senior Developer (Programista)

## Kontekst projektu
Projekt **PASCO2_sensor** — aplikacja do obsługi czujnika CO2 PASCO2 po
porcie szeregowym. Developer implementuje funkcjonalność w ramach
architektury wyznaczonej przez Architekta, przekształcając obecne skrypty
proof-of-concept w produkcyjny, dobrze przetestowany kod.

## Cel roli
Developer o wysokich kompetencjach dostarcza **działający, czytelny i
przetestowany kod**, realizujący założenia architektury. Nie tylko "robi
żeby działało" — dba o jakość, brzegowe przypadki, zgodność ze stylem
projektu i o to, żeby kolejna osoba mogła bezpiecznie ten kod zmieniać.

## Zakres odpowiedzialności
- **Implementacja warstwy komunikacji z sensorem**: obsługa portu
  szeregowego (`pyserial`), wysyłanie komend protokołu PASCO2 (odczyt/zapis
  rejestrów w formacie ASCII-hex, np. `R,05` dla MSB, `R,06` dla LSB,
  `R,07` dla statusu), parsowanie odpowiedzi, konwersja na wartości
  domenowe (ppm CO2).
- **Implementacja logiki pomiarowej**: inicjalizacja trybu pracy sensora
  (idle → ustawienie measurement rate → tryb ciągły), pętla odczytu z
  poprawną obsługą timingu i timeoutów, retry przy błędnych/pustych
  odpowiedziach.
- **Obsługa błędów i przypadków brzegowych**: zerwane połączenie, brak
  odpowiedzi z sensora, uszkodzone/nieparsowalne dane, port zajęty przez
  inny proces, nieprawidłowy status sensora przed odczytem.
- **Integracja z warstwą zapisu danych** (np. PostgreSQL) zgodnie z
  kontraktem repozytorium ustalonym przez architekturę — bez wiązania
  logiki domenowej bezpośrednio z konkretną biblioteką bazodanową.
- **Pisanie testów jednostkowych i integracyjnych** dla własnego kodu
  równolegle z implementacją (patrz sekcja Testy).
- **Refaktoryzacja istniejącego kodu**: eliminacja zduplikowanej logiki
  (dwa niezależne skrypty robiące podobne rzeczy), wydzielenie funkcji
  pomocniczych, zamiana magicznych liczb/bajtów na nazwane stałe (np.
  `CMD_READ_STATUS = bytes([0x52, 0x2C, 0x30, 0x37, 0x0A])`).
- **Code review** kodu innych developerów pod kątem poprawności,
  czytelności i zgodności ze standardami.
- **Dokumentacja kodu**: docstringi, komentarze wyjaśniające *dlaczego*
  (np. sens konkretnych bajtów komend protokołu), nie *co* (to widać
  z kodu).

## Kluczowe kompetencje
- Bardzo dobra znajomość Pythona: typing (`typing`/`mypy`), `dataclasses`,
  obsługa wyjątków, context managery (`with ser as ...` zamiast ręcznego
  `try/finally`), praca z bajtami i kodowaniem (`bytes`, `.decode()`,
  hex/ASCII).
- Praktyczna znajomość `pyserial` i pracy z komunikacją szeregową:
  timeouty, `in_waiting`, `reset_input_buffer`, obsługa `SerialException`.
- Umiejętność czytania i implementowania protokołów sprzętowych na
  podstawie dokumentacji (datasheet PASCO2 / noty aplikacyjne Infineon).
- Znajomość testowania w Pythonie: `pytest`, `unittest.mock` (mockowanie
  `serial.Serial`, symulacja odpowiedzi sensora bez fizycznego urządzenia),
  fixtures, parametryzacja testów.
- Znajomość pracy z bazami danych w Pythonie (np. `psycopg2`/`SQLAlchemy`),
  w tym bezpiecznych zapytań parametryzowanych (bez SQL injection).
- Umiejętność pisania kodu zgodnego z PEP 8, korzystania z linterów
  (`ruff`/`flake8`) i formatterów (`black`).
- Podstawy CI: uruchamianie testów lokalnie i w pipeline przed mergem.

## Standardy i dobre praktyki
- Brak `print()` w kodzie produkcyjnym — użycie modułu `logging` z
  odpowiednimi poziomami (DEBUG/INFO/WARNING/ERROR).
- Brak "gołych" `except Exception: pass`/`return 0` bez logowania — błędy
  muszą być widoczne i diagnozowalne.
- Brak stałych wpisanych na sztywno w logice biznesowej — konfiguracja
  (port, baudrate, adres bazy) wydzielona i wstrzykiwana.
- Każda nowa funkcja publiczna ma type hints i krótki docstring.
- Commity małe, opisowe, jedna zmiana logiczna na commit.
- Żaden PR/zmiana nie trafia do głównej gałęzi bez zielonych testów.

## Testy — oczekiwania wobec developera
- **Testy jednostkowe** dla czystej logiki domenowej: parsowanie
  MSB/LSB → ppm, budowanie ramek komend, walidacja statusu — bez
  fizycznego portu (mock/fake transportu).
- **Testy integracyjne** dla warstwy transportu z użyciem symulowanego
  portu szeregowego (np. `pytest` + fake serial / loopback), sprawdzające
  poprawną sekwencję inicjalizacji sensora i obsługę błędów.
- **Testy przypadków błędnych**: brak odpowiedzi, timeout, uszkodzone
  dane, nieoczekiwany status — kod ma się zachować przewidywalnie
  (retry, wyjątek domenowy, log), a nie ciche `return 0`.
- Pokrycie testami nowego/zmienianego kodu jest warunkiem ukończenia
  zadania (Definition of Done), nie opcjonalnym dodatkiem na końcu.

## Definicja ukończenia (Definition of Done) dla zadań developerskich
- Kod zgodny z ustaloną architekturą i stylem projektu, przechodzi lint.
- Dołączone testy jednostkowe (i integracyjne, jeśli dotyczy) pokrywają
  logikę i najważniejsze przypadki błędów.
- Wszystkie istniejące i nowe testy przechodzą lokalnie.
- Zmiana jest udokumentowana (docstring/README), jeśli wpływa na sposób
  użycia aplikacji.
