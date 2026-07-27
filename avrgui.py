#!/usr/bin/env python3
# =========================================================================
#  Natywny GUI avrdude Linux v1.0-RC - Wersja Profesjonalna (Zintegrowana)
#  Licencja: GNU General Public License v3.0 (GPLv3)
# =========================================================================

#import im6.q16

import sys
import subprocess
import re
import os
import configparser
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QPushButton, QFileDialog, 
                             QTextEdit, QTabWidget, QLineEdit, QGroupBox, QFormLayout, QCheckBox)
from PyQt6.QtCore import QDir, QThread, pyqtSignal, Qt, QTimer

CONFIG_FILE = "gui_config.txt"
PINOUTS_FILE = "pinouts.txt"
LANG_DIR = "lang"

TXT = {
    "title": "Natywny GUI avrdude Linux v1.0-RC - Wersja Profesjonalna",
    "flash_box": "Pamięć FLASH",
    "eeprom_box": "Pamięć EEPROM",
    "browse": "Przeglądaj...",
    "write": "Zapisz",
    "read": "Odczytaj (Kopia)",
    "no_file_hex": "Nie wybrano pliku .hex",
    "no_file_eep": "Nie wybrano pliku .hex/.eep",
    "err_no_file": "Błąd: Najpierw wybierz plik do zapisu!",
    "cancel": "🛑 ZATRZYMAJ!",
    "eg.. -B 8 or -F (write if You want)": "np. -B 8 lub -F (wpisać jeśli tylko jeśli naprawdę potrzeba",
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
    "bod_18": "Włączone (1.8V)"
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

PINOUTS = {}
def load_or_create_pinouts():
    global PINOUTS
    if not os.path.exists(PINOUTS_FILE):
        try:
            with open(PINOUTS_FILE, "w", encoding="utf-8") as f:
                f.write("=== atmega328p ===\n          ATmega328P (DIP-28)\n===\n=== attiny85 ===\n           ATtiny85 (DIP-8)\n===\n")
        except Exception: pass
    if os.path.exists(PINOUTS_FILE):
        try:
            with open(PINOUTS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                blocks = re.findall(r'===\s*([a-zA-Z0-9_\-]+)\s*===\n(.*?)(?=\n===|$)', content, re.DOTALL)
                for mcu_name, mcu_text in blocks:
                    PINOUTS[mcu_name.lower().strip()] = mcu_text.strip()
        except Exception: pass

load_or_create_pinouts()
class AvrdudeWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                line = self.process.stderr.readline()
                if not line: break
                self.output_signal.emit(line)
            self.process.wait()
            self.finished_signal.emit(self.process.returncode)
        except Exception as e:
            self.output_signal.emit(f"\nBłąd wątku: {str(e)}\n")
            self.finished_signal.emit(-1)

    def cancel(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.output_signal.emit("\n🛑 PROCES PRZERWANY PRZEZ UŻYTKOWNIKA!\n")

class AvrdudessNative(QWidget):
    def __init__(self):
        super().__init__()
        self.programmers = ['ch341a', 'usbasp', 'serialupdi', 'arduino', 'wiring']
        self.mcus = ['atmega328p', 'attiny85', 'attiny1614', 'atmega8']
        self.worker = None
        self.flash_path = ""
        self.eeprom_path = ""
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

    def get_system_ports(self):
        ports = ['Brak (USBasp / USB)', 'usb']
        try:
            dev_dir = QDir('/dev')
            for file in dev_dir.entryList(["ttyUSB*", "ttyACM*"], QDir.Filter.System):
                ports.append(f"/dev/{file}")
        except Exception: pass
        return ports

    def autodetect_programmer(self):
        self.console.append("Scanning USB devices...")
        prog, port = None, None
        try:
            res = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
            out = res.stdout.lower()
            if "16c0:05dc" in out or "usbasp" in out:
                prog, port = "usbasp", "usb"
            # INTELIGENTNY SKANER: Łapie Twoje ID sprzętu 1a86:5512 lub frazę ch341 niezależnie od wielkości liter
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
        if port:
            self.port_combo.setCurrentText(port)
            self.console.append(f"👉 Detected Port: {port}")
            
        self.prog_combo.blockSignals(False)
        self.port_combo.blockSignals(False)
        self.console.append("✅ Autodetect finished!\n")

    def detect_mcu_signature(self):
        cmd = ['avrdude', '-v', '-p', 'm328p', '-c', self.prog_combo.currentText().strip()]
        port = self.port_combo.currentText().strip()
        if 'Brak' not in port and port != '': cmd.extend(['-P', port])
        self.console.setText("Reading device signature...\n")
        self.run_async_cmd(cmd, is_mcu_detect=True)
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
        current_mcu = self.mcu_combo.currentText().lower().strip()
        if current_mcu in PINOUTS: self.pinout_text.setText(PINOUTS[current_mcu])

    def initUI(self):
        self.setWindowTitle(TXT["title"])
        self.setGeometry(5, 30, 1020, 700)
        main_layout = QVBoxLayout()
        
        hw_box = QGroupBox(TXT["hw_config"])
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
        btn_detect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 4px;")
        btn_detect.clicked.connect(self.autodetect_programmer)

        btn_detect_mcu = QPushButton(TXT["detect_mcu"])
        btn_detect_mcu.setStyleSheet("background-color: #0288d1; color: white; font-weight: bold; padding: 4px;")
        btn_detect_mcu.clicked.connect(self.detect_mcu_signature)
        
        btn_erase = QPushButton(TXT["chip_erase"])
        btn_erase.setStyleSheet("background-color: #e65100; color: white; font-weight: bold; padding: 4px;")
        btn_erase.clicked.connect(self.chip_erase)
        
        self.btn_cancel = QPushButton(TXT["cancel"])
        self.btn_cancel.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold; padding: 4px;")
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

        self.tabs = QTabWidget()
        self.tab_mem = QWidget()
        mem_layout = QVBoxLayout()
        
        flash_box = QGroupBox(TXT["flash_box"])
        f_lay = QHBoxLayout()
        self.flash_label = QLabel(TXT["no_file_hex"])
        btn_flash_file = QPushButton(TXT["browse"])
        btn_flash_file.clicked.connect(lambda: self.choose_file('flash'))
        self.btn_flash_write = QPushButton(TXT["write"])
        self.btn_flash_read = QPushButton(TXT["read"])
        self.btn_flash_write.clicked.connect(lambda: self.execute_mem('flash', 'w'))
        self.btn_flash_read.clicked.connect(lambda: self.execute_mem('flash', 'r'))
        f_lay.addWidget(btn_flash_file)
        f_lay.addWidget(self.flash_label)
        f_lay.addWidget(self.btn_flash_write)
        f_lay.addWidget(self.btn_flash_read)
        flash_box.setLayout(f_lay)
        mem_layout.addWidget(flash_box)
        
        eeprom_box = QGroupBox(TXT["eeprom_box"])
        e_lay = QHBoxLayout()
        self.eeprom_label = QLabel(TXT["no_file_eep"])
        btn_eep_file = QPushButton(TXT["browse"])
        btn_eep_file.clicked.connect(lambda: self.choose_file('eeprom'))
        self.btn_eep_write = QPushButton(TXT["write"])
        self.btn_eep_read = QPushButton(TXT["read"])
        self.btn_eep_write.clicked.connect(lambda: self.execute_mem('eeprom', 'w'))
        self.btn_eep_read.clicked.connect(lambda: self.execute_mem('eeprom', 'r'))
        e_lay.addWidget(btn_eep_file)
        e_lay.addWidget(self.eeprom_label)
        e_lay.addWidget(self.btn_eep_write)
        e_lay.addWidget(self.btn_eep_read)
        eeprom_box.setLayout(e_lay)
        mem_layout.addWidget(eeprom_box)
        self.tab_mem.setLayout(mem_layout)
        
        self.tab_pinout = QWidget()
        pin_lay = QVBoxLayout()
        self.pinout_text = QTextEdit()
        self.pinout_text.setReadOnly(True)
        self.pinout_text.setStyleSheet("background-color: #263238; color: #ffffff; font-family: monospace;")
        pin_lay.addWidget(self.pinout_text)
        self.tab_pinout.setLayout(pin_lay)
        self.tab_fuses = QWidget()
        fuse_layout = QVBoxLayout()
        fields_box = QGroupBox(TXT["hex_direct"])
        fields_lay = QFormLayout()
        self.fuse_l = QLineEdit("0xE2")
        self.fuse_h = QLineEdit("0xDA")
        self.fuse_e = QLineEdit("0xFD")
        self.fuse_lock = QLineEdit("0xFF")
        fields_lay.addRow(QLabel("Low Fuse:"), self.fuse_l)
        fields_lay.addRow(QLabel("High Fuse:"), self.fuse_h)
        fields_lay.addRow(QLabel("Ext Fuse:"), self.fuse_e)
        fields_lay.addRow(QLabel("Lock Bits:"), self.fuse_lock)
        fields_box.setLayout(fields_lay)
        fuse_layout.addWidget(fields_box)
        
        opts_box = QGroupBox(TXT["interactive_calc"])
        opts_lay = QFormLayout()
        self.verify_check = QCheckBox(TXT["verify_fuses"])
        self.verify_check.setChecked(True)
        opts_lay.addRow(self.verify_check)
        self.clock_combo = QComboBox()
        self.clock_combo.addItems([TXT["clk_internal_8"], TXT["clk_external_16"], TXT["clk_internal_1"]])
        self.clock_combo.currentIndexChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addRow(QLabel(TXT["clock_system"]), self.clock_combo)
        self.wd_check = QCheckBox(TXT["watchdog_label"])
        self.wd_check.stateChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addRow(self.wd_check)
        self.bod_combo = QComboBox()
        self.bod_combo.addItems([TXT["bod_disabled"], TXT["bod_27"], TXT["bod_43"], TXT["bod_18"]])
        self.bod_combo.currentIndexChanged.connect(self.recalc_fuses_from_gui)
        opts_lay.addRow(QLabel(TXT["bod_label"]), self.bod_combo)
        opts_box.setLayout(opts_lay)
        fuse_layout.addWidget(opts_box)
        
        btn_lay = QHBoxLayout()
        b_r = QPushButton(TXT["read"])
        b_w = QPushButton(TXT["write"])
        b_r.clicked.connect(self.read_fuses)
        b_w.clicked.connect(self.write_fuses)
        btn_lay.addWidget(b_r)
        btn_lay.addWidget(b_w)
        fuse_layout.addLayout(btn_lay)
        self.tab_fuses.setLayout(fuse_layout)
        
        self.tabs.addTab(self.tab_mem, TXT["mem_tab"])
        self.tabs.addTab(self.tab_pinout, TXT["pinout_tab"])
        self.tabs.addTab(self.tab_fuses, TXT["fuses_tab"])
        main_layout.addWidget(self.tabs)
        
        main_layout.addWidget(QLabel(TXT["console_title"]))
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #1a1a1a; color: #00ff66; font-family: monospace;")
        main_layout.addWidget(self.console)
        
        self.setLayout(main_layout)
        self.update_pinout_view()

    def choose_file(self, mem_type):
        fn, _ = QFileDialog.getOpenFileName(self, "Wybierz plik", "", "Intel HEX (*.hex *.eep)")
        if fn:
            if mem_type == 'flash':
                self.flash_path = fn
                self.flash_label.setText(fn.split('/')[-1])
            else:
                self.eeprom_path = fn
                self.eeprom_label.setText(fn.split('/')[-1])
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

    def run_async_cmd(self, cmd, is_fuse_read=False, is_mcu_detect=False):
        self.btn_cancel.setEnabled(True)
        try:
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
                self.worker.cancel()
                self.worker.wait()
        except RuntimeError: self.worker = None

        self.worker = AvrdudeWorker(cmd)
        self.worker.output_signal.connect(self.append_console_output)
        if is_fuse_read: self.worker.finished_signal.connect(self.on_fuse_read_finished)
        elif is_mcu_detect: self.worker.finished_signal.connect(self.on_mcu_detect_finished)
        else: self.worker.finished_signal.connect(self.on_cmd_finished)
        self.worker.start()

    def append_console_output(self, text):
        self.console.append(text.strip('\r\n'))

    def cancel_operation(self):
        try:
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning(): self.worker.cancel()
        except RuntimeError: pass

    def on_cmd_finished(self, returncode):
        self.btn_cancel.setEnabled(False)
        if returncode == 0: self.console.append("\n✅ SUCCESS!")
        else: self.console.append("\n❌ ERROR!")

    def on_fuse_read_finished(self, returncode):
        self.on_cmd_finished(returncode)
        if returncode == 0:
            hex_values = re.findall(r'0x[0-9a-fA-F]+', self.console.toPlainText())
            if len(hex_values) >= 4:
                self.fuse_l.setText(hex_values[0])
                self.fuse_h.setText(hex_values[1])
                self.fuse_e.setText(hex_values[2])
                self.fuse_lock.setText(hex_values[3])

    def on_mcu_detect_finished(self, returncode):
        self.btn_cancel.setEnabled(False)
        output = self.console.toPlainText()
        sig_match = re.search(r'Device signature\s*=\s*([0-9a-fA-F ]+)', output, re.IGNORECASE)
        if sig_match:
            clean_sig = sig_match.group(1).replace(" ", "").upper().strip()
            s_map = {"1E950F": "atmega328p", "1E930B": "attiny85", "1E9411": "attiny1614", "1E9307": "atmega8"}
            if clean_sig in s_map:
                self.mcu_combo.setCurrentText(s_map[clean_sig])
                self.console.append(f"\n✅ DETECTED: {s_map[clean_sig]}!")
                return
        self.console.append("\n❌ MCU auto-select failed.")

    def chip_erase(self):
        cmd = self.build_base_cmd()
        cmd.append('-e')
        self.run_async_cmd(cmd)

    def recalc_fuses_from_gui(self):
        lfuse, hfuse, efuse = 0xE2, 0xDA, 0xFD
        if self.clock_combo.currentIndex() == 1: lfuse = 0xFF
        elif self.clock_combo.currentIndex() == 2: lfuse = 0x62
        if self.wd_check.isChecked(): hfuse &= ~(1 << 4)
        else: hfuse |= (1 << 4)
        if self.bod_combo.currentIndex() == 1: efuse = 0xFC
        elif self.bod_combo.currentIndex() == 2: efuse = 0xF9
        elif self.bod_combo.currentIndex() == 3: efuse = 0xFE
        self.fuse_l.setText(f"0x{lfuse:02X}")
        self.fuse_h.setText(f"0x{hfuse:02X}")
        self.fuse_e.setText(f"0x{efuse:02X}")

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

    def read_fuses(self):
        cmd = self.build_base_cmd()
        cmd.extend(['-U', 'lfuse:r:-:h', '-U', 'hfuse:r:-:h', '-U', 'efuse:r:-:h', '-U', 'lock:r:-:h'])
        self.run_async_cmd(cmd, is_fuse_read=True)

    def write_fuses(self):
        cmd = self.build_base_cmd()
        cmd.extend(['-U', f'lfuse:w:{self.fuse_l.text()}:m', '-U', f'hfuse:w:{self.fuse_h.text()}:m', '-U', f'efuse:w:{self.fuse_e.text()}:m', '-U', f'lock:w:{self.fuse_lock.text()}:m'])
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
