# Changelog

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/).

## [Unreleased] – 2026-10-18

### Dodano
- **Podgląd pinoutu jako obraz.** Program zakłada katalog `pinouts/` i wyświetla w nim obrazek
  dla wybranego procesora (PNG, JPG, JPEG, WEBP, BMP, SVG). Rozpoznaje warianty nazw
  (`atmega328p` ↔ `m328p`, `attiny85` ↔ `t85`) i skanuje katalog przy każdej zmianie procesora,
  więc nowe pliki działają bez restartu. Dla ATmega328P i ATtiny85 program sam rysuje
  domyślne schematy, jeśli plików jeszcze nie ma. Brakujący obrazek zastępuje komunikat
  z nazwą pliku i katalogiem.
- **Zakładka ESP8266 (esptool):** wykrycie układu (`chip_id` + `flash_id`), kasowanie flasha,
  zapis pliku `.bin` pod wskazany adres, odczyt kopii flasha (512 KB – 4 MB), wybór prędkości
  transmisji oraz przycisk odświeżania listy portów.
- **Zakładka ESP OTA (WiFi):** wgrywanie firmware lub systemu plików (SPIFFS/LittleFS) przez
  sieć, natywnie w Pythonie, protokołem ArduinoOTA (zaproszenie UDP, opcjonalne uwierzytelnienie
  hasłem, transfer TCP z postępem w konsoli i możliwością anulowania).
- **Wyszukiwanie urządzeń OTA w sieci** przez mDNS (`_arduino._tcp`), bez dodatkowych zależności.
- **Osobna konsola dla esptool/OTA** na zakładkach ESP. Elementy dotyczące wyłącznie avrdude
  (Autodetect, Detect MCU, Chip Erase, programator, procesor, flagi) są tam wyłączone.
- **Przycisk „Wyczyść logi”** nad konsolą avrdude.
- Wykrywanie portów szeregowych (`/dev/ttyUSB*`, `/dev/ttyACM*`) przez `glob`.
  Autodetect wpisuje port dla programatorów szeregowych (arduino, serialupdi, wiring).
- Obsługa wielu poleceń wykonywanych kolejno w jednym wątku roboczym.
- **Dokumentacja i pliki projektu:** `README.md` (PL) i `README.en.md` (EN), `CHANGELOG.md`,
  pełny tekst licencji GPLv3 (`LICENSE`), `requirements.txt`, `.gitignore`, reguły udev
  (`udev/99-avr.rules`), gotowe tłumaczenie angielskie (`lang/lang.en`) i opis katalogu `pinouts/`.

### Zmieniono
- **Wygląd GUI** według przygotowanych makiet: tytuły nad ramkami, ramki 2 px, kolorowe przyciski
  akcji (zielony, niebieski, pomarańczowy, czerwony), szare przyciski nieaktywne.
- **Zakładka Fuses:** układ według makiety: wąska lewa ramka z polami na całą szerokość, kalkulator
  z listami o stałej szerokości, przyciski „Odczytaj” i „Zapisz” pod ramkami, przy ich prawej
  krawędzi.
- **Zakładka Pamięć:** ramki FLASH i EEPROM ułożone obok siebie, o połowę niższe. Długa nazwa
  pliku nie rozpycha okna, a pełna ścieżka jest w podpowiedzi.
- **Rozmiary:** wysokość pola zakładek zależy od otwartej zakładki, a odstępy w oknie są
  zminimalizowane, dzięki czemu czarne pole logów zajmuje maksimum miejsca.
- Na zakładce **Pinout** nie ma konsoli, a pole z obrazkiem zajmuje całą dostępną powierzchnię.
- „Detect MCU” nie czyści już konsoli. Komunikaty autodetectu pozostają widoczne,
  a wykrywanie używa ostatniej sygnatury z logu.
- Worker łączy stdout i stderr avrdude, żeby żaden potok się nie zapychał.
- Kalkulator fuse'ów zmienia tylko te bity, których dotyczy dana opcja, a po odczycie
  z układu ustawia kontrolki zgodnie z wczytanymi wartościami.

### Naprawiono
- **Odczyt fuse'ów nie działał.** Wartości trafiały na stdout, którego program nie czytał.
  Teraz każdy bezpiecznik jest zapisywany do pliku tymczasowego jako surowy bajt i stamtąd
  wczytywany. Gdy nowszy avrdude odmawia odczytu układu bez któregoś bezpiecznika (np. ATmega8
  bez efuse), program ponawia odczyt pojedynczo. Brakujące bezpieczniki pokazuje jako „N/A”
  i pomija przy zapisie.
- **Błędne wartości BOD w kalkulatorze.** Teraz: wyłączony = `0xFF`, 2,7 V = `0xFD`,
  4,3 V = `0xFC`, 1,8 V = `0xFE`. Domyślne pola: `0xE2` / `0xD9` / `0xFF` (wg noty ATmega328P).
- **Walidacja zapisu fuse'ów:** niepoprawna wartość hex jest zgłaszana, zamiast trafić do avrdude.
- **„Detect MCU” nigdy nie rozpoznawał układu.** Wyrażenie regularne wyciągało z `0x1e950f`
  tylko „0”. Poprawiono także sygnaturę ATtiny1614 (`0x1E9422`) i dodano kilka popularnych układów.
- **Autodetect nie wpisywał portu** dla programatorów szeregowych (CH340), przez co avrdude
  używał domyślnego `/dev/ttyS0`.

### Usunięto
- Tekstowe pinouty (`pinouts.txt`) na rzecz obrazów z katalogu `pinouts/`.

### Znane ograniczenia
- Zakładki ESP8266 i ESP OTA nie zostały jeszcze sprawdzone na prawdziwym module ESP-01S.
- Kalkulator fuse'ów obsługuje wyłącznie ATmega328P.
- Zapis fuse'ów nie wymaga potwierdzenia.
- Plik konfiguracji i katalog `lang/` powstają względem katalogu roboczego (uruchamiaj program
  z jego katalogu).
