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

La mappa spaziale di retardance nel pannello di sinistra resta a risoluzione
nativa per mostrare bene il dettaglio; i punti dell'embedding a destra sono
colorati con il valore di delta letto alla stessa posizione sparsa usata per
le feature, cosi' i colori sono confrontabili fra i due pannelli.

Questo script NON modifica ``utils.DOWNSAMPLE_FACTOR``: il downsample globale
del resto della pipeline rimane intatto.
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

import final_utils as utils

try:
    matplotlib.use('TkAgg')
except Exception:
    pass

# =============================================================================
# UMAP CONFIGURATION
# =============================================================================

UMAP_SPARSE_STRIDE = 20
UMAP_FIT_SAMPLE = 20000
UMAP_N_NEIGHBORS = 80
UMAP_MIN_DIST = 0.008
UMAP_METRIC = 'euclidean'

DOLP_MIN = 0.05
S0_MIN = 1e-6
RANDOM_STATE = 42

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

def _build_feature_matrix(S0, S1, S2, S3, DoLP, delta_deg, valid_mask):
    s1, s2, s3 = _normalize_stokes(S0, S1, S2, S3)
    flat_valid = valid_mask.ravel()
    features = np.column_stack([
        s1.ravel(), s2.ravel(), s3.ravel(),
        DoLP.ravel(), delta_deg.ravel(),
    ])[flat_valid]
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

def _fit_umap(features, delta_valid=None, theta_valid=None):
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

    if delta_valid is not None and theta_valid is not None:
        r1_d, _ = pearsonr(embedding[:, 0], delta_valid)
        r2_d, _ = pearsonr(embedding[:, 1], delta_valid)
        r1_t, _ = pearsonr(embedding[:, 0], theta_valid)
        r2_t, _ = pearsonr(embedding[:, 1], theta_valid)
        print(f"\nUMAP interpretability (Pearson r):")
        print(f"  UMAP1 <-> delta : {r1_d:+.3f}   |   UMAP1 <-> theta : {r1_t:+.3f}")
        print(f"  UMAP2 <-> delta : {r2_d:+.3f}   |   UMAP2 <-> theta : {r2_t:+.3f}")

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

# =============================================================================
# MAIN
# =============================================================================

def run(sample_name=None, show=True, save_path=None, sparse_stride=None):
    if sample_name is None:
        sample_name = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))
    stride = sparse_stride if sparse_stride is not None else UMAP_SPARSE_STRIDE

    print("--- Polarimetric pipeline (UMAP full-res) ---")
    print(f"  Sparse stride: {stride}px (feature grid), DOWNSAMPLE_FACTOR globale "
          f"invariato: {utils.DOWNSAMPLE_FACTOR}")
    utils.reset_saturation_accumulator()

    # Caricamento e calcolo Stokes a risoluzione nativa: questa e' la parte
    # "costosa" di UMAP. Il resto della pipeline del progetto NON e' toccato.
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
    DoLP, _ = utils.calculate_dolp_aolp(S0, S1_al, S2_al)
    delta_deg, theta_deg = utils.calculate_retardance_and_fast_axis(
        S0, S1_al, S2_al, S3, bg_mask, smooth_sigma=0)

    sat_mask = utils.get_saturation_mask(1)
    if sat_mask is not None and sat_mask.any():
        for arr in (DoLP, delta_deg, theta_deg):
            if arr is not None:
                arr[sat_mask] = np.nan

    # Sparse-grid: il cuore della variante U1. Prendiamo un pixel ogni
    # ``stride`` su entrambi gli assi, senza mediare con i vicini, cosi' le
    # transizioni nette fra regioni polarimetriche non vengono sfumate.
    print(f"--- UMAP (sparse-grid stride={stride}) ---")
    grid_mask = _sparse_grid_mask(S0.shape, stride)
    base_valid = _build_validity_mask(S0, DoLP, bg_mask, sat_mask)
    valid_mask = base_valid & grid_mask

    features, valid_indices = _build_feature_matrix(
        S0, S1_al, S2_al, S3, DoLP, delta_deg, valid_mask)
    total_grid_points = int(grid_mask.sum())
    print(f"  Valid sparse pixels: {features.shape[0]} / {total_grid_points} "
          f"punti di griglia ({100.0 * features.shape[0] / max(total_grid_points, 1):.1f}%)")

    if features.shape[0] < 100:
        print("Too few valid pixels.")
        return None

    delta_valid = delta_deg.ravel()[valid_indices] if delta_deg is not None else None
    theta_valid = theta_deg.ravel()[valid_indices] if theta_deg is not None else None

    embedding = _fit_umap(features, delta_valid, theta_valid)

    fig = plot_retardance_and_umap(
        embedding=embedding,
        delta_deg=delta_deg,
        valid_indices=valid_indices,
        sample_name=sample_name,
    )

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"  Saved: {save_path}")
    if show:
        plt.show()
    return fig

if __name__ == "__main__":
    run()
