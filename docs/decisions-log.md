# Dziennik decyzji i stanu projektu

> Ten plik to podsumowanie pracy wykonanej z Claude w sesji w chmurze (Cowork),
> ktora nie jest widoczna w historii sesji rozszerzenia Claude Code w VS Code
> (ta sesja byla polaczona przez folder na urzadzeniu, a nie przez repozytorium
> GitHub od startu). Sluzy jako kontekst przy dalszej pracy nad projektem w VS Code.

## Cel projektu

Aplikacja Python do obslugi czujnika CO2 Infineon PASCO2 (plytka ewaluacyjna
Sensor2Go) po porcie szeregowym. Zastapienie dwoch prowizorycznych skryptow
proof-of-concept pelnoprawna aplikacja z testami i CI.

## Architektura (warstwowa / ports-and-adapters)

- `pasco2/transport/` - interfejs I/O do sprzetu (`SensorTransport` Protocol),
  implementacja `SerialTransport` (pyserial).
- `pasco2/protocol/` - czysta logika komend/parsowania, bez I/O
  (`commands.py`, `frames.py`).
- `pasco2/application/` - orkiestracja (`MeasurementService`).
- `pasco2/storage/` - interfejs `MeasurementRepository` + implementacje
  (`InMemoryMeasurementRepository`, `SqliteMeasurementRepository`,
  `PostgresMeasurementRepository`).
- `pasco2/cli/main.py` - "composition root" (laczy wszystko, wczytuje .env,
  wybiera repozytorium wg `DATABASE_URL`).

Decyzja architektoniczna spisana w `docs/adr/0001-architektura-warstwowa.md`.

Testy z podwojnikami (test doubles) zamiast prawdziwego sprzetu/bazy:
`FakeSerialTransport` (kolejka odpowiedzi per-komenda, FIFO),
`InMemoryMeasurementRepository`.

## Kluczowe fakty o protokole PASCO2 (zweryfikowane na prawdziwym sensorze)

Pelne, surowe dane pomiarowe i historia diagnostyki: `docs/protocol-notes.md`.
Skrot najwazniejszych ustalen:

- Komendy ASCII: `W,<rejestr>,<wartosc>\n` (zapis) / `R,<rejestr>\n` (odczyt).
  ACK = `\x06\n`.
- Rejestry: `0x02`/`0x03` = LSB/MSB predkosci pomiaru, `0x04` = konfiguracja
  trybu (idle=`00`, continuous=`02`), `0x05`/`0x06` = MSB/LSB CO2 ppm,
  `0x07` = status.
- **Bit DATA_RDY = `0x10`** w rejestrze statusu - trzeba na niego czekac,
  zanim odczyta sie MSB/LSB, inaczej mozna zlapac stare/zerowe dane. Bit
  `0x20` to przejsciowy stan pojawiajacy sie chwile przed `0x10`.
- **Port po otwarciu resetuje sie** (USB-UART bridge resetuje MCU przy DTR) -
  wymagane opoznienie startowe (empirycznie 1.5 s) przed wyslaniem komend.
- **Prawdziwy port sensora to COM6** ("USB Serial Device"), nie COM3 (to byl
  Intel AMT SOL - inne urzadzenie, nie sensor). Pomylka wynikala z braku
  weryfikacji w Menadzerze urzadzen.
- Jedyna empirycznie zweryfikowana wartosc `measurement_interval` to **10 s**
  (`PASCO2_MEASUREMENT_INTERVAL_S=10`). Inne wartosci prawdopodobnie dzialaja,
  ale nie zostaly przetestowane - do weryfikacji przez `scripts/watch_status.py`.

## Naprawione bledy (z realnego uzycia)

1. **Slepy odczyt MSB/LSB** - pierwotny kod ignorowal status i zawsze
   odczytywal dane od razu -> naprawione przez `_wait_until_data_ready()`
   w `MeasurementService`, oparte o `is_data_ready()` / `STATUS_DATA_READY_BIT`.
2. **Podwojne tempo odczytow** - `run_forever()` mial wlasny `time.sleep()`
   NIEZALEZNY od pollingu DATA_RDY -> usuniety parametr `interval_s`,
   tempo pochodzi wylacznie z pollingu w `read_measurement()`.
3. **Zly port (COM3 zamiast COM6)** - zdiagnozowane przez Menadzer urzadzen.
4. **Zerowe odczyty przy pierwszym tescie na sprzecie** - brak opoznienia po
   otwarciu portu -> dodano `startup_delay_s=1.5` w `SerialTransport.open()`.
5. **`.env` nie byl wczytywany** - `AppConfig.from_env()` czyta tylko realne
   zmienne srodowiskowe procesu, nikt nie wolal `load_dotenv()` -> dodano
   `python-dotenv` + wywolanie `load_dotenv()` na poczatku `main()`.
   Potwierdzone dzialanie przez uzytkownika po `pip install -e ".[dev]"`.

## Persystencja danych

Wybrano **SQLite** (zero-setup, biblioteka standardowa `sqlite3`) zamiast
PostgreSQL. `DATABASE_URL` w `.env` dziala jako przelacznik implementacji
(`build_repository()` w `cli/main.py`):
- `sqlite:///plik.db` -> `SqliteMeasurementRepository`
- `postgresql://...` -> `PostgresMeasurementRepository` (wymaga extras `[postgres]`)
- puste / nierozpoznany schemat -> `InMemoryMeasurementRepository` (fallback,
  bez trwalej persystencji, z ostrzezeniem w logu)

Potwierdzone dzialanie end-to-end na prawdziwym sprzecie - realne odczyty CO2
z timestampami zapisane w `pasco2_measurements.db` (np. 689, 692, 693, 695 ppm).

## CI

`.github/workflows/ci.yml` - GitHub Actions, macierz Python 3.10/3.11/3.12:
- `lint-and-test`: ruff + pytest (z artefaktem coverage)
- `build-check`: `python -m build`

Testy oznaczone markerem `e2e` (zalezne od sprzetu/bazy) sa wylaczone z
domyslnego przebiegu pytest (`addopts = "-m \"not e2e\""` w `pyproject.toml`).

Stan testow na koniec sesji: **34/34 przechodza**, `ruff check` czysty.

## VS Code

Dodana konfiguracja workspace (`.vscode/settings.json`, `launch.json`,
`extensions.json`): interpreter, formatter ruff, wykrywanie testow pytest,
4 konfiguracje debugowania (cli.main, diagnose_sensor.py COM6,
watch_status.py COM6 60s, pytest biezacego pliku).

**Uwaga:** sciezka interpretera w `settings.json` zaklada istnienie
`.venv` w katalogu projektu - w trakcie sesji nie znaleziono takiego
srodowiska na komputerze uzytkownika. Moze wymagac recznego utworzenia
(`python -m venv .venv`) lub recznego wyboru interpretera w VS Code.

## Otwarte / niedokonczone watki

- Nie potwierdzono jeszcze pelnego, wklejonego wyniku lokalnego `pytest`
  uruchomionego przez uzytkownika (tylko ustne "dziala").
- **Commit `67a8fa4` (konfiguracja VS Code) nie zostal jeszcze wypchniety
  do GitHub** (branch "ahead of origin/main by 1 commit" w chwili pisania
  tego pliku - warto zrobic `git push`).
- Niesledzony plik `pasco2_measurements.db` w katalogu roboczym (baza z
  testow na sprzecie) - do rozwazenia czy dodac do `.gitignore`, czy
  zostawic bez sledzenia.
- Mozliwe nastepne kroki zaproponowane wczesniej (nie wybrane): skrypt do
  podgladu zapisanych pomiarow, uruchamianie aplikacji jako usluga w tle
  (np. Task Scheduler na Windows).
