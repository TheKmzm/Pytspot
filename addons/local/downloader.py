import os
import yt_dlp
from pathlib import Path

# Cesta, kam se bude stahovat (např. C:/Users/Ty/Music/Redify)
DOWNLOAD_DIR = os.path.join(Path.home(), "Music", "Redify")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class Downloader:
    def download_to_mp3(self, url, filename_prefix=""):
        """Stáhne video/audio z URL a převede ho na MP3."""
        
        # Nastavení pro yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f'{filename_prefix}%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # Název výsledného mp3 souboru (yt-dlp změní příponu)
                final_filename = os.path.splitext(filename)[0] + ".mp3"
                return final_filename
        except Exception as e:
            print(f"Download Error: {e}")
            return None

    def get_local_files(self):
        """Vrátí seznam MP3 souborů ve složce."""
        files = []
        if os.path.exists(DOWNLOAD_DIR):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith(".mp3"):
                    full_path = os.path.join(DOWNLOAD_DIR, f)
                    files.append({
                        "name": f.replace(".mp3", ""), # Název bez přípony
                        "path": full_path,
                        "type": "local_file"
                    })
        return files