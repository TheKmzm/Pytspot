import yt_dlp
import vlc
import time

def play_youtube_audio(video_url):
    print("Processing URL...")

    # 1. Configure yt-dlp to get the best audio URL (no video)
    ydl_opts = {
        'format': 'bestaudio/best',  # specific audio only
        'noplaylist': True,          # download single video, not playlist
        'quiet': True,               # suppress chatter
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)

        print(f"Now Playing: {title}")
        print(f"Duration: {duration} seconds")

        # 2. Setup VLC to stream the audio
        instance = vlc.Instance('--no-video') # ensure video is disabled
        player = instance.media_player_new()
        media = instance.media_new(audio_url)
        player.set_media(media)
        
        player.play()

        # 3. Keep the script running while audio plays
        # VLC plays in a separate thread, so we must pause the main thread
        time.sleep(1.5) # Give the player time to start
        while player.is_playing():
            time.sleep(1)
            
        print("Finished.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace this with your YouTube URL
    url = input("Enter YouTube URL: ")
    play_youtube_audio(url)