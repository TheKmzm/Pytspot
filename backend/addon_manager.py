import os
import importlib.util

class AddonManager:
    def __init__(self, main_app):
        self.main_app = main_app  # Reference na SpotifyGUI (aby addon mohl ovládat appku)
        self.addons = []
        
        # Cesta ke složce 'addons' v kořenovém adresáři projektu
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.addons_dir = os.path.join(base_dir, "addons")

    def load_addons(self):
        """Projde složku addons a dynamicky načte všechny moduly."""
        if not os.path.exists(self.addons_dir):
            os.makedirs(self.addons_dir)
            return

        for item in os.listdir(self.addons_dir):
            addon_path = os.path.join(self.addons_dir, item)
            
            # Hledáme složky, které nezačínají podtržítkem (např. __pycache__)
            if os.path.isdir(addon_path) and not item.startswith("__"):
                main_file = os.path.join(addon_path, "addon.py")
                
                if os.path.exists(main_file):
                    self._load_addon(item, main_file)

    def _load_addon(self, folder_name, file_path):
        """Fyzicky načte Python soubor z dané cesty."""
        try:
            # 1. Dynamický import souboru
            spec = importlib.util.spec_from_file_location(folder_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 2. Zavoláme inicializační funkci addonu (musí se jmenovat setup_addon)
            if hasattr(module, 'setup_addon'):
                # Předáme hlavní aplikaci do addonu
                addon_instance = module.setup_addon(self.main_app)
                self.addons.append(addon_instance)
                print(f"📦 Addon Loaded: {addon_instance.name}")
            else:
                print(f"⚠️ Addon {folder_name} nemá funkci 'setup_addon'.")
                
        except Exception as e:
            print(f"❌ Failed to load addon {folder_name}: {e}")