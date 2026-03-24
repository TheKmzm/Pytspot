from pypresence import Presence, PipeClosed, InvalidID
import time

# ZDE vlož své CLIENT ID z Discord Developer Portal
CLIENT_ID = "1466013629454352478"  # <--- ZMĚNIT!  # <--- UJISTI SE, ŽE TU MÁŠ SVÉ ČÍSLO

class DiscordClient:
    def __init__(self):
        self.rpc = None
        self.connected = False
        self.last_track = None
        self.start_time = None

    def connect(self):
        """Pokusí se připojit k Discordu."""
        try:
            self.rpc = Presence(CLIENT_ID)
            self.rpc.connect()
            self.connected = True
            print("Discord RPC Connected!")
        except Exception as e:
            # Nevypisujeme chybu pokaždé, aby to nespamovalo log, pokud Discord neběží
            self.connected = False

    def update(self, title, artist, image_url=None, is_playing=True, duration_sec=0, progress_sec=0):
        # 1. Pokud nejsme připojeni, zkusíme to teď
        if not self.connected:
            self.connect()
            if not self.connected: return # Stále nic, zkusíme to zase příště

        # 2. Logika pro pauzu/změnu stavu
        if not is_playing:
            try: self.rpc.clear()
            except: pass
            return

        current_track_id = f"{title}-{artist}"
        
        # 3. Výpočet časů
        if current_track_id != self.last_track:
            self.last_track = current_track_id
            self.start_time = int(time.time())
        
        # Pokud známe délku a pozici, vypočítáme "Konec za..."
        start = None
        end = None
        
        if duration_sec > 0:
            # Discord preferuje "End Timestamp" pro odpočet
            remaining = duration_sec - progress_sec
            end = int(time.time() + remaining)
        else:
            # Pokud neznáme délku (rádio), ukážeme "Uplynulý čas"
            start = self.start_time

        # 4. Odeslání update (s ochranou proti pádu)
        try:
            self.rpc.update(
                state=f"by {artist}",
                details=title,
                large_image="logo",  # Ujisti se, že máš asset "logo" na Dev portálu
                large_text="Redify Player",
                small_image="play_icon" if is_playing else "pause_icon",
                start=start,
                end=end
            )
            # print(f"Discord Updated: {title}") # Odkomentuj pro debug
            
        except PipeClosed:
            print("Discord Pipe Closed! Reconnecting...")
            self.connected = False
            self.connect() # Okamžitý pokus o reconnect
            
        except Exception as e:
            print(f"Discord Update Error: {e}")
            self.connected = False