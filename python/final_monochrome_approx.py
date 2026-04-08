"""
Stima della Lunghezza d'Onda Preponderante per Canali RGB (Sensore BSI-CMOS)
Metodo: Baricentro con Soglia (Thresholded Centroid)

Crediti Sensibilità Spettrale (Samsung Galaxy S22 Telephoto proxy per S24):
Color Lab Eilat - Spectral Sensitivity Estimation Web
URL: https://color-lab-eilat.github.io/Spectral-sensitivity-estimation-web/
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# Assicuriamoci che la cartella di output esista
os.makedirs('outputs', exist_ok=True)

# ==========================================
# 1. CARICAMENTO DATI E ALLINEAMENTO
# ==========================================
try:
    df_camera = pd.read_csv('spettri/Samsung-Galaxy-S22-Rear-Telephoto-Camera.csv')
    df_sorgente = pd.read_csv('spettri/rgb.csv', sep=';')
except FileNotFoundError as e:
    print(f"Errore nel caricamento dei file: {e}")
    exit()

lam_min = max(df_camera['wavelength'].min(), df_sorgente['lambda'].min())
lam_max = min(df_camera['wavelength'].max(), df_sorgente['lambda'].max())
lam_comune = np.arange(np.ceil(lam_min), np.floor(lam_max) + 1, 1.0)

sens_R = np.interp(lam_comune, df_camera['wavelength'], df_camera['red'])
sens_G = np.interp(lam_comune, df_camera['wavelength'], df_camera['green'])
sens_B = np.interp(lam_comune, df_camera['wavelength'], df_camera['blue'])
spettro_sorgente = np.interp(lam_comune, df_sorgente['lambda'], df_sorgente['rgb'])

# ==========================================
# 2. CALCOLO SPETTRO EFFETTIVO E METRICHE
# ==========================================
eff_R = sens_R * spettro_sorgente
eff_G = sens_G * spettro_sorgente
eff_B = sens_B * spettro_sorgente

# Soglia per il calcolo del baricentro
SOGLIA_TAGLIO = 0.3

def calcola_metriche_soglia(lambda_array, spettro_effettivo, soglia_pct):
    picco_idx = np.argmax(spettro_effettivo)
    picco_val = lambda_array[picco_idx]
    max_intensita = spettro_effettivo[picco_idx]

    valore_soglia = max_intensita * soglia_pct
    maschera = spettro_effettivo >= valore_soglia

    lam_filtrato = lambda_array[maschera]
    spettro_filtrato = spettro_effettivo[maschera]

    area_filtrata = np.sum(spettro_filtrato)
    if area_filtrata != 0:
        centroide_val = np.sum(lam_filtrato * spettro_filtrato) / area_filtrata
    else:
        centroide_val = picco_val

    return picco_val, centroide_val

picco_R, centroide_R = calcola_metriche_soglia(lam_comune, eff_R, SOGLIA_TAGLIO)
picco_G, centroide_G = calcola_metriche_soglia(lam_comune, eff_G, SOGLIA_TAGLIO)
picco_B, centroide_B = calcola_metriche_soglia(lam_comune, eff_B, SOGLIA_TAGLIO)

print(f"--- Risultati Analisi (Soglia {SOGLIA_TAGLIO*100:.0f}%) ---")
print(f"Canale ROSSO  -> Picco: {picco_R:.0f} nm | Baricentro: {centroide_R:.0f} nm")
print(f"Canale VERDE  -> Picco: {picco_G:.0f} nm | Baricentro: {centroide_G:.0f} nm")
print(f"Canale BLU    -> Picco: {picco_B:.0f} nm | Baricentro: {centroide_B:.0f} nm")

# ==========================================
# 3. PLOTTING PER PUBBLICAZIONE (LAYOUT 5 PANNELLI)
# ==========================================
# Impostiamo sharex=True in modo che l'asse X sia uno solo e perfettamente allineato
fig, axs = plt.subplots(5, 1, figsize=(10, 14), dpi=150, sharex=True)
fig.subplots_adjust(hspace=0.15, top=0.95, bottom=0.08) # Riduciamo lo spazio verticale tra i grafici

fig.suptitle(f"Analisi Spettrale dei Canali RGB (Baricentro con soglia {SOGLIA_TAGLIO*100:.0f}%)",
             fontsize=16, fontweight='bold')

fig.text(0.5, 0.02, 'Dati Sensore (S22 proxy): Color Lab Eilat (github.io/Spectral-sensitivity-estimation-web)',
         ha='center', fontsize=9, color='dimgray')

# --- Pannello 1: Sensibilità Fotocamera ---
axs[0].plot(lam_comune, sens_R, color='#d62728', label='Sensibilità R')
axs[0].plot(lam_comune, sens_G, color='#2ca02c', label='Sensibilità G')
axs[0].plot(lam_comune, sens_B, color='#1f77b4', label='Sensibilità B')
axs[0].set_ylabel("Risposta Relativa", fontsize=10)
axs[0].set_title("Sensibilità Spettrale del Sensore", loc='left', fontsize=12)
axs[0].grid(True, linestyle=':', alpha=0.6)
axs[0].legend(loc='upper right', fontsize=9)

# --- Pannello 2: Spettro Sorgente ---
axs[1].plot(lam_comune, spettro_sorgente, color='black')
axs[1].fill_between(lam_comune, spettro_sorgente, color='gray', alpha=0.2)
axs[1].set_ylabel("Intensità", fontsize=10)
axs[1].set_title("Spettro di Emissione della Sorgente", loc='left', fontsize=12)
axs[1].grid(True, linestyle=':', alpha=0.6)

# --- Trova il massimo globale per uniformare l'asse Y dei segnali effettivi ---
max_eff_globale = max(np.max(eff_R), np.max(eff_G), np.max(eff_B))
ylim_max = max_eff_globale * 1.15 # Aggiunge un 15% di margine superiore

# --- Pannello 3: Segnale Effettivo ROSSO ---
axs[2].plot(lam_comune, eff_R, color='#d62728')
axs[2].fill_between(lam_comune, eff_R, where=(eff_R >= np.max(eff_R)*SOGLIA_TAGLIO), color='#d62728', alpha=0.3)
axs[2].axvline(x=centroide_R, color='black', linestyle='--', alpha=0.8,
               label=f'Centroide: {centroide_R:.0f} nm')
axs[2].set_ylabel("Segnale R", fontsize=10)
axs[2].set_ylim(0, ylim_max)
axs[2].grid(True, linestyle=':', alpha=0.6)
axs[2].legend(loc='upper right', fontsize=9)

# --- Pannello 4: Segnale Effettivo VERDE ---
axs[3].plot(lam_comune, eff_G, color='#2ca02c')
axs[3].fill_between(lam_comune, eff_G, where=(eff_G >= np.max(eff_G)*SOGLIA_TAGLIO), color='#2ca02c', alpha=0.3)
axs[3].axvline(x=centroide_G, color='black', linestyle='--', alpha=0.8,
               label=f'Centroide: {centroide_G:.0f} nm')
axs[3].set_ylabel("Segnale G", fontsize=10)
axs[3].set_ylim(0, ylim_max)
axs[3].grid(True, linestyle=':', alpha=0.6)
axs[3].legend(loc='upper right', fontsize=9)

# --- Pannello 5: Segnale Effettivo BLU ---
axs[4].plot(lam_comune, eff_B, color='#1f77b4')
axs[4].fill_between(lam_comune, eff_B, where=(eff_B >= np.max(eff_B)*SOGLIA_TAGLIO), color='#1f77b4', alpha=0.3)
axs[4].axvline(x=centroide_B, color='black', linestyle='--', alpha=0.8,
               label=f'Centroide: {centroide_B:.0f} nm')
axs[4].set_ylabel("Segnale B", fontsize=10)
axs[4].set_xlabel("Lunghezza d'onda $\lambda$ (nm)", fontsize=12)
axs[4].set_ylim(0, ylim_max)
axs[4].grid(True, linestyle=':', alpha=0.6)
axs[4].legend(loc='upper right', fontsize=9)

# ==========================================
# 4. SALVATAGGIO ED ESPOSIZIONE
# ==========================================
# Salva il grafico in formato PDF vettoriale (ideale per LaTeX / Word)
nome_file_output = "outputs/Analisi_Spettrale_S24_RGB.pdf"
plt.savefig(nome_file_output, format='pdf', bbox_inches='tight')
print(f"Grafico vettoriale salvato con successo come: {nome_file_output}")

# --- SALVATAGGIO CSV Wavelengths ---
csv_output_file = "outputs/rgb_wavelengths.csv"
df_wavelengths = pd.DataFrame({
    "canale": ["R", "G", "B"],
    "centroide": [round(centroide_R), round(centroide_G), round(centroide_B)]
})

# Convertiamo in intero prima di salvare, in modo da rimuovere definitivamente le cifre decimali dal formato
df_wavelengths["centroide"] = df_wavelengths["centroide"].astype(int)

df_wavelengths.to_csv(csv_output_file, index=False)
print(f"File CSV salvato con successo come: {csv_output_file}")

plt.show()