import subprocess
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

#udelej vypnuti


class spotify_process():
    def __init__(self):
        global librespot_process
        librespot_process = None
    
    def start_libre(self,name):
        try:
            cwd = os.getcwd()
            env_path = os.path.join(cwd, "backend",".env")

            load_dotenv(env_path)
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            librespot_process = subprocess.Popen(
                [os.path.join(cwd,"spotify_agent", "librespot.exe"), "-n", name, "-b", "320"],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW 
            )

            # Chvíli počkáme, než se přehrávač probudí a připojí k síti
            time.sleep(4)
            print("Spotify running")
            


            # --- 2. OVLÁDÁNÍ PŘES SPOTIFY API ---
            # Tady bys měl své údaje ze Spotify For Developers
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                scope="user-modify-playback-state user-read-playback-state"
            ))

            # --- 3. UKONČENÍ ---

            # Když se tvůj Python skript vypíná, musí zabít i ten librespot na pozadí
            #player_process.terminate()
            #print("Přehrávač byl bezpečně vypnut.")
        except Exception as e:
            print(f"Failed to start librespot: {e}")

    def cleanup():
        """Kills the background process when the app closes."""
        global librespot_process
        if librespot_process:
            print("Stopping Librespot...")
            librespot_process.terminate()
            librespot_process = None


if __name__ == "__main__":
    sp = spotify_process()
    sp.start_libre("Test")
    input("Stiskni Enter pro ukončení programu...\n")
    

