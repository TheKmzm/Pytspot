import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyClient:
    def __init__(self):
        # Zde doplň své údaje z Developer Dashboardu
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="59a0e2f913c5478ca49df9529b8f8687",
            client_secret="ceba348353234a55bd0af9ebaeacc704",
            redirect_uri="http://127.0.0.1:8888/callback",
            scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private"
        ))

    def get_current_track(self):
        try:
            current = self.sp.current_playback()
            if current and current['is_playing']:
                track = current['item']
                return {
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album_art': track['album']['images'][0]['url'],
                    'is_playing': True
                }
            return None
        except:
            return None

    def next_track(self):
        self.sp.next_track()

    def prev_track(self):
        self.sp.previous_track()

    def play_pause(self):
        playback = self.sp.current_playback()
        if playback and playback['is_playing']:
            self.sp.pause_playback()
        else:
            self.sp.start_playback()