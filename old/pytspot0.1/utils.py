import requests
from PIL import Image
from io import BytesIO
import threading
import customtkinter as ctk
import tkinter 
import os
import hashlib

# Globální cache v paměti (pro aktuální běh)
IMAGE_MEM_CACHE = {}
session = requests.Session()

# Složka pro trvalé ukládání
CACHE_DIR = "img_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cache_path(url):
    """Vytvoří bezpečný název souboru z URL pomocí MD5 hashe"""
    hash_obj = hashlib.md5(url.encode())
    filename = hash_obj.hexdigest() + ".png"
    return os.path.join(CACHE_DIR, filename)

def load_image_async(url, size, callback):
    if not url: return

    # 1. Rychlá kontrola paměti (RAM)
    cache_key = f"{url}_{size}"
    if cache_key in IMAGE_MEM_CACHE:
        callback(IMAGE_MEM_CACHE[cache_key])
        return

    def thread_proc():
        try:
            cache_path = get_cache_path(url)
            img_data = None

            # 2. Kontrola disku (HDD/SSD)
            if os.path.exists(cache_path):
                try:
                    img_data = Image.open(cache_path)
                    # Musíme načíst data do paměti, jinak by open() držel soubor
                    img_data.load() 
                except:
                    pass # Pokud je soubor poškozený, stáhneme ho znovu

            # 3. Pokud není na disku, stáhneme z internetu
            if img_data is None:
                response = session.get(url, timeout=5)
                response.raise_for_status()
                img_data = Image.open(BytesIO(response.content))
                
                # Uložíme na disk pro příště (originální velikost)
                with open(cache_path, "wb") as f:
                    f.write(response.content)

            # 4. Změna velikosti (Resampling)
            # Použijeme kopii, abychom nezměnili originál v paměti pro jiné velikosti
            img_resized = img_data.copy().resize(size, Image.Resampling.BILINEAR)
            
            # Vytvoření CTkImage
            ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=size)
            
            # Uložit do RAM cache
            IMAGE_MEM_CACHE[cache_key] = ctk_img
            
            # Bezpečná aktualizace UI
            try:
                root = tkinter._default_root
                if root:
                    root.after(0, lambda: callback(ctk_img))
                else:
                    callback(ctk_img)
            except:
                callback(ctk_img)

        except Exception as e:
            print(f"Chyba obrázku ({url}): {e}")
    
    threading.Thread(target=thread_proc, daemon=True).start()