# Notatki protokolu PASCO2 - ustalenia empiryczne

Ten dokument zbiera fakty **zweryfikowane na prawdziwym sprzecie**
(Infineon PASCO2 na plytce Sensor2Go), nie tylko wywnioskowane z kodu
legacy skryptow. Data weryfikacji: 2026-09-21.

## Port

Sensor pojawia sie w Windowsie jako **"USB Serial Device"**. W konkretnym
przypadku bylo to **COM6**, NIE COM3 - COM3 na tym samym komputerze to
"Intel(R) Active Management Technology - SOL" (wirtualny port Intel
AMT/vPro, niezwiazany z sensorem). Zawsze sprawdzaj w Menedzerze urzadzen
(Porty COM i LPT), ktory port to faktycznie "USB Serial Device" zanim
zalozysz, ze to COM3.

## Reset przy otwarciu portu

Otwarcie portu resetuje mikrokontroler sensora (typowe dla mostkow
USB-UART sterujacych DTR). Bez odczekania sensor nie odpowiada na
zadne komendy (wszystkie odpowiedzi puste). Zaimplementowane jako
`SerialTransport(startup_delay_s=1.5)` (domyslnie 1.5s) w
`pasco2/transport/serial_transport.py`.

## Sekwencja inicjalizacji - potwierdzona

Komendy `W,04,00` (idle) -> `W,02,00` + `W,03,0A` (measurement rate) ->
`W,04,02` (tryb ciagly) - kazda dostaje odpowiedz `\x06\n` (ASCII ACK).
Sekwencja jest poprawna.

## Rejestr statusu (R,07) - bit DATA_RDY

**Kluczowe odkrycie**: `MeasurementService` w wersji sprzed tej
weryfikacji odczytywal status, ale **go ignorowal** i zawsze leciat po
MSB/LSB bez sprawdzenia gotowosci danych - efekt byl przypadkowy (czasem
stare dane, czasem "0 ppm" gdy zadany pomiar jeszcze sie nie zakonczyl).

Zmierzone empirycznie (`scripts/watch_status.py`, rate=10s):

| status (hex) | znaczenie |
|---|---|
| `0x00` | miedzy pomiarami - brak nowych danych |
| `0x20` | pojawia sie na jedna probke tuz przed `0x10` (prawdopodobnie "pomiar w toku") |
| `0x10` | **DATA_RDY** - MSB/LSB zawieraja swiezy pomiar dokladnie w tej probce |

`STATUS_DATA_READY_BIT = 0x10` w `pasco2/protocol/commands.py`,
`is_data_ready()` w `pasco2/protocol/frames.py`.

**Poprawka**: `MeasurementService.read_measurement()` teraz poluje status
co `status_poll_interval_s` (domyslnie 1s) az bit `0x10` sie zapali (z
limitem `max_wait_for_data_s`), dopiero wtedy czyta MSB/LSB. `run_forever()`
nie ma juz osobnego `time.sleep(interval)` - tempo wyznacza sam sensor
przez DATA_RDY (wczesniejsza wersja dodawalaby dodatkowe opoznienie na
wierzch, efektywnie spowalniajac pomiary).

## Okres pomiaru (measurement rate)

Wartosc `10` (sekund) zapisana do rejestru `0x03` (MSB), `0x00` do
rejestru `0x02` (LSB) dala **empirycznie okres pomiaru ~10 sekund**
(zmierzone: 10.4s, 9.2s, 10.0s, 10.2s, 10.9s odstepy - srednio ~10s,
naturalny jitter).

`build_measurement_rate_commands(rate_seconds)` w `commands.py` pozwala
sparametryzowac te wartosc, ale **semantyka dla wartosci innych niz 10
nie zostala zweryfikowana** - dokladny uklad bitow rejestru rate (czy to
faktycznie liniowe sekundy, czy inna jednostka/skala) nie jest
potwierdzony z dokumentacji, tylko wywnioskowany z jednego dzialajacego
pomiaru. Zmieniajac te wartosc w konfiguracji, **zawsze zweryfikuj
`scripts/watch_status.py`** zanim zalozysz, ze nowy okres jest taki, jak
oczekujesz.

## Realne odczyty CO2

W trakcie testu (pomieszczenie, osoba przy sensorze): 557 -> 560 -> 564
-> 566 -> 568 -> 569 ppm w ciagu ~60s. Wartosci w rozsadnym zakresie dla
pomieszczenia (tlo atmosferyczne ~420 ppm, wzrost typowy przy obecnosci
osoby w poblizu czujnika) - protokol i parsowanie MSB/LSB uznajemy za
poprawne.

## Skrypty diagnostyczne

- `scripts/diagnose_sensor.py PORT BAUD` - jednorazowy dump surowych
  bajtow calej sekwencji inicjalizacji + 5 probek odczytu.
- `scripts/watch_status.py PORT BAUD CZAS_S` - obserwacja rejestru
  statusu w czasie, do weryfikacji timingu i bitu DATA_RDY.

Uzywaj ich przy kazdej zmianie w warstwie `transport/`/`protocol/`, zanim
zaufasz zmianie w pelnej aplikacji dzialajacej bez nadzoru.
