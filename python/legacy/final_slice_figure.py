"""Slice diagonale di retardance per la tesi.

Riusa geometria, rilevamento plateaus e fit through-origin di
``final_slice_debug``; applica stile pubblicazione coerente con
``final_thesis_figure`` (serif, titoli italiani, 300 dpi). Per ogni canale
del dataset ``strati_v2`` produce:

- PDF pubblicabile in ``Images/generated/strati_v2/<CH>_slice.pdf`` con
  layout a 3 pannelli (mappa di retardance con banda sovrapposta, profilo
  1D con plateau etichettati, fit through-origin delta = m * n).
- HTML plotly interattivo in ``Images/generated/strati_v2/interactive/<CH>_slice.html``
  con il profilo 1D (hover = data cursor) e le barre dei plateau.
"""

import os
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try:
    import plotly.graph_objects as go
    _PLOTLY_OK = True
except ImportError:
    _PLOTLY_OK = False

import final_utils as utils
import final_slice_debug as fsd


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
    'image.interpolation': 'none',
})


DATASET_DEFAULT = 'strati_v2'
CHANNELS = [(0, 'R'), (1, 'G'), (2, 'B')]


# =============================================================================
# FIGURA PDF (3 pannelli)
# =============================================================================

def make_publication_figure(delta, t_vals, delta_slice, circ_std, X, Y,
                            center_ds, dataset_name, channel_char,
                            wavelength, crop_idx, plateaus, fit):
    cx_ds, cy_ds = center_ds
    crop_s, crop_e = crop_idx

    if fit is not None:
        fig, axes = plt.subplots(
            1, 3, figsize=(11.0, 3.6),
            gridspec_kw={'width_ratios': [1.0, 1.4, 0.7]})
    else:
        fig, axes = plt.subplots(
            1, 2, figsize=(8.5, 3.6),
            gridspec_kw={'width_ratios': [1.0, 1.3]})

    # --- Pannello mappa ---
    ax_map = axes[0]
    im = ax_map.imshow(delta, cmap='twilight', vmin=0, vmax=360, origin='upper')
    cbar = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.03)
    cbar.set_label(r'$\delta$ (°)')

    mid_col = X.shape[1] // 2
    sl = slice(crop_s, crop_e + 1)
    ax_map.plot(X[:, mid_col], Y[:, mid_col], '-', color='gray',
                lw=0.5, alpha=0.5)
    ax_map.plot(X[:, 0], Y[:, 0], 'w-', lw=0.4, alpha=0.4)
    ax_map.plot(X[:, -1], Y[:, -1], 'w-', lw=0.4, alpha=0.4)
    ax_map.plot(X[sl, mid_col], Y[sl, mid_col], 'r-', lw=1.0)
    ax_map.plot(X[sl, 0], Y[sl, 0], 'y-', lw=0.6, alpha=0.9)
    ax_map.plot(X[sl, -1], Y[sl, -1], 'y-', lw=0.6, alpha=0.9)
    ax_map.plot(cx_ds, cy_ds, 'r+', mew=1.5, ms=8)

    ax_map.set_xlim(0, delta.shape[1] - 1)
    ax_map.set_ylim(delta.shape[0] - 1, 0)
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    ax_map.set_title(fr'Mappa di $\delta$ - canale {channel_char} '
                     fr'($\lambda={wavelength:.0f}$ nm)', pad=6)

    # --- Pannello profilo 1D ---
    ax_prof = axes[1]
    arc_native = t_vals * utils.DOWNSAMPLE_FACTOR
    ax_prof.plot(arc_native[sl], delta_slice[sl], 'k-', lw=1.1,
                 label=r'$\delta$ medio (banda)')
    ax_prof.fill_between(arc_native[sl],
                         delta_slice[sl] - circ_std[sl],
                         delta_slice[sl] + circ_std[sl],
                         color='gray', alpha=0.25,
                         label=r'$\pm \sigma$ circolare')
    ax_prof.axhline(0, color='lightgray', lw=0.4)
    ax_prof.axhline(360, color='lightgray', lw=0.4)

    if plateaus:
        for p in plateaus:
            ax_prof.plot([p['arc_start'], p['arc_end']],
                         [p['delta_med'], p['delta_med']],
                         color='tab:red', lw=2.0, solid_capstyle='butt',
                         zorder=5)
            ax_prof.axvspan(p['arc_start'], p['arc_end'],
                            color='tab:red', alpha=0.05, zorder=0)
            ax_prof.annotate(
                f"{p['label']}\n{p['delta_med']:.1f}°",
                xy=(p['arc_mid'], p['delta_med']),
                xytext=(0, 10), textcoords='offset points',
                ha='center', va='bottom', fontsize=7, color='tab:red',
                bbox=dict(boxstyle='round,pad=0.2', fc='white',
                          ec='tab:red', lw=0.4, alpha=0.85),
                zorder=6)
        ax_prof.plot([], [], color='tab:red', lw=2.0,
                     label='plateau (mediana)')

    ax_prof.set_xlabel('ascissa curvilinea lungo la slice (px nativi)')
    ax_prof.set_ylabel(r'$\delta$ (°)')
    ax_prof.set_ylim(-10, 370)
    ax_prof.set_yticks(np.arange(0, 361, 60))
    ax_prof.grid(alpha=0.3)
    ax_prof.legend(loc='lower right', fontsize=7, framealpha=0.9)
    ax_prof.set_title(
        fr'Profilo lungo slice a {fsd.SLICE_ANGLE_DEG:.0f}° '
        f'(ancora ({fsd.SLICE_POINT_NATIVE_XY[0]}, '
        f'{fsd.SLICE_POINT_NATIVE_XY[1]}))', pad=6)

    # --- Pannello fit through-origin ---
    if fit is not None:
        ax_fit = axes[2]
        x_fit = fit['x']
        y_fit = fit['y']
        slope = fit['slope']

        for xi, yi, lbl in zip(x_fit, y_fit, fit['labels']):
            if lbl.endswith('L'):
                marker, color = 'o', 'tab:blue'
            elif lbl.endswith('R'):
                marker, color = 's', 'tab:orange'
            else:
                marker, color = 'D', 'tab:green'
            ax_fit.plot(xi, yi, marker=marker, color=color, ms=6,
                        markeredgecolor='k', markeredgewidth=0.5,
                        linestyle='none', zorder=3)
            ax_fit.annotate(lbl, (xi, yi), xytext=(4, 3),
                            textcoords='offset points', fontsize=6)

        x_max = float(x_fit.max())
        xs = np.array([0.0, x_max + 0.3])
        ax_fit.plot(xs, slope * xs, 'k--', lw=1.0,
                    label=fr'$\delta = {slope:.2f}\,n$')

        n_unw = int(fit.get('n_unwrapped', 0))
        if n_unw:
            ax_fit.plot(x_fit, fit['y_raw'], 'x', color='gray', ms=5,
                        alpha=0.5, zorder=2)

        ax_fit.set_xlim(0, x_max + 0.5)
        ymax = max(float(y_fit.max()) * 1.05,
                   slope * (x_max + 0.3) * 1.05, 360.0)
        ax_fit.set_ylim(0, ymax)
        ax_fit.set_xlabel(r'numero di strati $n$')
        ax_fit.set_ylabel(
            r'$\delta$ unwrap (°)' if n_unw else r'$\delta$ (°)')
        ax_fit.grid(alpha=0.3)
        unw_note = f" (+{n_unw} unwrap)" if n_unw else ""
        ax_fit.set_title(
            fr'Fit $\delta = m\,n${unw_note}' '\n'
            fr'$m={slope:.2f}$°/strato, $R^2={fit["r2"]:.3f}$',
            pad=6)

        handles = [
            Line2D([], [], marker='o', color='tab:blue', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='lato sinistro (L)'),
            Line2D([], [], marker='s', color='tab:orange', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='lato destro (R)'),
            Line2D([], [], marker='D', color='tab:green', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='centro'),
            Line2D([], [], color='k', linestyle='--', label='fit'),
        ]
        ax_fit.legend(handles=handles, loc='lower right', fontsize=6,
                      framealpha=0.9)

    fig.suptitle(fr'Slice diagonale - {dataset_name}, canale {channel_char}',
                 fontsize=11, y=1.02)
    fig.tight_layout()
    return fig


# =============================================================================
# HTML INTERATTIVO (profilo 1D + plateau)
# =============================================================================

def make_interactive_html(t_vals, delta_slice, circ_std, crop_idx, plateaus,
                          dataset_name, channel_char, wavelength, out_path):
    if not _PLOTLY_OK:
        print("  (avviso: plotly non disponibile, HTML non generato)")
        return False

    crop_s, crop_e = crop_idx
    sl = slice(crop_s, crop_e + 1)
    arc_native = t_vals * utils.DOWNSAMPLE_FACTOR

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=arc_native[sl],
        y=delta_slice[sl] + circ_std[sl],
        mode='lines', line=dict(width=0, color='gray'),
        showlegend=False, hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=arc_native[sl],
        y=delta_slice[sl] - circ_std[sl],
        mode='lines', line=dict(width=0, color='gray'),
        fill='tonexty', fillcolor='rgba(150,150,150,0.25)',
        name='± σ circolare', hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=arc_native[sl],
        y=delta_slice[sl],
        mode='lines', line=dict(color='black', width=1.5),
        name='δ medio (banda)',
        hovertemplate='ascissa: %{x:.0f} px<br>δ: %{y:.2f}°<extra></extra>',
    ))

    if plateaus:
        for p in plateaus:
            fig.add_trace(go.Scatter(
                x=[p['arc_start'], p['arc_end']],
                y=[p['delta_med'], p['delta_med']],
                mode='lines',
                line=dict(color='red', width=3),
                name=f"{p['label']}: {p['delta_med']:.1f}°",
                hovertemplate=(f"<b>{p['label']}</b><br>"
                               f"δ = {p['delta_med']:.2f}°<br>"
                               f"σ = {p['delta_std']:.2f}°<br>"
                               f"ascissa [{p['arc_start']:.0f}, "
                               f"{p['arc_end']:.0f}] px<extra></extra>"),
                showlegend=False,
            ))

    fig.update_layout(
        title=(f"Slice diagonale - {dataset_name}, canale {channel_char} "
               f"(λ = {wavelength:.0f} nm)"),
        xaxis=dict(title='ascissa curvilinea lungo la slice (px nativi)'),
        yaxis=dict(title='δ (°)', range=[-10, 370],
                   tickvals=list(range(0, 361, 60))),
        width=1000, height=520,
        margin=dict(l=70, r=30, t=70, b=60),
        template='simple_white',
        hovermode='x unified',
    )
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        fig.write_html(out_path, include_plotlyjs='cdn', full_html=True)
        print(f"  HTML salvato: {out_path}")
        return True
    except Exception as e:
        print(f"  (avviso: HTML non scritto per {out_path}: {e})")
        return False


# =============================================================================
# BATCH
# =============================================================================

def run_channel(dataset, channel_idx, channel_char, images_root):
    utils.TARGET_FOLDER = f'./raw/{dataset}'
    utils.POL_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'pol')
    utils.WAV_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'wav')
    utils.WAVEPLATE_AXES_SWAPPED = 'lambdamezzi' in dataset.lower()
    utils.TARGET_CHANNEL_IDX = channel_idx

    delta, _S0, _bg_mask, wavelength = fsd.run_pipeline()
    dataset_name = os.path.basename(utils.TARGET_FOLDER.rstrip('/').rstrip('\\'))

    t_vals, X, Y, center_ds, _dir, _perp = fsd.build_slice_grid(
        delta.shape,
        fsd.SLICE_POINT_NATIVE_XY,
        fsd.SLICE_ANGLE_DEG,
        utils.DOWNSAMPLE_FACTOR,
        fsd.SLICE_HALF_WIDTH_NATIVE_PX,
        fsd.SLICE_STEP_NATIVE_PX,
    )

    delta_slice, circ_std = fsd.sample_thick_slice(delta, X, Y)

    if fsd.AUTO_CROP_TO_SAMPLE:
        crop_idx = fsd.find_sample_crop(
            delta_slice, t_vals, utils.DOWNSAMPLE_FACTOR,
            fsd.AUTO_CROP_EDGE_MARGIN_DEG,
            fsd.AUTO_CROP_IGNORE_NATIVE_PX)
    else:
        crop_idx = (0, len(t_vals) - 1)

    plateaus = []
    if fsd.PLATEAU_DETECT:
        plateaus = fsd.detect_plateaus(
            delta_slice, t_vals, utils.DOWNSAMPLE_FACTOR, crop_idx,
            fsd.PLATEAU_SMOOTH_SIGMA_SAMPLES,
            fsd.PLATEAU_GRADIENT_THRESH_DEG,
            fsd.PLATEAU_MIN_LENGTH_NATIVE_PX,
            fsd.PLATEAU_LABELS)

    fit = None
    if fsd.LAYER_FIT_THROUGH_ORIGIN and plateaus:
        fit = fsd.fit_layers_through_origin(plateaus)

    fig = make_publication_figure(
        delta, t_vals, delta_slice, circ_std, X, Y, center_ds,
        dataset_name, channel_char, wavelength, crop_idx, plateaus, fit)

    out_pdf_dir = os.path.join(images_root, dataset_name)
    out_html_dir = os.path.join(images_root, dataset_name, 'interactive')
    os.makedirs(out_pdf_dir, exist_ok=True)
    pdf_path = os.path.join(out_pdf_dir, f'{channel_char}_slice.pdf')
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"  PDF salvato: {pdf_path}")

    html_path = os.path.join(out_html_dir, f'{channel_char}_slice.html')
    make_interactive_html(t_vals, delta_slice, circ_std, crop_idx, plateaus,
                          dataset_name, channel_char, wavelength, html_path)

    if fit is not None:
        print(f"  slope = {fit['slope']:.2f}°/strato, "
              f"R^2 = {fit['r2']:.3f}, "
              f"RMS = {fit['rms']:.2f}°, "
              f"unwrap = {fit.get('n_unwrapped', 0)}")


def run_dataset(dataset=DATASET_DEFAULT,
                images_root='../Images/generated'):
    t_total = time.time()
    for ch_idx, ch_label in CHANNELS:
        print(f"\n=== {dataset} / canale {ch_label} ===")
        t0 = time.time()
        run_channel(dataset, ch_idx, ch_label, images_root)
        print(f"  [{ch_label}] elapsed: {time.time()-t0:.1f}s")
    print(f"\nTotale: {(time.time()-t_total)/60:.1f} min")


if __name__ == '__main__':
    run_dataset()
