"""Istogrammi di retardance per la tesi.

Riusa ``compute_polarimetric_maps_fullres`` di ``final_umap`` per ottenere la
mappa di delta a risoluzione nativa con maschera sparse-grid + bg + saturazione
gia' applicate. Produce per ogni canale:

- PDF pubblicabile in ``Images/generated/<dataset>/<CH>_hist_delta.pdf``, con
  barre colorate via colormap ciclica ``twilight`` (stessa della mappa di
  retardance in tesi) cosi' l'asse x e' visivamente una colorbar.
- HTML plotly interattivo in
  ``Images/generated/<dataset>/interactive/<CH>_hist_delta.html``, hover per
  identificare a colpo d'occhio i picchi dei singoli strati.

L'asse y viene clippato al massimo dei bin centrali (esclusi i primi e gli
ultimi ``HIST_EDGE_EXCLUDE_DEG`` gradi) per non far saturare la scala con i
picchi artificiali vicino a 0 e 360 gradi dovuti al wrap della retardance e al
rumore residuo di bordo.
"""
import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm

try:
    import plotly.graph_objects as go
    _PLOTLY_OK = True
except ImportError:
    _PLOTLY_OK = False

import final_utils as utils
import final_umap as fu

# =============================================================================
# STILE PUBBLICAZIONE (coerente con final_thesis_figure.py)
# =============================================================================

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'text.usetex': False,
    'mathtext.fontset': 'cm',
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
})

HIST_BINS = 180           # 2 deg per bin
HIST_CMAP = 'twilight'
HIST_EDGE_EXCLUDE_DEG = fu.HIST_EDGE_EXCLUDE_DEG

# =============================================================================
# HELPERS
# =============================================================================

def _bar_colors(centers_deg, cmap_name=HIST_CMAP):
    cmap = plt.get_cmap(cmap_name)
    return [cmap(c / 360.0) for c in centers_deg]


def _mpl_cmap_to_plotly(cmap_name, n=64):
    cmap = plt.get_cmap(cmap_name)
    stops = np.linspace(0.0, 1.0, n)
    scale = []
    for s in stops:
        r, g, b, _ = cmap(float(s))
        scale.append([float(s), f"rgb({int(255*r)},{int(255*g)},{int(255*b)})"])
    return scale


def _inner_ymax(counts, centers):
    inner = ((centers > HIST_EDGE_EXCLUDE_DEG)
             & (centers < 360 - HIST_EDGE_EXCLUDE_DEG))
    if inner.any() and counts[inner].size > 0:
        return float(counts[inner].max())
    return float(counts.max()) if counts.size else 1.0

# =============================================================================
# PLOT PDF
# =============================================================================

def plot_hist_pdf(delta_valid, sample_name, save_path, bins=HIST_BINS):
    counts, edges = np.histogram(delta_valid, bins=bins, range=(0, 360))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    colors = _bar_colors(centers)

    fig, ax = plt.subplots(figsize=(4.5, 2.8))
    ax.bar(centers, counts, width=widths, color=colors,
           edgecolor='none', align='center')

    ymax_inner = _inner_ymax(counts, centers)
    ax.set_xlim(0, 360)
    ax.set_ylim(0, ymax_inner * 1.25)
    ax.set_xticks(np.arange(0, 361, 60))
    ax.set_xlabel(r"$\delta$ (deg)")
    ax.set_ylabel("# pixel validi")
    ax.set_title(fr"Istogramma della retardance - {sample_name}", pad=6)
    ax.axvspan(0, HIST_EDGE_EXCLUDE_DEG, color='gray', alpha=0.08, linewidth=0)
    ax.axvspan(360 - HIST_EDGE_EXCLUDE_DEG, 360, color='gray',
               alpha=0.08, linewidth=0)
    ax.grid(True, axis='y', linestyle=':', alpha=0.4)

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path)
    plt.close(fig)
    print(f"  PDF salvato: {save_path}")

# =============================================================================
# PLOT HTML INTERATTIVO
# =============================================================================

def plot_hist_html(delta_valid, sample_name, save_path, bins=HIST_BINS):
    if not _PLOTLY_OK:
        print("  (avviso: plotly non disponibile, HTML non generato)")
        return False

    counts, edges = np.histogram(delta_valid, bins=bins, range=(0, 360))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    ymax_inner = _inner_ymax(counts, centers)

    cmap = plt.get_cmap(HIST_CMAP)
    bar_colors = [
        f"rgb({int(255*r)},{int(255*g)},{int(255*b)})"
        for r, g, b, _ in (cmap(c / 360.0) for c in centers)
    ]

    hover = (r"delta: %{x:.1f} deg<br>"
             r"# pixel: %{y}<extra></extra>")

    fig = go.Figure(
        data=go.Bar(
            x=centers,
            y=counts,
            width=widths,
            marker=dict(color=bar_colors, line=dict(width=0)),
            hovertemplate=hover,
            name=sample_name,
        )
    )
    # Shading per le zone escluse dal clip.
    fig.add_vrect(x0=0, x1=HIST_EDGE_EXCLUDE_DEG,
                  fillcolor='lightgray', opacity=0.25, line_width=0)
    fig.add_vrect(x0=360 - HIST_EDGE_EXCLUDE_DEG, x1=360,
                  fillcolor='lightgray', opacity=0.25, line_width=0)

    fig.update_layout(
        title=f"Istogramma della retardance - {sample_name}",
        xaxis=dict(title='delta (deg)', range=[0, 360],
                   tickmode='array', tickvals=list(range(0, 361, 30))),
        yaxis=dict(title='# pixel validi', range=[0, ymax_inner * 1.25]),
        bargap=0,
        width=900, height=500,
        margin=dict(l=60, r=30, t=60, b=50),
        template='simple_white',
    )
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        fig.write_html(save_path, include_plotlyjs='cdn', full_html=True)
        print(f"  HTML salvato: {save_path}")
        return True
    except Exception as e:
        print(f"  (avviso: HTML non scritto per {save_path}: {e})")
        return False

# =============================================================================
# BATCH
# =============================================================================

DATASET_DEFAULT = 'strati_v2'
CHANNELS = [(0, 'R'), (1, 'G'), (2, 'B')]


def run_dataset(dataset=DATASET_DEFAULT, images_root='../Images/generated',
                waveplate_swap=False):
    utils.TARGET_FOLDER = f'./raw/{dataset}'
    utils.POL_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'pol')
    utils.WAV_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'wav')
    utils.WAVEPLATE_AXES_SWAPPED = waveplate_swap

    out_pdf_dir = os.path.join(images_root, dataset)
    out_html_dir = os.path.join(images_root, dataset, 'interactive')

    t_total = time.time()
    for ch_idx, ch_label in CHANNELS:
        utils.TARGET_CHANNEL_IDX = ch_idx
        print(f"\n=== {dataset} / {ch_label} ===")
        t0 = time.time()

        maps = fu.compute_polarimetric_maps_fullres()
        if maps is None:
            print(f"  [{ch_label}] skip: carica RAW fallito")
            continue

        delta_valid = maps['delta_deg'].ravel()[maps['valid_indices']]
        delta_valid = delta_valid[np.isfinite(delta_valid)]
        print(f"  pixel validi: {delta_valid.size}")

        sample_name = f"{dataset} - canale {ch_label}"
        pdf_path = os.path.join(out_pdf_dir, f"{ch_label}_hist_delta.pdf")
        html_path = os.path.join(out_html_dir, f"{ch_label}_hist_delta.html")

        plot_hist_pdf(delta_valid, sample_name, pdf_path)
        plot_hist_html(delta_valid, sample_name, html_path)

        print(f"  [{ch_label}] elapsed: {time.time()-t0:.1f}s")

    print(f"\nTotal: {(time.time()-t_total)/60:.1f} min")


if __name__ == '__main__':
    run_dataset()
