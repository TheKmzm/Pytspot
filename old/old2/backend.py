import json
import os
import spotipy
import requests
from spotipy.oauth2 import SpotifyOAuth

# --- Konstanty ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
HISTORY_PATH = os.path.join(BASE_DIR, 'search_history.json')
CACHE_PATH = os.path.join(BASE_DIR, '.spotify_cache')
MAX_HISTORY = 15

class SpotifyClient:
    def __init__(self):
        """Inicializuje Spotify klienta, načte konfiguraci a nastaví autentizaci."""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Nepodařilo se načíst nebo zpracovat config.json: {e}") from e

        scope = (
            "user-read-playback-state,"
            "user-modify-playback-state,"
            "user-read-currently-playing,"
            "playlist-read-private,"
            "playlist-read-collaborative,"
            "user-library-read"
        )

        auth_manager = SpotifyOAuth(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri'],
            scope=scope,
            cache_path=CACHE_PATH,
            open_browser=True
        )

        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        self.history = self.load_history()

    # --- Formátování dat ---
    def _format_track(self, track_info):
        """Zformátuje syrová data o skladbě ze Spotipy do jednoduššího slovníku."""
        if not track_info or 'artists' not in track_info:
            return None
        return {
            'id': track_info['id'],
            'name': track_info['name'],
            'artist': ", ".join([a['name'] for a in track_info['artists']]),
            'album': track_info['album']['name'],
            'duration_ms': track_info['duration_ms'],
            'uri': track_info['uri'],
            'cover_url': track_info['album']['images'][0]['url'] if track_info['album']['images'] else None
        }

    # --- Získávání playlistů a skladeb ---
    def get_playlists(self):
        """Získá playlisty aktuálního uživatele."""
        playlists = self.sp.current_user_playlists()
        return playlists.get('items', [])

    def get_playlist_tracks(self, playlist_id):
        """Získá všechny skladby pro dané ID playlistu."""
        results = self.sp.playlist_items(playlist_id, fields='items(track(id,name,artists,album(name,images),duration_ms,uri))')
        tracks = []
        for item in results.get('items', []):
            if item and item.get('track'):
                formatted = self._format_track(item['track'])
                if formatted:
                    tracks.append(formatted)
        return tracks

    def search(self, query):
        """Vyhledá skladby na Spotify."""
        results = self.sp.search(q=query, type='track', limit=50)
        tracks = []
        for item in results.get('tracks', {}).get('items', []):
            formatted = self._format_track(item)
            if formatted:
                tracks.append(formatted)
        return tracks

    # --- Ovládání přehrávání ---
    def get_playback_state(self):
        """Získá aktuální stav přehrávání."""
        state = self.sp.current_playback()
        if not state or not state.get('item'):
            return None
        
        track_info = self._format_track(state['item'])
        
        return {
            'is_active': True,
            'is_playing': state['is_playing'],
            'progress': state['progress_ms'],
            'duration': state['item']['duration_ms'],
            'name': track_info['name'],
            'artist': track_info['artist'],
            'cover_url': track_info['cover_url']
        }

    def control(self, action, uri=None, pos_ms=None, val=None):
        """Ovládá přehrávání: play, pause, next, prev, seek, volume, queue."""
        try:
            if action == 'play':
                self.sp.start_playback()
            elif action == 'play_uri':
                self.sp.start_playback(uris=[uri])
            elif action == 'pause':
                self.sp.pause_playback()
            elif action == 'next':
                self.sp.next_track()
            elif action == 'prev':
                self.sp.previous_track()
            elif action == 'seek':
                self.sp.seek_track(pos_ms)
            elif action == 'volume':
                self.sp.volume(val)
            elif action == 'queue':
                self.sp.add_to_queue(uri)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Spotify API Error při akci '{action}': {e}")

    # --- Extra funkce ---
    def get_audio_features(self, track_id):
        """Získá audio vlastnosti skladby jako BPM, energie, atd."""
        features = self.sp.audio_features([track_id])[0]
        if not features:
            return None
        
        keys = ["C", "C♯/D♭", "D", "D♯/E♭", "E", "F", "F♯/G♭", "G", "G♯/A♭", "A", "A♯/B♭", "B"]
        key_name = keys[features['key']]
        mode = "Dur" if features['mode'] == 1 else "moll"

        return {
            'bpm': round(features['tempo']),
            'energy': round(features['energy'] * 100),
            'dance': round(features['danceability'] * 100),
            'key': f"{key_name} {mode}"
        }

    def get_cover(self, url):
        """Stáhne obrázek z URL."""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.content
        except requests.RequestException:
            return None

    # --- Historie vyhledávání ---
    def load_history(self):
        """Načte historii vyhledávání z JSON souboru."""
        if not os.path.exists(HISTORY_PATH):
            return []
        try:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
                return self.history
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []
            return []

    def save_search_to_history(self, query):
        """Přidá dotaz do historie, zamezí duplicitám a ořízne historii."""
        if query in self.history:
            self.history.remove(query)
        self.history.insert(0, query)
        self.history = self.history[:MAX_HISTORY]
        
        try:
            with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except IOError as e:
            print(f"Chyba při ukládání historie: {e}")