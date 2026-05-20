"""Visualizzazione 3-pannelli del cluster vincente HDBSCAN su UMAP.

Pannelli:
    1. Scatter UMAP colorato per AoLP o δ + cerchi rossi sui punti del cluster.
    2. Mappa spaziale del valore (AoLP o δ) con scatter rossi sui pixel del cluster.
    3. Istogramma del valore (tutti i pixel sample + overlay cluster scalato).

Usato dalle celle `D-aolp` e `D-delta` del notebook. La logica HDBSCAN +
statistica circolare resta in `umap_runner.cluster_umap_hdbscan_by_*`.
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from .plotting import save_and_show
from . import umap_runner as _umap


def plot_cluster_winner_panels(*, mode,
                                channel, dataset,
                                stokes_data_ch,
                                cache_entry,
                                cluster_masks, info, win_idx, labels,
                                output_dir,
                                save_plots=True, show=True,
                                hist_bins=180):
    """Compone figura 3-pannelli con winner cluster evidenziato.

    `mode` ∈ {'aolp', 'delta'} seleziona cmap, range, etichette assi e nome PDF.
    `cache_entry` = (embedding, aolp_2D, delta_2D, valid_indices, S0_shape).
    Salva PDF `{output_dir}/{dataset}/{channel}_{mode}_winner.pdf` e ritorna
    il path. None se nessun winner valido.
    """
    if win_idx < 0:
        return None

    embedding, _aolp_emb, _delta_emb, valid_indices, _S0_shape = cache_entry
    winner_info = info[win_idx]
    winner_label = winner_info['label']
    winner_mask_img = cluster_masks[win_idx]
    emb_winner_sel = labels == winner_label

    if mode == 'aolp':
        value_map = stokes_data_ch['AoLP']
        cmap = plt.get_cmap('viridis')
        sample_mask = ~stokes_data_ch['bg_mask']
        valid_pix = sample_mask & np.isfinite(value_map)
        all_vals = value_map[valid_pix]
        vmin, vmax = _umap.aolp_clip_range(all_vals)
        unit_label = 'AoLP (°)'
        delta_tex = r'$\psi$ (°)'
        median_fmt = '{:+.1f}°'
        cbar_extend = 'both'
        pdf_name = f"{channel}_aolp_winner.pdf"
        hist_title = f"{channel}: AoLP hist (winner overlay)"
        suptitle_value = f"AoLP median={winner_info['median_deg']:+.1f}°"
    elif mode == 'delta':
        value_map = stokes_data_ch['delta']
        cmap = plt.get_cmap('twilight')
        sample_mask = ~stokes_data_ch['bg_mask']
        valid_pix = sample_mask & np.isfinite(value_map)
        all_vals = value_map[valid_pix]
        vmin, vmax = 0.0, 360.0
        unit_label = r'$\delta$ (°)'
        delta_tex = r'$\delta$ (°)'
        median_fmt = '{:.1f}°'
        cbar_extend = 'neither'
        pdf_name = f"{channel}_delta_winner.pdf"
        hist_title = f"{channel}: δ hist (winner overlay)"
        suptitle_value = f"δ median={winner_info['median_deg']:.1f}°"
    else:
        raise ValueError(f"mode sconosciuto: {mode!r}")

    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    val_at_emb = value_map.ravel()[valid_indices]

    fig, axs = plt.subplots(1, 3, figsize=(13.5, 3.8))

    # Pannello 1 — UMAP scatter
    ax_s = axs[0]
    sc = ax_s.scatter(embedding[:, 0], embedding[:, 1],
                      c=val_at_emb, cmap=cmap, vmin=vmin, vmax=vmax,
                      s=2.5, alpha=0.85, edgecolors='none', rasterized=True)
    ax_s.scatter(embedding[emb_winner_sel, 0], embedding[emb_winner_sel, 1],
                 s=14, facecolors='none', edgecolors='red',
                 linewidths=0.6, alpha=0.9, rasterized=True,
                 label=f"winner (L{winner_label:+d})")
    ax_s.set_xlabel('UMAP 1'); ax_s.set_ylabel('UMAP 2')
    ax_s.set_title(f"{channel}: UMAP scatter", fontsize=9, pad=4)
    ax_s.legend(loc='best', fontsize=7, framealpha=0.85)
    fig.colorbar(sc, ax=ax_s, fraction=0.046, pad=0.03,
                  extend=cbar_extend, label=unit_label)

    # Pannello 2 — mappa spaziale + scatter rosso winner
    ax_m = axs[1]
    im = ax_m.imshow(value_map, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    yy, xx = np.nonzero(winner_mask_img)
    ax_m.scatter(xx, yy, s=2.0, c='red', alpha=0.6, edgecolors='none', rasterized=True)
    ax_m.set_title(
        f"{channel}: map (winner n={winner_info['size']}, "
        f"median={median_fmt.format(winner_info['median_deg'])})",
        fontsize=8, pad=4)
    ax_m.axis('off')
    fig.colorbar(im, ax=ax_m, fraction=0.046, pad=0.03,
                  extend=cbar_extend, label=unit_label)

    # Pannello 3 — istogramma (tutti i sample + overlay winner scalato)
    ax_h = axs[2]
    win_vals = value_map[winner_mask_img & sample_mask]
    counts_all, edges = np.histogram(all_vals, bins=hist_bins, range=(vmin, vmax))
    counts_win, _ = np.histogram(win_vals, bins=hist_bins, range=(vmin, vmax))
    emb_in_sample = int(sample_mask.ravel()[valid_indices].sum())
    scale_win = len(all_vals) / max(emb_in_sample, 1)
    counts_win_scaled = counts_win * scale_win
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_colors = [cmap(norm(c)) for c in centers]
    ax_h.bar(centers, counts_all, width=widths, color=bar_colors,
              edgecolor='none', align='center', label='tutti i pixel')
    ax_h.bar(centers, counts_win_scaled, width=widths, color='red',
              alpha=0.85, edgecolor='none', align='center',
              label=f'winner × {scale_win:.1f}')
    median_label = ("median = " + median_fmt.format(winner_info['median_deg']))
    ax_h.axvline(winner_info['median_deg'], color='darkred', linestyle='--',
                  linewidth=1.2, label=median_label)
    ymax = float(np.percentile(counts_all, 99)) if counts_all.size else 1.0
    ax_h.set_xlim(vmin, vmax)
    ax_h.set_ylim(0, ymax * 1.15)
    ax_h.set_xlabel(delta_tex)
    ax_h.set_ylabel('# pixel sample')
    ax_h.set_title(hist_title, fontsize=9, pad=4)
    ax_h.grid(True, axis='y', linestyle=':', alpha=0.4)
    ax_h.legend(loc='upper right', fontsize=7, framealpha=0.85)

    fig.suptitle(f"{dataset}/{channel}  —  winner L{winner_label:+d}  ({suptitle_value})",
                  fontsize=10, y=1.02)
    fig.tight_layout()

    out_path = None
    if save_plots:
        out_dir = os.path.join(output_dir, dataset)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, pdf_name)
    save_and_show(fig, out_path, show=show, fmt='pdf')
    plt.close(fig)
    return out_path
