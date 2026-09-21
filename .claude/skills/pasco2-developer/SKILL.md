---
name: pasco2-developer
description: Użyj tego skilla podczas implementowania funkcjonalności aplikacji PASCO2_sensor w Pythonie — obsługa portu szeregowego, protokół PASCO2 (komendy W/R, MSB/LSB, ppm), logika pomiarowa, zapis do bazy danych, refaktoryzacja pas_co2.py/PASCO2Monitor.py. Uruchamiaj przy każdym pisaniu lub zmienianiu kodu produkcyjnego w tym projekcie, razem z testami dla tej zmiany.
---

# Senior Developer — PASCO2_sensor

Pełny opis roli: `roles/senior-developer.md`. Architekturę, w którą musi się
wpasować kod, opisuje skill `pasco2-architekt` (warstwy `transport/`,
`protocol/`, `application/`, `storage/`, `cli/`).

## Zanim zaczniesz pisać kod
1. Sprawdź, do której warstwy należy zadanie (transport / protocol /
   application / storage / cli).
2. Jeśli interfejs dla tej warstwy jeszcze nie istnieje — najpierw zdefiniuj
   go (patrz `pasco2-architekt`), potem implementuj.
3. Planuj od razu testy dla tej zmiany — nie „na koniec”.

## Znane fakty o protokole PASCO2 (z istniejącego kodu, do wykorzystania
## i zweryfikowania w implementacji)
- Komendy wysyłane jako ASCII: `W,<rejestr>,<wartość>\n` (zapis) i
  `R,<rejestr>\n` (odczyt), np. `bytes([0x52, 0x2C, 0x30, 0x35, 0x0A])`
  = `R,05\n`.
- Sekwencja inicjalizacji trybu ciągłego: idle (`W,04,00`) → measurement
  rate (`W,02,00`, `W,03,0A`) → tryb ciągły (`W,04,02`).
- Odczyt pomiaru: status (`R,07`) → MSB (`R,05`) → LSB (`R,06`) →
  `ppm = (msb << 8) + lsb`.
- Odpowiedzi przychodzą jako ASCII-hex, dekodowane i parsowane `int(...,
  16)`.
- **Zamień magiczne bajty na nazwane stałe** w module `protocol/` (np.
  `CMD_IDLE`, `CMD_READ_STATUS`, `REG_MSB`, `REG_LSB`) — nie kopiuj
  surowych `bytes([...])` po kodzie.

## Zasady implementacji obowiązkowe w tym projekcie
- Żadnego `except Exception: return 0` bez logowania — błąd parsowania ma
  rzucić jawny wyjątek domenowy (np. `SensorProtocolError`) albo być
  zalogowany na poziomie WARNING/ERROR z kontekstem (jaka komenda, jaka
  odpowiedź).
- Żadnego `print()` w kodzie produkcyjnym — `logging.getLogger(__name__)`.
- `PORT`, `BAUD_RATE`, connection string bazy — parametry wstrzykiwane
  (konfiguracja/env), nie stałe globalne w module.
- Użyj context managera dla portu szeregowego i połączenia z bazą
  (`with`), nie ręcznego `try/finally` z `if 'ser' in locals()`.
- Type hints na każdej nowej funkcji/metodzie publicznej + krótki
  docstring (po polsku lub angielsku — zgodnie z resztą pliku).
- Commity małe i opisowe, jedna logiczna zmiana na commit.

## Definition of Done dla każdej zmiany
- [ ] Kod w odpowiedniej warstwie, zgodny z interfejsami z `pasco2-architekt`.
- [ ] Brak `print`, brak cichych `except`, brak stałych na sztywno.
- [ ] Testy jednostkowe dla logiki domenowej (parsowanie, budowanie ramek).
- [ ] Testy integracyjne dla transportu/bazy z użyciem faków (patrz
      `pasco2-qa-testy`), jeśli zmiana tego dotyczy.
- [ ] Wszystkie testy (`pytest`) przechodzą lokalnie.
- [ ] Lint (`ruff`/`flake8`) czysty.
- [ ] Docstring/README zaktualizowany, jeśli zmienia się sposób użycia.

## Refaktoryzacja istniejących skryptów
`pas_co2.py` i `PASCO2Monitor.py` robią podobne rzeczy dwoma różnymi
sposobami (prosty nasłuch vs. pełna sekwencja komend). Docelowo mają się
stać cienkimi punktami wejścia (`cli/`) korzystającymi z tych samych
modułów `transport/`, `protocol/`, `application/` — bez duplikacji logiki
odczytu portu ani parsowania.
