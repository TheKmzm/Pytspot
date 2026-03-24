# frontend/styles.py

#css neumim pomooooooooooct

# --- BAREVNÁ SCHÉMATA ---
THEMES = {
    "Red":    {"accent": "#E50914", "hover": "#FF3333"},
    "Green":  {"accent": "#1DB954", "hover": "#1ED760"},
    "Blue":   {"accent": "#007BFF", "hover": "#3395FF"},
    "Purple": {"accent": "#BB86FC", "hover": "#D7A8FF"},
    "Orange": {"accent": "#FF8800", "hover": "#FFAA44"},
    "Pink":   {"accent": "#FF007F", "hover": "#FF4DA6"}, 
    "Cyan":   {"accent": "#00E5FF", "hover": "#66F0FF"},
    "Yellow": {"accent": "#FFD700", "hover": "#FFE44D"},
    "Lime":   {"accent": "#CDDC39", "hover": "#E6EE9C"},
}

def get_stylesheet(theme_name="Red", compact_mode=False, ultra_compact=False, light_mode=False, hide_scrollbars=False):
    """Generuje CSS string na základě všech nastavení."""
    
    # 1. Barvy (Tmavý vs Světlý režim)
    colors = THEMES.get(theme_name, THEMES["Red"])
    accent = colors["accent"]
    hover = colors["hover"]

    if light_mode:
        bg_main = "#FFFFFF"       # Bílé pozadí
        bg_sec  = "#F0F0F0"       # Světle šedá (inputy, karty)
        bg_hover = "#E0E0E0"
        text_main = "#000000"     # Černý text
        text_sec  = "#555555"     # Šedý text
        border_col = "#CCCCCC"
    else:
        bg_main = "#121212"       # Tmavé pozadí
        bg_sec  = "#242424"       # Tmavě šedá
        bg_hover = "#202020"
        text_main = "#FFFFFF"     # Bílý text
        text_sec  = "#B3B3B3"     # Šedý text
        border_col = "#333333"

    # 2. Velikosti (Compact / Ultra Compact)
    pad_btn = "6px 10px"
    font_size = "13px"
    row_height = "50px"
    
    # Logika pro Sidebar položky
    if ultra_compact:
        sb_pad = "0px 2px"
        sb_font = "11px"
        sb_height = "18px" # Pevná výška pro ultra hustý seznam
    elif compact_mode:
        sb_pad = "2px 4px"
        sb_font = "12px"
        sb_height = "auto"
    else:
        sb_pad = "4px 8px"
        sb_font = "13px"
        sb_height = "auto"

    if compact_mode:
        pad_btn = "2px 5px"
        font_size = "12px"
        row_height = "35px"

    # 3. Scrollbary
    sb_width = "0px" if hide_scrollbars else "8px"

    # --- GENERUJEME CSS ---

    return f"""
    /* GLOBAL RESET */
    QMainWindow {{ background-color: {bg_main}; color: {text_main}; border: none; }}
    QWidget {{ background-color: {bg_main}; color: {text_main}; border: none; }}
    QFrame {{ border: none; }} 
    QLabel {{ color: {text_main}; border: none; background: transparent; }} /* Všechny labely průhledné */

    /* GLOBAL BUTTONS */
    QPushButton {{ E
        background-color: transparent; 
        color: {text_sec}; 
        font-weight: bold; 
        border: none;       /* Žádný rámeček globálně */
        outline: none;      /* Žádný obrys při kliknutí */
        text-align: left;
        padding: {pad_btn};
        border-radius: 4px;
        font-size: {font_size};
    }}
    QPushButton:hover {{ 
        color: {text_main}; 
        background-color: {bg_hover};
    }}
    QPushButton:pressed {{ background-color: {accent}; color: white; }}

    /* --- PLAYER CONTROLS (Spodní lišta) --- */
    QPushButton#ControlBtn {{
        background-color: transparent;
        text-align: center;
        padding: 0px;
        border: none; /* Pojistka */
    }}
    QPushButton#ControlBtn:hover {{
        background-color: transparent; /* Žádné šedé pozadí při najetí na ikony */
        color: {accent}; /* Volitelné: ikona se může přebarvit */
    }}

    /* --- SIDEBAR NAV --- */
    QPushButton#NavBtn {{
        padding: {pad_btn};
        margin: 0px;
        height: 20px;
    }}

    /* --- BIG PLAY BUTTON (Playlist) --- */
    QPushButton#BigPlayBtn {{
        background-color: {accent}; 
        color: white; 
        border-radius: 30px; /* Kulaté (polovina z 60px) */
        font-size: 28px; 
        text-align: center;
        padding-bottom: 3px;
        border: none;
    }}
    QPushButton#BigPlayBtn:hover {{ background-color: {hover}; }}

    /* --- SEARCH BAR --- */
    QLineEdit {{ 
        background-color: {bg_sec}; 
        color: {text_main}; 
        border-radius: 15px; 
        padding: {pad_btn}; 
        border: 1px solid {border_col}; /* Pouze search bar má tenký rámeček */
        font-size: {font_size};
    }}
    QLineEdit:focus {{ border: 1px solid {accent}; }}
    
    /* ... (zbytek stylů pro ListWidget, Sliders, Scrollbars zůstává stejný) ... */
    
    /* LIST WIDGETS */
    QListWidget {{ background-color: {bg_main}; border: none; outline: none; min-height: 100px; max-height: 10000px; }}

    /* SIDEBAR ITEMS */
    QListWidget#SidebarList::item {{ 
        padding: {sb_pad}; 
        color: {text_sec}; 
        font-size: {sb_font};
        border-radius: 3px;
        margin: 0px;
        height: {sb_height};
        border: none;
    }}
    QListWidget#SidebarList::item:selected {{ 
        background-color: {bg_hover}; 
        color: {text_main}; 
        border-left: 2px solid {accent};
    }}
    QListWidget#SidebarList::item:hover {{ 
        color: {text_main}; 
        background-color: {bg_hover};
    }}
    
    /* MAIN TRACK ROWS */
    QListWidget::item {{ height: {row_height}; border-bottom: 1px solid {border_col}; }}
    QListWidget::item:selected {{ background-color: {bg_hover}; color: {accent}; }}

    /* SLIDERS */
    QSlider::groove:horizontal {{ height: 4px; background: {bg_sec}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ 
        background: {text_main}; 
        width: 10px; height: 10px; margin: -3px 0; border-radius: 5px; 
    }}
    QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}

    /* SCROLLBARS */
    QScrollBar:vertical {{ width: {sb_width}; background: transparent; }}
    QScrollBar::handle:vertical {{ background: {bg_sec}; border-radius: 3px; min-height: 20px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    """