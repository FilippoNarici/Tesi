"""
Generazione di figure singole per la tesi.
Produce un file PDF vettoriale per il parametro selezionato in final_utils.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # backend non interattivo per salvataggio diretto
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import final_utils as utils

# =============================================================================
# STILE PUBBLICAZIONE
# =============================================================================

plt.rcParams.update({
    # Font
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    # Figure
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    # LaTeX-compatible text rendering
    'text.usetex': False,
    'mathtext.fontset': 'cm',
    # Lines & axes
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'image.interpolation': 'none',
})

# =============================================================================
# CONFIGURAZIONE PARAMETRI FIGURE
# =============================================================================

# Dizionario con metadati per ogni parametro plottabile
PARAM_CONFIG = {
    'S0': {
        'titolo': 'Intensità totale $S_0$',
        'unita': 'conteggi (u.a.)',
        'cmap': None,  # scelto dinamicamente in base al canale
        'vmin': None,
        'vmax': None,
    },
    'S1': {
        'titolo': 'Parametro di Stokes $S_1$',
        'unita': 'conteggi (u.a.)',
        'cmap': 'bwr',
        'vmin': 'sym99',
        'vmax': 'sym99',
    },
    'S2': {
        'titolo': 'Parametro di Stokes $S_2$',
        'unita': 'conteggi (u.a.)',
        'cmap': 'bwr',
        'vmin': 'sym99',
        'vmax': 'sym99',
    },
    'S3': {
        'titolo': 'Parametro di Stokes $S_3$',
        'unita': 'conteggi (u.a.)',
        'cmap': 'bwr',
        'vmin': 'sym99',
        'vmax': 'sym99',
    },
    'DoLP': {
        'titolo': 'Grado di polarizzazione lineare (DoLP)',
        'unita': None,
        'cmap': 'viridis',
        'vmin': 0,
        'vmax': 1,
    },
    'AoLP': {
        'titolo': "Angolo di polarizzazione lineare (AoLP)",
        'unita': '°',
        'cmap': 'twilight',
        'vmin': -90,
        'vmax': 90,
    },
    'delta': {
        'titolo': 'Ritardo di fase $\\delta$',
        'unita': '°',
        'cmap': 'twilight',
        'vmin': -180,
        'vmax': 180,
    },
    'theta': {
        'titolo': 'Asse veloce $\\theta$',
        'unita': '°',
        'cmap': 'twilight',
        'vmin': -90,
        'vmax': 90,
    },
    'mask': {
        'titolo': 'Maschera di sfondo',
        'unita': None,
        'cmap': 'gray',
        'vmin': 0,
        'vmax': 1,
    },
}

# =============================================================================
# FUNZIONI DI PLOTTING
# =============================================================================

def _get_s0_cmap(channel_idx):
    """Restituisce la colormap monocromatica per S0 in base al canale."""
    cmaps = {
        0: LinearSegmentedColormap.from_list('nero_rosso', ['black', 'red']),
        1: LinearSegmentedColormap.from_list('nero_verde', ['black', 'green']),
        2: LinearSegmentedColormap.from_list('nero_blu', ['black', 'blue']),
    }
    return cmaps.get(channel_idx, 'gray')


def _resolve_limits(data, vmin_spec, vmax_spec):
    """Risolve i limiti di colore: numeri fissi o 'sym99' per simmetria al 99°percentile."""
    if vmin_spec == 'sym99':
        bound = np.percentile(np.abs(data), 99)
        return -bound, bound
    return vmin_spec, vmax_spec


def generate_figure(param_name, data, channel_idx=0):
    """Genera e salva una singola figura PDF per il parametro richiesto."""

    cfg = PARAM_CONFIG[param_name]

    # Colormap
    if cfg['cmap'] is None:
        cmap = _get_s0_cmap(channel_idx)
    else:
        cmap = cfg['cmap']

    # Limiti colore
    vmin, vmax = _resolve_limits(data, cfg['vmin'], cfg['vmax'])

    # Dimensione figura: proporzionale ai dati, ~8 cm di larghezza
    H, W = data.shape
    aspect = H / W
    fig_w = 3.35  # ~85 mm, larghezza colonna singola tipica
    fig_h = fig_w * aspect
    # Spazio extra per la colorbar
    fig_w_total = fig_w + 0.7

    fig, ax = plt.subplots(figsize=(fig_w_total, fig_h))

    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    ax.set_title(cfg['titolo'], pad=6)
    ax.axis('off')

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    if cfg['unita']:
        cbar.set_label(cfg['unita'])

    return fig


# =============================================================================
# PIPELINE PRINCIPALE
# =============================================================================

def main():
    param_name = utils.THESIS_FIGURE_PARAM
    if param_name not in PARAM_CONFIG:
        print(f"Errore: parametro '{param_name}' non riconosciuto.")
        print(f"Parametri disponibili: {', '.join(PARAM_CONFIG.keys())}")
        return

    print(f"--- Generazione figura per: {param_name} ---")

    # Determina se servono S3 e i parametri derivati
    needs_s3 = param_name in ('S3', 'delta', 'theta', 'mask')
    needs_retardance = param_name in ('delta', 'theta')
    needs_dolp_aolp = param_name in ('DoLP', 'AoLP')

    # 1. Caricamento Stokes lineari (servono sempre)
    angles, stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER,
        utils.TARGET_CHANNEL_IDX,
        downsample_factor=utils.DOWNSAMPLE_FACTOR,
        invert_angles=True
    )
    if stack is None or angles is None:
        print("Errore: impossibile caricare i dati di polarizzazione lineare.")
        return

    S0, S1, S2 = utils.calculate_linear_stokes(angles, stack)

    # 2. S3 (se necessario o per la maschera)
    S3 = None
    if needs_s3 or needs_retardance:
        wavelength = utils.get_channel_wavelength(utils.WAVELENGTHS_CSV, utils.TARGET_CHANNEL_IDX)
        S3 = utils.calculate_s3(utils.WAV_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
                                utils.DOWNSAMPLE_FACTOR, wavelength)

    # 3. Maschera e allineamento (servono per quasi tutto tranne S0 grezzo)
    bg_mask = utils.generate_background_mask(S0, S3)
    S1_al, S2_al = utils.align_reference_frame(S1, S2, bg_mask)

    # 4. Calcoli derivati
    DoLP, AoLP = None, None
    delta_deg, theta_deg = None, None

    if needs_dolp_aolp or param_name in ('S1', 'S2'):
        DoLP, AoLP = utils.calculate_dolp_aolp(S0, S1_al, S2_al)

    if needs_retardance:
        delta_deg, theta_deg = utils.calculate_retardance_and_fast_axis(
            S0, S1_al, S2_al, S3, bg_mask)

    # 5. Seleziona i dati da plottare
    data_map = {
        'S0': S0,
        'S1': S1_al,
        'S2': S2_al,
        'S3': S3,
        'DoLP': DoLP,
        'AoLP': AoLP,
        'delta': delta_deg,
        'theta': theta_deg,
    }

    if param_name == 'mask':
        S0_norm = (S0 - np.min(S0)) / (np.max(S0) - np.min(S0) + 1e-8)
        data = np.where(bg_mask, S0_norm, 0.0)
    else:
        data = data_map[param_name]

    if data is None:
        print(f"Errore: dati non disponibili per '{param_name}'. Servono le immagini con lamina λ/4?")
        return

    # 6. Genera e salva la figura
    fig = generate_figure(param_name, data, utils.TARGET_CHANNEL_IDX)

    # Percorso output: Images/generated/<nome_campione>/
    sample_name = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))
    out_dir = os.path.join(utils.THESIS_FIGURES_DIR, sample_name)
    os.makedirs(out_dir, exist_ok=True)

    channel_prefix = {0: 'R', 1: 'G', 2: 'B'}.get(utils.TARGET_CHANNEL_IDX, 'X')
    filename = f"{channel_prefix}_{param_name}.pdf"
    out_path = os.path.join(out_dir, filename)
    fig.savefig(out_path, format='pdf')
    plt.close(fig)

    print(f"Figura salvata: {out_path}")
    print("--- Fatto ---")


if __name__ == "__main__":
    main()
