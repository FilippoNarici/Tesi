"""UMAP helpers: validity mask, normalize, feature builder, color spec.

I run_interactive_dataset / run_dataset_rgb completi vivono ancora nel legacy
final_umap.py (utility esterna, non orchestrata dal notebook). Qui solo i
mattoni atomici riusabili dalle celle analysis_cells.
"""
import numpy as np

S0_MIN = 1e-6
DOLP_MIN = 0.20
UMAP_AXIS_CONFIDENCE_MIN = 0.05

AOLP_CMAP = 'viridis'
AOLP_CLIP_PCT = (1.0, 99.0)
DELTA_CMAP = 'twilight'
DELTA_VMIN = 0.0
DELTA_VMAX = 360.0
DELTA_EDGE_EXCLUDE_DEG = 20.0

UMAP_SPARSE_STRIDE = 20
UMAP_FIT_SAMPLE = 20000
UMAP_N_NEIGHBORS = 80
UMAP_MIN_DIST = 0.008
UMAP_METRIC = 'euclidean'
RANDOM_STATE = 42


def normalize_stokes(S0, S1, S2, S3):
    """(s1, s2, s3) = (S1, S2, S3) / S0 con guardia su |S0| < S0_MIN."""
    safe_S0 = np.where(np.abs(S0) < S0_MIN, np.nan, S0)
    s1 = S1 / safe_S0
    s2 = S2 / safe_S0
    s3 = (S3 / safe_S0) if S3 is not None else np.zeros_like(S0)
    return s1, s2, s3


def build_validity_mask(S0, DoLP, bg_mask, sat_mask=None, theta_deg=None,
                        axis_conf_min=UMAP_AXIS_CONFIDENCE_MIN,
                        dolp_min=DOLP_MIN):
    """Maschera booleana di pixel adatti a UMAP.

    Esclude bg, NaN/Inf, S0 sotto soglia, DoLP basso, pixel saturati, e
    (se theta_deg fornita) pixel con sin^2(2 theta) sotto axis_conf_min
    (zona degenere delle formule retardance).
    """
    sample_mask = ~bg_mask
    finite = (np.isfinite(S0) & np.isfinite(DoLP)
              & (np.abs(S0) >= S0_MIN))
    bright_enough = DoLP >= dolp_min
    valid = sample_mask & finite & bright_enough
    if sat_mask is not None:
        valid &= ~sat_mask
    if theta_deg is not None and axis_conf_min > 0.0:
        sin2_2theta = np.sin(np.deg2rad(2.0 * theta_deg)) ** 2
        confidence = np.where(np.isfinite(sin2_2theta), sin2_2theta, 0.0)
        valid &= confidence > axis_conf_min
    return valid


def default_feature_mode(color_by):
    """Mappa color_by ('aolp'|'delta') -> feature_mode di default.

    Rami separati per modifica futura indipendente; attualmente entrambi
    puntano a 'no_delta' = (s1, s2, s3, DoLP).
    """
    if color_by == 'aolp':
        return 'no_delta'
    elif color_by == 'delta':
        return 'no_delta'
    raise ValueError(f"color_by sconosciuto: {color_by!r}")


def build_feature_matrix(S0, S1, S2, S3, DoLP, valid_mask,
                         feature_mode='no_delta'):
    """Costruisce matrice (N_valid, F) di feature per UMAP.

    Modalita' attive:
      - 'no_delta': (s1, s2, s3, DoLP)
    """
    s1, s2, s3 = normalize_stokes(S0, S1, S2, S3)
    flat_valid = valid_mask.ravel()
    if feature_mode == 'no_delta':
        cols = [s1.ravel(), s2.ravel(), s3.ravel(), DoLP.ravel()]
    else:
        raise ValueError(f"feature_mode sconosciuto: {feature_mode}")
    features = np.column_stack(cols)[flat_valid]
    valid_indices = np.flatnonzero(flat_valid)
    return features.astype(np.float32), valid_indices


def aolp_clip_range(aolp_valid, pct=AOLP_CLIP_PCT):
    """Clip percentile sui pixel finiti; fallback [-90, 90] su dist degenere."""
    finite = aolp_valid[np.isfinite(aolp_valid)]
    if finite.size == 0:
        return -90.0, 90.0
    vmin, vmax = np.percentile(finite, pct)
    if vmax - vmin < 1.0:
        return -90.0, 90.0
    return float(vmin), float(vmax)


def color_spec(color_by, aolp_deg=None, delta_deg=None, valid_indices=None):
    """Dict con cmap, range, etichette e file di export per AoLP o delta."""
    import matplotlib.pyplot as plt

    if color_by == 'aolp':
        if aolp_deg is None or valid_indices is None:
            raise ValueError("color_by='aolp' richiede aolp_deg e valid_indices")
        valid_vals = aolp_deg.ravel()[valid_indices]
        vmin, vmax = aolp_clip_range(valid_vals)
        return {
            'mode': 'aolp',
            'value_map': aolp_deg,
            'value_valid': valid_vals,
            'cmap': plt.get_cmap(AOLP_CMAP),
            'vmin': vmin, 'vmax': vmax,
            'hist_range': (vmin, vmax),
            'hist_edge_exclude': 0.0,
            'cbar_extend': 'both',
            'bar_tex': r'\bar\psi',
            'unit_label': r'$\psi$ (deg)',
            'map_title': r'(a) AoLP $\psi$ (deg)',
            'map_title_short': r'AoLP $\psi$',
            'hist_title': r'(c) Istogramma $\psi$',
            'panel_title_root': 'Polarimetric UMAP + AoLP',
            'export_subdir': 'aolp_umap',
            'export_map_file': 'aolp_map.pdf',
            'export_hist_file': 'aolp_hist.pdf',
        }
    elif color_by == 'delta':
        if delta_deg is None or valid_indices is None:
            raise ValueError("color_by='delta' richiede delta_deg e valid_indices")
        valid_vals = delta_deg.ravel()[valid_indices]
        return {
            'mode': 'delta',
            'value_map': delta_deg,
            'value_valid': valid_vals,
            'cmap': plt.get_cmap(DELTA_CMAP),
            'vmin': DELTA_VMIN, 'vmax': DELTA_VMAX,
            'hist_range': (DELTA_VMIN, DELTA_VMAX),
            'hist_edge_exclude': DELTA_EDGE_EXCLUDE_DEG,
            'cbar_extend': 'neither',
            'bar_tex': r'\bar\delta',
            'unit_label': r'$\delta$ (deg)',
            'map_title': r'(a) Retardance $\delta$ (deg)',
            'map_title_short': r'Retardance $\delta$',
            'hist_title': r'(c) Istogramma $\delta$',
            'panel_title_root': r'Polarimetric UMAP + $\delta$',
            'export_subdir': 'delta_umap',
            'export_map_file': 'delta_map.pdf',
            'export_hist_file': 'delta_hist.pdf',
        }
    raise ValueError(f"color_by sconosciuto: {color_by!r}")


def fit_umap(features, n_neighbors=UMAP_N_NEIGHBORS, min_dist=UMAP_MIN_DIST,
             metric=UMAP_METRIC, random_state=RANDOM_STATE,
             fit_sample=UMAP_FIT_SAMPLE):
    """Fitta UMAP su un subsample casuale di features, poi transforma tutto."""
    import umap

    n_points = features.shape[0]
    if n_points == 0:
        return np.empty((0, 2), dtype=np.float32)

    if fit_sample < n_points:
        rng = np.random.default_rng(random_state)
        fit_idx = rng.choice(n_points, size=fit_sample, replace=False)
        fit_features = features[fit_idx]
    else:
        fit_features = features

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric=metric,
        random_state=random_state,
    )
    reducer.fit(fit_features)
    return reducer.transform(features).astype(np.float32)
