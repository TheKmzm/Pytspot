import os
import time
import wave
import pyaudio
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from backend.core import SpotifyClient

# --- KONFIGURACE ---
# Získej klíč zde: https://
# aistudio.google.com/app/apikey
os.environ["GOOGLE_API_KEY"] = "AIzaSyAqY06rk5ClDMvvUqku9raUBo8Z-DWLlB8"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class SpotifyVoiceAssistant:
    def __init__(self):
        print("Initializuji Spotify Clienta...")
        self.spotify = SpotifyClient()
        
        # Definice nástrojů pro Gemini (aby věděl, co umí ovládat)
        self.tools_map = {
            'play_pause': self.spotify.play_pause,
            'next_track': self.spotify.next_track,
            'previous_track': self.spotify.previous_track,
            'get_current_song': self.print_current_song,
            'set_volume': self.spotify.set_volume,
            'search_and_play': self.search_logic
        }
        
        # Inicializace modelu s nástroji
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            tools=[self.tools_map.values()] # Automaticky převede funkce na definice nástrojů
        )

        # Chat session (aby si pamatoval kontext)
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    def print_current_song(self):
        """Zjistí, co právě hraje a vypíše to."""
        info = self.spotify.get_current_song_info()
        if info:
            return f"Právě hraje: {info['name']} od {info['artist']}"
        return "Nic nehraje."

    def search_logic(self, query: str):
        """Vyhledá písničku a spustí první výsledek."""
        print(f"Hledám: {query}...")
        results = self.spotify.search(query, search_type='track', limit=1)
        if results:
            track = results[0]
            print(f"Spouštím: {track['name']} - {track['artist']}")
            self.spotify.play_uri(track['uri'])
            return f"Přehrávám {track['name']}"
        return "Nic jsem nenašel."

    def record_audio(self, filename="command.wav", duration=4):
        """Nahraje krátký audio klip z mikrofonu."""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        print(f"🎤 MLUV TEĎ ({duration}s)... (Např: 'Pusť Taylor Swift' nebo 'Další písnička')")
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
            
        print("🛑 Nahrávání ukončeno.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return filename

    def listen_and_act(self):
        # 1. Nahrát hlas
        audio_file = self.record_audio()
        
        # 2. Nahrát soubor do Gemini API (dočasně)
        print("Odesílám audio do Gemini...")
        uploaded_file = genai.upload_file(path=audio_file)
        
        # Čekání na zpracování souboru (u audia je to bleskové, ale pro jistotu)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(0.5)
            uploaded_file = genai.get_file(uploaded_file.name)

        # 3. Poslat prompt s audiem
        # Gemini pochopí audio a samo zavolá Python funkci díky 'enable_automatic_function_calling'
        response = self.chat.send_message([
            "Jsi hlasový asistent pro Spotify. Poslouchej audio příkaz a vykonej příslušnou akci.",
            "Pokud uživatel chce pustit interpreta nebo písničku, použij 'search_and_play'.",
            "Mluv česky.",
            uploaded_file
        ])
        
        # 4. Výsledek
        print(f"🤖 Gemini: {response.text}")

if __name__ == "__main__":
    assistant = SpotifyVoiceAssistant()
    
    while True:
        input("\nStiskni ENTER pro nahrávání příkazu (nebo Ctrl+C pro konec)...")
        assistant.listen_and_act()