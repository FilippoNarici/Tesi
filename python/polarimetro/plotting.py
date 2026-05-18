"""Helper di plotting per figure della tesi.

Mattoni atomici: stile rcParams pubblicazione, save+show, mask overlay RGB.
La composizione di pannelli resta nelle celle del notebook.
"""
import os

import matplotlib.pyplot as plt
import numpy as np


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
