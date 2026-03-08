import json
import os

CONFIG_FILE = "data/config.json"

DEFAULT_CONFIG = {
    "theme": "Red",
    "compact_mode": True,
    "ultra_compact": True,
    "light_mode": False,
    "hide_scrollbars": True,
    "default_volume": 100
}

class SettingsManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Chyba při načítání configu: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Chyba při ukládání configu: {e}")

    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()