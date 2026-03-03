import requests
from bs4 import BeautifulSoup
import re

# --- CONFIGURATION ---
GENIUS_ACCESS_TOKEN = "uPvNfB78QtkCDOPQd0kyY7q5q_VO27RHRIiBZLggx-00N7YgZWCGjGM-Zvwyl4O_" 
# ^^^ PASTE YOUR TOKEN ABOVE ^^^

class GeniusClient:
    def __init__(self):
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}

    def clean_text(self, text):
        """Cleans up the raw HTML text into readable lyrics."""
        # Replace <br> with newlines
        text = text.replace("<br/>", "\n").replace("<br>", "\n")
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()

    def get_lyrics(self, title, artist):
        """Orchestrates the search and scrape process."""
        if not GENIUS_ACCESS_TOKEN or GENIUS_ACCESS_TOKEN == "YOUR_GENIUS_TOKEN_HERE":
            return "Error: Please add your Genius Access Token in backend/lyrics.py"

        print(f"Searching Genius for: {title} by {artist}")
        
        # 1. SEARCH FOR THE SONG
        search_url = f"{self.base_url}/search"
        data = {'q': f"{title} {artist}"}
        
        try:
            response = requests.get(search_url, params=data, headers=self.headers)
            json_data = response.json()
            
            song_path = None
            
            # Loop through hits to find a matching artist (to avoid covers)
            for hit in json_data['response']['hits']:
                hit_artist = hit['result']['primary_artist']['name'].lower()
                if artist.lower() in hit_artist or hit_artist in artist.lower():
                    song_path = hit['result']['path']
                    break
            
            # If no strict artist match, take the first result
            if not song_path and json_data['response']['hits']:
                song_path = json_data['response']['hits'][0]['result']['path']

            if not song_path:
                return "Lyrics not found on Genius."

            # 2. SCRAPE THE LYRICS PAGE
            page_url = f"https://genius.com{song_path}"
            page = requests.get(page_url)
            html = BeautifulSoup(page.text, "html.parser")
            
            # Genius stores lyrics in containers with this data attribute
            lyrics_containers = html.select('div[data-lyrics-container="true"]')
            
            if not lyrics_containers:
                return "Could not parse lyrics text."

            lyrics_text = ""
            for div in lyrics_containers:
                # Get inner HTML to preserve <br> tags before cleaning
                # Decode to handle special characters
                text_part = div.decode_contents() 
                lyrics_text += text_part + "\n"

            return self.clean_text(lyrics_text)

        except Exception as e:
            return f"Connection Error: {e}"