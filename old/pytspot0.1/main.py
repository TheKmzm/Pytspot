import customtkinter as ctk
import tkinter as tk 
from service import SpotifyService
from components import Sidebar, PlayerControl, BrowserTab, LyricsPanel
from utils import load_image_async
import threading

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spotify Browser Pro")
        self.geometry("1200x800")

        # --- KONFIGURACE SLUŽEB ---
        self.service = SpotifyService(
            spotify_id="59a0e2f913c5478ca49df9529b8f8687",
            spotify_secret="ceba348353234a55bd0af9ebaeacc704",
            genius_id="TxXcaRBdbYEh492LG8-pvPy8WXI4k4vxnRaBO_roEDcqFL0yR6uIA3iqWX_Oe76C",
            genius_secret="bFjHHozm519ef_Uvhlfy9I5lVqm33R7DuopSk4zsENJFDjbNIB8DQAGgx9iFVZL8IznnVgqdjrFaofOCxFTTiQ"
        )
        
        self.last_cover_url = None
        self.current_track_id = None 
        self.current_features = None 
        self.user_playlists = [] 

        # Klávesové zkratky
        self.bind("<space>", self.on_key_space)
        self.bind("<Control-Right>", lambda e: self.service.control('next'))
        self.bind("<Control-Left>", lambda e: self.service.control('prev'))

        # --- GRID ---
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0) 
        self.grid_rowconfigure(0, weight=1)    
        self.grid_rowconfigure(1, weight=0)    

        # 1. Sidebar
        self.sidebar = Sidebar(self, 
                               on_playlist_click=self.on_sidebar_playlist_click, 
                               on_search=self.on_sidebar_search, 
                               on_playlist_right_click=self.on_sidebar_playlist_right_click,
                               on_open_visualizer=self.on_sidebar_open_visualizer,
                               width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 2. TabView
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # 3. Lyrics Panel
        self.lyrics_panel = LyricsPanel(self, width=300)
        self.lyrics_visible = False
        
        # Ovládací tlačítka karet
        self.btn_close = ctk.CTkButton(self.tab_view, text="×", width=30, height=30,
                                       fg_color="#D32F2F", hover_color="#B71C1C",
                                       font=("Arial", 16, "bold"),
                                       command=lambda: self.close_active_tab())
        self.btn_close.place(relx=1.0, x=-40, y=5, anchor="ne")

        self.btn_plus = ctk.CTkButton(self.tab_view, text="+", width=30, height=30,
                                      fg_color="#1DB954", hover_color="#1aa34a",
                                      font=("Arial", 16, "bold"),
                                      command=lambda: self.add_new_tab())
        self.btn_plus.place(relx=1.0, x=-5, y=5, anchor="ne")

        self.tabs_content = {} 
        self.tab_count = 0

        self.add_new_tab("Domů")

        # 4. Player
        cmds = {
            'prev': lambda: self.service.control('prev'),
            'next': lambda: self.service.control('next'),
            'play_pause': self.toggle_play,
            'shuffle': lambda state: self.service.control('shuffle', state=state),
            'set_volume': lambda val: self.service.set_volume(val),
            'set_device': lambda dev_id: self.service.transfer_playback(dev_id),
            'queue': self.open_queue,
            'lyrics': self.toggle_lyrics
        }
        self.player = PlayerControl(self, callbacks=cmds, height=120, fg_color="#222")
        self.player.grid(row=1, column=0, columnspan=3, sticky="ew")

        # Načtení dat
        self.user_playlists = self.service.get_playlists()
        self.sidebar.load_data(self.user_playlists)
        self.refresh_devices()
        
        # Spuštění hlavní smyčky
        self.update_loop()

    # --- HANDLERY ---

    def on_key_space(self, event):
        widget = self.focus_get()
        if not isinstance(widget, (ctk.CTkEntry, tk.Entry, ctk.CTkTextbox)):
            self.toggle_play()

    def show_context_menu(self, item, event):
        if not event: return
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="▶ Přehrát", command=lambda: self.play_from_menu(item))
        
        if item.get('type') != 'track':
            menu.add_command(label="Otevřít v nové kartě", command=lambda: self.open_item_in_new_tab(item))
        
        menu.add_separator()
        
        if item.get('type') == 'track':
            menu.add_command(label="Přidat do fronty", command=lambda: self.add_to_queue_callback(item['uri']))
            playlist_menu = tk.Menu(menu, tearoff=0)
            for pl in self.user_playlists:
                playlist_menu.add_command(label=pl['name'], 
                                          command=lambda pid=pl['id'], uri=item['uri']: self.add_to_playlist(pid, uri))
            menu.add_cascade(label="Přidat do playlistu...", menu=playlist_menu)

        menu.tk_popup(event.x_root, event.y_root)

    def play_from_menu(self, item):
        itype = item.get('type', 'track')
        if itype == 'track':
            self.service.control('play_single_track', track_uri=item['uri'])
        elif itype == 'playlist' or itype == 'album':
            self.service.control('play_context', context_uri=item['uri'])

    def add_to_playlist(self, playlist_id, track_uri):
        threading.Thread(target=self.service.add_track_to_playlist, args=(playlist_id, track_uri), daemon=True).start()

    def toggle_lyrics(self):
        if self.lyrics_visible:
            self.lyrics_panel.grid_forget()
            self.lyrics_visible = False
        else:
            self.lyrics_panel.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
            self.lyrics_visible = True
            if self.current_track_id:
                data = self.service.get_playback_state()
                if data:
                    self.fetch_lyrics(data['name'], data['artist'])

    def fetch_audio_analysis(self, track_id):
        def thread():
            feats = self.service.get_audio_features(track_id)
            self.current_features = feats
        threading.Thread(target=thread, daemon=True).start()

    def fetch_lyrics(self, track_name, artist_name):
        self.lyrics_panel.set_text(f"Hledám text pro:\n{track_name} - {artist_name}...")
        def thread():
            lyrics = self.service.get_lyrics(track_name, artist_name)
            self.lyrics_panel.set_text(lyrics)
        threading.Thread(target=thread, daemon=True).start()

    def add_new_tab(self, title=None):
        self.tab_count += 1
        if not title: title = f"Karta {self.tab_count}"
        if title in self.tabs_content: title = f"{title} ({self.tab_count})"

        self.tab_view.add(title)
        self.tab_view.set(title)
        
        tab_frame = self.tab_view.tab(title)
        
        browser_tab = BrowserTab(tab_frame, 
                                 service=self.service, 
                                 player_callback=self.global_play_callback,
                                 image_loader=load_image_async,
                                 rename_callback=self.rename_active_tab,
                                 open_new_tab_callback=self.show_context_menu, 
                                 add_queue_callback=self.add_to_queue_callback)
        browser_tab.pack(fill="both", expand=True)
        self.tabs_content[title] = browser_tab
        self.lift_buttons()
        return browser_tab

    def add_to_queue_callback(self, uri):
        threading.Thread(target=self.service.add_to_queue, args=(uri,), daemon=True).start()

    def open_item_in_new_tab(self, item):
        itype = item.get('type', 'track')
        if itype == 'artist':
            new_tab = self.add_new_tab(item['name'])
            new_tab.go_to_artist_page({'artist_id': item['id'], 'artist': item['name']})
        elif itype == 'playlist':
            new_tab = self.add_new_tab(item['name'])
            new_tab.load_playlist({'id': item['id'], 'uri': item['uri'], 'name': item['name']})
        elif itype == 'album':
            new_tab = self.add_new_tab(item['name'])
            new_tab.load_album({'id': item['id'], 'uri': item['uri'], 'name': item['name']})

    def close_active_tab(self):
        try:
            if len(self.tabs_content) <= 1: return
            active_name = self.tab_view.get()
            if active_name in self.tabs_content: del self.tabs_content[active_name]
            self.tab_view.delete(active_name)
            self.lift_buttons()
        except: pass

    def replace_active_tab(self, new_name):
        try:
            old_name = self.tab_view.get()
            if old_name == new_name: return self.tabs_content[old_name]
            if len(new_name) > 20: new_name = new_name[:18] + "..."
            new_browser = self.add_new_tab(new_name)
            if old_name in self.tabs_content: del self.tabs_content[old_name]
            self.tab_view.delete(old_name)
            return new_browser
        except: return None

    def rename_active_tab(self, new_name):
        try:
            old_name = self.tab_view.get()
            if old_name == new_name: return
            old_browser = self.tabs_content.get(old_name)
            state = None
            if old_browser and hasattr(old_browser, 'save_state'):
                state = old_browser.save_state()
            new_browser = self.replace_active_tab(new_name)
            if new_browser and state: new_browser.load_state(state)
        except: pass

    def lift_buttons(self):
        self.btn_plus.lift()
        self.btn_close.lift()

    def get_active_tab(self):
        try:
            active_name = self.tab_view.get()
            return self.tabs_content.get(active_name)
        except: return None

    def open_queue(self):
        active_tab = self.get_active_tab()
        if active_tab: active_tab.load_queue()

    def on_sidebar_playlist_click(self, playlist_data):
        new_browser = self.replace_active_tab(playlist_data['name'])
        if new_browser: new_browser.load_playlist(playlist_data)

    def on_sidebar_playlist_right_click(self, playlist_data, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Otevřít v nové kartě", 
                         command=lambda: self.open_item_in_new_tab({'type': 'playlist', 'id': playlist_data['id'], 'uri': playlist_data['uri'], 'name': playlist_data['name']}))
        menu.tk_popup(event.x_root, event.y_root)
    
    def on_sidebar_search(self, query, search_type="track"):
        icon = "🎵" if search_type == "track" else "👤" if search_type == "artist" else "📜"
        label = f"{icon} {query}"
        new_browser = self.replace_active_tab(label)
        if new_browser: new_browser.search(query, search_type)

    def on_sidebar_open_visualizer(self):
        new_browser = self.replace_active_tab("Vizualizér")
        if new_browser: new_browser.load_visualizer()

    def global_play_callback(self, track_uri, context_uri):
        if track_uri is None and context_uri:
             self.service.control('play_context', context_uri=context_uri)
        elif context_uri:
            self.service.control('play_track_in_context', context_uri=context_uri, track_uri=track_uri)
        else:
            self.service.control('play_single_track', track_uri=track_uri)

    def toggle_play(self):
        data = self.service.get_playback_state()
        if data: self.service.control('play_pause', is_playing=data['is_playing'])

    def refresh_devices(self, current_device_id=None):
        devices = self.service.get_devices()
        self.player.update_devices(devices, current_device_id)

    # --- OPTIMALIZOVANÁ SMYČKA (ZDE BYLA CHYBA) ---
    def update_loop(self):
        next_check = 1000
        
        data = self.service.get_playback_state()
        if data:
            self.title(f"{data['name']} • {data['artist']} | Spotify Pro")

            track_id = data.get('id')
            if track_id and track_id != self.current_track_id:
                self.current_track_id = track_id
                self.current_features = None 
                self.fetch_audio_analysis(track_id)
                if self.lyrics_visible:
                    self.fetch_lyrics(data['name'], data['artist'])

            self.player.update_info(data, self.current_features)
            
            if data['cover_url'] != self.last_cover_url:
                self.last_cover_url = data['cover_url']
                load_image_async(data['cover_url'], (80, 80), self.player.set_cover)
            self.refresh_devices(data.get('device_id'))

            # Pokud nehraje hudba, zpomalíme refresh
            if not data['is_playing']:
                next_check = 4000
        else:
            self.title("Spotify Browser Pro")
            next_check = 5000
        
        self.after(next_check, self.update_loop)

if __name__ == "__main__":
    app = App()
    app.mainloop()