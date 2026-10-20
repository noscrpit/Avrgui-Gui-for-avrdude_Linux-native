#!/usr/bin/env python3
# =========================================================================
#  Natywny GUI for avrdude Linux v1.0-RC
#  Autor: Wszyscy, którzy przyłączą się lub zmodyfikują i udostępnią ten projekt.
#  Licencja: GNU General Public License v3.0 (GPLv3)
# =========================================================================

import sys
import glob
import socket
import struct
import hashlib
import time
import subprocess
import re
import os
import shutil
import tempfile
import configparser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QComboBox, QPushButton, QFileDialog,
                             QTextEdit, QTabWidget, QLineEdit, QGroupBox, QFormLayout, QCheckBox,
                             QSizePolicy)
from PyQt6.QtCore import QDir, QThread, pyqtSignal, Qt, QTimer, QSize, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "gui_config.txt"
LANG_DIR = "lang"
PINOUT_DIR = os.path.join(SCRIPT_DIR, "pinouts")
PINOUT_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".svg")

TXT = {
    "title": "Natywny GUI dla avrdude Linux v1.0-RC",
    "flash_box": "Pamięć FLASH",
    "eeprom_box": "Pamięć EEPROM",
    "browse": "Przeglądaj...",
    "write": "Zapisz",
    "read": "Odczytaj (Kopia)",
    "no_file_hex": "Nie wybrano pliku .hex",
    "no_file_eep": "Nie wybrano pliku .hex/.eep",
    "err_no_file": "Błąd: Najpierw wybierz plik do zapisu!",
    "cancel": "🛑 ZATRZYMAJ!",
    "eg.. -B 8 or -F (write if You want)": "np. -B 8 lub -F (wpisać jeśli tylko jeśli naprawdę potrzeba)",
    "detect_prog": "🔍 Wykryj programator (Autodetect)",
    "detect_mcu": "🧬 Wykryj proc (Detect MCU)",
    "chip_erase": "🧹 Czyszczenie (Chip Erase)",
    "mem_tab": "Pamięć (Flash/EEPROM)",
    "pinout_tab": "Podgląd Pinów (Pinout)",
    "fuses_tab": "Bezpieczniki (Fuses/Locks)",
    "console_title": "Logi i wynik operacji AVRDUDE:",
    "hw_config": "Konfiguracja Sprzętowa",
    "control_auto": "Kontrola i automatyzacja:",
    "prog_label": "Programator (-c):",
    "mcu_label": "Procesor (-p):",
    "port_label": "Port (-P):",
    "flags_label": "Dodatkowe flagi:",
    "hex_direct": "Wartości bezpośrednie (Hex)",
    "interactive_calc": "Interaktywny Kalkulator Bezpieczników",
    "verify_fuses": "Weryfikuj pamięć i bezpieczniki po zapisie (Verify)",
    "clock_system": "System taktowania (Zegar):",
    "watchdog_label": "Włączony na stałe Watchdog Timer (WDT)",
    "bod_label": "Ochrona przed spadkiem napięcia (BOD):",
    "clk_internal_8": "Wewnętrzny oscylator 8 MHz (Domyślny)",
    "clk_external_16": "Zewnętrzny kwarc 8-16 MHz (Szybki)",
    "clk_internal_1": "Wewnętrzny oscylator 1 MHz",
    "bod_disabled": "Wyłączone (BOD disabled)",
    "bod_27": "Włączone (2.7V)",
    "bod_43": "Włączone (4.3V)",
    "bod_18": "Włączone (1.8V)",
    "pinout_missing": "Brak obrazka pinoutu dla układu: {mcu}\n\nWrzuć plik graficzny (PNG / JPG / SVG) o nazwie\n{mcu}.png\ndo katalogu:\n{dir}",
    "esp_tab": "ESP8266 (esptool)",
    "esp_fw_box": "Firmware ESP (.bin)",
    "esp_backup_box": "Kopia pamięci flash",
    "esp_tools_box": "Narzędzia esptool",
    "esp_no_file": "Nie wybrano pliku .bin",
    "esp_addr": "Adres:",
    "esp_size": "Rozmiar flash:",
    "esp_detect": "🧬 Wykryj układ (chip-id + flash-id)",
    "esp_erase": "🧹 Kasuj flash (erase_flash)",
    "esp_baud": "Prędkość (baud):",
    "esp_hint": "ESP-01S: zasilanie 3,3 V (NIE 5 V!). Tryb programowania: GPIO0 połączone z GND w momencie włączenia zasilania, CH_PD (EN) do 3,3 V. Port wybierz w polu Port (-P) na górze, np. /dev/ttyUSB0.",
    "ota_tab": "ESP OTA (WiFi)",
    "ota_box": "Wgrywanie przez WiFi (OTA)",
    "ota_host": "Adres (IP / nazwa):",
    "ota_port": "Port:",
    "ota_pass": "Hasło OTA:",
    "ota_type": "Typ:",
    "ota_type_fw": "Firmware (flash)",
    "ota_type_fs": "System plików (SPIFFS/LittleFS)",
    "ota_upload": "📡 Wgraj przez WiFi (OTA)",
    "ota_no_file": "Nie wybrano pliku .bin",
    "ota_hint": "OTA działa tylko wtedy, gdy w ESP jest już wgrany program z obsługą ArduinoOTA - pierwszy raz wgraj go kablem (zakładka ESP8266). Plik .bin to skompilowany szkic (Arduino IDE: Szkic -> Eksportuj skompilowany plik binarny). Komputer i ESP muszą być w tej samej sieci, a zapora na komputerze musi przepuszczać połączenie przychodzące od ESP.",
    "esp_console_title": "Logi esptool / OTA:",
    "ota_scan": "🔍 Szukaj",
    "esp_ports": "🔄 Porty",
    "clear_logs": "🧹 Wyczyść logi",
    "fuse_read": "Odczytaj"
}

def generate_lang_template():
    os.makedirs(LANG_DIR, exist_ok=True)
    template_path = os.path.join(LANG_DIR, "lang.template")
    try:
        config = configparser.ConfigParser()
        config['TRANSLATION'] = TXT
        with open(template_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except Exception: pass

def load_external_language():
    global TXT
    generate_lang_template()
    sys_lang = os.environ.get('LANG', 'pl').split('_')[0].lower()
    if sys_lang != 'pl':
        lang_file = os.path.join(LANG_DIR, "lang.en")
        if os.path.exists(lang_file):
            try:
                config = configparser.ConfigParser()
                config.read(lang_file, encoding='utf-8')
                if 'TRANSLATION' in config:
                    for key in TXT.keys():
                        if key in config['TRANSLATION']:
                            TXT[key] = config['TRANSLATION'][key]
            except Exception: pass

load_external_language()

# =========================================================================
#  PINOUTY - katalog "pinouts" ze zdjęciami / schematami układów
# =========================================================================

def ensure_pinout_dir():
    """Zakłada katalog pinouts, jeśli go nie ma."""
    try:
        os.makedirs(PINOUT_DIR, exist_ok=True)
    except Exception: pass

def pinout_candidates(mcu):
    """Warianty nazwy układu (atmega328p <-> m328p, attiny85 <-> t85)."""
    mcu = mcu.lower().strip()
    names = [mcu]
    if mcu.startswith('atmega'): names.append('m' + mcu[6:])
    elif mcu.startswith('attiny'): names.append('t' + mcu[6:])
    elif re.match(r'^m\d', mcu): names.append('atmega' + mcu[1:])
    elif re.match(r'^t\d', mcu): names.append('attiny' + mcu[1:])
    return names

def find_pinout_image(mcu):
    """Zwraca ścieżkę do obrazka dla układu albo None. Katalog jest skanowany przy każdym wywołaniu,
    więc nowo dodane pliki działają bez restartu programu."""
    if not mcu or not os.path.isdir(PINOUT_DIR): return None
    files = {}
    try:
        for f in os.listdir(PINOUT_DIR):
            stem, ext = os.path.splitext(f)
            if ext.lower() in PINOUT_EXTS:
                files.setdefault(stem.lower().strip(), os.path.join(PINOUT_DIR, f))
    except Exception: return None
    for cand in pinout_candidates(mcu):
        if cand in files: return files[cand]
    return None

# Dane do wygenerowania domyślnych obrazków (tylko gdy ich jeszcze nie ma w katalogu)
DEFAULT_PINOUTS = {
    "atmega328p": (
        "ATmega328P (DIP-28)",
        ["PC6 / RESET", "PD0 / RXD", "PD1 / TXD", "PD2 / INT0", "PD3 / INT1 / OC2B", "PD4 / T0 / XCK", "VCC",
         "GND", "PB6 / XTAL1", "PB7 / XTAL2", "PD5 / T1 / OC0B", "PD6 / AIN0 / OC0A", "PD7 / AIN1", "PB0 / ICP1"],
        ["PC5 / ADC5 / SCL", "PC4 / ADC4 / SDA", "PC3 / ADC3", "PC2 / ADC2", "PC1 / ADC1", "PC0 / ADC0", "GND",
         "AREF", "AVCC", "PB5 / SCK", "PB4 / MISO", "PB3 / MOSI / OC2A", "PB2 / SS / OC1B", "PB1 / OC1A"],
        "ISP: VCC(7), GND(8/22), MOSI(17), MISO(18), SCK(19), RESET(1)"),
    "attiny85": (
        "ATtiny85 (DIP-8)",
        ["PB5 / RESET", "PB3 / XTAL1 / ADC3", "PB4 / XTAL2 / ADC2", "GND"],
        ["VCC", "PB2 / SCK / SCL / ADC1", "PB1 / MISO / OC1A", "PB0 / MOSI / SDA / AIN0"],
        "ISP: VCC(8), GND(4), MOSI(5), MISO(6), SCK(7), RESET(1)"),
}

def _pin_color(label):
    up = label.upper()
    if 'VCC' in up: return QColor("#ff8a80")
    if 'GND' in up: return QColor("#80deea")
    if any(k in up for k in ('RESET', 'MOSI', 'MISO', 'SCK')): return QColor("#ffd54f")
    return QColor("#ffffff")

def draw_dip_pinout(path, title, left, right, note):
    """Rysuje prosty schemat układu DIP i zapisuje go jako PNG."""
    rows = len(left)
    row_h, top, width, body_w = 44, 90, 900, 240
    height = top + rows * row_h + 90
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#263238"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    f = QFont("DejaVu Sans"); f.setPixelSize(30); f.setBold(True); p.setFont(f)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 15, width, 55), Qt.AlignmentFlag.AlignCenter, title)

    bx, by, bh = (width - body_w) / 2, top, rows * row_h
    p.setPen(QPen(QColor("#b0bec5"), 3))
    p.setBrush(QColor("#37474f"))
    p.drawRoundedRect(QRectF(bx, by, body_w, bh), 8, 8)
    p.drawArc(QRectF(width / 2 - 18, by - 18, 36, 36), 180 * 16, 180 * 16)  # wycięcie oznaczające pin 1

    f2 = QFont("DejaVu Sans"); f2.setPixelSize(19); p.setFont(f2)
    for i in range(rows):
        y = by + i * row_h + row_h / 2
        pin_l, pin_r = i + 1, 2 * rows - i
        p.setPen(QPen(QColor("#b0bec5"), 4))
        p.drawLine(int(bx - 38), int(y), int(bx), int(y))
        p.drawLine(int(bx + body_w), int(y), int(bx + body_w + 38), int(y))
        p.setPen(QColor("#cfd8dc"))
        p.drawText(QRectF(bx + 10, y - row_h / 2, 60, row_h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(pin_l))
        p.drawText(QRectF(bx + body_w - 70, y - row_h / 2, 60, row_h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(pin_r))
        p.setPen(_pin_color(left[i]))
        p.drawText(QRectF(bx - 48 - 320, y - row_h / 2, 320, row_h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, left[i])
        p.setPen(_pin_color(right[i]))
        p.drawText(QRectF(bx + body_w + 48, y - row_h / 2, 320, row_h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, right[i])

    p.setPen(QColor("#ffd54f"))
    p.drawText(QRectF(0, by + bh + 25, width, 40), Qt.AlignmentFlag.AlignCenter, note)
    p.end()
    img.save(path)

def generate_default_pinouts():
    """Tworzy obrazki dla układów, dla których w katalogu pinouts jeszcze nic nie ma."""
    for mcu, (title, left, right, note) in DEFAULT_PINOUTS.items():
        try:
            if find_pinout_image(mcu) is None:
                draw_dip_pinout(os.path.join(PINOUT_DIR, f"{mcu}.png"), title, left, right, note)
        except Exception: pass

class PinoutView(QLabel):
    """Ciemne pole, które wyświetla obrazek skalowany do maksymalnej dostępnej powierzchni."""
    def __init__(self):
        super().__init__()
        self._pix = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setStyleSheet("background-color: #263238; color: #ffffff; font-family: monospace; font-size: 14px;")

    def sizeHint(self): return QSize(100, 100)
    def minimumSizeHint(self): return QSize(1, 1)

    def show_image(self, path):
        pix = QPixmap(path)
        if pix.isNull():
            self.show_message(f"Nie można wczytać pliku:\n{path}")
            return
        self._pix = pix
        self._refresh()

    def show_message(self, text):
        self._pix = None
        self.setPixmap(QPixmap())
        self.setText(text)

    def _refresh(self):
        if self._pix is not None and self.width() > 1 and self.height() > 1:
            self.setPixmap(self._pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

# =========================================================================
#  WĄTEK URUCHAMIAJĄCY AVRDUDE
# =========================================================================

class FitTabWidget(QTabWidget):
    """QTabWidget, którego wysokość zależy tylko od otwartej zakładki (zwykły bierze wysokość najwyższej zakładki)."""
    def _fit(self, size, getter):
        page = self.currentWidget()
        if page is None or self.count() == 0: return size
        tallest = max(getter(self.widget(i)) for i in range(self.count()))
        return QSize(size.width(), max(0, size.height() - tallest + getter(page)))

    def sizeHint(self):
        return self._fit(super().sizeHint(), lambda w: w.sizeHint().height())

    def minimumSizeHint(self):
        return self._fit(super().minimumSizeHint(), lambda w: w.minimumSizeHint().height())

class AvrdudeWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmds):
        super().__init__()
        self.cmds = cmds          # lista poleceń; wykonywane po kolei
        self.process = None
        self._cancelled = False

    def run(self):
        rc_total = 0
        try:
            for cmd in self.cmds:
                if self._cancelled: break
                if len(self.cmds) > 1:
                    self.output_signal.emit("$ " + " ".join(cmd))
                # stderr i stdout razem - dzięki temu żaden potok się nie zapycha
                self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in iter(self.process.stdout.readline, ''):
                    self.output_signal.emit(line)
                self.process.wait()
                if self.process.returncode != 0: rc_total = self.process.returncode
            if self._cancelled and rc_total == 0: rc_total = -1
            self.finished_signal.emit(rc_total)
        except Exception as e:
            self.output_signal.emit(f"\nBłąd wątku: {str(e)}\n")
            self.finished_signal.emit(-1)

    def cancel(self):
        self._cancelled = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.output_signal.emit("\n🛑 PROCES PRZERWANY PRZEZ UŻYTKOWNIKA!\n")

# =========================================================================
#  STYLE
# =========================================================================

def action_button_style(color, hover, disabled="#b9b9b9"):
    return (f"QPushButton {{ background-color: {color}; color: white; font-weight: bold; "
            f"padding: 7px 10px; border: none; border-radius: 3px; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
            f"QPushButton:pressed {{ background-color: {hover}; padding-top: 8px; }}"
            f"QPushButton:disabled {{ background-color: {disabled}; color: #f4f4f4; }}")

# Tytuł nad ramką (jak na obrazach), ramka 2 px (wewnętrzne pola) lub 1 px (konfiguracja sprzętowa)
GROUP_STYLE = """
QGroupBox#hwBox   { border: 1px solid #c4c4c4; margin-top: 20px; padding-top: 4px; }
QGroupBox#frameBox { border: 2px solid #7a7a7a; margin-top: 20px; padding-top: 4px; }
QGroupBox#memBox   { border: 2px solid #7a7a7a; margin-top: 17px; padding-top: 0px; }
QGroupBox::title  { subcontrol-origin: margin; subcontrol-position: top left; left: 0px; padding: 0px 2px; }
"""

FUSE_NAMES = ['lfuse', 'hfuse', 'efuse', 'lock']

def parse_hex_byte(text, default=None):
    m = re.fullmatch(r'\s*(?:0x)?([0-9a-fA-F]{1,2})\s*', text or '')
    return int(m.group(1), 16) if m else default

OTA_FLASH, OTA_FS, OTA_AUTH = 0, 100, 200   # polecenia protokołu ArduinoOTA (jak w espota.py)

def ota_upload(host, port, password, path, command, log, cancelled, track_socket):
    """Wysyła plik do ESP8266 przez WiFi protokołem ArduinoOTA. Zwraca 0 przy sukcesie, 1 przy błędzie.
    Przebieg: zaproszenie UDP -> (opcjonalnie uwierzytelnienie) -> ESP łączy się TCP z komputerem -> wysyłka danych."""
    try:
        ip = socket.gethostbyname(host)
    except Exception as e:
        log(f"❌ Cannot resolve '{host}': {e}")
        return 1
    with open(path, 'rb') as f:
        data = f.read()
    size = len(data)
    if size == 0:
        log("❌ The file is empty.")
        return 1
    md5 = hashlib.md5(data).hexdigest()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    track_socket(srv)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('', 0))
    srv.listen(1)
    local_port = srv.getsockname()[1]

    remote = (ip, port)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    track_socket(udp)
    invitation = f"{command} {local_port} {size} {md5}\n".encode()
    reply = ""
    log(f"Sending invitation to {ip}:{port} ({size} bytes)...")
    for attempt in range(1, 6):
        if cancelled(): return 1
        udp.sendto(invitation, remote)
        udp.settimeout(3)
        try:
            reply = udp.recv(37).decode(errors='ignore').strip()
            break
        except socket.timeout:
            log(f"  no response (try {attempt}/5)")
    else:
        log("❌ No response from the ESP. Check the address / WiFi and that the firmware has ArduinoOTA enabled.")
        return 1

    if reply != "OK":
        if reply.startswith("AUTH"):
            if not password:
                log("❌ The device requires an OTA password.")
                return 1
            nonce = reply.split()[1]
            cnonce = hashlib.md5(f"{os.path.basename(path)}{size}{md5}{ip}".encode()).hexdigest()
            passmd5 = hashlib.md5(password.encode()).hexdigest()
            result = hashlib.md5(f"{passmd5}:{nonce}:{cnonce}".encode()).hexdigest()
            udp.sendto(f"{OTA_AUTH} {cnonce} {result}\n".encode(), remote)
            udp.settimeout(10)
            try:
                reply = udp.recv(32).decode(errors='ignore').strip()
            except socket.timeout:
                reply = ""
            if reply != "OK":
                log("❌ Authentication failed (wrong password?).")
                return 1
            log("Authenticated.")
        else:
            log(f"❌ Unexpected reply from the device: {reply!r}")
            return 1

    log("Waiting for the device to connect back...")
    srv.settimeout(1)
    deadline = time.time() + 15
    conn = None
    while conn is None:
        if cancelled(): return 1
        if time.time() > deadline:
            log("❌ The device did not connect back (firewall blocking incoming TCP? different network?).")
            return 1
        try:
            conn, _ = srv.accept()
        except socket.timeout:
            pass
    track_socket(conn)
    conn.settimeout(20)

    offset, last_pct, last_ok = 0, -1, False
    while offset < size:
        if cancelled(): return 1
        chunk = data[offset:offset + 1460]
        conn.sendall(chunk)
        offset += len(chunk)
        res = conn.recv(10).decode(errors='ignore')
        if not res and offset < size:
            log("❌ The device closed the connection during upload.")
            return 1
        last_ok = 'OK' in res
        pct = offset * 100 // size
        if pct // 10 > last_pct // 10:
            log(f"Uploading: {pct}%")
        last_pct = pct

    if not last_ok:
        log("Waiting for the result...")
        conn.settimeout(3)
        deadline = time.time() + 60
        while time.time() < deadline and not cancelled():
            try:
                res = conn.recv(32).decode(errors='ignore')
            except socket.timeout:
                continue
            if 'OK' in res:
                last_ok = True
                break
            if not res:
                break
    if last_ok:
        log("The device accepted the upload and is rebooting.")
        return 0
    log("❌ No confirmation from the device.")
    return 1

class OtaWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, host, port, password, path, command):
        super().__init__()
        self.args = (host, port, password, path, command)
        self._cancelled = False
        self._socks = []

    def run(self):
        rc = 1
        try:
            rc = ota_upload(*self.args, lambda m: self.output_signal.emit(m), lambda: self._cancelled, self._socks.append)
        except Exception as e:
            if not self._cancelled: self.output_signal.emit(f"\n❌ OTA error: {e}")
            rc = -1
        finally:
            for sk in self._socks:
                try: sk.close()
                except Exception: pass
        if self._cancelled and rc == 0: rc = -1
        self.finished_signal.emit(rc)

    def cancel(self):
        self._cancelled = True
        self.output_signal.emit("\n🛑 PROCES PRZERWANY PRZEZ UŻYTKOWNIKA!\n")

MDNS_GROUP, MDNS_PORT = '224.0.0.251', 5353
OTA_SERVICE = '_arduino._tcp.local'

def _dns_name(buf, off):
    """Czyta nazwę DNS (z obsługą kompresji). Zwraca (nazwa, offset za nazwą)."""
    labels, end, hops = [], None, 0
    while True:
        ln = buf[off]
        if ln == 0:
            off += 1
            break
        if ln & 0xC0 == 0xC0:
            if end is None: end = off + 2
            off = ((ln & 0x3F) << 8) | buf[off + 1]
            hops += 1
            if hops > 20: raise ValueError("DNS name loop")
            continue
        off += 1
        labels.append(buf[off:off + ln].decode(errors='ignore'))
        off += ln
    return '.'.join(labels), (end if end is not None else off)

def build_mdns_query(unicast=False):
    name = b''.join(bytes([len(p)]) + p.encode() for p in OTA_SERVICE.split('.')) + b'\0'
    return struct.pack('!6H', 0, 0, 1, 0, 0, 0) + name + struct.pack('!HH', 12, 0x8001 if unicast else 1)

def parse_arduino_mdns(buf, sender_ip):
    """Wyciąga z odpowiedzi mDNS urządzenia reklamujące usługę _arduino._tcp (ArduinoOTA)."""
    if len(buf) < 12: return []
    qd, an, ns, ar = struct.unpack('!4H', buf[4:12])
    off = 12
    for _ in range(qd):
        _, off = _dns_name(buf, off)
        off += 4
    recs = []
    for _ in range(an + ns + ar):
        name, off = _dns_name(buf, off)
        typ, _cls, _ttl, rdlen = struct.unpack('!HHIH', buf[off:off + 10])
        off += 10
        recs.append((name, typ, off, rdlen))
        off += rdlen
    instances, srv, addr = [], {}, {}
    for name, typ, ro, rl in recs:
        if typ == 12 and name.lower() == OTA_SERVICE:
            instances.append(_dns_name(buf, ro)[0])
        elif typ == 33 and rl >= 7:
            port = struct.unpack('!H', buf[ro + 4:ro + 6])[0]
            srv[name.lower()] = (port, _dns_name(buf, ro + 6)[0].lower())
        elif typ == 1 and rl == 4:
            addr[name.lower()] = socket.inet_ntoa(buf[ro:ro + 4])
    devices = []
    suffix = '.' + OTA_SERVICE
    for inst in instances:
        port, target = srv.get(inst.lower(), (8266, ''))
        short = inst[:-len(suffix)] if inst.lower().endswith(suffix) else inst
        devices.append({'name': short, 'ip': addr.get(target) or sender_ip, 'port': port})
    return devices

def scan_arduino_ota(timeout=3.5):
    """Szuka w sieci lokalnej urządzeń z ArduinoOTA przez mDNS. Zwraca listę {'name','ip','port'}."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError: pass
        unicast = False
        try:
            sock.bind(('', MDNS_PORT))
        except OSError:
            sock.bind(('', 0))
            unicast = True      # bez portu 5353 prosimy o odpowiedź unicastem
        try:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                            struct.pack('4s4s', socket.inet_aton(MDNS_GROUP), socket.inet_aton('0.0.0.0')))
        except OSError: pass
        try: sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        except OSError: pass
        query = build_mdns_query(unicast)
        found, next_send, end = {}, 0, time.time() + timeout
        while time.time() < end:
            if time.time() >= next_send:
                try: sock.sendto(query, (MDNS_GROUP, MDNS_PORT))
                except OSError: pass
                next_send = time.time() + 1.2
            sock.settimeout(0.3)
            try:
                buf, addr = sock.recvfrom(9000)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                for dev in parse_arduino_mdns(buf, addr[0]):
                    found.setdefault(dev['ip'], dev)
            except Exception: pass
        return list(found.values())
    finally:
        sock.close()

class MdnsWorker(QThread):
    result_signal = pyqtSignal(list)

    def run(self):
        try: devices = scan_arduino_ota(3.5)
        except Exception: devices = []
        self.result_signal.emit(devices)

def find_esptool():
    """Zwraca prefiks polecenia esptool (lista) albo None, jeśli narzędzia nie ma w systemie."""
    for name in ('esptool', 'esptool.py'):
        path = shutil.which(name)
        if path: return [path]
    try:  # instalacja przez pip --user bywa poza PATH
        r = subprocess.run([sys.executable, '-m', 'esptool', '--help'], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, timeout=8)
        if r.returncode == 0: return [sys.executable, '-m', 'esptool']
    except Exception: pass
    return None

ESP_SIZES = [0x80000, 0x100000, 0x200000, 0x400000]   # 512 KB, 1 MB, 2 MB, 4 MB

class AvrdudessNative(QWidget):
    def __init__(self):
        super().__init__()
        self.programmers = ['ch341a', 'usbasp', 'serialupdi', 'arduino', 'wiring']
        self.mcus = ['atmega328p', 'attiny85', 'attiny1614', 'atmega8']
        self.worker = None
        self.flash_path = ""
        self.eeprom_path = ""
        self.esp_path = ""
        self.ota_path = ""
        self.mdns_worker = None
        self._fuse_tmp = None
        self._fuse_stage = 0
        self._fuse_base = []
        ensure_pinout_dir()
        generate_default_pinouts()
        self.load_avrdude_config()
        self.initUI()
        self.load_settings()

    def load_avrdude_config(self):
        try:
            res_p = subprocess.run(['avrdude', '-c', '?'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            out_p = res_p.stderr if res_p.stderr else res_p.stdout
            found_p = re.findall(re.compile(r'^\s+([a-zA-Z0-9_\-]+)\s+=', re.MULTILINE), out_p)
            if found_p: self.programmers = sorted(list(set(found_p + self.programmers)))
            
            res_m = subprocess.run(['avrdude', '-p', '?'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            out_m = res_m.stderr if res_m.stderr else res_m.stdout
            found_m = re.findall(re.compile(r'^\s+([a-zA-Z0-9_\-]+)\s+=', re.MULTILINE), out_m)
            if found_m: self.mcus = sorted(list(set(found_m + self.mcus)))
        except Exception: pass

    def get_serial_ports(self):
        """Zwraca listę wykrytych portów szeregowych USB (CH340/FTDI -> ttyUSB, Arduino/ATmega16U2 -> ttyACM)."""
        return sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))

    def get_system_ports(self):
        return ['Brak (USBasp / USB)', 'usb'] + self.get_serial_ports()

    def autodetect_programmer(self):
        self.console.append("Scanning USB devices...")
        prog, port = None, None
        try:
            res = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            out = res.stdout.lower()
            if "16c0:05dc" in out or "usbasp" in out:
                prog, port = "usbasp", "usb"
            # INTELIGENTNY SKANER: Łapie ID sprzętu 1a86:5512 lub frazę ch341 niezależnie od wielkości liter
            elif "1a86:5512" in out or "ch341" in out:
                prog, port = "ch341a", "usb"
            elif "1a86:5523" in out:
                prog, port = "serialupdi", None
            elif "1a86:7523" in out or "ch340" in out:
                prog, port = "arduino", None
        except Exception: pass

        # BLOKADA SYGNAŁÓW: PyQt6 nie wymaże ani portu, ani programatora podczas odświeżania listy!
        self.prog_combo.blockSignals(True)
        self.port_combo.blockSignals(True)
        
        current_ports = self.get_system_ports()
        self.port_combo.clear()
        self.port_combo.addItems(current_ports)

        if prog:
            if self.prog_combo.findText(prog) == -1:
                self.prog_combo.addItem(prog)
            self.prog_combo.setCurrentText(prog)
            self.console.append(f"👉 Detected Programmer: {prog}")
        # Programatory szeregowe (arduino, serialupdi itd.) nie używają "usb" - wybieramy znaleziony port /dev/tty*
        if prog in ('arduino', 'serialupdi', 'wiring') and not port:
            serial_ports = self.get_serial_ports()
            if serial_ports:
                port = serial_ports[0]
                if len(serial_ports) > 1:
                    self.console.append(f"ℹ️ Found several serial ports: {', '.join(serial_ports)} (using {port})")
            else:
                self.console.append("⚠️ No /dev/ttyUSB* or /dev/ttyACM* found (check the cable / 'dialout' group).")
        if port:
            if self.port_combo.findText(port) == -1:
                self.port_combo.addItem(port)
            self.port_combo.setCurrentText(port)
            self.console.append(f"👉 Detected Port: {port}")
            
        self.prog_combo.blockSignals(False)
        self.port_combo.blockSignals(False)
        self.console.append("✅ Autodetect finished!\n")

    def detect_mcu_signature(self):
        cmd = ['avrdude', '-v', '-p', 'm328p', '-c', self.prog_combo.currentText().strip()]
        port = self.port_combo.currentText().strip()
        if 'Brak' not in port and port != '': cmd.extend(['-P', port])
        self.console.append("Reading device signature... (" + " ".join(cmd) + ")\n")
        self.run_async_cmd(cmd, kind='mcu_detect')

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 1 and os.path.exists(lines[0]):
                        self.flash_path = lines[0]
                        self.flash_label.setText(lines[0].split('/')[-1])
                    if len(lines) >= 2: self.flags_input.setText(lines[1])
            except Exception: pass

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                f.write(f"{self.flash_path}\n{self.flags_input.text().strip()}")
        except Exception: pass

    def update_pinout_view(self):
        """Pokazuje obrazek z katalogu pinouts dla aktualnie wybranego procesora."""
        current_mcu = self.mcu_combo.currentText().lower().strip()
        path = find_pinout_image(current_mcu)
        if path:
            self.pinout_view.show_image(path)
        else:
            self.pinout_view.show_message(TXT["pinout_missing"].format(mcu=current_mcu or "?", dir=PINOUT_DIR))

    def on_tab_changed(self, index):
        """Pinout: tylko czarne pole (bez konsoli). Zakładki AVR: konsola avrdude. Zakładki ESP: konsola esptool/OTA."""
        page = self.tabs.widget(index)
        is_pinout = page is self.tab_pinout
        is_esp = page is self.tab_esp or page is self.tab_ota
        show_avr = not is_pinout and not is_esp
        self.console_bar.setVisible(show_avr)
        self.console.setVisible(show_avr)
        self.esp_console_label.setVisible(is_esp)
        self.esp_console.setVisible(is_esp)
        self.main_layout.setStretchFactor(self.tabs, 1 if is_pinout else 0)
        self.main_layout.setStretchFactor(self.console, 1 if show_avr else 0)
        self.main_layout.setStretchFactor(self.esp_console, 1 if is_esp else 0)
        # Pole zakładek nie rośnie ponad wysokość zawartości (całe wolne miejsce dostaje konsola); Pinout rośnie na całość
        self.tabs.setSizePolicy(QSizePolicy.Policy.Preferred,
                                QSizePolicy.Policy.Expanding if is_pinout else QSizePolicy.Policy.Maximum)
        self.tabs.updateGeometry()
        for w in self.avr_only_widgets:
            w.setEnabled(not is_esp)

    def make_frame_box(self, title):
        box = QGroupBox(title)
        box.setObjectName("frameBox")
        return box

    def initUI(self):
        self.setWindowTitle(TXT["title"])
        self.setGeometry(5, 30, 1020, 735)
        self.setStyleSheet(GROUP_STYLE)
        self.main_layout = main_layout = QVBoxLayout()
        main_layout.setSpacing(3)
        main_layout.setContentsMargins(8, 6, 8, 4)
        
        hw_box = QGroupBox(TXT["hw_config"])
        hw_box.setObjectName("hwBox")
        hw_layout = QFormLayout()
        
        self.prog_combo = QComboBox()
        self.prog_combo.setEditable(True)
        self.prog_combo.addItems(self.programmers)
        
        self.mcu_combo = QComboBox()
        self.mcu_combo.setEditable(True)
        self.mcu_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mcu_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.mcu_combo.addItems(self.mcus)
        if 'atmega328p' in self.mcus: self.mcu_combo.setCurrentText('atmega328p')
        self.mcu_combo.currentTextChanged.connect(self.update_pinout_view)
        
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.get_system_ports())
        
        self.flags_input = QLineEdit()
        self.flags_input.setPlaceholderText("eg. -B 8 or -F (write if You want)")
        self.flags_input.textChanged.connect(self.save_settings)
        
        btn_detect = QPushButton(TXT["detect_prog"])
        btn_detect.setStyleSheet(action_button_style("#66bb6a", "#57a85b"))
        btn_detect.clicked.connect(self.autodetect_programmer)

        btn_detect_mcu = QPushButton(TXT["detect_mcu"])
        btn_detect_mcu.setStyleSheet(action_button_style("#29b6f6", "#1ea3e0"))
        btn_detect_mcu.clicked.connect(self.detect_mcu_signature)
        
        btn_erase = QPushButton(TXT["chip_erase"])
        btn_erase.setStyleSheet(action_button_style("#ff8a50", "#f2763a"))
        btn_erase.clicked.connect(self.chip_erase)
        
        self.btn_cancel = QPushButton(TXT["cancel"])
        self.btn_cancel.setStyleSheet(action_button_style("#e0484d", "#cc363b", "#c98285"))
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_operation)
        
        action_layout = QHBoxLayout()
        action_layout.addWidget(btn_detect)
        action_layout.addWidget(btn_detect_mcu)
        action_layout.addWidget(btn_erase)
        action_layout.addWidget(self.btn_cancel)
        
        hw_layout.addRow(QLabel(TXT["control_auto"]), action_layout)
        hw_layout.addRow(QLabel(TXT["prog_label"]), self.prog_combo)
        hw_layout.addRow(QLabel(TXT["mcu_label"]), self.mcu_combo)
        hw_layout.addRow(QLabel(TXT["port_label"]), self.port_combo)
        hw_layout.addRow(QLabel(TXT["flags_label"]), self.flags_input)
        hw_box.setLayout(hw_layout)
        main_layout.addWidget(hw_box)
        # Wyłączane na zakładkach ESP (dotyczą tylko avrdude)
        self.avr_only_widgets = [btn_detect, btn_detect_mcu, btn_erase, self.prog_combo, self.mcu_combo, self.flags_input]

        self.tabs = FitTabWidget()

        # ---------------- Zakładka: Pamięć (FLASH i EEPROM obok siebie - połowa wysokości) ----------------
        self.tab_mem = QWidget()
        mem_layout = QHBoxLayout()
        mem_layout.setContentsMargins(6, 0, 4, 6)
        mem_layout.setSpacing(10)
        
        flash_box = self.make_frame_box(TXT["flash_box"])
        flash_box.setObjectName("memBox")
        f_lay = QHBoxLayout()
        f_lay.setContentsMargins(6, 0, 6, 3)
        f_lay.setSpacing(4)
        self.flash_label = QLabel(TXT["no_file_hex"])
        self.flash_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)   # długa nazwa pliku nie rozpycha okna
        btn_flash_file = QPushButton(TXT["browse"])
        btn_flash_file.clicked.connect(lambda: self.choose_file('flash'))
        self.btn_flash_write = QPushButton(TXT["write"])
        self.btn_flash_read = QPushButton(TXT["read"])
        self.btn_flash_write.clicked.connect(lambda: self.execute_mem('flash', 'w'))
        self.btn_flash_read.clicked.connect(lambda: self.execute_mem('flash', 'r'))
        f_lay.addWidget(btn_flash_file)
        f_lay.addWidget(self.flash_label, 1)
        f_lay.addWidget(self.btn_flash_write)
        f_lay.addWidget(self.btn_flash_read)
        flash_box.setLayout(f_lay)
        mem_layout.addWidget(flash_box, 1, Qt.AlignmentFlag.AlignTop)
        
        eeprom_box = self.make_frame_box(TXT["eeprom_box"])
        eeprom_box.setObjectName("memBox")
        e_lay = QHBoxLayout()
        e_lay.setContentsMargins(6, 0, 6, 3)
        e_lay.setSpacing(4)
        self.eeprom_label = QLabel(TXT["no_file_eep"])
        self.eeprom_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        btn_eep_file = QPushButton(TXT["browse"])
        btn_eep_file.clicked.connect(lambda: self.choose_file('eeprom'))
        self.btn_eep_write = QPushButton(TXT["write"])
        self.btn_eep_read = QPushButton(TXT["read"])
        self.btn_eep_write.clicked.connect(lambda: self.execute_mem('eeprom', 'w'))
        self.btn_eep_read.clicked.connect(lambda: self.execute_mem('eeprom', 'r'))
        e_lay.addWidget(btn_eep_file)
        e_lay.addWidget(self.eeprom_label, 1)
        e_lay.addWidget(self.btn_eep_write)
        e_lay.addWidget(self.btn_eep_read)
        eeprom_box.setLayout(e_lay)
        mem_layout.addWidget(eeprom_box, 1, Qt.AlignmentFlag.AlignTop)
        self.tab_mem.setLayout(mem_layout)
        
        # ---------------- Zakładka: Pinout (obrazek zamiast tekstu) ----------------
        self.tab_pinout = QWidget()
        pin_lay = QVBoxLayout()
        pin_lay.setContentsMargins(6, 6, 6, 6)
        self.pinout_view = PinoutView()
        pin_lay.addWidget(self.pinout_view)
        self.tab_pinout.setLayout(pin_lay)

        # ---------------- Zakładka: Fuses / Locks (układ jak na zrzucie fuses.png) ----------------
        self.tab_fuses = QWidget()
        fuse_layout = QGridLayout()
        fuse_layout.setContentsMargins(6, 6, 6, 6)
        fuse_layout.setHorizontalSpacing(10)
        fuse_layout.setVerticalSpacing(2)

        # Lewa ramka: wartości bezpośrednie (pola wypełniają ramkę)
        fields_box = self.make_frame_box(TXT["hex_direct"])
        fields_box.setFixedWidth(300)
        fields_lay = QFormLayout()
        fields_lay.setContentsMargins(8, 4, 8, 6)
        fields_lay.setVerticalSpacing(6)
        fields_lay.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        fields_lay.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.fuse_l = QLineEdit("0xE2")
        self.fuse_h = QLineEdit("0xD9")
        self.fuse_e = QLineEdit("0xFF")
        self.fuse_lock = QLineEdit("0xFF")
        fields_lay.addRow(QLabel("Low Fuse:"), self.fuse_l)
        fields_lay.addRow(QLabel("High Fuse:"), self.fuse_h)
        fields_lay.addRow(QLabel("Ext Fuse:"), self.fuse_e)
        fields_lay.addRow(QLabel("Lock Bits:"), self.fuse_lock)
        fields_box.setLayout(fields_lay)

        # Prawa ramka: kalkulator (listy o stałej szerokości, reszta wolna)
        opts_box = self.make_frame_box(TXT["interactive_calc"])
        opts_lay = QGridLayout()
        opts_lay.setContentsMargins(8, 4, 8, 6)
        opts_lay.setVerticalSpacing(6)
        self.verify_check = QCheckBox(TXT["verify_fuses"])
        self.verify_check.setChecked(True)
        opts_lay.addWidget(self.verify_check, 0, 0, 1, 3)

        self.clock_combo = QComboBox()
        self.clock_combo.setFixedWidth(295)
        self.clock_combo.addItems([TXT["clk_internal_8"], TXT["clk_external_16"], TXT["clk_internal_1"]])
        self.clock_combo.currentIndexChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addWidget(QLabel(TXT["clock_system"]), 1, 0)
        opts_lay.addWidget(self.clock_combo, 1, 1)

        self.wd_check = QCheckBox(TXT["watchdog_label"])
        self.wd_check.stateChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addWidget(self.wd_check, 2, 0, 1, 3)

        self.bod_combo = QComboBox()
        self.bod_combo.setFixedWidth(295)
        self.bod_combo.addItems([TXT["bod_disabled"], TXT["bod_27"], TXT["bod_43"], TXT["bod_18"]])
        self.bod_combo.currentIndexChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addWidget(QLabel(TXT["bod_label"]), 3, 0)
        opts_lay.addWidget(self.bod_combo, 3, 1)
        opts_lay.setColumnStretch(2, 1)
        opts_box.setLayout(opts_lay)

        # Przyciski POD ramkami, przy ich prawej krawędzi: Odczytaj (pod lewą), Zapisz (pod prawą)
        b_r = QPushButton(TXT["fuse_read"])
        b_w = QPushButton(TXT["write"])
        b_r.setFixedWidth(200)
        b_w.setFixedWidth(200)
        b_r.clicked.connect(self.read_fuses)
        b_w.clicked.connect(self.write_fuses)
        read_row = QHBoxLayout()
        read_row.setContentsMargins(0, 0, 8, 0)
        read_row.addStretch(1)
        read_row.addWidget(b_r)
        write_row = QHBoxLayout()
        write_row.setContentsMargins(0, 0, 8, 0)
        write_row.addStretch(1)
        write_row.addWidget(b_w)

        fuse_layout.addWidget(fields_box, 0, 0, Qt.AlignmentFlag.AlignTop)
        fuse_layout.addWidget(opts_box, 0, 1, Qt.AlignmentFlag.AlignTop)
        fuse_layout.addLayout(read_row, 1, 0)
        fuse_layout.addLayout(write_row, 1, 1)
        fuse_layout.setColumnStretch(1, 1)
        fuse_layout.setRowStretch(2, 1)
        self.tab_fuses.setLayout(fuse_layout)
        
        # ---------------- Zakładka: ESP8266 (esptool) ----------------
        self.tab_esp = QWidget()
        esp_layout = QHBoxLayout()
        esp_left = QVBoxLayout()
        esp_right = QVBoxLayout()

        esp_fw_box = self.make_frame_box(TXT["esp_fw_box"])
        fw_lay = QHBoxLayout()
        self.esp_label = QLabel(TXT["esp_no_file"])
        btn_esp_file = QPushButton(TXT["browse"])
        btn_esp_file.clicked.connect(self.choose_esp_file)
        self.esp_addr = QLineEdit("0x0")
        # self.esp_addr.setFixedWidth(90)
        btn_esp_write = QPushButton(TXT["write"])
        btn_esp_write.clicked.connect(self.esp_write)
        fw_lay.addWidget(btn_esp_file)
        fw_lay.addWidget(self.esp_label, 1)
        fw_lay.addWidget(QLabel(TXT["esp_addr"]))
        fw_lay.addWidget(self.esp_addr)
        fw_lay.addWidget(btn_esp_write)
        esp_fw_box.setLayout(fw_lay)
        esp_left.addWidget(esp_fw_box)

        esp_bk_box = self.make_frame_box(TXT["esp_backup_box"])
        bk_lay = QHBoxLayout()
        self.esp_size = QComboBox()
        self.esp_size.addItems(["512 KB", "1 MB (ESP-01S)", "2 MB", "4 MB"])
        self.esp_size.setCurrentIndex(1)
        btn_esp_read = QPushButton(TXT["read"])
        btn_esp_read.clicked.connect(self.esp_read)
        bk_lay.addWidget(QLabel(TXT["esp_size"]))
        bk_lay.addWidget(self.esp_size)
        bk_lay.addStretch(1)
        bk_lay.addWidget(btn_esp_read)
        esp_bk_box.setLayout(bk_lay)
        esp_left.addWidget(esp_bk_box)
        esp_left.addStretch(1)

        esp_tools_box = self.make_frame_box(TXT["esp_tools_box"])
        tools_lay = QGridLayout()
        btn_esp_detect = QPushButton(TXT["esp_detect"])
        btn_esp_detect.setStyleSheet(action_button_style("#29b6f6", "#1ea3e0"))
        btn_esp_detect.clicked.connect(self.esp_detect)
        btn_esp_erase = QPushButton(TXT["esp_erase"])
        btn_esp_erase.setStyleSheet(action_button_style("#ff8a50", "#f2763a"))
        btn_esp_erase.clicked.connect(self.esp_erase)
        self.esp_baud = QComboBox()
        self.esp_baud.addItems(["115200", "230400", "460800", "921600"])
        tools_lay.addWidget(btn_esp_detect, 0, 0, 1, 3)
        tools_lay.addWidget(btn_esp_erase, 1, 0, 1, 3)
        tools_lay.addWidget(QLabel(TXT["esp_baud"]), 2, 0)
        tools_lay.addWidget(self.esp_baud, 2, 1)
        btn_esp_ports = QPushButton(TXT["esp_ports"])
        btn_esp_ports.clicked.connect(self.refresh_ports)
        tools_lay.addWidget(btn_esp_ports, 2, 2)
        esp_tools_box.setLayout(tools_lay)
        esp_right.addWidget(esp_tools_box)
        esp_hint = QLabel(TXT["esp_hint"])
        esp_hint.setWordWrap(True)
        esp_hint.setStyleSheet("color: #555555;")
        esp_right.addWidget(esp_hint)
        esp_right.addStretch(1)

        esp_layout.addLayout(esp_left, 3)
        esp_layout.addLayout(esp_right, 2)
        self.tab_esp.setLayout(esp_layout)

        # ---------------- Zakładka: ESP OTA (WiFi) ----------------
        self.tab_ota = QWidget()
        ota_layout = QHBoxLayout()
        ota_box = self.make_frame_box(TXT["ota_box"])
        ota_grid = QGridLayout()
        self.ota_host = QComboBox()
        self.ota_host.setEditable(True)
        self.ota_host.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.ota_host.lineEdit().setPlaceholderText("192.168.1.50 / esp8266-xxxxxx.local")
        btn_ota_scan = QPushButton(TXT["ota_scan"])
        btn_ota_scan.clicked.connect(self.ota_scan)
        self.ota_port = QLineEdit("8266")
        self.ota_port.setFixedWidth(70)
        self.ota_pass = QLineEdit()
        self.ota_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.ota_pass.setPlaceholderText("(puste = bez hasła)")
        self.ota_type = QComboBox()
        self.ota_type.addItems([TXT["ota_type_fw"], TXT["ota_type_fs"]])
        btn_ota_file = QPushButton(TXT["browse"])
        btn_ota_file.clicked.connect(self.choose_ota_file)
        self.ota_label = QLabel(TXT["ota_no_file"])
        btn_ota_go = QPushButton(TXT["ota_upload"])
        btn_ota_go.setStyleSheet(action_button_style("#66bb6a", "#57a85b"))
        btn_ota_go.clicked.connect(self.ota_start)
        ota_grid.addWidget(QLabel(TXT["ota_host"]), 0, 0)
        ota_grid.addWidget(self.ota_host, 0, 1)
        ota_grid.addWidget(QLabel(TXT["ota_port"]), 0, 2)
        ota_grid.addWidget(self.ota_port, 0, 3)
        ota_grid.addWidget(btn_ota_scan, 0, 4)
        ota_grid.addWidget(QLabel(TXT["ota_pass"]), 1, 0)
        ota_grid.addWidget(self.ota_pass, 1, 1)
        ota_grid.addWidget(QLabel(TXT["ota_type"]), 1, 2)
        ota_grid.addWidget(self.ota_type, 1, 3)
        ota_file_row = QHBoxLayout()
        ota_file_row.addWidget(btn_ota_file)
        ota_file_row.addWidget(self.ota_label, 1)
        ota_file_row.addWidget(btn_ota_go)
        ota_grid.addLayout(ota_file_row, 2, 0, 1, 5)
        ota_grid.setColumnStretch(1, 1)
        ota_box.setLayout(ota_grid)
        ota_right = QVBoxLayout()
        ota_hint = QLabel(TXT["ota_hint"])
        ota_hint.setWordWrap(True)
        ota_hint.setStyleSheet("color: #555555;")
        ota_right.addWidget(ota_hint)
        ota_right.addStretch(1)
        ota_left = QVBoxLayout()
        ota_left.addWidget(ota_box)
        ota_left.addStretch(1)
        ota_layout.addLayout(ota_left, 3)
        ota_layout.addLayout(ota_right, 2)
        self.tab_ota.setLayout(ota_layout)

        self.tabs.addTab(self.tab_mem, TXT["mem_tab"])
        self.tabs.addTab(self.tab_pinout, TXT["pinout_tab"])
        self.tabs.addTab(self.tab_fuses, TXT["fuses_tab"])
        self.tabs.addTab(self.tab_esp, TXT["esp_tab"])
        self.tabs.addTab(self.tab_ota, TXT["ota_tab"])
        main_layout.addWidget(self.tabs)
        
        # ---------------- Konsola (widoczna poza zakładką Pinout) ----------------
        self.console_label = QLabel(TXT["console_title"])
        self.btn_clear_log = QPushButton(TXT["clear_logs"])
        self.btn_clear_log.setFixedHeight(22)
        self.btn_clear_log.clicked.connect(lambda: self.console.clear())
        self.console_bar = QWidget()          # wiersz: napis + przycisk (widoczność przełączana razem)
        console_bar_lay = QHBoxLayout()
        console_bar_lay.setContentsMargins(0, 0, 0, 0)
        console_bar_lay.addWidget(self.console_label, 1)
        console_bar_lay.addWidget(self.btn_clear_log)
        self.console_bar.setLayout(console_bar_lay)
        main_layout.addWidget(self.console_bar)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #1a1a1a; color: #00ff66; font-family: monospace;")
        main_layout.addWidget(self.console, 1)

        self.esp_console_label = QLabel(TXT["esp_console_title"])
        main_layout.addWidget(self.esp_console_label)
        self.esp_console = QTextEdit()
        self.esp_console.setReadOnly(True)
        self.esp_console.setStyleSheet("background-color: #1a1a1a; color: #00ff66; font-family: monospace;")
        main_layout.addWidget(self.esp_console, 1)
        
        self.setLayout(main_layout)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.on_tab_changed(self.tabs.currentIndex())
        self.recalc_fuses_from_gui()
        self.update_pinout_view()

    def choose_file(self, mem_type):
        fn, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", "", "Intel HEX (*.hex *.eep)")
        if fn:
            if mem_type == 'flash':
                self.flash_path = fn
                self.flash_label.setText(fn.split('/')[-1])
                self.flash_label.setToolTip(fn)
            else:
                self.eeprom_path = fn
                self.eeprom_label.setText(fn.split('/')[-1])
                self.eeprom_label.setToolTip(fn)
            self.save_settings()

    def build_base_cmd(self):
        cmd = ['avrdude', '-p', self.mcu_combo.currentText().strip(), '-c', self.prog_combo.currentText().strip()]
        port = self.port_combo.currentText().strip()
        if port == 'usb': cmd.extend(['-P', 'usb'])
        elif 'Brak' not in port and port != '': cmd.extend(['-P', port])
        if not self.verify_check.isChecked(): cmd.append('-V')
        flags = self.flags_input.text().strip()
        if flags: cmd.extend(flags.split())
        return cmd

    def run_async_cmd(self, cmds, kind=None, console=None):
        """cmds: pojedyncze polecenie (lista str) albo lista poleceń wykonywanych po kolei.
        console: widget, do którego trafia wyjście (domyślnie konsola avrdude)."""
        target = console or self.console
        if cmds and isinstance(cmds[0], str): cmds = [cmds]
        self.btn_cancel.setEnabled(True)
        try:
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.wait()
        except RuntimeError: self.worker = None

        self.worker = AvrdudeWorker(cmds)   # uruchamia dowolne polecenia zewnętrzne (avrdude, esptool)
        self.worker.output_signal.connect(lambda t, c=target: c.append(t.strip('\r\n')))
        if kind == 'fuse_read': self.worker.finished_signal.connect(self.on_fuse_read_finished)
        elif kind == 'mcu_detect': self.worker.finished_signal.connect(self.on_mcu_detect_finished)
        else: self.worker.finished_signal.connect(lambda rc, c=target: self.on_cmd_finished(rc, c))
        self.worker.start()

    def append_console_output(self, text):
        self.console.append(text.strip('\r\n'))

    def cancel_operation(self):
        try:
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning(): self.worker.cancel()
        except RuntimeError: pass

    def on_cmd_finished(self, returncode, console=None):
        console = console or self.console
        self.btn_cancel.setEnabled(False)
        if returncode == 0: console.append("\n✅ SUCCESS!")
        else: console.append("\n❌ ERROR!")

    # ---------------- Fuses / Locks ----------------

    def _fuse_widget(self, name):
        return {'lfuse': self.fuse_l, 'hfuse': self.fuse_h, 'efuse': self.fuse_e, 'lock': self.fuse_lock}[name]

    def _fuse_cleanup(self):
        if self._fuse_tmp:
            shutil.rmtree(self._fuse_tmp, ignore_errors=True)
            self._fuse_tmp = None

    def _fuse_read_args(self, name):
        # Format 'r' = surowy bajt zapisany do pliku (bez parsowania tekstu z konsoli)
        return ['-U', f'{name}:r:{self._fuse_tmp}/{name}.bin:r']

    def read_fuses(self):
        self._fuse_cleanup()
        self._fuse_tmp = tempfile.mkdtemp(prefix="avrgui_fuses_")
        self._fuse_stage = 1
        self._fuse_base = self.build_base_cmd()
        # efuse na końcu: układy bez efuse (np. ATmega8) nie blokują odczytu pozostałych
        cmd = list(self._fuse_base)
        for name in ['lfuse', 'hfuse', 'lock', 'efuse']:
            cmd.extend(self._fuse_read_args(name))
        self.console.append("Reading fuses...")
        self.run_async_cmd(cmd, kind='fuse_read')

    def _collect_fuse_values(self):
        values = {}
        for name in FUSE_NAMES:
            try:
                with open(os.path.join(self._fuse_tmp, f"{name}.bin"), 'rb') as f:
                    data = f.read(1)
                if data: values[name] = data[0]
            except Exception: pass
        return values

    def on_fuse_read_finished(self, returncode):
        cancelled = bool(self.worker and getattr(self.worker, '_cancelled', False))
        values = self._collect_fuse_values() if self._fuse_tmp else {}

        # Nowsze avrdude odmawia całej operacji, gdy układ nie ma któregoś bezpiecznika -> próba pojedynczo
        if not values and self._fuse_stage == 1 and not cancelled and self._fuse_tmp:
            self._fuse_stage = 2
            self.console.append("↻ Retrying: reading fuses one by one...")
            cmds = [self._fuse_base + self._fuse_read_args(n) for n in ['lfuse', 'hfuse', 'lock', 'efuse']]
            self.run_async_cmd(cmds, kind='fuse_read')
            return

        self.btn_cancel.setEnabled(False)
        if values:
            for name in FUSE_NAMES:
                w = self._fuse_widget(name)
                w.setText(f"0x{values[name]:02X}" if name in values else "N/A")
            self.sync_calc_from_fields()
            summary = ", ".join(f"{n}=0x{values[n]:02X}" for n in FUSE_NAMES if n in values)
            self.console.append(f"\n✅ FUSES READ: {summary}")
        else:
            self.console.append("\n❌ ERROR! Could not read fuses.")
        self._fuse_cleanup()

    def write_fuses(self):
        cmd = self.build_base_cmd()
        to_write = []
        for name in FUSE_NAMES:
            text = self._fuse_widget(name).text().strip()
            if text.upper() in ('', 'N/A'): continue   # układ nie ma tego bezpiecznika
            val = parse_hex_byte(text)
            if val is None:
                self.console.setText(f"❌ Invalid hex value in {name}: '{text}' (expected e.g. 0xE2)")
                return
            to_write.append((name, val))
        if not to_write:
            self.console.setText("❌ Nothing to write.")
            return
        for name, val in to_write:
            cmd.extend(['-U', f'{name}:w:0x{val:02X}:m'])
        self.run_async_cmd(cmd)

    def recalc_fuses_from_gui(self):
        """Kalkulator dla ATmega328P: zmienia tylko te bity, których dotyczy dana opcja."""
        lfuse = {0: 0xE2, 1: 0xFF, 2: 0x62}.get(self.clock_combo.currentIndex(), 0xE2)

        hfuse = parse_hex_byte(self.fuse_h.text(), 0xD9)
        if self.wd_check.isChecked(): hfuse &= ~(1 << 4)    # WDTON zaprogramowany (0) = watchdog włączony na stałe
        else: hfuse |= (1 << 4)

        efuse = parse_hex_byte(self.fuse_e.text(), 0xFF)
        bod_bits = {0: 0b111, 1: 0b101, 2: 0b100, 3: 0b110}.get(self.bod_combo.currentIndex(), 0b111)  # off / 2.7V / 4.3V / 1.8V
        efuse = (efuse & ~0b111) | bod_bits

        self.fuse_l.setText(f"0x{lfuse:02X}")
        self.fuse_h.setText(f"0x{hfuse:02X}")
        self.fuse_e.setText(f"0x{efuse:02X}")

    def sync_calc_from_fields(self):
        """Po odczycie z układu ustawia kalkulator zgodnie z wczytanymi bajtami (bez nadpisywania pól)."""
        lfuse = parse_hex_byte(self.fuse_l.text())
        hfuse = parse_hex_byte(self.fuse_h.text())
        efuse = parse_hex_byte(self.fuse_e.text())
        for w in (self.clock_combo, self.wd_check, self.bod_combo): w.blockSignals(True)
        if lfuse is not None:
            idx = {0xE2: 0, 0xFF: 1, 0x62: 2}.get(lfuse)
            if idx is not None: self.clock_combo.setCurrentIndex(idx)
        if hfuse is not None:
            self.wd_check.setChecked(not (hfuse & (1 << 4)))
        if efuse is not None:
            idx = {0b111: 0, 0b101: 1, 0b100: 2, 0b110: 3}.get(efuse & 0b111)
            if idx is not None: self.bod_combo.setCurrentIndex(idx)
        for w in (self.clock_combo, self.wd_check, self.bod_combo): w.blockSignals(False)

    # ---------------- ESP8266 (esptool) - logi w konsoli esptool/OTA ----------------

    def choose_esp_file(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", "", "Binary (*.bin);;All files (*)")
        if fn:
            self.esp_path = fn
            self.esp_label.setText(fn.split('/')[-1])

    def refresh_ports(self):
        """Odświeża listę portów (kabel mógł zostać podłączony po starcie programu)."""
        current = self.port_combo.currentText()
        ports = self.get_system_ports()
        serial_ports = self.get_serial_ports()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current in ports and current.startswith('/dev/'): self.port_combo.setCurrentText(current)
        elif serial_ports: self.port_combo.setCurrentText(serial_ports[0])
        self.port_combo.blockSignals(False)
        if serial_ports:
            self.esp_console.append(f"Serial ports: {', '.join(serial_ports)} (selected: {self.port_combo.currentText()})")
        else:
            self.esp_console.append("⚠️ No /dev/ttyUSB* or /dev/ttyACM* found (check the cable / 'dialout' group).")

    def esp_base_cmd(self):
        """Podstawa polecenia esptool albo None (z komunikatem w konsoli), gdy czegoś brakuje."""
        tool = find_esptool()
        if not tool:
            self.esp_console.append("❌ esptool not found. Install it: sudo apt install esptool  (or: pip install esptool)")
            return None
        port = self.port_combo.currentText().strip()
        if not port.startswith('/dev/'):
            self.esp_console.append("❌ Select a serial port (e.g. /dev/ttyUSB0) in the Port (-P) field.")
            return None
        return tool + ['--port', port, '--baud', self.esp_baud.currentText().strip()]

    def esp_detect(self):
        base = self.esp_base_cmd()
        if base:
            self.esp_console.append("Detecting ESP chip... (GPIO0 must be held low on power-up)")
            self.run_async_cmd([base + ['chip-id'], base + ['flash-id']], console=self.esp_console)

    def esp_erase(self):
        base = self.esp_base_cmd()
        if base: self.run_async_cmd(base + ['erase_flash'], console=self.esp_console)

    def esp_write(self):
        if not self.esp_path:
            self.esp_console.append("❌ Select a .bin file first!")
            return
        addr = self.esp_addr.text().strip()
        if not re.fullmatch(r'0x[0-9a-fA-F]+|\d+', addr):
            self.esp_console.append(f"❌ Invalid address: '{addr}' (expected e.g. 0x0)")
            return
        base = self.esp_base_cmd()
        if base: self.run_async_cmd(base + ['write_flash', addr, self.esp_path], console=self.esp_console)

    def esp_read(self):
        base = self.esp_base_cmd()
        if not base: return
        sp, _ = QFileDialog.getSaveFileName(self, "Zapisz", "backup_esp8266.bin", "Binary (*.bin)")
        if not sp: return
        size = ESP_SIZES[self.esp_size.currentIndex()]
        self.run_async_cmd(base + ['read_flash', '0x0', f'0x{size:X}', sp], console=self.esp_console)

    # ---------------- ESP OTA (WiFi) ----------------

    def choose_ota_file(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", "", "Binary (*.bin);;All files (*)")
        if fn:
            self.ota_path = fn
            self.ota_label.setText(fn.split('/')[-1])

    def ota_scan(self):
        """Szuka urządzeń z ArduinoOTA w sieci (mDNS) i wypełnia listę adresów."""
        if self.mdns_worker and self.mdns_worker.isRunning(): return
        self.esp_console.append("Scanning the network for ArduinoOTA devices (mDNS)...")
        self.mdns_worker = MdnsWorker()
        self.mdns_worker.result_signal.connect(self.on_ota_scan_done)
        self.mdns_worker.start()

    def on_ota_scan_done(self, devices):
        if not devices:
            self.esp_console.append("❌ No devices found (the firmware needs ArduinoOTA; mDNS may be blocked - enter the IP manually).")
            return
        self.ota_host.clear()
        for d in devices:
            self.ota_host.addItem(f"{d['ip']}  ({d['name']})")
            self.esp_console.append(f"👉 Found: {d['name']} at {d['ip']}:{d['port']}")
        self.ota_host.setCurrentIndex(0)
        self.ota_port.setText(str(devices[0]['port']))

    def ota_start(self):
        text = self.ota_host.currentText().strip()
        host = text.split()[0] if text else ""     # pozycje z listy mają postać "IP  (nazwa)"
        if not host:
            self.esp_console.append("❌ Enter the ESP address (IP or name) first (or use Search).")
            return
        if not self.ota_path:
            self.esp_console.append("❌ Select a .bin file first!")
            return
        try:
            port = int(self.ota_port.text().strip())
            if not 1 <= port <= 65535: raise ValueError
        except ValueError:
            self.esp_console.append("❌ Invalid OTA port (default is 8266).")
            return
        command = OTA_FLASH if self.ota_type.currentIndex() == 0 else OTA_FS
        self.btn_cancel.setEnabled(True)
        try:
            if self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.wait()
        except RuntimeError: self.worker = None
        target = self.esp_console
        target.append(f"OTA: {self.ota_path} -> {host}:{port}")
        self.worker = OtaWorker(host, port, self.ota_pass.text(), self.ota_path, command)
        self.worker.output_signal.connect(lambda t, c=target: c.append(t.strip('\r\n')))
        self.worker.finished_signal.connect(lambda rc, c=target: self.on_cmd_finished(rc, c))
        self.worker.start()

    # ---------------- Wykrywanie procesora ----------------

    def on_mcu_detect_finished(self, returncode):
        self.btn_cancel.setEnabled(False)
        output = self.console.toPlainText()
        # avrdude pisze "Device signature = 0x1e950f" (nowsze) lub "= 1E 95 0F" (starsze)
        sig_matches = re.findall(r'Device signature\s*=\s*(?:0x)?([0-9a-fA-F]{2})\s?([0-9a-fA-F]{2})\s?([0-9a-fA-F]{2})', output, re.IGNORECASE)
        if sig_matches:
            clean_sig = "".join(sig_matches[-1]).upper()   # ostatnia sygnatura w konsoli
            s_map = {"1E950F": "atmega328p", "1E9514": "atmega328", "1E930B": "attiny85", "1E9422": "attiny1614",
                     "1E9307": "atmega8", "1E9406": "atmega168", "1E940B": "atmega168p", "1E930A": "atmega88",
                     "1E9587": "atmega32u4", "1E9801": "atmega2560", "1E9007": "attiny13", "1E910A": "attiny2313"}
            if clean_sig in s_map:
                self.mcu_combo.setCurrentText(s_map[clean_sig])
                self.console.append(f"\n✅ DETECTED: {s_map[clean_sig]}!")
                return
        self.console.append("\n❌ MCU auto-select failed.")

    def chip_erase(self):
        cmd = self.build_base_cmd()
        cmd.append('-e')
        self.run_async_cmd(cmd)

    def execute_mem(self, mem_type, mode):
        cmd = self.build_base_cmd()
        path = self.flash_path if mem_type == 'flash' else self.eeprom_path
        if mode == 'w':
            if not path:
                self.console.setText(TXT["err_no_file"])
                return
            cmd.extend(['-U', f'{mem_type}:w:{path}:i'])
        else:
            sp, _ = QFileDialog.getSaveFileName(self, "Zapisz", f"backup_{mem_type}.hex", "HEX (*.hex)")
            if not sp: return
            cmd.extend(['-U', f'{mem_type}:r:{sp}:i'])
        self.run_async_cmd(cmd)

    def check_avrdude_version(self):
        """Sprawdza wersję zainstalowanego w systemie narzędzia avrdude."""
        try:
            res = subprocess.run(['avrdude', '-?'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            output = res.stderr if res.stderr else res.stdout
            version_match = re.search(r'version\s+([0-9]+\.[0-9]+)', output, re.IGNORECASE)
            if version_match:
                version_str = version_match.group(1)
                self.console.append(f"🔎 avrdude version: {version_str}")
            else:
                self.console.append("⚠️ Could not parse avrdude version.")
        except Exception as e:
            self.console.append(f"❌ Error: {str(e)}")

    def closeEvent(self, event):
        self._fuse_cleanup()
        super().closeEvent(event)

    def showEvent(self, event):
        """Uruchamia się automatycznie w ułamku sekundy po fizycznym wyświetleniu okna na ekranie."""
        super().showEvent(event)
        QTimer.singleShot(300, self.check_avrdude_version)
        QTimer.singleShot(500, self.autodetect_programmer)
        QTimer.singleShot(800, self.detect_mcu_signature)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AvrdudessNative()
    ex.show()
    sys.exit(app.exec())
