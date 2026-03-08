import subprocess
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()
# --- 1. SPUŠTĚNÍ PŘEHRÁVAČE NA POZADÍ ---
print("Startuji neviditelný přehrávač...")

# Parametr CREATE_NO_WINDOW zajistí, že se na Windows neukáže žádné černé okno!
# Přikazujeme mu jméno zařízení a bitrate 320kbps.
# Můžeš přidat i parametry pro přihlášení jménem a heslem (pomocí -u a -p), pokud to chceš mít natvrdo.
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

player_process = subprocess.Popen(
    ["librespot.exe", "-n", "Moje Super Aplikace", "-b", "320"],
    startupinfo=startupinfo,
    creationflags=subprocess.CREATE_NO_WINDOW 
)

# Chvíli počkáme, než se přehrávač probudí a připojí k síti
time.sleep(4)
print("Přehrávač běží na pozadí!")

# --- 2. OVLÁDÁNÍ PŘES SPOTIFY API ---
# Tady bys měl své údaje ze Spotify For Developers
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state"
))

# Najdeme náš neviditelný přehrávač a pustíme hudbu
devices = sp.devices()
for d in devices['devices']:
    if d['name'] == 'Moje Super Aplikace':
        print("Přehrávač nalezen, pouštím hudbu!")
        # Příklad: Spustí přehrávání (pokud už má něco v queue) nebo pustí konkrétní album/playlist
        # sp.start_playback(device_id=d['id'], context_uri="spotify:album:1Je1IMUlBXcx1Fz0WE7oPT")
        break

# --- 3. UKONČENÍ ---
input("Stiskni Enter pro ukončení programu...\n")

# Když se tvůj Python skript vypíná, musí zabít i ten librespot na pozadí
player_process.terminate()
print("Přehrávač byl bezpečně vypnut.")