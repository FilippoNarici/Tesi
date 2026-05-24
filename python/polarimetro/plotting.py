"""Helper di plotting per figure della tesi.

Mattoni atomici: stile rcParams pubblicazione, save+show, mask overlay RGB,
configurazione mappe Stokes/derivati, cmap per canale e istogramma δ con
plateau strati. La composizione finale dei pannelli resta nelle celle.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


# Configurazione delle 8 mappe pubblicate dalla cella B.
STOKES_PARAM_CONFIG = {
    'S0':    {'titolo': r'Intensità totale $S_0$',
              'unita': 'conteggi (u.a.)', 'cmap': None,
              'vmin': None, 'vmax': None},
    'S1':    {'titolo': r'Parametro di Stokes $S_1$',
              'unita': 'conteggi (u.a.)', 'cmap': 'bwr',
              'vmin': 'sym99', 'vmax': 'sym99'},
    'S2':    {'titolo': r'Parametro di Stokes $S_2$',
              'unita': 'conteggi (u.a.)', 'cmap': 'bwr',
              'vmin': 'sym99', 'vmax': 'sym99'},
    'S3':    {'titolo': r'Parametro di Stokes $S_3$',
              'unita': 'conteggi (u.a.)', 'cmap': 'bwr',
              'vmin': 'sym99', 'vmax': 'sym99'},
    'DoLP':  {'titolo': r'Grado di polarizzazione lineare (DoLP)',
              'unita': None, 'cmap': 'viridis',
              'vmin': 0, 'vmax': 1},
    'AoLP':  {'titolo': r'Angolo di polarizzazione lineare (AoLP)',
              'unita': '°', 'cmap': 'twilight',
              'vmin': -90, 'vmax': 90},
    'delta': {'titolo': r'Ritardo di fase $\delta$',
              'unita': '°', 'cmap': 'twilight',
              'vmin': 0, 'vmax': 360},
    'theta': {'titolo': r'Asse veloce $\theta$',
              'unita': '°', 'cmap': 'twilight',
              'vmin': 0, 'vmax': 90},
}

STOKES_PARAM_ORDER = ('S0', 'S1', 'S2', 'S3', 'DoLP', 'AoLP', 'delta', 'theta')

# cmap monocromatica nero→colore_canale per S0 (R, G, B).
_S0_CMAPS_BY_INDEX = {
    0: LinearSegmentedColormap.from_list('nero_rosso', ['black', 'red']),
    1: LinearSegmentedColormap.from_list('nero_verde', ['black', 'green']),
    2: LinearSegmentedColormap.from_list('nero_blu',   ['black', 'blue']),
}


def make_s0_cmap(channel_idx):
    """Restituisce cmap nero→rosso/verde/blu per il canale dato."""
    return _S0_CMAPS_BY_INDEX[channel_idx]


def apply_thesis_style():
    """rcParams stile pubblicazione: serif, font scalati, dpi 300, bbox tight."""
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
        'image.interpolation': 'none',
    })


def save_and_show(fig, path, show=True, fmt='pdf'):
    """Salva fig su path e (opzionale) plt.show(). Crea dir parent se manca."""
    if path is not None:
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        fig.savefig(path, format=fmt)
        print(f"  saved: {path}")
    if show:
        plt.show()


def plot_mask_overlay_figure(S0_bg, bg_mask, poincare_mask, wav_mean,
                              title, out_pdf, show=True, fig_w=3.35):
    """Costruisce figura overlay maschere bg + Poincaré e la salva.

    Sopra `mask_overlay_rgb`, aggiunge titolo + legenda 3-patch:
    grigio = entrambe (bg utile), blu = XOR (wav debug), rosso = nessuna
    (sample). Chiude la figura.
    """
    from matplotlib.patches import Patch
    overlay = mask_overlay_rgb(S0_bg, bg_mask, poincare_mask, wav_mean=wav_mean)
    H, W, _ = overlay.shape
    aspect = H / W
    fig, ax = plt.subplots(figsize=(fig_w + 0.2, fig_w * aspect))
    ax.imshow(overlay, aspect='equal')
    ax.set_title(title, pad=6)
    ax.axis('off')
    handles = [
        Patch(facecolor='#bfbfbf', edgecolor='none', label='entrambe (S0)'),
        Patch(facecolor='#0040ff', edgecolor='none', label='XOR (wav debug)'),
        Patch(facecolor='#ff0000', edgecolor='none', label='nessuna (sample)'),
    ]
    ax.legend(handles=handles, loc='lower right', fontsize=6,
              framealpha=0.85, handlelength=1.2,
              borderpad=0.3, labelspacing=0.25)
    save_and_show(fig, out_pdf, show=show, fmt='pdf')
    plt.close(fig)


def resolve_sym_limits(data, vmin_spec, vmax_spec):
    """Risolve specifiche `'sym99'` → ±(99-percentile di |data|), else passthrough."""
    if vmin_spec == 'sym99':
        bound = float(np.nanpercentile(np.abs(data), 99))
        return -bound, bound
    return vmin_spec, vmax_spec


def mpl_cmap_to_plotly_scale(cmap, n=64):
    """Converte cmap matplotlib (nome o oggetto) in scala plotly (lista [s, 'rgb(...)'])."""
    cmap_obj = plt.get_cmap(cmap) if isinstance(cmap, str) else cmap
    scale = []
    for s in np.linspace(0.0, 1.0, n):
        r, g, b, _ = cmap_obj(float(s))
        scale.append([float(s), f"rgb({int(255*r)},{int(255*g)},{int(255*b)})"])
    return scale


def make_param_figure(data, *, title, unit, cmap, vmin, vmax, fig_w=3.35):
    """Figura mappa parametro (imshow + colorbar). Restituisce fig (non chiude).

    vmin/vmax accettano `'sym99'`. Caller fa save+close.
    """
    vmin_r, vmax_r = resolve_sym_limits(data, vmin, vmax)
    H, W = data.shape
    aspect = H / W
    fig, ax = plt.subplots(figsize=(fig_w + 0.7, fig_w * aspect))
    im = ax.imshow(data, cmap=cmap, vmin=vmin_r, vmax=vmax_r, aspect='equal')
    ax.set_title(title, pad=6)
    ax.axis('off')
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    if unit:
        cbar.set_label(unit)
    return fig


def save_param_html(data, out_path, *, title, unit, cmap, vmin, vmax):
    """Heatmap plotly interattivo (CDN). vmin/vmax accettano `'sym99'`.

    Restituisce True se scritto, False se plotly assente o errore I/O.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return False
    vmin_r, vmax_r = resolve_sym_limits(data, vmin, vmax)
    H, W = data.shape
    fig = go.Figure(data=go.Heatmap(
        z=data,
        colorscale=mpl_cmap_to_plotly_scale(cmap),
        zmin=vmin_r, zmax=vmax_r,
        hovertemplate='x: %{x}<br>y: %{y}<br>valore: %{z:.4g}<extra></extra>',
        colorbar=dict(title=unit or ''),
    ))
    fig.update_layout(
        title=title,
        xaxis=dict(scaleanchor='y', constrain='domain'),
        yaxis=dict(autorange='reversed'),
        width=min(1000, 80 + W),
        height=min(900, 80 + H),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    try:
        fig.write_html(out_path, include_plotlyjs='cdn', full_html=True)
        return True
    except Exception as e:
        print(f"  (avviso: HTML plotly non scritto per {out_path}: {e})")
        return False


def fmt_sci(value):
    """Notazione scientifica LaTeX `coeff · 10^{exp}` con 2 cifre coeff."""
    if value == 0:
        return "0"
    exponent = int(np.floor(np.log10(abs(value))))
    coeff = value / (10 ** exponent)
    return rf"{coeff:.2f} \cdot 10^{{{exponent}}}"


def mask_overlay_rgb(S0, bg_mask, poincare_mask, wav_mean=None):
    """Costruisce overlay (H, W, 3) per visualizzare le due maschere bg.

    Codifica:
      * both (bg_mask & poincare_mask)  -> grayscale S0 (bg utile per S1/S2 e Poincare)
      * xor  (bg_mask ^ poincare_mask)  -> gradient nero->blu da wav_mean (se data)
                                           altrimenti rosso 0.5 * S0
      * neither                          -> rosso pieno x S0 (sample o fuori scena)
    """
    S0n = (S0 - np.min(S0)) / (np.max(S0) - np.min(S0) + 1e-8)
    if poincare_mask is None or poincare_mask.shape != bg_mask.shape:
        poincare_mask = np.zeros_like(bg_mask)

    both = bg_mask & poincare_mask
    xor = bg_mask ^ poincare_mask
    neither = (~bg_mask) & (~poincare_mask)

    rgb = np.zeros((*bg_mask.shape, 3), dtype=np.float32)
    rgb[both, 0] = S0n[both]
    rgb[both, 1] = S0n[both]
    rgb[both, 2] = S0n[both]
    if wav_mean is not None and wav_mean.shape == bg_mask.shape:
        wav_n = wav_mean / (float(wav_mean.max()) + 1e-8)
        rgb[xor, 2] = wav_n[xor]
    else:
        rgb[xor, 0] = 0.5 * S0n[xor]
    rgb[neither, 0] = S0n[neither]

    return np.clip(rgb, 0, 1)


# Etichette plateau strati (1L..5..1R) → frazione y nell'asse per posizionare le label.
# Step di 0.04 dal basso (1L) verso l'alto (1R) → griglia leggibile senza sovrapposizioni.
STRATI_LABEL_Y_FRAC = {
    '1L': 0.62, '2L': 0.66, '3L': 0.70, '4L': 0.74,
    '5':  0.78,
    '4R': 0.82, '3R': 0.86, '2R': 0.90, '1R': 0.94,
}


def plot_delta_strati_histogram(delta_values, layer_delta_wrap, labels,
                                 *, title, out_pdf=None, show=True,
                                 hist_bins=180, edge_exclude_deg=20.0,
                                 figsize=(3.6, 2.6), cmap_name='twilight'):
    """Istogramma δ ∈ [0°, 360°) con plateau strati come vline + etichetta.

    `delta_values`: 1D array dei δ del sample (già filtrato bg+NaN).
    `layer_delta_wrap`: array di δ wrap-360 per ogni plateau.
    `labels`: lista di etichette stesso ordine di `layer_delta_wrap`
        (es. '1L', '2L', ..., '5', ..., '1R'). Mappato in y via `STRATI_LABEL_Y_FRAC`.
    `edge_exclude_deg`: zone grigie ai due estremi (0°/360°) dove il wrap rende
        l'istogramma poco informativo; ymax calcolato escludendole.
    Restituisce la figura (chiusa dopo il save).
    """
    cmap = plt.get_cmap(cmap_name)
    counts, edges = np.histogram(delta_values, bins=hist_bins, range=(0.0, 360.0))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_colors = [cmap(c / 360.0) for c in centers]

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(centers, counts, width=widths, color=bar_colors,
            edgecolor='none', align='center')

    if edge_exclude_deg > 0.0:
        inner = ((centers > edge_exclude_deg)
                 & (centers < 360.0 - edge_exclude_deg))
        ymax = (float(counts[inner].max())
                 if (inner.any() and counts[inner].size)
                 else (float(counts.max()) if counts.size else 1.0))
        ax.set_ylim(0, ymax * 1.45)
        ax.axvspan(0.0, edge_exclude_deg, color='gray', alpha=0.08)
        ax.axvspan(360.0 - edge_exclude_deg, 360.0, color='gray', alpha=0.08)
    else:
        ymax = float(np.percentile(counts, 99)) if counts.size else 1.0
        ax.set_ylim(0, ymax * 1.35)

    trans = ax.get_xaxis_transform()
    for delta_wrap, lbl in zip(layer_delta_wrap, labels):
        ax.axvline(float(delta_wrap), color='black', lw=0.7,
                    linestyle='--', alpha=0.6)
        yfrac = STRATI_LABEL_Y_FRAC.get(lbl, 0.94)
        ax.text(float(delta_wrap), yfrac, lbl, transform=trans,
                 ha='center', va='top', fontsize=6, rotation=90,
                 color='black',
                 bbox=dict(facecolor='white', alpha=0.85,
                           edgecolor='none', pad=0.6))

    ax.set_xlim(0.0, 360.0)
    ax.set_xlabel(r'$\delta$ (°)')
    ax.set_ylabel('# pixel sample')
    ax.set_title(title, pad=4, fontsize=9)
    ax.grid(True, axis='y', linestyle=':', alpha=0.4)

    save_and_show(fig, out_pdf, show=show, fmt='pdf')
    plt.close(fig)
    return counts, edges, bar_colors


def save_delta_strati_histogram_html(delta_values, layer_delta_wrap,
                                      layer_delta_unwrap, labels,
                                      out_html, *, title,
                                      hist_bins=180, cmap_name='twilight'):
    """Variante interattiva plotly di `plot_delta_strati_histogram`.

    Mostra hover con δ wrap + δ unwrap di ogni plateau. Restituisce True
    se scritto, False se plotly manca o I/O fallisce.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        return False
    cmap = plt.get_cmap(cmap_name)
    counts, edges = np.histogram(delta_values, bins=hist_bins, range=(0.0, 360.0))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_rgb = [f'rgb({int(255*c[0])},{int(255*c[1])},{int(255*c[2])})'
                for c in (cmap(v / 360.0) for v in centers)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=centers, y=counts, width=widths,
                          marker_color=bar_rgb, name='counts'))
    for delta_wrap, delta_unw, lbl in zip(layer_delta_wrap, layer_delta_unwrap, labels):
        fig.add_vline(x=float(delta_wrap), line_dash='dash', line_color='black',
                       annotation_text=f'{lbl} (δ_unw={delta_unw:.0f}°)',
                       annotation_position='top')
    fig.update_layout(
        title=title,
        xaxis_title='δ (°)', yaxis_title='# pixel sample',
        xaxis=dict(range=[0, 360]),
        template='plotly_white', width=780, height=420,
    )
    try:
        fig.write_html(out_html, include_plotlyjs='cdn')
        return True
    except Exception as e:
        print(f"  (avviso: HTML hist δ non scritto: {e})")
        return False
