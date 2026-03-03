import customtkinter as ctk
from PIL import Image
import requests
from io import BytesIO
import threading
import time
from spotify_client import SpotifyClient # Import třídy z kroku 2

# Nastavení vzhledu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") # Spotify barvy

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.client = SpotifyClient()
        
        self.title("Můj Spotify Client")
        self.geometry("400x500")

        # 1. Obal Alba
        self.album_image = ctk.CTkLabel(self, text="") # Placeholder
        self.album_image.pack(pady=20)

        # 2. Název skladby a umělce
        self.track_label = ctk.CTkLabel(self, text="Loading...", font=("Arial", 20, "bold"))
        self.track_label.pack()
        
        self.artist_label = ctk.CTkLabel(self, text="", font=("Arial", 14))
        self.artist_label.pack(pady=(0, 20))

        # 3. Ovládací tlačítka (Frame)
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.pack()

        self.btn_prev = ctk.CTkButton(self.controls_frame, text="<<", width=50, command=self.client.prev_track)
        self.btn_prev.grid(row=0, column=0, padx=10)

        self.btn_play = ctk.CTkButton(self.controls_frame, text="Play/Pause", width=100, command=self.client.play_pause)
        self.btn_play.grid(row=0, column=1, padx=10)

        self.btn_next = ctk.CTkButton(self.controls_frame, text=">>", width=50, command=self.client.next_track)
        self.btn_next.grid(row=0, column=2, padx=10)

        # Spuštění vlákna pro aktualizaci UI
        self.update_loop()

    def update_ui(self):
        """Tato funkce běží každou sekundu a ptá se Spotify, co hraje"""
        data = self.client.get_current_track()
        
        if data:
            self.track_label.configure(text=data['name'])
            self.artist_label.configure(text=data['artist'])
            self.btn_play.configure(text="Pause" if data['is_playing'] else "Play")
            
            # Načítání obrázku (pokročilejší by bylo cachovat ho)
            # Zde je to zjednodušené:
            # V reálné appce bys kontroloval, jestli se obrázek změnil, abys ho nestahoval pořád dokola.
            pass 
        else:
            self.track_label.configure(text="Spotify nehraje")

        self.after(1000, self.update_ui) # Zavolá se znovu za 1000ms

    def update_loop(self):
        self.update_ui()

if __name__ == "__main__":
    app = App()
    app.mainloop()