import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()


class SpotifyClient:
    def __init__(self):

        self.client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
        
        # Scopes determine what your app is allowed to do
        # We need scopes for playback control, reading library, and modifying volume
        self.scope = (
            "user-read-playback-state "
            "user-modify-playback-state "
            "user-library-read "
            "playlist-read-private "
            "user-read-recently-played"
        )

        self.sp = None
        self.authenticate()

    def authenticate(self):
        """Authenticates the user using Spotify OAuth."""
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            print("Authentication Successful!")
        except Exception as e:
            print(f"Authentication Failed: {e}")

    def get_volume(self):
        """
        Returns the current volume (0-100) of the active device.
        Returns None if no device is active.
        """
        try:
            playback = self.sp.current_playback()
            
            # Check if playback exists and has a 'device' object
            if playback and playback.get('device'):
                return playback['device']['volume_percent']
            
            return None
            
        except Exception as e:
            print(f"Error fetching volume: {e}")
            return None

    def get_current_playback(self):
        """Returns the full JSON of the current playing track/episode."""
        return self.sp.current_playback()

    def get_current_song_info(self):
        """
        Robust helper to extract Name, Artist, IDs, and Art.
        """
        try:
            playback = self.sp.current_playback()
            
            if not playback or not playback.get('item'):
                return None

            track = playback['item']
            track_type = playback.get('currently_playing_type', 'track')
            
            # --- HANDLE PODCASTS ---
            if track_type == 'episode':
                return {
                    "name": track['name'],
                    "artist": track['show']['name'],
                    "artist_id": None, # Podcasts don't have artist IDs in the same way
                    "album_id": None,
                    "album_art": track['images'][0]['url'] if track['images'] else None,
                    "is_playing": playback['is_playing'],
                    "shuffle_state": playback['shuffle_state'],
                    "progress_ms": playback['progress_ms'],
                    "duration_ms": track['duration_ms'],
                    "uri": track['uri'],
                    "type": "episode"
                }

            # --- HANDLE TRACKS ---
            # 1. Get Album Art
            image_url = "https://misc.scdn.co/liked-songs/liked-songs-300.png"
            if track['album']['images']:
                image_url = track['album']['images'][0]['url']

            # 2. Get Artist Name AND ID
            artist_name = "Unknown"
            artist_id = None
            if track['artists']:
                artist_name = track['artists'][0]['name']
                artist_id = track['artists'][0]['id']  # <--- WE NEED THIS

            # 3. Get Album ID
            album_id = track['album'].get('id')

            return {
                "name": track['name'],
                "artist": artist_name,
                "artist_id": artist_id, # <--- Added to return dictionary
                "album_id": album_id,
                "album_art": image_url,
                "is_playing": playback['is_playing'],
                "progress_ms": playback['progress_ms'],
                "duration_ms": track['duration_ms'],
                "uri": track['uri'],
                "type": "track"
            }

        except Exception as e:
            print(f"Error fetching playback info: {e}")
            return None

    def play_pause(self):
        """
        Toggles play/pause. 
        FORCE PLAY: If no device is active, it wakes up the first available device.
        """
        try:
            playback = self.sp.current_playback()

            # 1. If currently playing -> PAUSE
            if playback and playback.get('is_playing'):
                self.sp.pause_playback()
                return "Paused"

            # 2. If paused -> TRY TO PLAY
            # If the session is stale, 'start_playback' might fail because no device is active.
            try:
                self.sp.start_playback()
                return "Resumed"
            except Exception:
                # 3. FORCE WAKE-UP LOGIC
                # If the simple 'play' failed, it means we lost connection to the device.
                print("No active device found. Attempting to force wake a device...")
                
                devices = self.sp.devices()
                if devices and devices['devices']:
                    # Grab the first available device (e.g., your open PC app or Phone)
                    first_device_id = devices['devices'][0]['id']
                    device_name = devices['devices'][0]['name']
                    
                    # The Magic Command: Transfer playback AND force play
                    self.sp.transfer_playback(device_id=first_device_id, force_play=True)
                    return f"Forced Resumed on {device_name}"
                else:
                    print("CRITICAL: No Spotify devices found. Open Spotify on a device first.")
                    return "No Devices Open"

        except Exception as e:
            print(f"Play/Pause Error: {e}")
            return "Error"

    def next_track(self):
        self.sp.next_track()

    def previous_track(self):
        self.sp.previous_track()

    def set_volume(self, volume_percent):
        """Sets volume (0-100)."""
        try:
            self.sp.volume(volume_percent)
        except Exception as e:
            print(f"Cannot set volume (active device might not support it): {e}")

    def get_user_playlists(self, limit=50):
        """Fetches the user's playlists."""
        results = self.sp.current_user_playlists(limit=limit)
        playlists = []
        for item in results['items']:
            # Handle cases where playlist has no image
            image_url = item['images'][0]['url'] if item['images'] else None
            playlists.append({
                "name": item['name'],
                "id": item['id'],
                "uri": item['uri'],          # <--- THIS WAS MISSING
                "image": image_url,
                "total_tracks": item['tracks']['total']
            })
        return playlists

    def search(self, query, search_type='track', limit=50):
        """
        Searches for tracks, artists, albums, or playlists.
        """
        try:
            results = self.sp.search(q=query, type=search_type, limit=limit)
            items = []

            # 1. Handle TRACKS
            if search_type == 'track':
                # Check if key exists first
                if 'tracks' in results and results['tracks']['items']:
                    for track in results['tracks']['items']:
                        if not track: continue  # <--- SAFETY CHECK
                        
                        img = None
                        if track.get('album') and track['album'].get('images'):
                            img = track['album']['images'][0]['url']
                            
                        items.append({
                            "type": "track",
                            "name": track['name'],
                            "artist": track['artists'][0]['name'],
                            "uri": track['uri'],
                            "id": track['id'],
                            "image": img
                        })

            # 2. Handle ARTISTS
            elif search_type == 'artist':
                if 'artists' in results and results['artists']['items']:
                    for artist in results['artists']['items']:
                        if not artist: continue # <--- SAFETY CHECK
                        
                        img = artist['images'][0]['url'] if artist.get('images') else None
                        items.append({
                            "type": "artist",
                            "name": artist['name'],
                            "uri": artist['uri'],
                            "id": artist['id'],
                            "image": img,
                            "followers": artist['followers']['total']
                        })

            # 3. Handle ALBUMS
            elif search_type == 'album':
                if 'albums' in results and results['albums']['items']:
                    for album in results['albums']['items']:
                        if not album: continue # <--- SAFETY CHECK
                        
                        img = album['images'][0]['url'] if album.get('images') else None
                        items.append({
                            "type": "album",
                            "name": album['name'],
                            "artist": album['artists'][0]['name'],
                            "uri": album['uri'],
                            "id": album['id'],
                            "image": img,
                            "date": album['release_date']
                        })

            # 4. Handle PLAYLISTS
            elif search_type == 'playlist':
                if 'playlists' in results and results['playlists']['items']:
                    for pl in results['playlists']['items']:
                        if not pl: continue # <--- SAFETY CHECK
                        
                        img = pl['images'][0]['url'] if pl.get('images') else None
                        owner = pl['owner']['display_name'] if pl.get('owner') else "Unknown"
                        
                        items.append({
                            "type": "playlist",
                            "name": pl['name'],
                            "artist": owner, # Mapped to artist for GUI compatibility
                            "owner": owner,
                            "uri": pl['uri'],
                            "id": pl['id'],
                            "image": img
                        })

            return items

        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def play_uri(self, uri):
        """Plays a specific Context URI (Album, Playlist) or Track URI."""
        # Check if it's a context (playlist/album) or a single track
        if "track" in uri:
            self.sp.start_playback(uris=[uri])
        else:
            self.sp.start_playback(context_uri=uri)

    def get_devices(self):
        """Returns a list of available devices (Phone, PC, Echo, etc.)"""
        devices = self.sp.devices()
        return devices['devices']

    def transfer_playback(self, device_id):
        """Moves the music to a specific device."""
        self.sp.transfer_playback(device_id=device_id, force_play=True)

    def add_to_queue(self, track_uri):
            """Adds a track to the end of the user's current queue."""
            try:
                self.sp.add_to_queue(track_uri)
                print(f"Added {track_uri} to queue")
            except Exception as e:
                print(f"Error adding to queue: {e}")

    def get_album_page(self, album_id):
        """Fetches full album details and tracklist."""
        try:
            # Clean ID if it's a URI
            if "spotify:album:" in album_id:
                album_id = album_id.split(":")[-1]

            album = self.sp.album(album_id)
            
            
            # Extract tracks cleanly
            tracklist = []
            for t in album['tracks']['items']:
                tracklist.append({
                    "name": t['name'],
                    "duration_ms": t['duration_ms'],
                    "track_number": t['track_number'],
                    "uri": t['uri'],
                    # Albums usually share the same cover, but good to have reference
                    "artist": t['artists'][0]['name'] 
                })

            return {
                "name": album['name'],
                "artist": album['artists'][0]['name'],
                "release_date": album['release_date'],
                "image": album['images'][0]['url'] if album['images'] else None,
                "total_tracks": album['total_tracks'],
                "copyright": album['copyrights'][0]['text'] if album['copyrights'] else "",
                "tracks": tracklist
            }
        except Exception as e:
            print(f"Error fetching album: {e}")
            return None

    def get_artist_page(self, artist_id):
        """
        Fetches Artist profile: Bio info, Top Tracks, and Albums.
        """
        try:
            if "spotify:artist:" in artist_id:
                artist_id = artist_id.split(":")[-1]

            # 1. Main Artist Metadata (Image, Followers)
            artist = self.sp.artist(artist_id)
            
            # 2. Top Tracks (The "Popular" section)
            top_tracks_raw = self.sp.artist_top_tracks(artist_id)
            top_tracks = []
            for t in top_tracks_raw['tracks'][:20]: # Limit to top 20
                img = t['album']['images'][0]['url'] if t['album']['images'] else None
                top_tracks.append({
                    "name": t['name'],
                    "image": img,
                    "uri": t['uri']
                })

            # 3. Discography (Albums)
            # We filter for 'album' to avoid seeing hundreds of singles/remixes
            albums_raw = self.sp.artist_albums(artist_id, album_type='album', limit=10)
            albums = []
            seen_names = set() # Helper to remove duplicates (Spotify API returns many duplicates)
            
            for a in albums_raw['items']:
                if a['name'] not in seen_names:
                    seen_names.add(a['name'])
                    img = a['images'][0]['url'] if a['images'] else None
                    albums.append({
                        "name": a['name'],
                        "image": img,
                        "year": a['release_date'][:4], # Get just the year (YYYY)
                        "uri": a['uri']
                    })

            return {
                "name": artist['name'],
                "followers": f"{artist['followers']['total']:,}", # Adds commas (e.g. 1,000,000)
                "genres": artist['genres'],
                "image": artist['images'][0]['url'] if artist['images'] else None,
                "top_tracks": top_tracks,
                "albums": albums
            }

        except Exception as e:
            print(f"Error fetching artist: {e}")
            return None

    def get_playlist_tracks(self, playlist_id):
        """Fetches ALL tracks from a playlist (handles pagination)."""
        try:
            if "spotify:playlist:" in playlist_id:
                playlist_id = playlist_id.split(":")[-1]

            # 1. Get first page (limit 100)
            results = self.sp.playlist_items(playlist_id, additional_types=['track'], limit=100)
            tracks = results['items']

            # 2. Loop to get remaining pages
            while results['next']:
                results = self.sp.next(results)
                tracks.extend(results['items'])

            cleaned_tracks = []
            for item in tracks:
                track = item['track']
                if not track: continue 
                
                img = "https://misc.scdn.co/liked-songs/liked-songs-300.png"
                if track['album']['images']:
                    img = track['album']['images'][0]['url']

                cleaned_tracks.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "uri": track['uri'],
                    "image": img,
                    "duration_ms": track['duration_ms']
                })
            return cleaned_tracks
        except Exception as e:
            print(f"Error fetching playlist items: {e}")
            return []

    def seek_track(self, position_ms):
        """Seeks to the given position in milliseconds."""
        try:
            self.sp.seek_track(position_ms)
        except Exception as e:
            print(f"Seek failed: {e}")

    def get_queue(self):
        """Fetches the user's queue."""
        try:
            return self.sp.queue()
        except Exception as e:
            print(f"Queue error: {e}")
            return None

    def play_track_in_context(self, track_uri, context_uri):
        """
        Plays a specific track WITHIN a specific context (Playlist/Album).
        This ensures the music continues after the song ends.
        """
        try:
            # offset={"uri": ...} tells Spotify where to start in the list
            self.sp.start_playback(context_uri=context_uri, offset={"uri": track_uri})
        except Exception as e:
            print(f"Context Playback Error: {e}")

    def get_user_name(self):
        """Fetches the user's display name."""
        try:
            user = self.sp.current_user()
            return user['display_name']
        except:
            return "Music Lover"

    def play_liked_songs(self):
        """
        Fetches the user's saved tracks and plays them.
        (Spotify API doesn't allow playing 'Liked Songs' as a context, so we pass a list of URIs).
        """
        try:
            print("Fetching Liked Songs...")
            # 1. Get the most recent 50 liked songs
            results = self.sp.current_user_saved_tracks(limit=50)
            
            if not results['items']:
                print("No liked songs found.")
                return

            # 2. Extract URIs
            uris = [item['track']['uri'] for item in results['items']]
            
            self.sp.shuffle(True)
            
            # 3. Start Playback
            # Note: This creates an ad-hoc queue of these 50 songs
            self.sp.start_playback(uris=uris)
            print("Playing Liked Songs.")
            
        except Exception as e:
            print(f"Error playing liked songs: {e}")

    def toggle_shuffle(self, state):
        """
        Toggles Shuffle mode.
        state: True (Shuffle On) or False (Shuffle Off)
        """
        try:
            self.sp.shuffle(state)
        except Exception as e:
            print(f"Error toggling shuffle: {e}")

    def play_list(self, uris, start_uri=None):
        """
        Plays a custom list of track URIs (e.g., Artist Top Tracks).
        Optionally starts at a specific track in that list.
        """
        try:
            if start_uri:
                # offset={"uri": ...} tells Spotify exactly which song in the list to begin with
                self.sp.start_playback(uris=uris, offset={"uri": start_uri})
            else:
                self.sp.start_playback(uris=uris)
        except Exception as e:
            print(f"Error playing list: {e}")

    def add_track_to_playlist(self, playlist_id, track_uris):
        """
        Adds one or more tracks to a playlist.
        track_uris: Can be a single string or a list of strings.
        """
        try:
            # Ensure it's a list
            if isinstance(track_uris, str):
                track_uris = [track_uris]
            
            self.sp.playlist_add_items(playlist_id, track_uris)
            print(f"Added to playlist {playlist_id}")
            return True
        except Exception as e:
            print(f"Error adding to playlist: {e}")
            return False

    def get_recently_played(self, limit=50):
        """Fetches the user's recently played tracks."""
        try:
            results = self.sp.current_user_recently_played(limit=limit)
            tracks = []
            for item in results['items']:
                track = item['track']
                # Get Image
                img = None
                if track['album']['images']:
                    img = track['album']['images'][0]['url']

                tracks.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "uri": track['uri'],
                    "image": img,
                    "duration_ms": track['duration_ms']
                })
            return tracks
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []

    def save_item_locally(self, data):
        """Saves a track/artist/playlist dict to a local JSON file."""
        filename = "saved_items.json"
        items = self.get_saved_items()
        
        # Check for duplicates (by URI)
        for i in items:
            if i.get('uri') == data.get('uri'):
                print("Item already saved.")
                return False
        
        items.append(data)
        
        try:
            with open(filename, 'w') as f:
                json.dump(items, f, indent=4)
            print(f"Saved: {data['name']}")
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def get_saved_items(self):
        """Reads the local JSON file."""
        filename = "saved_items.json"
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return []

    def remove_item_locally(self, uri):
        """Removes an item by URI."""
        filename = "saved_items.json"
        items = self.get_saved_items()
        
        new_items = [i for i in items if i.get('uri') != uri]
        
        with open(filename, 'w') as f:
            json.dump(new_items, f, indent=4)

    def play_context(self, context_uri):
        """Přehraje album, playlist nebo umělce (Vyžadováno pro AI)."""
        try:
            self.sp.start_playback(context_uri=context_uri)
        except Exception as e:
            print(f"Chyba při play_context: {e}")