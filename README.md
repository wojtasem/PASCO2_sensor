# PASCO2_sensor

Aplikacja do odczytu stezenia CO2 z czujnika PASCO2 (Infineon) po porcie
szeregowym (UART) i zapisu pomiarow (opcjonalnie do PostgreSQL).

## Struktura projektu

```
pasco2/
  transport/      # komunikacja z portem szeregowym (interfejs SensorTransport)
  protocol/        # komendy i parsowanie protokolu PASCO2 (czysta logika, bez I/O)
  application/      # orkiestracja: inicjalizacja sensora, petla pomiarowa
  storage/          # zapis pomiarow (PostgreSQL / w pamieci)
  cli/              # punkt wejscia aplikacji (wiaze wszystko razem)
tests/
  unit/             # testy logiki domenowej (bez mockow sprzetu)
  integration/      # testy z FakeSerialTransport / repozytorium w pamieci
  fakes/            # atrapy (test doubles) uzywane w testach
docs/adr/           # decyzje architektoniczne (Architecture Decision Records)
roles/               # opisy rol (architekt, developer, QA) dla tego projektu
.claude/skills/      # skille Claude Code oparte o powyzsze role
legacy/              # oryginalne skrypty proof-of-concept (przed refaktoryzacja)
```

Architektura jest warstwowa (ports & adapters): `application/` i `protocol/`
zaleza tylko od interfejsow (`SensorTransport`, `MeasurementRepository`),
nigdy od konkretnych implementacji jak `pyserial` czy `SQLAlchemy`. Dzieki
temu logike da sie testowac bez fizycznego czujnika i bez prawdziwej bazy
danych. Szczegoly decyzji: `docs/adr/0001-architektura-warstwowa.md`.

## Wymagania
- Python 3.10+

## Instalacja (tryb developerski)
```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -e ".[dev]"
# opcjonalnie, jesli chcesz zapisywac pomiary do PostgreSQL:
pip install -e ".[postgres]"
```

## Konfiguracja
Skopiuj `.env.example` do `.env` i dostosuj wartosci:

| Zmienna | Opis | Domyslnie |
|---|---|---|
| `PASCO2_PORT` | port COM czujnika | `COM3` |
| `PASCO2_BAUDRATE` | predkosc transmisji | `9600` |
| `PASCO2_MEASUREMENT_INTERVAL_S` | odstep miedzy pomiarami (s) | `5` |
| `PASCO2_LOG_LEVEL` | poziom logowania | `INFO` |
| `DATABASE_URL` | connection string PostgreSQL (opcjonalne) | brak |

Jesli `DATABASE_URL` nie jest ustawiony, pomiary trzymane sa tylko w
pamieci procesu (tryb dev/demo) — aplikacja dziala, ale nic nie
persystuje po zamknieciu.

## Uruchomienie
```bash
python -m pasco2.cli.main
```

## Testy
```bash
pip install -e ".[dev]"
pytest
```
Testy jednostkowe i integracyjne dzialaja **bez fizycznego czujnika i bez
prawdziwej bazy danych** — uzywaja `FakeSerialTransport`
(`tests/fakes/fake_transport.py`) i repozytorium w pamieci
(`pasco2/storage/memory_repository.py`). Testy oznaczone
`@pytest.mark.e2e` wymagaja realnego sprzetu/bazy i sa domyslnie
pomijane (patrz `pyproject.toml`, `addopts = "-m \"not e2e\""`).

Pokrycie kodu:
```bash
pytest --cov=pasco2
```

## Role i skille
Opisy rol w `roles/*.md` (architekt, senior developer, inzynier QA) oraz
odpowiadajace im skille Claude Code w `.claude/skills/` opisuja podzial
odpowiedzialnosci, standardy kodu i wymagania testowe obowiazujace w tym
projekcie. Warto je przeczytac przed wiekszymi zmianami.

## Status migracji
Oryginalne skrypty proof-of-concept (`pas_co2.py`, `PASCO2Monitor.py`)
zostaly przeniesione do `legacy/` i zachowane jako punkt odniesienia dla
logiki protokolu. Docelowo `python -m pasco2.cli.main` w pelni je
zastepuje.
