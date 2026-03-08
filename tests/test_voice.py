import speech_recognition as sr
import ollama
import json
import sys
import warnings
import time

# Potlačení warningů
warnings.filterwarnings("ignore")

# Tvůj backend
from backend.core import SpotifyClient

# Barvy
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

class SmartBrain:
    def __init__(self):
        print(f"{BLUE}[INIT] Načítám Llama 3.2...{RESET}")
        self.model = "llama3.2"

    def think(self, user_text):
        """
        Analyzuje text až poté, co bylo detekováno klíčové slovo.
        """
        system_prompt = """
        You are an AI converting voice commands for Spotify into JSON.
        
        STRICT RULES:
        1. Return ONLY JSON.
        2. If command is nonsense -> {"action": "ignore"}
        
        MAPPING:
        - "další", "next", "skip" -> {"action": "next"}
        - "předchozí", "back", "prev" -> {"action": "prev"}
        - "stop", "pause", "ticho" -> {"action": "pause"}
        - "hraj", "resume", "pokračuj" -> {"action": "resume"}
        - "volume [N]", "hlasitost [N]" -> {"action": "volume", "level": N}
        - "pusť [X]", "play [X]" -> {"action": "play", "query": "[X]", "type": "track"}
        """
        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_text},
            ], format='json')
            return json.loads(response['message']['content'])
        except:
            return None

def execute_command(client, cmd):
    """Vykoná příkaz (stejné jako předtím)."""
    if not cmd: return
    action = cmd.get('action')

    if action == 'ignore': return

    print(f"{MAGENTA}⚡ AKCE: {action.upper()}{RESET}")

    try:
        if action == 'play':
            print(f"🔍 Hledám: {cmd.get('query')}")
            res = client.search(cmd.get('query'), limit=1)
            if res:
                client.play_uri(res[0]['uri'])
                print(f"▶ Hraji: {res[0]['name']}")
        
        elif action == 'pause': client.pause_playback()
        elif action == 'resume': client.start_playback()
        elif action == 'next': client.next_track()
        elif action == 'prev': client.previous_track()
        elif action == 'volume': client.set_volume(cmd.get('level'))

    except Exception as e:
        print(f"{RED}Chyba: {e}{RESET}")

def main_loop():
    # 1. Start Spotify
    try:
        print("Připojuji Spotify...")
        client = SpotifyClient()
    except:
        print("Spotify chyba."); sys.exit(1)

    # 2. Start AI
    brain = SmartBrain()
    
    # 3. Nastavení mikrofonu
    r = sr.Recognizer()
    # Whisper potřebuje trochu vyšší citlivost
    r.energy_threshold = 300 
    r.dynamic_energy_threshold = True
    
    # Použijeme model "small" (nebo "base" pro rychlost)
    WHISPER_MODEL = "small" 

    print(f"\n{GREEN}🟢 PŘIPRAVEN! Řekni 'Spotify [příkaz]'{RESET}")
    print(f"{GREEN}   Např: 'Spotify, pusť Rammstein' nebo 'Spotify další'{RESET}\n")

    with sr.Microphone() as source:
        # Rychlá kalibrace šumu na začátku
        r.adjust_for_ambient_noise(source, duration=1)
        
        while True:
            try:
                # Posloucháme...
                print(f"{BLUE}👂 Poslouchám...{RESET}", end="\r")
                
                # phrase_time_limit=5: Po 5 vteřinách mluvení to utne (aby se nezasekl)
                # timeout=1: Čeká 1s na začátek řeči, jinak zkusí znova (to drží smyčku živou)
                try:
                    audio = r.listen(source, timeout=2, phrase_time_limit=6)
                except sr.WaitTimeoutError:
                    continue # Nikdo nic neřekl, jedeme dál

                # Máme zvuk -> Whisper
                # print(f"{YELLOW}🧠 Zpracovávám...   {RESET}", end="\r")
                text = r.recognize_whisper(audio, model=WHISPER_MODEL).strip()
                
                # Pokud je text prázdný nebo jen šum
                if not text or len(text) < 4: continue

                # --- HLAVNÍ TRIK: WAKE WORD DETEKCE ---
                # Převedeme na malá písmena a odstraníme interpunkci
                clean_text = text.lower().replace(".", "").replace(",", "").replace("!", "")
                
                # Zkontrolujeme, jestli věta obsahuje "spotify"
                if "spotify" in clean_text:
                    print(f"\n🗣️  Slyšel jsem: '{text}'")
                    
                    # Odstraníme slovo "spotify" z příkazu, abychom AI nepletli
                    # Např. "Spotify pusť hudbu" -> "pusť hudbu"
                    command_text = clean_text.replace("spotify", "").strip()
                    
                    if len(command_text) < 2:
                        print(f"{RED}⚠️ Řekl jsi jen 'Spotify', ale chybí příkaz.{RESET}")
                        continue

                    # Pošleme to mozku
                    cmd_json = brain.think(command_text)
                    execute_command(client, cmd_json)
                    
                    print(f"\n{GREEN}🟢 Čekám na další povel...{RESET}")
                
                else:
                    # Pokud jsi mluvil, ale neřekl "Spotify", ignorujeme to (nebo vypíšeme šedě)
                    # print(f"\033[90m(Ignorováno: {text})\033[0m", end="\r")
                    pass

            except KeyboardInterrupt:
                print("\nUkončuji...")
                break
            except Exception as e:
                # Občas Whisper spadne na divném zvuku, ignorujeme to
                continue

if __name__ == "__main__":
    main_loop()