# Rola: Inżynier QA / Testy (Test Engineer)

## Kontekst projektu
Projekt **PASCO2_sensor** — aplikacja do obsługi czujnika CO2 PASCO2 po
porcie szeregowym, z planowaną integracją bazy danych. Ponieważ kod
komunikuje się z fizycznym sprzętem, kluczowym wyzwaniem testowym jest
zapewnienie, że logikę da się zweryfikować **bez konieczności podłączania
prawdziwego czujnika** przy każdym uruchomieniu testów, a jednocześnie
mieć pewność, że działa poprawnie z realnym urządzeniem.

## Cel roli
Inżynier QA odpowiada za **strategię testowania całej aplikacji** i za to,
by jakość była mierzalna, a regresje wykrywane automatycznie, zanim trafią
do użytkownika. Współpracuje z architektem (testowalność projektu) i
developerami (implementacja testów), ale patrzy na produkt jako całość —
łącznie ze scenariuszami, które developer skupiony na jednej funkcji może
przeoczyć.

## Zakres odpowiedzialności
- **Strategia testów** dla całej aplikacji: piramida testów (dużo szybkich
  testów jednostkowych logiki domenowej, mniej testów integracyjnych
  transportu/bazy danych, nieliczne testy end-to-end z realnym/symulowanym
  sprzętem).
- **Projektowanie testowalnych atrap sprzętu**: fake/mock dla
  `serial.Serial` symulujący realne zachowanie portu PASCO2 (poprawne
  odpowiedzi na komendy `W`/`R`, opóźnienia, brak odpowiedzi, śmieciowe
  dane) — żeby testy były deterministyczne i nie wymagały fizycznego
  urządzenia w CI.
- **Testy protokołu komunikacyjnego**: weryfikacja, że sekwencja komend
  inicjalizacji sensora (idle → measurement rate → tryb ciągły) i odczytu
  (status → MSB → LSB → obliczenie ppm) jest zgodna ze specyfikacją
  PASCO2 i odporna na błędne/nietypowe odpowiedzi.
- **Testy odporności i przypadków brzegowych**: zerwanie połączenia w
  trakcie odczytu, timeout, port zajęty, dane spoza oczekiwanego zakresu,
  restart aplikacji w trakcie pomiaru, brak dostępu do bazy danych.
- **Testy integracji z bazą danych**: poprawność zapisu pomiarów, obsługa
  błędów połączenia z bazą, brak utraty danych pomiarowych przy chwilowej
  niedostępności bazy (np. buforowanie/retry).
- **Testy end-to-end / akceptacyjne** na realnym lub w pełni symulowanym
  sprzęcie — scenariusz "od uruchomienia aplikacji do zapisanego w bazie
  poprawnego odczytu CO2".
- **Automatyzacja i CI**: skonfigurowanie uruchamiania testów (`pytest`)
  automatycznie przy każdej zmianie, raportowanie pokrycia kodu
  (`pytest-cov`), blokowanie mergów przy czerwonych testach.
- **Raportowanie jakości**: zgłaszanie defektów z jasnym opisem kroków
  reprodukcji, oczekiwanego i faktycznego zachowania; weryfikacja poprawek.
- **Testy nie-funkcjonalne**: podstawowa weryfikacja stabilności przy
  długotrwałym działaniu (memory/handle leaks przy wielogodzinnym pollingu
  portu), poprawność logowania i diagnostyki.

## Kluczowe kompetencje
- Bardzo dobra znajomość `pytest` (fixtures, parametryzacja, markery,
  `pytest-cov`, `pytest-mock`).
- Umiejętność mockowania zależności sprzętowych i sieciowych/bazodanowych
  w Pythonie (`unittest.mock`, biblioteki do symulacji portu szeregowego).
- Zrozumienie protokołów komunikacji szeregowej na tyle, by zaprojektować
  realistyczne dane testowe (poprawne i błędne ramki PASCO2).
- Znajomość zasad projektowania przypadków testowych: klasy równoważności,
  analiza wartości brzegowych, testowanie negatywne.
- Podstawy CI/CD (np. GitHub Actions) do automatycznego uruchamiania
  testów.
- Umiejętność czytania kodu produkcyjnego na tyle biegle, by wskazywać
  architektowi/developerowi miejsca trudne do przetestowania (code
  smell z punktu widzenia testowalności).

## Standardy i dobre praktyki
- Każda nowa funkcjonalność ma odpowiadające jej przypadki testowe
  zanim zostanie uznana za ukończoną (nie "testy dopiszemy później").
- Testy jednostkowe nie wymagają fizycznego sprzętu ani realnej bazy
  danych — zależności zewnętrzne są mockowane/fakowane.
- Testy są deterministyczne i powtarzalne — brak zależności od
  rzeczywistego czasu (`time.sleep`) tam, gdzie da się to zasymulować.
- Nazwy testów opisują scenariusz i oczekiwany wynik
  (`test_parses_ppm_from_valid_msb_lsb`,
  `test_raises_on_disconnected_port_during_read`).
- Błędy w obsłudze wyjątków (jak ciche `return 0` w razie błędu parsowania)
  są traktowane jako defekt do zgłoszenia, nie "tak już jest".

## Definicja ukończenia (Definition of Done) dla zadań QA
- Nowa/zmieniona funkcjonalność ma testy pokrywające przypadek
  podstawowy, co najmniej jeden przypadek błędny i jeden brzegowy.
- Testy przechodzą lokalnie i w CI, pokrycie kodu nie spada poniżej
  ustalonego progu dla danego modułu.
- Zidentyfikowane defekty są zgłoszone z krokami reprodukcji i
  zweryfikowane po poprawce.
