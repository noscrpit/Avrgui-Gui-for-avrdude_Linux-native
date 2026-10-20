# Native GUI for avrdude (Linux)

[English version → README.en.md](README.en.md)

Natywna, lekka nakładka graficzna (PyQt6) na **avrdude** do programowania mikrokontrolerów AVR,
rozszerzona o obsługę **ESP8266** przez **esptool** oraz wgrywanie firmware **przez WiFi (OTA)**.

> **Status: `v1.0-RC`.** Część AVR jest podstawową funkcjonalnością programu. Zakładki **ESP8266**
> i **ESP OTA** są **eksperymentalne** i wymagają potwierdzenia na prawdziwym sprzęcie.

## Spis treści
- [Funkcje](#funkcje)
- [Wymagania](#wymagania)
- [Szybki start](#szybki-start)
- [Obsługa](#obsługa)
- [Struktura plików](#struktura-plików)
- [Język interfejsu](#język-interfejsu)
- [Uprawnienia (udev, dialout)](#uprawnienia-udev-dialout)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Ograniczenia](#ograniczenia)
- [Współtworzenie](#współtworzenie)
- [Licencja](#licencja)

## Funkcje

**AVR (avrdude)**
- Zapis i odczyt (kopia) pamięci **FLASH** i **EEPROM** (Intel HEX).
- Odczyt i zapis **bezpieczników i lock bitów** z interaktywnym kalkulatorem
  (zegar, watchdog, BOD, weryfikacja po zapisie).
- Kasowanie układu (Chip Erase) oraz przycisk **ZATRZYMAJ** przerywający bieżącą operację.
- **Autodetect programatora** po USB (USBasp, CH341A, serialupdi, Arduino/CH340) wraz z wpisaniem portu.
- **Wykrywanie procesora** na podstawie sygnatury.
- **Podgląd pinoutu jako obraz** z katalogu `pinouts/` (własne zdjęcia lub schematy).
- Listy programatorów i procesorów pobierane z zainstalowanego avrdude.
- Konsola z logami operacji i przycisk **Wyczyść logi**.

**ESP8266 (esptool)** *(eksperymentalne)*
- Wykrycie układu (`chip_id`, `flash_id`) i kasowanie flasha.
- Zapis pliku `.bin` pod wybrany adres oraz odczyt kopii flasha (512 KB – 4 MB).
- Wybór prędkości transmisji i odświeżanie listy portów.
- Osobna konsola logów esptool.

**ESP OTA (WiFi)** *(eksperymentalne)*
- Wgrywanie **firmware** lub **systemu plików** (SPIFFS/LittleFS) protokołem **ArduinoOTA**,
  zaimplementowanym natywnie w Pythonie (bez `espota.py`).
- Obsługa hasła OTA, postęp w konsoli, możliwość anulowania.
- **Wyszukiwanie urządzeń w sieci** przez mDNS.

## Wymagania

| Składnik | Wymagany | Uwagi |
|---|---|---|
| Python 3.9+ | tak | |
| PyQt6 | tak | interfejs graficzny |
| avrdude | tak | programowanie AVR |
| usbutils (`lsusb`) | zalecany | autodetect programatora |
| esptool | opcjonalnie | tylko zakładka ESP8266 |

Debian / Ubuntu:

```bash
sudo apt install python3 python3-pyqt6 avrdude usbutils
sudo apt install esptool            # opcjonalnie, dla ESP8266
```

Inne dystrybucje: zainstaluj odpowiedniki pakietów albo użyj środowiska wirtualnego
(`python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt`).

## Szybki start

```bash
git clone <adres-repozytorium>
cd <katalog>
python3 avrgui.py
```

Program nie wymaga instalacji. Uruchamiaj go **z jego katalogu** – plik konfiguracji
i katalog `lang/` są zapisywane względem bieżącego katalogu roboczego.

## Obsługa

**Pasek konfiguracji (góra okna)**
1. Kliknij **Wykryj programator** – program rozpozna sprzęt i wpisze programator oraz port.
2. Kliknij **Wykryj proc**, aby odczytać sygnaturę układu, albo wybierz procesor ręcznie.
3. W polu **Dodatkowe flagi** możesz wpisać własne opcje avrdude (np. `-B 8`, `-F`).

**Pamięć (Flash/EEPROM)** – wybierz plik `.hex` i kliknij **Zapisz** albo użyj
**Odczytaj (Kopia)**, aby zapisać zawartość układu do pliku.

**Podgląd Pinów** – pokazuje obrazek z `pinouts/` dla wybranego procesora.
Własne zdjęcie dodasz, kopiując plik do katalogu pod nazwą układu, np. `pinouts/atmega328p.png`.

**Bezpieczniki (Fuses/Locks)** – **Odczytaj** pobiera wartości z układu, a **Zapisz** wysyła je do układu.
Pola „N/A” oznaczają bezpiecznik, którego układ nie ma; są pomijane przy zapisie.

> ⚠️ **Uwaga:** błędne ustawienie fuse'ów (np. zegara lub linii RESET) może zablokować układ.
> Zanim klikniesz **Zapisz**, upewnij się, że rozumiesz skutki.

**ESP8266 (esptool)** – wybierz port w polu **Port (-P)**, przełącz układ w tryb programowania
(GPIO0 do GND przy starcie, CH_PD/EN do 3,3 V) i użyj **Wykryj układ**, **Kasuj flash**, **Zapisz**
lub **Odczytaj (Kopia)**. Moduły ESP zasilaj z **3,3 V**.

**ESP OTA (WiFi)** – wpisz adres IP (lub nazwę `.local`) albo kliknij **Szukaj**, wybierz plik `.bin`
i kliknij **Wgraj przez WiFi (OTA)**.
- W ESP musi już działać program z obsługą **ArduinoOTA** (pierwszy raz wgraj go kablem).
- Plik `.bin` to skompilowany szkic (Arduino IDE: *Szkic → Eksportuj skompilowany plik binarny*).
- Komputer i ESP muszą być w tej samej sieci, a zapora musi przepuszczać połączenie przychodzące od ESP
  (ESP łączy się zwrotnie z komputerem na losowym porcie TCP).

## Struktura plików

```
avrgui.py          główny program
requirements.txt   zależności Pythona
CHANGELOG.md       lista zmian
LICENSE            GNU GPL v3
lang/lang.en       gotowe tłumaczenie angielskie
pinouts/           obrazy pinoutów układów (program tworzy katalog, jeśli go brak)
udev/99-avr.rules  reguły udev dla programatorów USB
```

Pliki tworzone w czasie pracy:

| Plik | Położenie | Opis |
|---|---|---|
| `pinouts/*.png` | obok `avrgui.py` | domyślne schematy ATmega328P i ATtiny85 (tylko gdy ich brak) |
| `gui_config.txt` | katalog roboczy | zapamiętany plik FLASH i dodatkowe flagi |
| `lang/lang.template` | katalog roboczy | szablon tłumaczeń (odtwarzany przy każdym starcie) |

## Język interfejsu

Domyślny język to polski. Gotowe tłumaczenie angielskie jest w `lang/lang.en` – program wczytuje je,
gdy zmienna `LANG` nie jest polska:

```bash
LANG=en_US.UTF-8 python3 avrgui.py
```

Własny język: skopiuj `lang/lang.template` (powstaje po pierwszym uruchomieniu) do `lang/lang.en`,
przetłumacz wartości i zostaw klucze bez zmian. Brakujące klucze są uzupełniane tekstami polskimi.

## Uprawnienia (udev, dialout)

**Porty szeregowe** (`/dev/ttyUSB*`, `/dev/ttyACM*`) – dodaj użytkownika do grupy `dialout`
i zaloguj się ponownie:

```bash
sudo usermod -aG dialout "$USER"
```

**Programatory USB** (USBasp, CH341A) – zainstaluj dołączone reguły udev
i podłącz programator ponownie:

```bash
sudo cp udev/99-avr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Rozwiązywanie problemów

| Objaw | Co sprawdzić |
|---|---|
| Pole Port pokazuje „Brak” | Kabel; na zakładce ESP przycisk **🔄 Porty**; użytkownik w grupie `dialout`. |
| avrdude używa `/dev/ttyS0` | Nie wybrano portu – kliknij **Wykryj programator** albo wybierz port ręcznie. |
| „Detect MCU” wskazuje zły układ | Autodetect rozpoznaje programator po ID USB, nie układ. Wybierz procesor ręcznie. CH340 może być też adapterem ESP. |
| `esptool not found` | `sudo apt install esptool` lub `pip install esptool`. |
| OTA: „No response from the ESP” | Adres/WiFi, ArduinoOTA w szkicu, ta sama sieć. |
| OTA: „did not connect back” | Zapora na komputerze blokuje połączenie przychodzące. |
| „Szukaj” niczego nie znajduje | mDNS bywa blokowany przez router lub zaporę – wpisz adres IP ręcznie. |
| Ostrzeżenie o wersji pliku konfiguracji | Komunikat avrdude (niezgodność `avrdude.conf` z wersją programu), zwykle nieszkodliwy. |

## Ograniczenia

- Kalkulator fuse'ów liczy wartości **tylko dla ATmega328P**. Dla innych układów używaj pól „Wartości bezpośrednie”.
- Autodetekcja procesora zna ograniczoną listę sygnatur (m.in. ATmega328/328P/168/168P/88/8/2560/32U4,
  ATtiny85/13/2313/1614).
- Zapis fuse'ów nie wymaga dodatkowego potwierdzenia.
- ESP8266 i OTA są eksperymentalne; OTA obsługuje wyłącznie urządzenia z ArduinoOTA.
- Program jest przeznaczony dla Linuksa.

## Współtworzenie

Zgłoszenia błędów i propozycje zmian są mile widziane. Przy zgłoszeniu podaj wersję avrdude
(`avrdude -?`), dystrybucję, używany programator oraz fragment logu z konsoli programu.

## Licencja

Projekt jest udostępniany na licencji **GNU General Public License v3.0 (GPLv3)** – pełny tekst w pliku
[LICENSE](LICENSE). Autorami są wszyscy, którzy dołączą do projektu lub zmodyfikują go i udostępnią dalej.
