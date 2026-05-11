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
