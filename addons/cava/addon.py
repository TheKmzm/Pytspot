import os
import platform
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QProcess # Zásadní import pro běh procesů v Qt

class CavaAddon:
    def __init__(self, main_app):
        self.app = main_app
        self.name = "Cava Visualizer"
        self.icon = "📊"
        self.cava_exe = os.path.join("addons", "cava", "cava_win", "cava.exe")
        self.config_file = os.path.join("addons", "cava", "config.txt")
        
        # Zde budeme držet referenci na běžící proces
        self.cava_process = None

    def on_click(self):
        """Launches the Cava audio visualizer."""
        system = platform.system()
        
        if system == "Windows":
            # Zabráníme vícenásobnému spuštění, pokud už uživatel na tlačítko kliknul
            if self.cava_process is not None and self.cava_process.state() == QProcess.ProcessState.Running:
                print("Cava už běží!")
                return

            try:
                # Vytvoření asynchronního procesu v rámci Qt
                self.cava_process = QProcess(self.app) 
                
                # Propojíme signál "mám nová data" s naší funkcí
                self.cava_process.readyReadStandardOutput.connect(self.handle_stdout)
                
                # Nastavíme cestu a argumenty
                self.cava_process.setProgram(self.cava_exe)
                self.cava_process.setArguments(["-p", self.config_file])
                
                # Spustíme proces (bez blokování GUI!)
                self.cava_process.start()
                print("Cava byla spuštěna na pozadí.")

            except Exception as e:
                self.show_error(f"Failed to launch Cava:\n{e}")
                
        elif system == "Linux":
            print("Linux zatím není nastavený")

    def handle_stdout(self):
        """
        Tato funkce se zavolá automaticky (tzv. slot), 
        kdykoliv Cava vygeneruje nový řádek dat do konzole.
        """
        if not self.cava_process:
            return

        # Přečteme všechny dostupné řádky z bufferu (rychlé a neblokující)
        while self.cava_process.canReadLine():
            # Načtení řádku, převedení z bajtů na string a odstranění bílých znaků
            line = self.cava_process.readLine().data().decode('utf-8').strip()
            
            # Zahození posledního prázdného prvku
            raw_values = line.split(';')[:-1]
            if not raw_values:
                continue
            
            try:
                # Převod na čísla
                bars = [int(val) for val in raw_values]
                
                # Tady jsou tvá data! Tisknou se, zatímco GUI plně reaguje.
                print(bars)
                
                # TODO: Zde můžeš data poslat do svého kreslícího widgetu
                # Například: self.app.vykresli_sloupce(bars)

            except ValueError:
                # Pokud by Cava vypsala něco nečekaného (třeba error hlášku), ignorujeme to
                pass

    def show_error(self, message):
        msg = QMessageBox(self.app)
        msg.setWindowTitle("Cava Visualizer Error")
        msg.setText(message)
        msg.setStyleSheet("background-color: #222; color: white;")
        msg.exec()

def setup_addon(main_app):
    return CavaAddon(main_app)