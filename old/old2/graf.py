import matplotlib.pyplot as plt
import numpy as np

# Naměřená data
# v_measured: naměřené rychlosti (m/s)
# f_measured: naměřené frekvence (Hz)
# Záporná rychlost znamená vzdalování, kladná přibližování.

data = [
    (-0.191, 39039), (0.350, 39099), (0.476, 39108), (0.789, 39145),
    (0.159, 39077), (-0.371, 39017), (-0.498, 39003), (-0.797, 38975),
    (-0.185, 39039), (0.352, 39094), (0.499, 39115), (0.795, 39136),
    (0.157, 39077), (-0.372, 39017), (-0.519, 39002), (-0.767, 38972),
    (-0.185, 39039), (0.360, 39100), (0.506, 39117), (0.796, 39146),
    (0.162, 39078), (-0.388, 39016), (-0.516, 39002), (-0.811, 38973),
    (-0.184, 39039), (0.369, 39101), (0.510, 39117), (0.797, 39142),
    (0.154, 39077), (-0.394, 39015), (-0.535, 39000), (-0.782, 38978),
    (-0.192, 39038), (0.380, 39102), (0.517, 39118), (0.839, 39151),
    (0.154, 39077), (-0.392, 39015), (-0.516, 39002), (-0.799, 38971),
    (-0.185, 39039), (0.375, 39102), (0.523, 39118), (0.826, 39143),
    (0.159, 39077), (-0.404, 39014), (-0.547, 39000), (-0.798, 38969)
]

# Rozdělení dat do polí
v = np.array([x[0] for x in data])
f = np.array([x[1] for x in data])

# Lineární regrese (metoda nejmenších čtverců)
# Hledáme fit ve tvaru f = a*v + b
a, b = np.polyfit(v, f, 1)

# Výpočet rychlosti zvuku z regrese (c = f0 / a)
f0 = b
c_measured = f0 / a

print(f"Rovnice regrese: f = {a:.2f} * v + {b:.2f}")
print(f"Klidová frekvence f0: {f0:.2f} Hz")
print(f"Vypočtená rychlost zvuku c: {c_measured:.2f} m/s")

# Příprava grafu
plt.figure(figsize=(10, 6))

# Vykreslení naměřených bodů
plt.scatter(v, f, color='blue', alpha=0.7, label='Naměřené hodnoty', s=30)

# Vykreslení regresní přímky
x_line = np.linspace(min(v), max(v), 100)
y_line = a * x_line + b
plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Regrese (a={a:.1f}, b={b:.0f})')

# Úprava vzhledu grafu
plt.title('Závislost frekvence na rychlosti zdroje (Dopplerův jev)', fontsize=14)
plt.xlabel('Rychlost zdroje $v$ [m/s]\n(záporná hodnota = vzdalování)', fontsize=12)
plt.ylabel('Naměřená frekvence $f\'$ [Hz]', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11)

# Zobrazení rovnice a rychlosti zvuku přímo v grafu
info_text = (f"$f = {a:.2f}v + {b:.0f}$\n"
             f"$c_{{mer}} \\approx {c_measured:.1f}$ m/s")
plt.text(0.05, 0.95, info_text, transform=plt.gca().transAxes, 
         fontsize=12, verticalalignment='top', 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()

# Uložení do souboru (volitelné)
# plt.savefig('doppler_graf.png', dpi=300)

# Zobrazení grafu
plt.show()