from yt_dlp import YoutubeDL

class SoundCloudClient:
    def __init__(self):
        # Options for searching (fast)
        self.search_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'extract_flat': True, # Fast search (no details yet)
        }
        
        # Options for resolving stream URL (slower, gets full details)
        self.stream_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
        }

    def search(self, query, limit=30):
        """Searches SoundCloud and returns list of tracks."""
        search_query = f"scsearch{limit}:{query}"
        results = []
        
        try:
            with YoutubeDL(self.search_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                for entry in info['entries']:
                    results.append({
                        "name": entry.get('title'),
                        "artist": entry.get('uploader'),
                        "uri": entry.get('url'), # This is the web URL (e.g. soundcloud.com/artist/song)
                        "type": "soundcloud",
                        "image": None # Flat search doesn't always get images to save speed
                    })
        except Exception as e:
            print(f"SoundCloud Search Error: {e}")
            
        return results

    def get_stream_info(self, url):
        """Resolves the direct stream URL and cover art."""
        try:
            with YoutubeDL(self.stream_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "stream_url": info['url'],
                    "thumbnail": info.get('thumbnail'),
                    "duration": info.get('duration'),
                    "title": info.get('title'),
                    "artist": info.get('uploader')
                }
        except Exception as e:
            print(f"Stream Error: {e}")
            return None