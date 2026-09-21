---
name: pasco2-qa-testy
description: Użyj tego skilla przy pisaniu, planowaniu lub przeglądaniu testów aplikacji PASCO2_sensor — testy jednostkowe protokołu, mockowanie portu szeregowego (pyserial), testy integracyjne z bazą danych, testy odporności na błędy sprzętowe, konfiguracja pytest i CI. Uruchamiaj razem z pasco2-developer przy każdej zmianie kodu, oraz osobno przy projektowaniu strategii testów dla nowej funkcjonalności.
---

# Inżynier QA / Testy — PASCO2_sensor

Pełny opis roli: `roles/inzynier-qa-testy.md`.

## Piramida testów dla tego projektu
1. **Testy jednostkowe (najwięcej, najszybsze)** — moduł `protocol/`:
   budowanie ramek komend, parsowanie MSB/LSB → ppm, walidacja statusu.
   Zero I/O, zero mocków portu — czyste funkcje/klasy.
2. **Testy integracyjne (transport)** — moduł `application/` +
   `transport/` z użyciem `FakeSerialTransport` symulującego realne
   zachowanie portu PASCO2 (poprawne odpowiedzi, opóźnienia, brak
   odpowiedzi, śmieciowe/uszkodzone dane).
3. **Testy integracyjne (storage)** — `storage/` z bazą testową (np.
   SQLite w pamięci albo testowy kontener Postgres) lub fake
   repozytorium — sprawdzają zapis pomiaru i obsługę błędu połączenia.
4. **Testy end-to-end (najmniej)** — pełny przepływ „start aplikacji →
   symulowany/realny sensor → zapis w bazie”, uruchamiane osobno od
   szybkiego zestawu jednostkowego (np. marker `@pytest.mark.e2e`).

## Jak budować fake portu szeregowego
`FakeSerialTransport` implementuje ten sam interfejs co `SensorTransport`
z `pasco2-architekt`. Ma bufor komend → odpowiedzi (słownik lub kolejka),
żeby test mógł zadeklarować: „na `R,05` odpowiedz `X`”. Musi też umieć
symulować:
- brak odpowiedzi (pusty `readline()` / timeout),
- uszkodzone dane (bajty nie dające się zdekodować/sparsować),
- zerwanie połączenia w trakcie sekwencji odczytu (wyjątek przy N-tym
  wywołaniu).

## Obowiązkowe przypadki testowe dla każdej nowej funkcjonalności
- **Przypadek podstawowy** (happy path) — poprawne dane wejściowe/
  odpowiedzi sensora.
- **Przypadek błędny** — brak odpowiedzi / timeout / uszkodzone dane /
  nieoczekiwany status → oczekiwane zachowanie to jawny wyjątek lub log +
  retry, NIGDY ciche `return 0`/`pass`.
- **Przypadek brzegowy** — np. wartość MSB/LSB na granicy zakresu, pusty
  bufor, port zajęty przez inny proces.

## Konwencje nazewnictwa testów
`test_<co>_<warunek>_<oczekiwany_efekt>`, np.:
- `test_parses_ppm_from_valid_msb_lsb`
- `test_raises_sensor_protocol_error_on_garbage_response`
- `test_retries_on_timeout_then_succeeds`
- `test_repository_save_persists_measurement_with_timestamp`

## Konfiguracja narzędzi
- `pytest` jako runner, `pytest-mock`/`unittest.mock` do mockowania,
  `pytest-cov` do pokrycia kodu.
- Testy jednostkowe i integracyjne (transport/storage) muszą przechodzić
  **bez** fizycznego czujnika i bez realnej bazy produkcyjnej — to
  warunek uruchamiania ich w CI.
- Testy e2e ze sprzętem/bazą oznaczone osobnym markerem i uruchamiane
  opcjonalnie (nie blokują standardowego `pytest`).

## Definition of Done dla zadania QA
- [ ] Nowa/zmieniona funkcjonalność ma testy: podstawowy + błędny +
      brzegowy.
- [ ] Żaden test nie wymaga fizycznego portu COM ani realnej bazy do
      przejścia w CI.
- [ ] `pytest` zielony lokalnie, pokrycie nowego kodu nie spada poniżej
      ustalonego progu.
- [ ] Zidentyfikowane podczas testów defekty zgłoszone z krokami
      reprodukcji.
