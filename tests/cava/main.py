import os
import subprocess

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

cava_exe = os.path.join("tests", "cava", "cava_win", "cava.exe")
config_file = os.path.join("tests", "cava", "config.txt")

cava_process = subprocess.Popen(
    [cava_exe, "-p", config_file],
    startupinfo=startupinfo,
    creationflags=subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.PIPE,  # Klíčové: Zachytává výstup programu
    text=True                # Klíčové: Převádí bajty rovnou na text (string)
)

print("Poslouchám Cava stream... (Zastavíš pomocí Ctrl+C)")

try:
    # Nekonečná smyčka, která čte výstup řádek po řádku, jak ho Cava generuje
    for line in cava_process.stdout:
        # Odstranění mezer/odřádkování, rozdělení podle středníku a zahození posledního prázdného prvku
        raw_values = line.strip().split(';')[:-1]
        
        if not raw_values:
            continue
            
        # Převedení textových hodnot na celá čísla
        bars = [int(val) for val in raw_values]
        
        # Tady máš svoje pole čísel (výšky sloupců) připravené k použití!
        print(bars) 

except KeyboardInterrupt:
    print("\nUkončuji...")
finally:
    # Je nesmírně důležité proces zabít, až skript skončí, 
    # jinak ti zůstane viset na pozadí ve Správci úloh!
    cava_process.kill()


