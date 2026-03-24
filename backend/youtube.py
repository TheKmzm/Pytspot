from yt_dlp import YoutubeDL

class YouTubeClient:
    def __init__(self):
        # Rychlé vyhledávání (zde cookies nepotřebujeme, vyhledávání je veřejné)
        self.search_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'extract_flat': True,
        }
        
        # Detailní info pro přehrání (ZDE JE ZMĚNA)
        # Musíme použít cookies z prohlížeče, abychom obešli "Bot Detection"
        self.stream_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            # Tímto si yt-dlp sáhne pro cookies do Chrome. 
            # Pokud používáš Edge, napiš ('edge',). Pokud Firefox, napiš ('firefox',).
            'cookiesfrombrowser': ('chrome',), 
        }

    def search(self, query, limit=30):
        """Vyhledá videa na YouTube."""
        search_query = f"ytsearch{limit}:{query}"
        results = []
        
        try:
            with YoutubeDL(self.search_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                for entry in info['entries']:
                    results.append({
                        "name": entry.get('title'),
                        "artist": entry.get('uploader'),
                        "uri": entry.get('url'),
                        "type": "youtube",
                        "image": None
                    })
        except Exception as e:
            print(f"YouTube Search Error: {e}")
            
        return results

    def get_stream_info(self, url):
        """Získá přímou audio URL a náhled."""
        try:
            # Tady se použijí cookies z prohlížeče
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
            print(f"YT Stream Error: {e}")
            return None