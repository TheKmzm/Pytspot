import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import requests
from bs4 import BeautifulSoup 

class SpotifyService:
    def __init__(self, spotify_id, spotify_secret, genius_id=None, genius_secret=None):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=spotify_id,
            client_secret=spotify_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private"
        ))
        
        self.audio_features_available = True
        self.genius_token = None
        
        # Genius Auth (zkráceno pro přehlednost, stejné jako předtím)
        if genius_id and genius_secret:
            self._authenticate_genius(genius_id, genius_secret)

    def _authenticate_genius(self, client_id, client_secret):
        try:
            url = "https://api.genius.com/oauth/token"
            data = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.genius_token = response.json().get("access_token")
        except: pass

    # --- NOVÁ FUNKCE: PŘIDÁNÍ DO PLAYLISTU ---
    def add_track_to_playlist(self, playlist_id, track_uri):
        """Přidá jednu skladbu do playlistu"""
        try:
            self.sp.playlist_add_items(playlist_id, [track_uri])
            print(f"Skladba {track_uri} přidána do {playlist_id}")
            return True
        except Exception as e:
            print(f"Chyba při přidávání do playlistu: {e}")
            return False

    # --- Zbytek metod beze změny (zkopírujte si obsah z předchozí verze, pokud je potřeba) ---
    def get_lyrics(self, track_name, artist_name):
        if not self.genius_token: return "Genius API nedostupné."
        try:
            headers = {"Authorization": f"Bearer {self.genius_token}"}
            q = f"{track_name.split('-')[0].strip()} {artist_name}"
            res = requests.get("https://api.genius.com/search", params={"q": q}, headers=headers).json()
            if res['response']['hits']:
                url = res['response']['hits'][0]['result']['url']
                page = requests.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')
                divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
                text = "\n\n".join([d.get_text(separator="\n") for d in divs])
                return text if text else f"Text nenalezen automatem.\nOdkaz: {url}"
            return "Text nenalezen."
        except: return "Chyba při hledání textu."

    def get_audio_features(self, track_id):
        if not self.audio_features_available: return None
        try:
            f = self.sp.audio_features([track_id])[0]
            if f:
                keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                return {'bpm': int(f['tempo']), 'energy': int(f['energy']*100), 'key': keys[f['key']]}
        except SpotifyException as e:
            if e.http_status == 403: self.audio_features_available = False
        except: pass
        return None

    def get_queue(self):
        # ... (Kód get_queue z předchozí verze) ...
        try:
            queue_data = self.sp.queue()
            tracks = []
            if queue_data and queue_data.get('currently_playing'):
                item = queue_data['currently_playing']
                tracks.append({'type': 'track', 'name': item['name'], 'uri': item['uri'], 'artist': item['artists'][0]['name'], 'is_current': True})
            if queue_data and queue_data.get('queue'):
                for item in queue_data['queue']:
                    tracks.append({'type': 'track', 'name': item['name'], 'uri': item['uri'], 'artist': item['artists'][0]['name'], 'is_current': False})
            return tracks
        except: return []

    def get_playback_state(self):
        # ... (Kód get_playback_state z předchozí verze) ...
        try:
            curr = self.sp.current_playback()
            if curr and curr.get('item'):
                return {
                    'name': curr['item']['name'], 'id': curr['item']['id'], 'artist': curr['item']['artists'][0]['name'],
                    'cover_url': curr['item']['album']['images'][0]['url'] if curr['item']['album']['images'] else None,
                    'is_playing': curr['is_playing'], 'shuffle': curr['shuffle_state'],
                    'volume': curr['device']['volume_percent'], 'device_id': curr['device']['id'],
                    'progress_ms': curr['progress_ms'], 'duration_ms': curr['item']['duration_ms']
                }
        except: return None

    def get_playlists(self):
        try: return self.sp.current_user_playlists(limit=50)['items']
        except: return []

    def get_playlist_tracks(self, playlist_id, offset=0, limit=50):
        # ... (Kód get_playlist_tracks z předchozí verze) ...
        try:
            res = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)
            tracks = []
            for i in res['items']:
                if i['track']:
                    tracks.append({'type':'track', 'name':i['track']['name'], 'uri':i['track']['uri'], 'artist':i['track']['artists'][0]['name'], 'duration_ms':i['track']['duration_ms'], 'artist_id': i['track']['artists'][0]['id']})
            return tracks
        except: return []

    def get_album_tracks(self, album_id):
        # ... (Kód get_album_tracks) ...
        try:
            res = self.sp.album_tracks(album_id, limit=50)
            tracks = []
            for t in res['items']:
                tracks.append({'type':'track', 'name':t['name'], 'uri':t['uri'], 'artist':t['artists'][0]['name'], 'duration_ms':t['duration_ms']})
            return tracks
        except: return []

    def search(self, query, search_type='track'):
        # ... (Kód search z předchozí verze) ...
        try:
            res = self.sp.search(q=query, limit=50, type=search_type)
            items = []
            if search_type == 'track':
                for t in res['tracks']['items']:
                    items.append({'type':'track', 'name':t['name'], 'uri':t['uri'], 'artist':t['artists'][0]['name'], 'duration_ms':t['duration_ms'], 'artist_id': t['artists'][0]['id']})
            elif search_type == 'artist':
                for a in res['artists']['items']:
                    items.append({'type':'artist', 'name':a['name'], 'id':a['id'], 'image_url':a['images'][0]['url'] if a['images'] else None, 'followers':a['followers']['total'], 'genres': ""})
            elif search_type == 'playlist':
                for p in res['playlists']['items']:
                    if p: items.append({'type':'playlist', 'name':p['name'], 'id':p['id'], 'uri':p['uri'], 'owner':p['owner']['display_name'], 'image_url':p['images'][0]['url'] if p['images'] else None})
            elif search_type == 'album':
                for a in res['albums']['items']:
                    items.append({'type':'album', 'name':a['name'], 'id':a['id'], 'uri':a['uri'], 'year':a['release_date'][:4], 'image_url':a['images'][0]['url'] if a['images'] else None})
            return items
        except: return []

    def get_artist_details(self, artist_id):
        # ... (Kód get_artist_details) ...
        try:
            artist = self.sp.artist(artist_id)
            top = self.sp.artist_top_tracks(artist_id)['tracks']
            albums = self.sp.artist_albums(artist_id, limit=50)['items']
            
            t_tracks = [{'type':'track', 'name':t['name'], 'uri':t['uri'], 'artist':t['artists'][0]['name'], 'duration_ms':t['duration_ms']} for t in top]
            
            seen = set()
            albs = []
            for a in albums:
                if a['name'] not in seen:
                    seen.add(a['name'])
                    albs.append({'type':'album', 'name':a['name'], 'id':a['id'], 'uri':a['uri'], 'year':a['release_date'][:4], 'image_url':a['images'][0]['url'] if a['images'] else None})

            return {'name': artist['name'], 'image_url': artist['images'][0]['url'] if artist['images'] else None, 'followers':artist['followers']['total'], 'genres':", ".join(artist['genres'][:2]), 'top_tracks':t_tracks, 'albums':albs}
        except: return None

    def add_to_queue(self, uri):
        try: self.sp.add_to_queue(uri)
        except: pass

    def control(self, action, **kwargs):
        try:
            if action == 'play_pause':
                if kwargs.get('is_playing'): self.sp.pause_playback()
                else: self.sp.start_playback()
            elif action == 'next': self.sp.next_track()
            elif action == 'prev': self.sp.previous_track()
            elif action == 'shuffle': self.sp.shuffle(kwargs.get('state'))
            elif action == 'play_track_in_context': self.sp.start_playback(context_uri=kwargs['context_uri'], offset={'uri': kwargs['track_uri']})
            elif action == 'play_single_track': self.sp.start_playback(uris=[kwargs['track_uri']])
            elif action == 'play_context': self.sp.start_playback(context_uri=kwargs['context_uri'])
        except: pass

    def set_volume(self, val):
        try: self.sp.volume(int(val))
        except: pass
    
    def get_devices(self):
        try: return self.sp.devices()['devices']
        except: return []
    
    def transfer_playback(self, did):
        try: self.sp.transfer_playback(device_id=did, force_play=True)
        except: pass