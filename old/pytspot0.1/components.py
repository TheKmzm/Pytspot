import customtkinter as ctk
import threading
import tkinter 
import random

# Barvy a helpery zůstávají stejné...
COLOR_ACCENT = "#3B8ED0"        
COLOR_ACCENT_HOVER = "#36719F"  
COLOR_BG_ITEM = "#2B2B2B"       
COLOR_BG_HOVER = "#3A3A3A"
COLOR_TEXT_MAIN = "white"
COLOR_TEXT_SUB = "#A0A0A0"

def format_ms(ms):
    if not ms: return "--:--"
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    return f"{minutes}:{seconds:02d}"

class Sidebar(ctk.CTkScrollableFrame):
    def __init__(self, master, on_playlist_click, on_search, on_playlist_right_click=None, on_open_visualizer=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_click = on_playlist_click
        self.on_right_click = on_playlist_right_click
        self.on_search_callback = on_search
        self.on_open_visualizer = on_open_visualizer
        self.buttons = []

        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", pady=(10, 10))
        
        self.entry = ctk.CTkEntry(self.search_frame, placeholder_text="Hledat...", 
                                  border_width=0, fg_color="#333333", corner_radius=15)
        self.entry.pack(fill="x", padx=10, pady=(0, 5), ipady=3)
        self.entry.bind("<Return>", lambda event: self.perform_search())
        
        self.filter_frame = ctk.CTkFrame(self.search_frame, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=10)
        
        self.search_type_var = ctk.StringVar(value="track") 
        self.type_menu = ctk.CTkOptionMenu(self.filter_frame, 
                                           variable=self.search_type_var,
                                           values=["track", "artist", "playlist", "album"],
                                           width=100,
                                           fg_color="#333333",
                                           button_color="#444444",
                                           button_hover_color="#555555",
                                           corner_radius=10)
        self.type_menu.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_search = ctk.CTkButton(self.filter_frame, text="🔍", width=35, 
                                        fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                                        corner_radius=10,
                                        command=self.perform_search)
        self.btn_search.pack(side="right")
        
        ctk.CTkFrame(self, height=2, fg_color="#333").pack(fill="x", pady=10, padx=10)
        
        self.lbl_library = ctk.CTkLabel(self, text="MOJE KNIHOVNA", font=("Arial", 12, "bold"), text_color=COLOR_TEXT_SUB, anchor="w")
        self.lbl_library.pack(fill="x", padx=15, pady=(5, 5))

        if self.on_open_visualizer:
            self.btn_viz = ctk.CTkButton(self, text="ılıll| Vizualizér |llılı", height=35, anchor="w",
                                         fg_color="transparent", hover_color=COLOR_BG_HOVER,
                                         corner_radius=5, font=("Arial", 13, "bold"), text_color=COLOR_ACCENT,
                                         command=self.on_open_visualizer)
            self.btn_viz.pack(fill="x", pady=1, padx=5)

    def perform_search(self):
        query = self.entry.get()
        search_type = self.search_type_var.get()
        if query: self.on_search_callback(query, search_type)

    def load_data(self, playlists):
        for btn in self.buttons: btn.destroy()
        self.buttons = []
        for pl in playlists:
            btn = ctk.CTkButton(self, text=pl['name'], height=35, anchor="w", 
                                fg_color="transparent", hover_color=COLOR_BG_HOVER,
                                corner_radius=5, font=("Arial", 13),
                                command=lambda p=pl: self.on_click(p))
            
            if self.on_right_click:
                # Upraveno: předáváme i event
                btn.bind("<Button-3>", lambda event, p=pl: self.on_right_click(p, event))
                
            btn.pack(fill="x", pady=1, padx=5)
            self.buttons.append(btn)

class TrackList(ctk.CTkFrame):
    def __init__(self, master, on_item_click, on_artist_click=None, on_item_right_click=None, on_add_queue=None, label_text="", **kwargs):
        super().__init__(master, **kwargs)
        self.on_item_click = on_item_click 
        self.on_artist_click = on_artist_click
        self.on_item_right_click = on_item_right_click 
        self.on_add_queue = on_add_queue
        self.all_tracks_data = []
        self._rendering_task = None 

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=100)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        self.img_label = ctk.CTkLabel(self.header_frame, text="")
        
        self.info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.info_box.pack(side="left", padx=10, fill="y")
        
        self.title_lbl = ctk.CTkLabel(self.info_box, text=label_text, font=("Arial", 24, "bold"), anchor="w")
        self.title_lbl.pack(anchor="w")
        
        self.btn_play_context = ctk.CTkButton(self.info_box, text="▶ PŘEHRÁT", 
                                              width=100, height=30, corner_radius=15,
                                              fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                                              font=("Arial", 12, "bold"))
        
        self.loading_lbl = ctk.CTkLabel(self.header_frame, text="Načítám...", text_color=COLOR_ACCENT)
        
        self.filter_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Rychlý filtr...", width=200,
                                         border_width=0, fg_color="#2A2A2A", corner_radius=15)
        self.filter_entry.pack(side="right", padx=5, anchor="ne")
        self.filter_entry.bind("<KeyRelease>", self.on_filter_change)

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.track_widgets = []

    def show_play_button(self, command):
        self.btn_play_context.configure(command=command)
        self.btn_play_context.pack(anchor="w", pady=(5,0))

    def hide_play_button(self):
        self.btn_play_context.pack_forget()

    def set_header_image(self, url, image_loader):
        if url:
            self.img_label.pack(side="left", padx=(0, 15))
            image_loader(url, (80, 80), self._set_img_callback)
        else:
            self.hide_header_image()

    def _set_img_callback(self, img):
        if not self.winfo_exists(): return
        self.img_label.configure(image=img)
        self.img_label.image = img

    def hide_header_image(self):
        self.img_label.pack_forget()
        self.img_label.configure(image=None)

    def show_loading(self, show=True):
        if not self.winfo_exists(): return
        if show: self.loading_lbl.pack(side="right", padx=10)
        else: self.loading_lbl.pack_forget()

    def configure(self, **kwargs):
        if 'label_text' in kwargs:
            self.title_lbl.configure(text=kwargs.pop('label_text'))
        super().configure(**kwargs)

    def clear(self):
        if self._rendering_task:
            self.after_cancel(self._rendering_task)
            self._rendering_task = None

        self.all_tracks_data = []
        self.filter_entry.delete(0, 'end')
        for w in self.track_widgets: w.destroy()
        self.track_widgets = []

    def load_tracks(self, tracks):
        self.clear()
        self.add_tracks(tracks)

    def add_tracks(self, tracks):
        self.all_tracks_data.extend(tracks)
        query = self.filter_entry.get().lower()
        items_to_render = tracks
        if query:
            items_to_render = [t for t in tracks if query in t['name'].lower()]
        self._render_queue(items_to_render, 0)

    def on_filter_change(self, event):
        query = self.filter_entry.get().lower()
        if self._rendering_task:
            self.after_cancel(self._rendering_task)
            self._rendering_task = None

        for w in self.track_widgets: w.destroy()
        self.track_widgets = []

        if not query:
            self._render_queue(self.all_tracks_data, 0)
            return
        
        filtered = [t for t in self.all_tracks_data if query in t['name'].lower()]
        self._render_queue(filtered, 0)

    def _render_queue(self, items, start_index):
        if not self.winfo_exists(): return 
        BATCH_SIZE = 10 
        end_index = min(start_index + BATCH_SIZE, len(items))
        chunk = items[start_index:end_index]
        for item in chunk:
            self._create_row(item)
        if end_index < len(items):
            self._rendering_task = self.after(20, lambda: self._render_queue(items, end_index))
        else:
            self._rendering_task = None

    def _create_row(self, item):
        row = ctk.CTkFrame(self.scroll_area, fg_color="transparent", corner_radius=6)
        row.pack(fill="x", pady=2, padx=5)
        
        item_type = item.get('type', 'track')
        btn_main = None

        if item_type == 'track':
            bg_color = COLOR_ACCENT if item.get('is_current') else COLOR_BG_ITEM
            hover_col = COLOR_ACCENT_HOVER if item.get('is_current') else COLOR_BG_HOVER
            
            if self.on_add_queue:
                btn_q = ctk.CTkButton(row, text="+", width=25, height=25, 
                                      fg_color="transparent", hover_color=COLOR_BG_HOVER,
                                      text_color=COLOR_TEXT_SUB, font=("Arial", 16, "bold"),
                                      command=lambda t=item: self.on_add_queue(t['uri']))
                btn_q.pack(side="right", padx=(5, 5))

            if item.get('duration_ms'):
                lbl = ctk.CTkLabel(row, text=format_ms(item['duration_ms']), width=50, text_color=COLOR_TEXT_SUB, anchor="e", font=("Arial", 12))
                lbl.pack(side="right", padx=(5, 5))
            
            if self.on_artist_click and item.get('artist_id'):
                btn_art = ctk.CTkButton(row, text=item['artist'], width=120, 
                                        fg_color="transparent", hover_color=COLOR_BG_HOVER,
                                        text_color=COLOR_TEXT_SUB, anchor="w",
                                        font=("Arial", 12),
                                        command=lambda t=item: self.on_artist_click(t))
                if self.on_item_right_click:
                    artist_payload = {'type': 'artist', 'id': item['artist_id'], 'name': item['artist']}
                    # Předáváme EVENT
                    btn_art.bind("<Button-3>", lambda event, a=artist_payload: self.on_item_right_click(a, event))
                btn_art.pack(side="right", padx=5)

            btn_main = ctk.CTkButton(row, text=f"{item['name']}", anchor="w", 
                                     fg_color=bg_color, hover_color=hover_col,
                                     text_color=COLOR_TEXT_MAIN, corner_radius=6, height=35,
                                     font=("Arial", 13),
                                     command=lambda t=item: self.on_item_click(t))
            btn_main.pack(side="left", fill="x", expand=True)

        elif item_type == 'artist':
            lbl_fol = ctk.CTkLabel(row, text=f"{item.get('followers', 0):,} fans", width=100, text_color=COLOR_TEXT_SUB, anchor="e")
            lbl_fol.pack(side="right", padx=(5, 10))
            btn_main = ctk.CTkButton(row, text=f"👤 {item['name']}", anchor="w", 
                                     fg_color="#1E1E1E", hover_color="#252525",
                                     corner_radius=6, height=40, font=("Arial", 14, "bold"),
                                     command=lambda t=item: self.on_item_click(t))
            btn_main.pack(side="left", fill="x", expand=True)

        elif item_type == 'playlist':
            lbl_own = ctk.CTkLabel(row, text=f"od {item.get('owner', '')}", width=100, text_color=COLOR_TEXT_SUB, anchor="e")
            lbl_own.pack(side="right", padx=(5, 10))
            btn_main = ctk.CTkButton(row, text=f"📜 {item['name']}", anchor="w", 
                                     fg_color="#1E1E1E", hover_color="#252525",
                                     corner_radius=6, height=40, font=("Arial", 13),
                                     command=lambda t=item: self.on_item_click(t))
            btn_main.pack(side="left", fill="x", expand=True)

        elif item_type == 'album':
            lbl_year = ctk.CTkLabel(row, text=item.get('year', ''), width=60, text_color=COLOR_TEXT_SUB, anchor="e")
            lbl_year.pack(side="right", padx=(5, 10))
            btn_main = ctk.CTkButton(row, text=f"💿 {item['name']}", anchor="w", 
                                     fg_color="#1E1E1E", hover_color="#252525",
                                     corner_radius=6, height=40, font=("Arial", 13),
                                     command=lambda t=item: self.on_item_click(t))
            btn_main.pack(side="left", fill="x", expand=True)
        
        # --- BIND RIGHT CLICK WITH EVENT ---
        if btn_main and self.on_item_right_click:
            btn_main.bind("<Button-3>", lambda event, t=item: self.on_item_right_click(t, event))

        self.track_widgets.append(row)

class ArtistView(ctk.CTkFrame):
    def __init__(self, master, on_track_click, on_item_right_click=None, on_add_queue=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_track_click = on_track_click
        self.on_item_right_click = on_item_right_click
        self.on_add_queue = on_add_queue
        self.current_data = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self, fg_color="#181818", corner_radius=0, height=180)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.img_label = ctk.CTkLabel(self.header, text="")
        self.img_label.pack(side="left", padx=30, pady=20)
        
        self.info_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.info_frame.pack(side="left", fill="y", pady=20, padx=10)
        
        self.name_lbl = ctk.CTkLabel(self.info_frame, text="Artist", font=("Arial", 40, "bold"), anchor="w")
        self.name_lbl.pack(anchor="w")
        
        self.meta_lbl = ctk.CTkLabel(self.info_frame, text="...", text_color=COLOR_TEXT_SUB, font=("Arial", 14))
        self.meta_lbl.pack(anchor="w")

        self.content_list = TrackList(self, 
                                      on_item_click=self.on_track_click, 
                                      on_item_right_click=self.on_item_right_click, 
                                      on_add_queue=self.on_add_queue,
                                      label_text="Top Skladby & Alba")
        self.content_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(10,10))

    def load_artist(self, data, image_loader):
        self.current_data = data
        self.name_lbl.configure(text=data['name'])
        self.meta_lbl.configure(text=f"{data['followers']:,} sledujících • {data['genres']}")
        if data['image_url']: image_loader(data['image_url'], (140, 140), self.set_image)
        self.content_list.clear()
        self.content_list.add_tracks(data['top_tracks'])
        if data.get('albums'):
            self.content_list.add_tracks(data['albums'])

    def set_image(self, img):
        if not self.winfo_exists(): return
        self.img_label.configure(image=img)
        self.img_label.image = img

# ... VisualizerView (beze změn) ...
class VisualizerView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="black") 
        self.canvas = ctk.CTkCanvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bars = []
        self.num_bars = 40
        self.is_animating = False
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.create_bars()

    def create_bars(self):
        self.canvas.delete("all")
        self.bars = []
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10: return
        bar_width = w / self.num_bars
        for i in range(self.num_bars):
            x0 = i * bar_width + 2
            x1 = (i + 1) * bar_width - 2
            y0 = h 
            y1 = h - 10 
            color = self.get_color(i, self.num_bars)
            bar_id = self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            self.bars.append(bar_id)

    def get_color(self, index, total):
        r = int(59 + (200 * (index / total)))
        g = 142
        b = 208
        r = min(255, max(0, r))
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_animation(self):
        if not self.is_animating:
            self.is_animating = True
            self.animate()

    def stop_animation(self):
        self.is_animating = False

    def animate(self):
        if not self.is_animating: return
        if not self.winfo_exists(): return 
        
        h = self.winfo_height()
        if h < 50: 
            self.after(100, self.animate)
            return

        for bar_id in self.bars:
            val = random.randint(10, int(h * 0.8))
            coords = self.canvas.coords(bar_id)
            if coords:
                x0, y0, x1, y1 = coords
                self.canvas.coords(bar_id, x0, h, x1, h - val)

        self.after(80, self.animate)

class LyricsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#181818") # Tmavé pozadí
        
        self.lbl_title = ctk.CTkLabel(self, text="Text Písně", font=("Arial", 18, "bold"))
        self.lbl_title.pack(pady=(20, 10), padx=10)
        
        self.textbox = ctk.CTkTextbox(self, font=("Arial", 14), text_color="#CCCCCC", fg_color="transparent")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
    def set_text(self, text):
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", text)

class PlayerControl(ctk.CTkFrame):
    def __init__(self, master, callbacks, **kwargs):
        super().__init__(master, **kwargs)
        self.callbacks = callbacks
        self.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0) 
        self.grid_columnconfigure(3, weight=0) 
        self.grid_columnconfigure(4, weight=0) 

        self.cover = ctk.CTkLabel(self, text="")
        self.cover.grid(row=0, column=0, rowspan=3, padx=15, pady=5)

        self.title_lbl = ctk.CTkLabel(self, text="---", font=("Arial", 15, "bold"))
        self.title_lbl.grid(row=0, column=1, sticky="sw", padx=10)
        self.artist_lbl = ctk.CTkLabel(self, text="---", font=("Arial", 12), text_color=COLOR_TEXT_SUB)
        self.artist_lbl.grid(row=1, column=1, sticky="nw", padx=10)
        
        self.features_lbl = ctk.CTkLabel(self, text="", font=("Arial", 11), text_color="#55AAAA")
        self.features_lbl.grid(row=2, column=1, sticky="nw", padx=10)

        self.btns_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btns_frame.grid(row=0, column=2, rowspan=3, padx=20)
        
        self.btn_lyrics = ctk.CTkButton(self.btns_frame, text="🎤", width=35, fg_color="transparent", hover_color="#333",
                                       text_color="white",
                                       command=lambda: callbacks['lyrics']())
        self.btn_lyrics.pack(side="left", padx=5)

        self.btn_queue = ctk.CTkButton(self.btns_frame, text="≡", width=35, fg_color="transparent", hover_color="#333",
                                       text_color="white",
                                       command=lambda: callbacks['queue']())
        self.btn_queue.pack(side="left", padx=5)

        self.btn_shuffle = ctk.CTkButton(self.btns_frame, text="🔀", width=35, fg_color="transparent", 
                                         text_color="gray", hover_color="#333", command=self.toggle_sh)
        self.btn_shuffle.pack(side="left", padx=5)
        
        ctk.CTkButton(self.btns_frame, text="⏮", width=40, fg_color="transparent", hover_color="#333",
                      font=("Arial", 16), command=callbacks['prev']).pack(side="left", padx=5)
        
        self.btn_play = ctk.CTkButton(self.btns_frame, text="⏯", width=50, height=50, 
                                      fg_color="white", text_color="black", hover_color="#ddd",
                                      corner_radius=25, font=("Arial", 20),
                                      command=callbacks['play_pause'])
        self.btn_play.pack(side="left", padx=10)
        
        ctk.CTkButton(self.btns_frame, text="⏭", width=40, fg_color="transparent", hover_color="#333",
                      font=("Arial", 16), command=callbacks['next']).pack(side="left", padx=5)

        self.vol_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.vol_frame.grid(row=0, column=3, rowspan=3, padx=15)
        ctk.CTkLabel(self.vol_frame, text="🔊", text_color="gray").pack()
        
        # --- ZMĚNA: Horizontální slider ---
        self.volume_slider = ctk.CTkSlider(self.vol_frame, from_=0, to=100, orientation="horizontal", 
                                           width=100, height=16, # Šířka místo výšky
                                           button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER,
                                           progress_color=COLOR_ACCENT,
                                           command=lambda v: callbacks['set_volume'](v))
        self.volume_slider.set(50)
        self.volume_slider.pack()

        self.device_var = ctk.StringVar(value="Zařízení")
        self.device_menu = ctk.CTkOptionMenu(self, variable=self.device_var, width=120, 
                                             fg_color="#222", button_color="#333",
                                             command=self.on_dev)
        self.device_menu.grid(row=0, column=4, rowspan=3, padx=10)
        self.device_map = {}

    def toggle_sh(self):
        self.is_sh = not getattr(self, 'is_sh', False)
        self.callbacks['shuffle'](self.is_sh)

    def on_dev(self, c):
        if c in self.device_map: self.callbacks['set_device'](self.device_map[c])

    def update_devices(self, devices, current_id):
        names = []
        self.device_map = {}
        for d in devices:
            name = f"{d['name']} ({d['id'][-4:]})"
            if d['id'] == current_id: self.device_var.set(f"🟢 {name}")
            names.append(name)
            self.device_map[name] = d['id']
        self.device_menu.configure(values=names)

    def update_info(self, data, audio_features=None):
        self.title_lbl.configure(text=data['name'])
        self.artist_lbl.configure(text=data['artist'])
        self.btn_play.configure(text="⏸" if data['is_playing'] else "▶")
        self.btn_shuffle.configure(text_color=COLOR_ACCENT if data['shuffle'] else "gray")
        self.is_sh = data['shuffle']
        
        info_text = ""
        if 'progress_ms' in data and 'duration_ms' in data:
            curr = format_ms(data['progress_ms'])
            total = format_ms(data['duration_ms'])
            info_text += f"{curr} / {total}"
        
        if audio_features:
            bpm = audio_features.get('bpm')
            key = audio_features.get('key')
            info_text += f"  |  BPM: {bpm}  Key: {key}"
            
        self.features_lbl.configure(text=info_text)

    def set_cover(self, img):
        if not self.winfo_exists(): return
        self.cover.configure(image=img)
        self.cover.image = img

class BrowserTab(ctk.CTkFrame):
    def __init__(self, master, service, player_callback, image_loader, rename_callback, open_new_tab_callback=None, add_queue_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.service = service
        self.player_callback = player_callback
        self.image_loader = image_loader
        self.rename_callback = rename_callback
        self.open_new_tab_callback = open_new_tab_callback
        self.add_queue_callback = add_queue_callback 
        self.current_context_uri = None
        self.queue_loop_id = None
        self._pending_title = None 
        
        self.current_playlist_id = None
        self.current_offset = 0
        self.batch_size = 50
        self.active_view = "tracklist"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.track_list = TrackList(self, 
                                    on_item_click=self.on_item_click_dispatcher,
                                    on_artist_click=self.go_to_artist_page,
                                    on_item_right_click=self.on_item_right_click_dispatcher,
                                    on_add_queue=self.on_add_queue_dispatcher,
                                    label_text="Vítejte")
        
        self.artist_view = ArtistView(self, 
                                      on_track_click=self.on_item_click_dispatcher,
                                      on_item_right_click=self.on_item_right_click_dispatcher,
                                      on_add_queue=self.on_add_queue_dispatcher)

        self.visualizer_view = VisualizerView(self)

        self.show_view("tracklist")

    # --- PŘEDÁVÁNÍ EVENTU DO DISPEČERA ---
    def on_item_right_click_dispatcher(self, item, event=None):
        if self.open_new_tab_callback:
            # Předáme item i event
            self.open_new_tab_callback(item, event)

    def on_add_queue_dispatcher(self, uri):
        if self.add_queue_callback:
            self.add_queue_callback(uri)

    # ... (Zbytek metod save_state, load_state, atd. beze změny) ...
    def save_state(self):
        return {
            'view': self.active_view,
            'tracklist_data': self.track_list.all_tracks_data,
            'tracklist_label': self.track_list.title_lbl.cget("text"),
            'artist_data': self.artist_view.current_data,
            'context': self.current_context_uri,
            'is_queue': (self.queue_loop_id is not None)
        }

    def load_state(self, state):
        if not state: return
        self.current_context_uri = state.get('context')
        if state.get('tracklist_data'):
            self.track_list.load_tracks(state['tracklist_data'])
            self.track_list.configure(label_text=state.get('tracklist_label', ""))
        if state.get('artist_data'):
            self.artist_view.load_artist(state['artist_data'], self.image_loader)
        self.show_view(state.get('view', 'tracklist'))
        if state.get('is_queue'):
            self.load_queue()

    def run_async(self, target_func, callback, *args):
        def thread_job():
            try:
                result = target_func(*args)
            except Exception as e:
                print(f"Async Error: {e}")
                result = []
            try:
                self.after(0, lambda: callback(result))
            except: pass
        threading.Thread(target=thread_job, daemon=True).start()

    def _stop_queue_loop(self):
        if self.queue_loop_id:
            self.after_cancel(self.queue_loop_id)
            self.queue_loop_id = None

    def show_view(self, view_name):
        self.active_view = view_name
        self.track_list.grid_forget()
        self.artist_view.grid_forget()
        self.visualizer_view.grid_forget()
        self.visualizer_view.stop_animation()

        if view_name == "tracklist": 
            self.track_list.grid(row=0, column=0, sticky="nsew")
        elif view_name == "artist": 
            self.artist_view.grid(row=0, column=0, sticky="nsew")
        elif view_name == "visualizer":
            self.visualizer_view.grid(row=0, column=0, sticky="nsew")
            self.visualizer_view.start_animation()

    def on_item_click_dispatcher(self, item):
        itype = item.get('type', 'track')
        if itype == 'track':
            uri = item.get('uri') if isinstance(item, dict) else item
            if uri: self.player_callback(uri, self.current_context_uri)
        elif itype == 'artist':
            self.go_to_artist_page({'artist_id': item['id'], 'artist': item['name']})
        elif itype == 'playlist':
            self.load_playlist({'id': item['id'], 'uri': item['uri'], 'name': item['name'], 'image_url': item.get('image_url')})
        elif itype == 'album':
            self.load_album({'id': item['id'], 'uri': item['uri'], 'name': item['name'], 'image_url': item.get('image_url')})

    def play_context(self):
        if self.current_context_uri:
            self.player_callback(None, self.current_context_uri)

    def load_visualizer(self):
        self._stop_queue_loop()
        self.current_context_uri = None
        if self.rename_callback: self.rename_callback("Vizualizér")
        self.show_view("visualizer")

    def load_album(self, album_data):
        self._stop_queue_loop()
        self.current_context_uri = album_data['uri']
        self.track_list.clear()
        self.track_list.show_loading(True)
        self.track_list.configure(label_text=f"Album: {album_data['name']}")
        self.track_list.show_play_button(self.play_context)
        img_url = album_data.get('image_url')
        self.track_list.set_header_image(img_url, self.image_loader)
        self.show_view("tracklist")
        self._pending_title = album_data['name']
        self.run_async(self.service.get_album_tracks, self._on_playlist_chunk_loaded, album_data['id'])

    def load_playlist(self, playlist_data):
        self._stop_queue_loop()
        self.current_context_uri = playlist_data['uri']
        self.current_playlist_id = playlist_data['id']
        self.current_offset = 0
        self.track_list.clear()
        self.track_list.show_loading(True)
        self.track_list.configure(label_text=playlist_data['name'])
        self.track_list.show_play_button(self.play_context)
        img_url = playlist_data.get('image_url')
        if not img_url and 'images' in playlist_data and playlist_data['images']:
             img_url = playlist_data['images'][0]['url']
        self.track_list.set_header_image(img_url, self.image_loader)
        self.show_view("tracklist")
        self._pending_title = playlist_data['name']
        self.run_async(self.service.get_playlist_tracks, self._on_playlist_chunk_loaded, self.current_playlist_id, 0, self.batch_size)

    def _on_playlist_chunk_loaded(self, tracks):
        self.track_list.show_loading(False)
        self.track_list.add_tracks(tracks)
        if self.current_playlist_id and len(tracks) == self.batch_size:
            self.current_offset += self.batch_size
            self.run_async(self.service.get_playlist_tracks, self._on_playlist_chunk_loaded, self.current_playlist_id, self.current_offset, self.batch_size)
        if self.rename_callback and self._pending_title:
            self.rename_callback(self._pending_title)
            self._pending_title = None

    def search(self, query, search_type):
        self._stop_queue_loop()
        self.current_context_uri = None
        self.track_list.clear()
        self.track_list.hide_header_image()
        self.track_list.hide_play_button()
        self.track_list.show_loading(True)
        icon = "🎵" if search_type == "track" else "👤" if search_type == "artist" else "📜"
        label = f"Hledám {icon}: {query}..."
        self.track_list.configure(label_text=label)
        self.show_view("tracklist")
        self._pending_title = f"{icon} {query}"
        self.run_async(self.service.search, self._on_search_loaded, query, search_type)

    def _on_search_loaded(self, items):
        self.track_list.show_loading(False)
        self.track_list.add_tracks(items)
        self.track_list.configure(label_text=f"Výsledky hledání")
        if self.rename_callback and self._pending_title:
            self.rename_callback(self._pending_title)
            self._pending_title = None

    def go_to_artist_page(self, track_data):
        self._stop_queue_loop()
        artist_id = track_data.get('artist_id')
        if not artist_id: return
        self._pending_title = track_data.get('artist', 'Artist')
        self.run_async(self.service.get_artist_details, self._on_artist_loaded, artist_id)

    def _on_artist_loaded(self, data):
        if data:
            self.artist_view.load_artist(data, self.image_loader)
            self.show_view("artist") 
            if self.rename_callback and self._pending_title:
                self.rename_callback(data['name'])
                self._pending_title = None

    def load_queue(self):
        self._stop_queue_loop()
        self.current_context_uri = None
        self.track_list.clear()
        self.track_list.hide_header_image()
        self.track_list.hide_play_button()
        if self.rename_callback: self.rename_callback("Fronta")
        self.show_view("tracklist")
        self._update_queue_loop()

    def _update_queue_loop(self):
        self.run_async(self.service.get_queue, self._on_queue_loaded)

    def _on_queue_loaded(self, tracks):
        self.track_list.clear()
        self.track_list.add_tracks(tracks)
        self.track_list.configure(label_text="Fronta přehrávání (Live)")
        self.queue_loop_id = self.after(5000, self._update_queue_loop)

    def play_specific_track(self, track_uri):
        self.player_callback(track_uri, self.current_context_uri)

    def play_artist_track(self, item):
        uri = item.get('uri') if isinstance(item, dict) else item
        if uri: self.player_callback(uri, None)