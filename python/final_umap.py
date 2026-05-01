"""UMAP embedding of the polarimetric Stokes maps (sparse-grid variant).

Il flusso di elaborazione dell'intera pipeline gira a ``DOWNSAMPLE_FACTOR``
come sempre, ma **solo** per UMAP questo script forza la lettura e il calcolo
degli Stokes a risoluzione nativa (``downsample_factor=1``) e poi campiona un
sottoinsieme sparso di pixel con passo ``UMAP_SPARSE_STRIDE``. In questo modo
UMAP riceve valori per-pixel non mediati (niente blur da block-average) ma il
numero di punti resta lo stesso del vecchio downsampling a blocchi, in modo
che il tempo di fit non esploda.

Il vettore di feature per ogni pixel campionato e': (s1, s2, s3, DoLP, delta)
con s_i = S_i/S_0 componenti di Stokes normalizzate, DoLP grado di
polarizzazione lineare, delta retardance in gradi su [0, 360). La retardance
entra come numero reale; la sua ciclicita' (359 deg e 1 deg sono vicini) non
e' rispettata dalla metrica euclidea, ma per i campioni di calibrazione il
valore resta lontano dai bordi e l'effetto e' trascurabile. Se in futuro si
volesse trattarla correttamente, sostituire ``delta`` con ``(sin delta,
cos delta)`` nel costruttore delle feature.

Output di default: figura a 3 pannelli (mappa AoLP | UMAP scatter | istogramma
AoLP), tutti colorati con cmap sequenziale ``viridis`` e autoscala via
percentili 1-99 sui pixel validi (la ciclicita' a 180 deg e' irrilevante:
distribuzioni reali stanno lontane dai bordi). AoLP e' calcolato dopo
``align_reference_frame``/``align_poincare_ellipticity``, quindi e' l'angolo di
polarizzazione lineare nel frame in cui il bg e' su S1 (bg-zeroed). Il
coloraggio per delta (legacy) resta disponibile via ``color_by='delta'``.

Questo script NON modifica ``utils.DOWNSAMPLE_FACTOR``: il downsample globale
del resto della pipeline rimane intatto.
"""

import os
import re
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

import final_utils as utils

# Anchor cwd a python/ all'import. Tutti i path relativi del progetto
# (./raw, ./outputs, ../Images/generated, ./raw/dark.dng in final_utils)
# assumono cwd = python/. Permette di lanciare lo script da PyCharm con
# working directory impostata alla root del repo (Tesi/) senza riconfigurare
# tutti i path. Idempotente: se gia' in python/, non fa nulla.
_PYDIR = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(os.getcwd()) != _PYDIR:
    print(f"[final_umap] chdir -> {_PYDIR}")
    os.chdir(_PYDIR)

try:
    matplotlib.use('TkAgg')
except Exception:
    pass

# Stile pubblicazione (coerente con final_delta_histogram / final_thesis_figure).
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 150,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'mathtext.fontset': 'cm',
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
})

# =============================================================================
# UMAP CONFIGURATION
# =============================================================================

UMAP_SPARSE_STRIDE = 20
UMAP_FIT_SAMPLE = 20000
UMAP_N_NEIGHBORS = 80
UMAP_MIN_DIST = 0.008
UMAP_METRIC = 'euclidean'

DOLP_MIN = 0.20
S0_MIN = 1e-6
RANDOM_STATE = 42
HIST_EDGE_EXCLUDE_DEG = 20.0

# Cmap AoLP autoscala: cmap sequenziale + clip percentile (cicli a 180 gradi
# non rilevante: distribuzioni reali stanno lontane dai bordi).
AOLP_CMAP = 'viridis'
AOLP_CLIP_PCT = (1.0, 99.0)

# =============================================================================
# FEATURE EXTRACTION
# =============================================================================

def _normalize_stokes(S0, S1, S2, S3):
    """Restituisce (s1, s2, s3) = (S1, S2, S3) / S0 con guardia su S0 piccolo."""
    safe_S0 = np.where(np.abs(S0) < S0_MIN, np.nan, S0)
    s1 = S1 / safe_S0
    s2 = S2 / safe_S0
    s3 = (S3 / safe_S0) if S3 is not None else np.zeros_like(S0)
    return s1, s2, s3

def _build_feature_matrix(S0, S1, S2, S3, DoLP, delta_deg, valid_mask,
                          feature_mode='full'):
    """feature_mode:
    - 'full': (s1, s2, s3, DoLP, delta_deg)
    - 'no_delta': (s1, s2, s3, DoLP) — utile per verificare se UMAP trova
      comunque la struttura senza l'hint esplicito di delta.
    """
    s1, s2, s3 = _normalize_stokes(S0, S1, S2, S3)
    flat_valid = valid_mask.ravel()
    cols = [s1.ravel(), s2.ravel(), s3.ravel(), DoLP.ravel()]
    if feature_mode == 'full':
        cols.append(delta_deg.ravel())
    elif feature_mode != 'no_delta':
        raise ValueError(f"feature_mode sconosciuto: {feature_mode}")
    features = np.column_stack(cols)[flat_valid]
    valid_indices = np.flatnonzero(flat_valid)
    return features.astype(np.float32), valid_indices

def _build_validity_mask(S0, DoLP, bg_mask, sat_mask=None):
    sample_mask = ~bg_mask
    finite = (np.isfinite(S0) & np.isfinite(DoLP)
              & (np.abs(S0) >= S0_MIN))
    bright_enough = DoLP >= DOLP_MIN
    valid = sample_mask & finite & bright_enough
    if sat_mask is not None:
        valid &= ~sat_mask
    return valid

def _sparse_grid_mask(shape, stride):
    """Booleana con True ogni ``stride`` pixel su entrambi gli assi."""
    mask = np.zeros(shape, dtype=bool)
    mask[::stride, ::stride] = True
    return mask

def _block_mean(arr, factor):
    """Media per blocchi ``factor x factor`` (crop ai multipli del factor)."""
    if factor <= 1:
        return arr
    H, W = arr.shape
    Hc, Wc = H - (H % factor), W - (W % factor)
    arr = arr[:Hc, :Wc]
    return arr.reshape(Hc // factor, factor, Wc // factor, factor).mean(axis=(1, 3))

def _bg_mask_native_resolution(S0_full, downsample_factor):
    """Genera la maschera di background al DOWNSAMPLE_FACTOR standard, poi la
    riporta a risoluzione nativa con nearest-neighbor upsample.

    A risoluzione nativa il Sobel di ``generate_background_mask`` reagisce al
    rumore fotonico per-pixel e produce una copertura edge del 70% circa che
    cancella il background dopo erosione. Calcolare la maschera al DOWNSAMPLE
    standard e poi upsamplarla restituisce lo stesso bg che il resto della
    pipeline del progetto utilizza: i risultati di UMAP sono cosi' coerenti
    con le mappe di retardance della tesi.
    """
    S0_ds = _block_mean(S0_full, downsample_factor)
    bg_ds = utils.generate_background_mask(S0_ds)
    H_full, W_full = S0_full.shape
    bg_full = np.repeat(np.repeat(bg_ds, downsample_factor, axis=0),
                        downsample_factor, axis=1)
    # Crop/pad ai confini per far corrispondere la shape nativa esatta.
    bg_native = np.zeros((H_full, W_full), dtype=bool)
    h, w = bg_full.shape
    h_cp = min(h, H_full)
    w_cp = min(w, W_full)
    bg_native[:h_cp, :w_cp] = bg_full[:h_cp, :w_cp]
    return bg_native

# =============================================================================
# UMAP FIT
# =============================================================================

def _fit_umap(features, delta_valid=None, theta_valid=None, aolp_valid=None):
    import umap

    n_points = features.shape[0]
    if n_points == 0:
        return np.empty((0, 2), dtype=np.float32)

    if UMAP_FIT_SAMPLE < n_points:
        rng = np.random.default_rng(RANDOM_STATE)
        fit_idx = rng.choice(n_points, size=UMAP_FIT_SAMPLE, replace=False)
        fit_features = features[fit_idx]
    else:
        fit_features = features

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric=UMAP_METRIC,
        random_state=RANDOM_STATE,
    )
    reducer.fit(fit_features)
    embedding = reducer.transform(features).astype(np.float32)

    print("\nUMAP interpretability (Pearson r):")
    if delta_valid is not None and theta_valid is not None:
        r1_d, _ = pearsonr(embedding[:, 0], delta_valid)
        r2_d, _ = pearsonr(embedding[:, 1], delta_valid)
        r1_t, _ = pearsonr(embedding[:, 0], theta_valid)
        r2_t, _ = pearsonr(embedding[:, 1], theta_valid)
        print(f"  UMAP1 <-> delta : {r1_d:+.3f}   |   UMAP1 <-> theta : {r1_t:+.3f}")
        print(f"  UMAP2 <-> delta : {r2_d:+.3f}   |   UMAP2 <-> theta : {r2_t:+.3f}")
    if aolp_valid is not None:
        # AoLP cyclic period 180: project to (sin 2psi, cos 2psi) for proper r.
        s = np.sin(np.deg2rad(2.0 * aolp_valid))
        c = np.cos(np.deg2rad(2.0 * aolp_valid))
        r1_s, _ = pearsonr(embedding[:, 0], s)
        r2_s, _ = pearsonr(embedding[:, 1], s)
        r1_c, _ = pearsonr(embedding[:, 0], c)
        r2_c, _ = pearsonr(embedding[:, 1], c)
        print(f"  UMAP1 <-> sin2psi : {r1_s:+.3f}   |   UMAP1 <-> cos2psi : {r1_c:+.3f}")
        print(f"  UMAP2 <-> sin2psi : {r2_s:+.3f}   |   UMAP2 <-> cos2psi : {r2_c:+.3f}")

    return embedding

# =============================================================================
# PLOTTING
# =============================================================================

def plot_retardance_and_umap(embedding, delta_deg, valid_indices,
                             sample_name=''):
    fig, (ax_map, ax_umap) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"Polarimetric UMAP - {sample_name}", fontsize=14)

    im_delta = ax_map.imshow(delta_deg, cmap='twilight', vmin=0, vmax=360)
    ax_map.set_title(r"(a) Retardance $\delta$ (deg) - full-res")
    ax_map.axis('off')
    cbar_a = fig.colorbar(im_delta, ax=ax_map, fraction=0.046, pad=0.04)
    cbar_a.set_label(r"$\delta$ (deg)")

    delta_valid = delta_deg.ravel()[valid_indices]
    sc = ax_umap.scatter(embedding[:, 0], embedding[:, 1],
                         c=delta_valid, cmap='twilight',
                         vmin=0, vmax=360, s=1.5, alpha=0.9)
    ax_umap.set_title(r"(b) UMAP embedding coloured by $\delta$")
    ax_umap.set_xlabel("UMAP 1")
    ax_umap.set_ylabel("UMAP 2")
    cbar_b = fig.colorbar(sc, ax=ax_umap, fraction=0.046, pad=0.04)
    cbar_b.set_label(r"$\delta$ (deg)")

    plt.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def _aolp_clip_range(aolp_valid, pct=AOLP_CLIP_PCT):
    """Clip percentile (default 1-99) sui pixel finiti per dare contrasto.
    Fallback al range pieno [-90, 90] se distribuzione degenere.
    """
    finite = aolp_valid[np.isfinite(aolp_valid)]
    if finite.size == 0:
        return -90.0, 90.0
    vmin, vmax = np.percentile(finite, pct)
    if vmax - vmin < 1.0:
        return -90.0, 90.0
    return float(vmin), float(vmax)


def plot_aolp_umap_hist(embedding, aolp_deg, valid_indices, sample_name='',
                        hist_bins=180):
    """Figura 3-pannelli colorata per AoLP (mappa | UMAP | istogramma).

    AoLP in [-90, 90] deg. Colormap sequenziale ``viridis`` con autoscala via
    percentili (default 1-99) calcolati sui pixel validi: distribuzioni reali
    stanno lontane dai bordi e una scala fissa [-90, 90] sprecava la dinamica
    della cmap. La ciclicita' a 180 deg non e' rilevante perche' i campioni
    polarimetrici reali non si avvicinano mai ai bordi della finestra.
    """
    fig = plt.figure(figsize=(16, 5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.0])
    ax_map = fig.add_subplot(gs[0])
    ax_umap = fig.add_subplot(gs[1])
    ax_hist = fig.add_subplot(gs[2])
    fig.suptitle(f"Polarimetric UMAP + AoLP - {sample_name}", fontsize=14)

    aolp_valid = aolp_deg.ravel()[valid_indices]
    vmin, vmax = _aolp_clip_range(aolp_valid)
    cmap = plt.get_cmap(AOLP_CMAP)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    print(f"  AoLP cmap range (1-99 pct): [{vmin:+.2f}, {vmax:+.2f}] deg")

    # (a) AoLP map full-res.
    im = ax_map.imshow(aolp_deg, cmap=cmap, vmin=vmin, vmax=vmax)
    ax_map.set_title(r"(a) AoLP $\psi$ (deg) - full-res")
    ax_map.axis('off')
    cbar_a = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04, extend='both')
    cbar_a.set_label(r"$\psi$ (deg)")

    # (b) UMAP scatter colorato per AoLP.
    sc = ax_umap.scatter(embedding[:, 0], embedding[:, 1],
                         c=aolp_valid, cmap=cmap,
                         vmin=vmin, vmax=vmax, s=1.5, alpha=0.9)
    ax_umap.set_title(r"(b) UMAP embedding coloured by $\psi$")
    ax_umap.set_xlabel("UMAP 1")
    ax_umap.set_ylabel("UMAP 2")
    cbar_b = fig.colorbar(sc, ax=ax_umap, fraction=0.046, pad=0.04, extend='both')
    cbar_b.set_label(r"$\psi$ (deg)")

    # (c) Istogramma AoLP, barre colorate per valore + y-axis clip al massimo
    # dei bin centrali (ignora i tail del clip cmap) per non saturare la scala
    # con eventuali picchi residui di sfondo.
    aolp_finite = aolp_valid[np.isfinite(aolp_valid)]
    counts, edges = np.histogram(aolp_finite, bins=hist_bins,
                                 range=(vmin, vmax))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    colors = [cmap(norm(c)) for c in centers]
    ax_hist.bar(centers, counts, width=widths, color=colors,
                edgecolor='none', align='center')
    ymax = float(np.percentile(counts, 99)) if counts.size else 1.0
    ax_hist.set_xlim(vmin, vmax)
    ax_hist.set_ylim(0, ymax * 1.15)
    ax_hist.set_xlabel(r"$\psi$ (deg)")
    ax_hist.set_ylabel("# pixel validi")
    ax_hist.set_title(r"(c) Istogramma $\psi$")
    ax_hist.grid(True, axis='y', linestyle=':', alpha=0.4)

    plt.tight_layout(rect=(0, 0, 1, 0.94))
    return fig

# =============================================================================
# MAIN
# =============================================================================

def plot_delta_histogram(delta_valid, sample_name, save_path, bins=180):
    """Istogramma di delta sui pixel validi su [0, 360), 2 gradi per bin di
    default. L'asse y viene clippato al massimo dei bin centrali (ignora i
    primi e gli ultimi ``HIST_EDGE_EXCLUDE_DEG`` gradi) perche' i residui di
    sfondo a basso DoLP producono picchi artificiali vicino a 0 e 360 che
    nascondono la struttura per-strato.
    """
    fig, ax = plt.subplots(figsize=(7, 4))
    counts, edges, _ = ax.hist(delta_valid, bins=bins, range=(0, 360),
                               color='steelblue', edgecolor='none')
    centers = 0.5 * (edges[:-1] + edges[1:])
    inner = (centers > HIST_EDGE_EXCLUDE_DEG) & (centers < 360 - HIST_EDGE_EXCLUDE_DEG)
    ymax_inner = counts[inner].max() if inner.any() and counts[inner].size > 0 else counts.max()
    ax.set_xlim(0, 360)
    ax.set_ylim(0, ymax_inner * 1.25)
    ax.set_xlabel(r"$\delta$ (deg)")
    ax.set_ylabel("# pixel validi")
    ax.set_title(fr"Istogramma $\delta$ - {sample_name}")
    ax.axvspan(0, HIST_EDGE_EXCLUDE_DEG, color='gray', alpha=0.08)
    ax.axvspan(360 - HIST_EDGE_EXCLUDE_DEG, 360, color='gray', alpha=0.08)
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Istogramma salvato: {save_path}")


def compute_polarimetric_maps_fullres(sparse_stride=None):
    """Carica RAW, calcola Stokes + DoLP + delta + theta a risoluzione nativa e
    prepara la maschera sparse-grid di validita'. NON modifica le globals della
    pipeline: ``utils.DOWNSAMPLE_FACTOR`` resta invariato, qui si forza solo il
    caricamento a ``downsample_factor=1``. Riusato da ``run`` (UMAP) e dal
    modulo ``final_delta_histogram`` per gli istogrammi pubblicabili.

    Restituisce un dict con: S0, S1_al, S2_al, S3, DoLP, delta_deg, theta_deg,
    bg_mask, sat_mask, valid_mask_sparse, valid_indices (flat).
    """
    stride = sparse_stride if sparse_stride is not None else UMAP_SPARSE_STRIDE
    utils.reset_saturation_accumulator()

    angles, stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
        downsample_factor=1, invert_angles=True)
    if stack is None or angles is None:
        return None

    S0, S1, S2 = utils.calculate_linear_stokes(angles, stack)
    wavelength = utils.get_channel_wavelength(utils.WAVELENGTHS_CSV,
                                              utils.TARGET_CHANNEL_IDX)
    S3 = utils.calculate_s3(utils.WAV_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
                            1, wavelength)

    bg_mask = _bg_mask_native_resolution(S0, utils.DOWNSAMPLE_FACTOR)
    S1_al, S2_al = utils.align_reference_frame(S1, S2, bg_mask)
    S1_al, S3 = utils.align_poincare_ellipticity(S0, S1_al, S3, bg_mask)
    DoLP, AoLP_deg = utils.calculate_dolp_aolp(S0, S1_al, S2_al)
    delta_deg, theta_deg = utils.calculate_retardance_and_fast_axis(
        S0, S1_al, S2_al, S3, bg_mask, smooth_sigma=0)

    sat_mask = utils.get_saturation_mask(1)
    if sat_mask is not None and sat_mask.any():
        for arr in (DoLP, AoLP_deg, delta_deg, theta_deg):
            if arr is not None:
                arr[sat_mask] = np.nan

    grid_mask = _sparse_grid_mask(S0.shape, stride)
    base_valid = _build_validity_mask(S0, DoLP, bg_mask, sat_mask)
    valid_mask = base_valid & grid_mask
    valid_indices = np.flatnonzero(valid_mask.ravel())
    return {
        'S0': S0, 'S1_al': S1_al, 'S2_al': S2_al, 'S3': S3,
        'DoLP': DoLP, 'AoLP_deg': AoLP_deg,
        'delta_deg': delta_deg, 'theta_deg': theta_deg,
        'bg_mask': bg_mask, 'sat_mask': sat_mask,
        'valid_mask_sparse': valid_mask, 'valid_indices': valid_indices,
        'sparse_stride': stride,
    }


def run(sample_name=None, show=True, save_path=None, sparse_stride=None,
        feature_mode='no_delta', histogram_path=None, color_by='aolp'):
    """Esegue UMAP sul dataset corrente (globals di ``final_utils``).

    feature_mode: 'no_delta' (default, feature = (s1, s2, s3, DoLP), pure
    Poincaré + magnitude — UMAP trova la struttura senza l'hint esplicito di
    delta che dominava euclidean per via della scala in gradi) oppure 'full'
    con delta_deg in coda.

    color_by: 'aolp' (default, figura 3-pannelli mappa+UMAP+istogramma) oppure
    'delta' (figura legacy 2-pannelli colorata per retardance).
    """
    if sample_name is None:
        sample_name = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))
    stride = sparse_stride if sparse_stride is not None else UMAP_SPARSE_STRIDE

    print("--- Polarimetric pipeline (UMAP full-res) ---")
    print(f"  Sparse stride: {stride}px (feature grid), DOWNSAMPLE_FACTOR globale "
          f"invariato: {utils.DOWNSAMPLE_FACTOR}")

    maps = compute_polarimetric_maps_fullres(sparse_stride=stride)
    if maps is None:
        return None

    S0, S1_al, S2_al, S3 = maps['S0'], maps['S1_al'], maps['S2_al'], maps['S3']
    DoLP = maps['DoLP']
    AoLP_deg = maps['AoLP_deg']
    delta_deg, theta_deg = maps['delta_deg'], maps['theta_deg']
    valid_mask = maps['valid_mask_sparse']

    print(f"--- UMAP (sparse-grid stride={stride}) ---")
    features, valid_indices = _build_feature_matrix(
        S0, S1_al, S2_al, S3, DoLP, delta_deg, valid_mask,
        feature_mode=feature_mode)
    grid_mask = _sparse_grid_mask(S0.shape, stride)
    total_grid_points = int(grid_mask.sum())
    print(f"  Valid sparse pixels: {features.shape[0]} / {total_grid_points} "
          f"punti di griglia ({100.0 * features.shape[0] / max(total_grid_points, 1):.1f}%) "
          f"[feature_mode={feature_mode}, dim={features.shape[1]}]")

    if features.shape[0] < 100:
        print("Too few valid pixels.")
        return None

    delta_valid = delta_deg.ravel()[valid_indices] if delta_deg is not None else None
    theta_valid = theta_deg.ravel()[valid_indices] if theta_deg is not None else None
    aolp_valid = AoLP_deg.ravel()[valid_indices] if AoLP_deg is not None else None

    if histogram_path is not None and delta_valid is not None:
        plot_delta_histogram(delta_valid, sample_name, histogram_path)

    embedding = _fit_umap(features, delta_valid, theta_valid, aolp_valid)

    if color_by == 'aolp':
        fig = plot_aolp_umap_hist(
            embedding=embedding,
            aolp_deg=AoLP_deg,
            valid_indices=valid_indices,
            sample_name=sample_name,
        )
    elif color_by == 'delta':
        fig = plot_retardance_and_umap(
            embedding=embedding,
            delta_deg=delta_deg,
            valid_indices=valid_indices,
            sample_name=sample_name,
        )
    else:
        raise ValueError(f"color_by sconosciuto: {color_by!r}")

    if save_path:
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"  Saved: {save_path}")
    if show:
        plt.show()
    return fig


# =============================================================================
# INTERACTIVE LASSO SELECTOR
# =============================================================================

def _draw_hist_centroid(ax, psi_mean, psi_std, color='red'):
    """Vline tratteggiata rossa al baricentro della selezione + etichetta con
    ψ media e incertezza. Coordinate: x in data, y in axes-fraction. Ritorna
    ``(vline, text)`` per cleanup successivo.
    """
    vline = ax.axvline(psi_mean, color=color, linewidth=1.0,
                       linestyle='--', zorder=4)
    text = ax.text(
        psi_mean, 0.97,
        fr" $\bar\psi = {psi_mean:+.2f}^\circ \pm {psi_std:.2f}$",
        color=color, ha='left', va='top',
        transform=ax.get_xaxis_transform(),
        fontsize=8, zorder=5)
    return vline, text


def _draw_umap_n_label(ax, embedding, sel_mask, n_sel, color='red'):
    """Etichetta ``N=...`` fuori dal cluster selezionato (sopra se c'e'
    spazio, altrimenti sotto), no bbox, stesso stile dell'etichetta vline.
    Ritorna l'artist Text per cleanup.
    """
    cx = float(embedding[sel_mask, 0].mean())
    y_max_sel = float(embedding[sel_mask, 1].max())
    y_min_sel = float(embedding[sel_mask, 1].min())
    y_lo, y_hi = ax.get_ylim()
    margin = 0.05 * (y_hi - y_lo) if y_hi > y_lo else 0.0
    pad = 0.4 * margin

    if y_max_sel + margin <= y_hi:
        y_text, va = y_max_sel + pad, 'bottom'
    else:
        y_text, va = y_min_sel - pad, 'top'
    return ax.text(
        cx, y_text, f"N = {n_sel}",
        color=color, ha='center', va=va,
        fontsize=8, zorder=6)


def _export_panels(dataset_label, channel_label,
                   embedding, aolp_deg, valid_indices, sel_mask,
                   S0_shape, vmin, vmax, hist_bins=180,
                   images_root='../Images/generated'):
    """Esporta 3 PDF single-panel publication-style in
    ``<images_root>/<dataset>/aolp_umap/<CH>/{aolp_map,umap_scatter,aolp_hist}.pdf``,
    overwrite a ogni invocazione. Stile (figsize, dpi, font) coerente con
    ``final_thesis_figure``. Legenda ψ media wrapped a 2 righe + patch rosso
    sull'istogramma se selezione presente.
    """
    out = os.path.join(images_root, dataset_label, 'aolp_umap', channel_label)
    os.makedirs(out, exist_ok=True)

    cmap = plt.get_cmap(AOLP_CMAP)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    H, W = S0_shape
    rows, cols = np.unravel_index(valid_indices, (H, W))
    aolp_valid = aolp_deg.ravel()[valid_indices]
    has_sel = sel_mask is not None and bool(sel_mask.any())

    # (a) AoLP map: stessa convenzione di final_thesis_figure (3.35 x ratio).
    aspect_img = H / W
    fig_w = 3.35
    fig_h = fig_w * aspect_img
    fig, ax = plt.subplots(figsize=(fig_w + 0.7, fig_h))
    im = ax.imshow(aolp_deg, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    ax.set_title(r'AoLP $\psi$', pad=6)
    ax.axis('off')
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, extend='both')
    cb.set_label(r'$\psi$ (deg)')
    if has_sel:
        ax.scatter(cols[sel_mask], rows[sel_mask], c='red', s=2.5,
                   alpha=0.9, edgecolors='none', zorder=5)
    fig.savefig(os.path.join(out, 'aolp_map.pdf'), format='pdf')
    plt.close(fig)

    # (b) UMAP scatter: square + colorbar.
    fig, ax = plt.subplots(figsize=(3.35 + 0.7, 3.35))
    ax.scatter(embedding[:, 0], embedding[:, 1],
               c=aolp_valid, cmap=cmap, vmin=vmin, vmax=vmax,
               s=2.0, alpha=0.85)
    ax.set_xlabel('UMAP 1')
    ax.set_ylabel('UMAP 2')
    ax.set_title('UMAP embedding', pad=6)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                      ax=ax, fraction=0.046, pad=0.03, extend='both')
    cb.set_label(r'$\psi$ (deg)')
    if has_sel:
        ax.scatter(embedding[sel_mask, 0], embedding[sel_mask, 1],
                   facecolors='none', edgecolors='red', s=18,
                   linewidths=0.5, zorder=5)
        _draw_umap_n_label(ax, embedding, sel_mask, int(sel_mask.sum()))
    fig.savefig(os.path.join(out, 'umap_scatter.pdf'), format='pdf')
    plt.close(fig)

    # (c) Istogramma.
    fig, ax = plt.subplots(figsize=(3.35, 2.2))
    aolp_finite = aolp_valid[np.isfinite(aolp_valid)]
    counts, edges = np.histogram(aolp_finite, bins=hist_bins,
                                 range=(vmin, vmax))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_colors = [cmap(norm(c)) for c in centers]
    ax.bar(centers, counts, width=widths, color=bar_colors,
           edgecolor='none', align='center')
    if has_sel:
        sel_aolp = aolp_valid[sel_mask]
        sel_aolp = sel_aolp[np.isfinite(sel_aolp)]
        sel_counts, _ = np.histogram(sel_aolp, bins=hist_bins,
                                     range=(vmin, vmax))
        ax.bar(centers, sel_counts, width=widths, color='red',
               edgecolor='none', alpha=0.9, align='center', zorder=3)
        psi_mean = float(np.mean(sel_aolp)) if sel_aolp.size else float('nan')
        psi_std = float(np.std(sel_aolp)) if sel_aolp.size else float('nan')
        _draw_hist_centroid(ax, psi_mean, psi_std)
    ymax = float(np.percentile(counts, 99)) if counts.size else 1.0
    ax.set_xlim(vmin, vmax)
    ax.set_ylim(0, ymax * 1.15)
    ax.set_xlabel(r'$\psi$ (deg)')
    ax.set_ylabel('# pixel validi')
    ax.set_title(r'Istogramma $\psi$', pad=6)
    ax.grid(True, axis='y', linestyle=':', alpha=0.4)
    fig.savefig(os.path.join(out, 'aolp_hist.pdf'), format='pdf')
    plt.close(fig)

    return out


class _PolyClickSelector:
    """Selettore poligonale minimale: aggiorna il disegno SOLO al click, mai
    sul mouse motion. Evita il lag della preview-line del ``PolygonSelector``
    standard di matplotlib su scatter densi.

    Click sinistro = aggiunge un vertice. Click destro o tasto Enter chiude il
    poligono e invoca ``onselect(verts)``. 'esc' resetta la sequenza in corso.
    """

    def __init__(self, ax, onselect):
        self.ax = ax
        self.onselect = onselect
        self.verts = []
        self._line = None
        canvas = ax.figure.canvas
        self._cid_click = canvas.mpl_connect('button_press_event', self._on_click)
        self._cid_key = canvas.mpl_connect('key_press_event', self._on_key)

    def _redraw_line(self, closed=False):
        if self._line is not None:
            self._line.remove()
            self._line = None
        if not self.verts:
            return
        pts = self.verts + [self.verts[0]] if closed else self.verts
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        (self._line,) = self.ax.plot(xs, ys, 'o-', color='red',
                                     linewidth=1.0, markersize=3.5,
                                     zorder=10)
        self.ax.figure.canvas.draw_idle()

    def _on_click(self, event):
        if event.inaxes is not self.ax or event.xdata is None:
            return
        if event.button == 1:
            self.verts.append((event.xdata, event.ydata))
            self._redraw_line(closed=False)
        elif event.button == 3 and len(self.verts) >= 3:
            self._close()

    def _on_key(self, event):
        if event.key == 'escape':
            self.clear()

    def _close(self):
        verts = list(self.verts)
        self._redraw_line(closed=True)
        self.onselect(verts)
        self.verts = []

    def clear(self):
        self.verts = []
        if self._line is not None:
            self._line.remove()
            self._line = None
            self.ax.figure.canvas.draw_idle()


def _interactive_panel(embedding, aolp_deg, valid_indices, S0_shape,
                       sample_name='', hist_bins=180,
                       dataset_label=None, channel_label=None):
    """Costruisce figura 3-pannelli (mappa | UMAP | istogramma) con
    selettore poligonale click-only sullo scatter UMAP. Click sinistro =
    vertice; click destro = chiude e seleziona; 'esc' = annulla sequenza in
    corso.

    Tasti: 'r' = reset overlay rossi, 'enter' = export 3 PDF in
    ``Images/generated/<dataset>/aolp_umap/<CH>/`` (overwrite),
    'q' = chiudi finestra.
    """
    from matplotlib.path import Path

    aolp_valid = aolp_deg.ravel()[valid_indices]
    vmin, vmax = _aolp_clip_range(aolp_valid)
    cmap = plt.get_cmap(AOLP_CMAP)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)

    H, W = S0_shape
    rows, cols = np.unravel_index(valid_indices, (H, W))

    fig = plt.figure(figsize=(16, 5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.0, 1.0])
    ax_map = fig.add_subplot(gs[0])
    ax_umap = fig.add_subplot(gs[1])
    ax_hist = fig.add_subplot(gs[2])
    fig.suptitle(f"Polarimetric UMAP + AoLP - {sample_name}", fontsize=13)

    im = ax_map.imshow(aolp_deg, cmap=cmap, vmin=vmin, vmax=vmax)
    ax_map.set_title(r"(a) AoLP $\psi$ (deg)")
    ax_map.axis('off')
    fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04,
                 extend='both').set_label(r"$\psi$ (deg)")

    ax_umap.scatter(embedding[:, 0], embedding[:, 1],
                    c=aolp_valid, cmap=cmap, vmin=vmin, vmax=vmax,
                    s=2.0, alpha=0.85)
    ax_umap.set_title(r"(b) UMAP embedding")
    ax_umap.set_xlabel("UMAP 1")
    ax_umap.set_ylabel("UMAP 2")
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                 ax=ax_umap, fraction=0.046, pad=0.04,
                 extend='both').set_label(r"$\psi$ (deg)")

    aolp_finite = aolp_valid[np.isfinite(aolp_valid)]
    counts, edges = np.histogram(aolp_finite, bins=hist_bins,
                                 range=(vmin, vmax))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_colors = [cmap(norm(c)) for c in centers]
    ax_hist.bar(centers, counts, width=widths, color=bar_colors,
                edgecolor='none', align='center')
    ymax = float(np.percentile(counts, 99)) if counts.size else 1.0
    ax_hist.set_xlim(vmin, vmax)
    ax_hist.set_ylim(0, ymax * 1.15)
    ax_hist.set_xlabel(r"$\psi$ (deg)")
    ax_hist.set_ylabel("# pixel validi")
    ax_hist.set_title(r"(c) Istogramma $\psi$")
    ax_hist.grid(True, axis='y', linestyle=':', alpha=0.4)

    state = {'map_pts': None, 'umap_ring': None, 'hist_bars': None,
             'hist_vline': None, 'hist_label': None,
             'umap_n_label': None, 'sel_mask': None}

    def clear_overlay():
        for k in ('map_pts', 'umap_ring', 'hist_vline', 'hist_label',
                  'umap_n_label'):
            if state[k] is not None:
                state[k].remove()
                state[k] = None
        if state['hist_bars'] is not None:
            for b in state['hist_bars']:
                b.remove()
            state['hist_bars'] = None
        state['sel_mask'] = None

    def on_select(verts):
        clear_overlay()
        if len(verts) < 3:
            fig.canvas.draw_idle()
            return
        path = Path(verts)
        sel = path.contains_points(embedding)
        if not sel.any():
            print("  selezione vuota")
            fig.canvas.draw_idle()
            return
        state['map_pts'] = ax_map.scatter(
            cols[sel], rows[sel], c='red', s=10, alpha=0.85,
            edgecolors='none', zorder=5)
        state['umap_ring'] = ax_umap.scatter(
            embedding[sel, 0], embedding[sel, 1],
            facecolors='none', edgecolors='red', s=22,
            linewidths=0.6, zorder=5)
        sel_aolp = aolp_valid[sel]
        sel_aolp = sel_aolp[np.isfinite(sel_aolp)]
        sel_counts, _ = np.histogram(sel_aolp, bins=hist_bins,
                                     range=(vmin, vmax))
        bars = ax_hist.bar(centers, sel_counts, width=widths,
                           color='red', edgecolor='none', alpha=0.9,
                           align='center', zorder=3)
        state['hist_bars'] = list(bars.patches)
        psi_mean = float(np.mean(sel_aolp)) if sel_aolp.size else float('nan')
        psi_std = float(np.std(sel_aolp)) if sel_aolp.size else float('nan')
        n_sel = int(sel.sum())
        state['hist_vline'], state['hist_label'] = _draw_hist_centroid(
            ax_hist, psi_mean, psi_std)
        state['umap_n_label'] = _draw_umap_n_label(
            ax_umap, embedding, sel, n_sel)
        state['sel_mask'] = sel
        print(f"  selezionati {n_sel} pixel  "
              f"psi medio = {psi_mean:+.2f} deg  (std = {psi_std:.2f})")
        fig.canvas.draw_idle()

    selector = _PolyClickSelector(ax_umap, on_select)

    def export_figure():
        if dataset_label is None or channel_label is None:
            print("  (export disabilitato: dataset_label/channel_label mancanti)")
            return
        out_dir = _export_panels(
            dataset_label=dataset_label,
            channel_label=channel_label,
            embedding=embedding,
            aolp_deg=aolp_deg,
            valid_indices=valid_indices,
            sel_mask=state['sel_mask'],
            S0_shape=S0_shape,
            vmin=vmin, vmax=vmax,
            hist_bins=hist_bins,
        )
        print(f"  esportato: {out_dir}/ (3 PDF)")

    def on_key(event):
        if event.key == 'r':
            selector.clear()
            clear_overlay()
            fig.canvas.draw_idle()
            print("  reset")
        elif event.key == 'enter':
            export_figure()
        elif event.key == 'q':
            plt.close(fig)

    fig.canvas.mpl_connect('key_press_event', on_key)

    print("\n--- comandi finestra interattiva ---")
    print("  click sinistro    : aggiunge vertice del poligono")
    print("  click destro      : chiude poligono e applica selezione")
    print("  esc               : annulla sequenza vertici in corso")
    print("  r                 : reset overlay rossi + selettore")
    print("  enter             : export 3 PDF in "
          "Images/generated/<dataset>/aolp_umap/<CH>/")
    print("  q                 : chiudi finestra")
    print("------------------------------------\n")

    plt.tight_layout(rect=(0, 0, 1, 0.94))
    return fig, selector


def _compute_or_load_cache(cache_path=None, sparse_stride=None,
                           feature_mode='no_delta'):
    """Restituisce ``(embedding, aolp_deg, valid_indices, S0_shape)`` oppure
    ``None`` su fallimento. Carica da ``cache_path`` se esiste, altrimenti
    calcola Stokes + UMAP e salva il cache.
    """
    if cache_path and os.path.exists(cache_path):
        print(f"[cache] carico {cache_path}")
        with np.load(cache_path) as d:
            return (d['embedding'].copy(),
                    d['aolp_deg'].copy(),
                    d['valid_indices'].copy(),
                    tuple(int(x) for x in d['S0_shape']))

    stride = sparse_stride if sparse_stride is not None else UMAP_SPARSE_STRIDE
    maps = compute_polarimetric_maps_fullres(sparse_stride=stride)
    if maps is None:
        return None
    S0 = maps['S0']
    AoLP_deg = maps['AoLP_deg']
    delta_deg = maps['delta_deg']
    DoLP = maps['DoLP']
    S1_al, S2_al, S3 = maps['S1_al'], maps['S2_al'], maps['S3']
    valid_mask = maps['valid_mask_sparse']
    features, valid_indices = _build_feature_matrix(
        S0, S1_al, S2_al, S3, DoLP, delta_deg, valid_mask,
        feature_mode=feature_mode)
    if features.shape[0] < 100:
        print("Too few valid pixels.")
        return None
    embedding = _fit_umap(features)
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
        np.savez_compressed(
            cache_path,
            embedding=embedding,
            aolp_deg=AoLP_deg,
            valid_indices=valid_indices,
            S0_shape=np.array(S0.shape, dtype=np.int64))
        print(f"[cache] salvato {cache_path}")
    return embedding, AoLP_deg, valid_indices, S0.shape


def run_interactive(sample_name=None, sparse_stride=None,
                    feature_mode='no_delta', cache_path=None,
                    dataset_label=None, channel_label=None):
    """UMAP + finestra interattiva con poligono click-only.

    Cache: se ``cache_path`` esiste, ricarica embedding+arrays evitando il
    recompute (~2 min/canale). Se non esiste e viene fornito, salva il cache
    dopo il calcolo.
    """
    if sample_name is None:
        sample_name = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))

    result = _compute_or_load_cache(cache_path=cache_path,
                                    sparse_stride=sparse_stride,
                                    feature_mode=feature_mode)
    if result is None:
        return None
    embedding, aolp_deg, valid_indices, S0_shape = result

    fig, _selector = _interactive_panel(
        embedding, aolp_deg, valid_indices, S0_shape,
        sample_name=sample_name,
        dataset_label=dataset_label,
        channel_label=channel_label)
    plt.show(block=True)
    return fig


# =============================================================================
# BATCH RGB
# =============================================================================

CHANNELS_RGB = [(0, 'R'), (1, 'G'), (2, 'B')]


def _set_dataset_globals(dataset, channel_idx, waveplate_swap=None):
    utils.TARGET_FOLDER = f'./raw/{dataset}'
    utils.POL_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'pol')
    utils.WAV_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'wav')
    if waveplate_swap is None:
        utils.WAVEPLATE_AXES_SWAPPED = 'lambdamezzi' in dataset.lower()
    else:
        utils.WAVEPLATE_AXES_SWAPPED = bool(waveplate_swap)
    utils.TARGET_CHANNEL_IDX = channel_idx


def run_interactive_dataset(dataset, channel_label='R', cache_dir='./outputs',
                            use_cache=True, waveplate_swap=None):
    """Wrapper: imposta globals per ``dataset``/``channel_label`` e apre la
    finestra interattiva. ``channel_label`` in {'R','G','B'}.

    Esempio:
        python -c "import final_umap; final_umap.run_interactive_dataset('zucchero', 'R')"
    """
    label_to_idx = {'R': 0, 'G': 1, 'B': 2}
    if channel_label not in label_to_idx:
        raise ValueError(f"channel_label deve essere R/G/B, non {channel_label!r}")
    channel_idx = label_to_idx[channel_label]
    _set_dataset_globals(dataset, channel_idx, waveplate_swap)
    cache_path = (os.path.join(cache_dir, f"umap_{dataset}_{channel_label}_cache.npz")
                  if use_cache else None)
    return run_interactive(sample_name=f"{dataset} - canale {channel_label}",
                           cache_path=cache_path,
                           dataset_label=dataset,
                           channel_label=channel_label)


def run_dataset_rgb(dataset, cache_dir='./outputs', use_cache=True,
                    waveplate_swap=None,
                    images_root='../Images/generated'):
    """Batch UMAP sui 3 canali RGB di ``dataset``. Per ogni canale:
    1. Carica/ricalcola cache npz in ``<cache_dir>/umap_<dataset>_<CH>_cache.npz``.
    2. Esporta 3 PDF single-panel publication-style in
       ``<images_root>/<dataset>/aolp_umap/<CH>/{aolp_map,umap_scatter,aolp_hist}.pdf``
       (overwrite, no selezione).
    """
    for ch_idx, ch_label in CHANNELS_RGB:
        _set_dataset_globals(dataset, ch_idx, waveplate_swap)
        print(f"\n=== {dataset} / {ch_label} ===")
        cache_path = (os.path.join(cache_dir, f"umap_{dataset}_{ch_label}_cache.npz")
                      if use_cache else None)
        result = _compute_or_load_cache(cache_path=cache_path)
        if result is None:
            print(f"  [{ch_label}] skip: pixel insufficienti")
            continue
        embedding, aolp_deg, valid_indices, S0_shape = result
        aolp_valid = aolp_deg.ravel()[valid_indices]
        vmin, vmax = _aolp_clip_range(aolp_valid)
        out_dir = _export_panels(
            dataset_label=dataset, channel_label=ch_label,
            embedding=embedding, aolp_deg=aolp_deg,
            valid_indices=valid_indices, sel_mask=None,
            S0_shape=S0_shape, vmin=vmin, vmax=vmax,
            images_root=images_root,
        )
        print(f"  [{ch_label}] esportato: {out_dir}/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="UMAP polarimetrico: interactive (default) o batch RGB.")
    parser.add_argument('mode', nargs='?',
                        choices=['interactive', 'batch', 'legacy'],
                        default='interactive',
                        help="interactive=finestra+poligono, batch=3 PDF "
                             "per canale RGB, legacy=run() su un canale")
    parser.add_argument('dataset', nargs='?', default=None,
                        help="nome cartella sotto raw/ "
                             "(default: bersaglio in final_utils.TARGET_FOLDER)")
    parser.add_argument('channel', nargs='?', choices=['R', 'G', 'B'],
                        default=None,
                        help="solo per mode=interactive "
                             "(default: final_utils.TARGET_CHANNEL_IDX)")
    parser.add_argument('--no-cache', action='store_true',
                        help="forza ricalcolo, ignora cache npz")
    args = parser.parse_args()

    if args.dataset is None:
        args.dataset = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))
    if args.channel is None:
        args.channel = ['R', 'G', 'B'][utils.TARGET_CHANNEL_IDX]
    print(f"[final_umap] mode={args.mode}  dataset={args.dataset}  "
          f"channel={args.channel}  use_cache={not args.no_cache}")

    if args.mode == 'batch':
        run_dataset_rgb(args.dataset, use_cache=not args.no_cache)
    elif args.mode == 'interactive':
        run_interactive_dataset(args.dataset, args.channel,
                                use_cache=not args.no_cache)
    else:
        run()
