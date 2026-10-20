# Native GUI for avrdude (Linux)

[Wersja polska → README.md](README.md)

A lightweight native GUI (PyQt6) for **avrdude** to program AVR microcontrollers, extended with
**ESP8266** support through **esptool** and firmware upload **over WiFi (OTA)**.

> **Status: `v1.0-RC`.** The AVR part is the core of the program. The **ESP8266** and **ESP OTA**
> tabs are **experimental** and still need confirmation on real hardware.

## Table of contents
- [Features](#features)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Usage](#usage)
- [File layout](#file-layout)
- [Interface language](#interface-language)
- [Permissions (udev, dialout)](#permissions-udev-dialout)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## Features

**AVR (avrdude)**
- Write and read (backup) **FLASH** and **EEPROM** (Intel HEX).
- Read and write **fuses and lock bits** with an interactive calculator
  (clock, watchdog, BOD, verify after write).
- Chip Erase and a **CANCEL** button that aborts the current operation.
- **Programmer autodetect** over USB (USBasp, CH341A, serialupdi, Arduino/CH340), including the port.
- **MCU detection** from the device signature.
- **Pinout viewer as an image** from the `pinouts/` directory (your own photos or diagrams).
- Programmer and processor lists are read from the installed avrdude.
- Log console with a **Clear logs** button.

**ESP8266 (esptool)** *(experimental)*
- Chip detection (`chip_id`, `flash_id`) and flash erase.
- Write a `.bin` file to a chosen address and read a flash backup (512 KB – 4 MB).
- Baud rate selection and a serial port refresh button.
- A separate esptool log console.

**ESP OTA (WiFi)** *(experimental)*
- Upload **firmware** or a **file system** (SPIFFS/LittleFS) using the **ArduinoOTA** protocol,
  implemented natively in Python (no `espota.py` needed).
- OTA password support, progress in the console, cancellation.
- **Network device discovery** via mDNS.

## Requirements

| Component | Required | Notes |
|---|---|---|
| Python 3.9+ | yes | |
| PyQt6 | yes | graphical interface |
| avrdude | yes | AVR programming |
| usbutils (`lsusb`) | recommended | programmer autodetect |
| esptool | optional | ESP8266 tab only |

Debian / Ubuntu:

```bash
sudo apt install python3 python3-pyqt6 avrdude usbutils
sudo apt install esptool            # optional, for ESP8266
```

Other distributions: install the equivalent packages or use a virtual environment
(`python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt`).

## Quick start

```bash
git clone <repository-url>
cd <directory>
LANG=en_US.UTF-8 python3 avrgui.py
```

No installation is needed. Run the program **from its own directory** – the configuration file
and the `lang/` directory are stored relative to the current working directory.
The interface is Polish by default; the English translation (`lang/lang.en`) is loaded when
`LANG` is not Polish.

## Usage

**Configuration bar (top of the window)**
1. Click **Autodetect Programmer** – the program identifies the hardware and fills in the programmer and port.
2. Click **Detect MCU** to read the device signature, or choose the processor manually.
3. Use **Additional Flags** for custom avrdude options (e.g. `-B 8`, `-F`).

**Memory (Flash/EEPROM)** – choose a `.hex` file and click **Write**, or use **Read (Backup)**
to save the chip contents to a file.

**Pinout Viewer** – shows the image from `pinouts/` for the selected processor.
Add your own picture by copying a file named after the chip, e.g. `pinouts/atmega328p.png`.

**Fuses/Locks** – **Read** loads the values from the chip, **Write** sends them to the chip.
Fields showing "N/A" mean the chip has no such fuse; they are skipped when writing.

> ⚠️ **Warning:** wrong fuse settings (e.g. clock source or the RESET pin) can lock the chip.
> Make sure you understand the consequences before clicking **Write**.

**ESP8266 (esptool)** – select the port in **Port (-P)**, put the chip into programming mode
(GPIO0 to GND at power-up, CH_PD/EN to 3.3 V) and use **Detect Chip**, **Erase Flash**, **Write**
or **Read (Backup)**. Power ESP modules from **3.3 V**.

**ESP OTA (WiFi)** – enter the IP address (or a `.local` name) or click **Search**, choose a `.bin`
file and click **Upload over WiFi (OTA)**.
- The ESP must already run a program with **ArduinoOTA** support (flash it over a cable the first time).
- The `.bin` file is a compiled sketch (Arduino IDE: *Sketch → Export Compiled Binary*).
- The computer and the ESP must be on the same network and the firewall must allow the incoming
  connection from the ESP (the ESP connects back to the computer on a random TCP port).

## File layout

```
avrgui.py          main program
requirements.txt   Python dependencies
CHANGELOG.md       change log
LICENSE            GNU GPL v3
lang/lang.en       ready-made English translation
pinouts/           chip pinout images (created automatically if missing)
udev/99-avr.rules  udev rules for USB programmers
```

Files created at run time:

| File | Location | Description |
|---|---|---|
| `pinouts/*.png` | next to `avrgui.py` | default ATmega328P and ATtiny85 diagrams (only if missing) |
| `gui_config.txt` | working directory | remembered FLASH file and extra flags |
| `lang/lang.template` | working directory | translation template (regenerated on each start) |

## Interface language

The default language is Polish. The English translation in `lang/lang.en` is loaded when the
`LANG` variable is not Polish:

```bash
LANG=en_US.UTF-8 python3 avrgui.py
```

For another language, copy `lang/lang.template` (created on first start) to `lang/lang.en`,
translate the values and keep the keys unchanged. Missing keys fall back to Polish text.

## Permissions (udev, dialout)

**Serial ports** (`/dev/ttyUSB*`, `/dev/ttyACM*`) – add your user to the `dialout` group
and log in again:

```bash
sudo usermod -aG dialout "$USER"
```

**USB programmers** (USBasp, CH341A) – install the bundled udev rules and replug the programmer:

```bash
sudo cp udev/99-avr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Troubleshooting

| Symptom | What to check |
|---|---|
| Port field shows "Brak" (none) | Cable; on the ESP tab the **🔄 Ports** button; user in the `dialout` group. |
| avrdude uses `/dev/ttyS0` | No port selected – click **Autodetect Programmer** or pick the port manually. |
| "Detect MCU" shows the wrong chip | Autodetect identifies the programmer by USB ID, not the chip. Choose the processor manually. A CH340 may also be an ESP adapter. |
| `esptool not found` | `sudo apt install esptool` or `pip install esptool`. |
| OTA: "No response from the ESP" | Address/WiFi, ArduinoOTA in the sketch, same network. |
| OTA: "did not connect back" | The computer's firewall blocks the incoming connection. |
| "Search" finds nothing | mDNS may be blocked by the router or firewall – enter the IP address manually. |
| Warning about the configuration file version | An avrdude message (`avrdude.conf` does not match the program version), usually harmless. |

## Limitations

- The fuse calculator computes values **for ATmega328P only**. For other chips use the "Direct Values" fields.
- MCU autodetection knows a limited set of signatures (incl. ATmega328/328P/168/168P/88/8/2560/32U4,
  ATtiny85/13/2313/1614).
- Writing fuses does not ask for confirmation.
- ESP8266 and OTA are experimental; OTA supports only devices running ArduinoOTA.
- The program targets Linux.

## Contributing

Bug reports and suggestions are welcome. Please include the avrdude version (`avrdude -?`),
your distribution, the programmer used and a snippet of the program's console log.

## License

This project is released under the **GNU General Public License v3.0 (GPLv3)** – full text in
[LICENSE](LICENSE). The authors are everyone who joins the project or modifies and redistributes it.
