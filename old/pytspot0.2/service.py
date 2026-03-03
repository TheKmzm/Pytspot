import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

class SpotifyService:
    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-public playlist-modify-private user-library-read"
        ))

    def get_playback_state(self):
        try:
            current = self.sp.current_playback()
            if current and current.get('item'):
                item = current['item']
                artist_name = item['artists'][0]['name'] if item['artists'] else "Unknown"
                cover_url = item['album']['images'][0]['url'] if item['album']['images'] else None
                
                return {
                    'is_active': True,
                    'name': item['name'],
                    'id': item['id'],
                    'artist': artist_name,
                    'cover_url': cover_url,
                    'is_playing': current['is_playing'],
                    'shuffle': current['shuffle_state'],
                    'progress_ms': current['progress_ms'],
                    'duration_ms': item['duration_ms'],
                    'volume': current['device']['volume_percent'],
                    'device_id': current['device']['id'],
                    'uri': item['uri']
                }
            return {'is_active': False}
        except: return None

    def get_queue(self):
        try:
            q = self.sp.queue()
            tracks = []
            if q.get('currently_playing'):
                tracks.append(self._parse_track(q['currently_playing'], is_current=True))
            for t in q.get('queue', []):
                tracks.append(self._parse_track(t, is_current=False))
            return tracks
        except: return []

    def _parse_track(self, t, is_current=False):
        return {
            'type': 'track',
            'name': t['name'],
            'id': t['id'],
            'uri': t['uri'],
            'artist': t['artists'][0]['name'] if t['artists'] else "Unknown",
            'artist_id': t['artists'][0]['id'] if t['artists'] else None,
            'duration_ms': t['duration_ms'],
            'is_current': is_current
        }

    def get_playlists(self):
        try: return self.sp.current_user_playlists(limit=50)['items']
        except: return []

    # --- OPRAVA: Přidány parametry offset a limit ---
    def get_playlist_tracks(self, playlist_id, offset=0, limit=100):
        try:
            res = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)
            tracks = []
            for item in res['items']:
                if item.get('track'):
                    tracks.append(self._parse_track(item['track']))
            return tracks
        except: return []
    
    def get_album_tracks(self, album_id):
        try:
            res = self.sp.album_tracks(album_id, limit=50)
            tracks = []
            for t in res['items']:
                tracks.append(self._parse_track(t))
            return tracks
        except: return []

    def search(self, query, stype='track'):
        try:
            res = self.sp.search(q=query, type=stype, limit=50)
            items = []
            if stype == 'track':
                items = [self._parse_track(t) for t in res['tracks']['items']]
            elif stype == 'artist':
                for a in res['artists']['items']:
                    items.append({'type': 'artist', 'name': a['name'], 'id': a['id'], 'followers': a['followers']['total'], 'image_url': a['images'][0]['url'] if a['images'] else None})
            elif stype == 'playlist':
                for p in res['playlists']['items']:
                    if p: items.append({'type': 'playlist', 'name': p['name'], 'id': p['id'], 'uri': p['uri'], 'owner': p['owner']['display_name'], 'image_url': p['images'][0]['url'] if p['images'] else None})
            elif stype == 'album':
                for a in res['albums']['items']:
                    items.append({'type': 'album', 'name': a['name'], 'id': a['id'], 'uri': a['uri'], 'year': a['release_date'][:4], 'image_url': a['images'][0]['url'] if a['images'] else None})
            return items
        except: return []

    def get_artist_details(self, artist_id):
        try:
            artist = self.sp.artist(artist_id)
            top = self.sp.artist_top_tracks(artist_id)['tracks']
            albums_raw = self.sp.artist_albums(artist_id, album_type='album,single', limit=50)
            
            top_tracks = [self._parse_track(t) for t in top]
            albums = []
            seen = set()
            for a in albums_raw['items']:
                if a['name'] not in seen:
                    seen.add(a['name'])
                    albums.append({'type': 'album', 'name': a['name'], 'id': a['id'], 'uri': a['uri'], 'year': a['release_date'][:4], 'image_url': a['images'][0]['url'] if a['images'] else None})

            return {'name': artist['name'], 'image_url': artist['images'][0]['url'] if artist['images'] else None, 'followers': artist['followers']['total'], 'genres': ", ".join(artist['genres'][:2]), 'top_tracks': top_tracks, 'albums': albums}
        except: return None

    def add_to_queue(self, uri):
        try: self.sp.add_to_queue(uri)
        except: pass

    def transfer_playback(self, device_id):
        try: self.sp.transfer_playback(device_id=device_id, force_play=True)
        except: pass

    def get_devices(self):
        try: return self.sp.devices()['devices']
        except: return []

    def control(self, command, **kwargs):
        try:
            if command == 'play': self.sp.start_playback()
            elif command == 'pause': self.sp.pause_playback()
            elif command == 'next': self.sp.next_track()
            elif command == 'prev': self.sp.previous_track()
            elif command == 'volume': self.sp.volume(kwargs['val'])
            elif command == 'play_uri':
                if "spotify:track" in kwargs['uri']: self.sp.start_playback(uris=[kwargs['uri']])
                else: self.sp.start_playback(context_uri=kwargs['uri'])
            elif command == 'play_context_track':
                self.sp.start_playback(context_uri=kwargs['context'], offset={'uri': kwargs['uri']})
        except: pass