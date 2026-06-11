"""UMAP helpers: validity mask, normalize, feature builder, color spec.

I run_interactive_dataset / run_dataset_rgb completi (selettore poligono
interattivo) non sono nel package: vivevano nel pre-refactor `final_umap.py`,
ora solo nella cronologia git. Qui i mattoni atomici riusabili dalle celle.
"""
import numpy as np

S0_MIN = 1e-6
DOLP_MIN = 0.0  # disattivato: sampling puro su bg_mask (no filtro DoLP)
UMAP_AXIS_CONFIDENCE_MIN = 0.0  # disattivato: no filtro sin^2(2theta) confidenza asse

AOLP_CMAP = 'viridis'
AOLP_CLIP_PCT = (1.0, 99.0)
DELTA_CMAP = 'twilight'
DELTA_VMIN = 0.0
DELTA_VMAX = 360.0
DELTA_EDGE_EXCLUDE_DEG = 20.0

UMAP_SPARSE_STRIDE = 20  # stride su pixel NATIVI (campionamento sparso)
UMAP_RANDOM_SAMPLE_N = 30000  # numero target di pixel campionati a caso fra i validi
UMAP_FIT_SAMPLE = 20000
UMAP_N_NEIGHBORS = 80
UMAP_MIN_DIST = 0.008
UMAP_METRIC = 'euclidean'
RANDOM_STATE = 42


def random_sample_mask(shape, base_valid, n_target=UMAP_RANDOM_SAMPLE_N, seed=RANDOM_STATE):
    """Campiona random n_target pixel fra quelli marcati True in base_valid.

    Restituisce una maschera booleana della stessa shape con n_target True
    (o tutti i validi se sono meno di n_target).
    """
    valid_idx = np.argwhere(base_valid)
    n_valid = valid_idx.shape[0]
    if n_valid == 0:
        return np.zeros(shape, dtype=bool)
    n = min(n_target, n_valid)
    rng = np.random.default_rng(seed)
    chosen = rng.choice(n_valid, size=n, replace=False)
    out = np.zeros(shape, dtype=bool)
    rows = valid_idx[chosen, 0]
    cols = valid_idx[chosen, 1]
    out[rows, cols] = True
    return out


def plot_sample_diagnostic(ax, S0, sample_mask, bg_mask=None, title=None):
    """Plot diagnostico: S0 in grayscale + pixel campionati come scatter rosso.

    Mostra dove sono caduti i punti del campionamento random. Va passato un
    asse matplotlib esistente (l'export del PDF/HTML resta a carico del chiamante).
    """
    import numpy as _np
    H, W = S0.shape
    s0_norm = _np.clip(S0 / (_np.nanpercentile(S0, 99.0) + 1e-9), 0.0, 1.0)
    ax.imshow(s0_norm, cmap='gray', aspect='equal')
    if bg_mask is not None:
        from matplotlib.colors import ListedColormap
        overlay = _np.zeros((H, W, 4))
        overlay[bg_mask] = [0.0, 0.4, 1.0, 0.18]
        ax.imshow(overlay)
    yy, xx = _np.nonzero(sample_mask)
    ax.scatter(xx, yy, s=0.3, c='red', alpha=0.85, edgecolors='none', rasterized=True)
    ax.set_xticks([]); ax.set_yticks([])
    if title is not None:
        ax.set_title(title, fontsize=9, pad=4)
    ax.text(0.02, 0.98, f'N = {len(yy)}', transform=ax.transAxes,
            va='top', ha='left', fontsize=7,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=2))


def normalize_stokes(S0, S1, S2, S3):
    """(s1, s2, s3) = (S1, S2, S3) / S0 con guardia su |S0| < S0_MIN."""
    safe_S0 = np.where(np.abs(S0) < S0_MIN, np.nan, S0)
    s1 = S1 / safe_S0
    s2 = S2 / safe_S0
    s3 = (S3 / safe_S0) if S3 is not None else np.zeros_like(S0)
    return s1, s2, s3


def build_validity_mask(S0, DoLP, bg_mask=None, sat_mask=None, theta_deg=None,
                        axis_conf_min=UMAP_AXIS_CONFIDENCE_MIN,
                        dolp_min=DOLP_MIN):
    """Maschera booleana di pixel adatti a UMAP.

    Esclude NaN/Inf, S0 sotto soglia, DoLP basso, pixel saturati, e
    (se theta_deg fornita) pixel con sin^2(2 theta) sotto axis_conf_min.
    `bg_mask=None` (default) NON esclude background; passare bg_mask per
    forzare l'esclusione.
    """
    finite = (np.isfinite(S0) & np.isfinite(DoLP)
              & (np.abs(S0) >= S0_MIN))
    bright_enough = DoLP >= dolp_min
    valid = finite & bright_enough
    if bg_mask is not None:
        valid &= ~bg_mask
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


def cluster_aolp_kmeans(AoLP_deg, bg_mask, n_clusters=5, random_state=RANDOM_STATE):
    """K-means su (sin(2θ), cos(2θ)) per pixel sample. Ritorna tutti i cluster + score.

    Score per cluster: `size_frac × R × ang_dist_deg²`, dove `ang_dist_deg` è la
    distanza angolare AoLP fra centroide del cluster e centroide globale di tutti
    i pixel sample (calcolata in 2θ-space, gestisce il wrap). Razionale: cluster
    dominante coincide col centroide globale (dist≈0) → score basso; cluster di
    rumore piccolo (size basso) → score basso; cluster medio con AoLP distinto
    dalla maggioranza → score alto. Quadratura su d_ang penalizza forte i cluster
    huge ma centrati sulla maggioranza (es. bg con d_ang piccolo).

    Restituisce:
      cluster_masks: list di bool array shape=bg_mask, uno per cluster.
      all_info: list di dict {k, size, size_frac, R, mean_deg, std_deg,
                              ang_dist_deg, score}.
      winner_idx: int, index del cluster con score massimo.
    Se troppo pochi pixel: (None, [], None).
    """
    from sklearn.cluster import KMeans

    sample_mask = (~bg_mask) & np.isfinite(AoLP_deg)
    if int(sample_mask.sum()) < n_clusters * 10:
        return None, [], None

    aolp_rad2 = np.deg2rad(2.0 * AoLP_deg[sample_mask])
    X = np.column_stack([np.sin(aolp_rad2), np.cos(aolp_rad2)])

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = km.fit_predict(X)

    # centroide globale (media su tutti i pixel sample) in 2θ-space
    s_g = float(X[:, 0].mean())
    c_g = float(X[:, 1].mean())
    R_g = float(np.sqrt(s_g ** 2 + c_g ** 2))
    if R_g > 1e-9:
        s_g_n, c_g_n = s_g / R_g, c_g / R_g
    else:
        s_g_n, c_g_n = 0.0, 1.0

    flat_pos = np.argwhere(sample_mask)
    total = X.shape[0]
    cluster_masks = []
    all_info = []
    for k in range(n_clusters):
        sel = labels == k
        n = int(sel.sum())
        cm = np.zeros_like(bg_mask, dtype=bool)
        if n > 0:
            cm[flat_pos[sel, 0], flat_pos[sel, 1]] = True
            s_mean = float(X[sel, 0].mean())
            c_mean = float(X[sel, 1].mean())
            R = float(np.sqrt(s_mean ** 2 + c_mean ** 2))
            mean_deg = float(np.degrees(np.arctan2(s_mean, c_mean)) / 2.0)
            std_deg = float(np.degrees(np.sqrt(max(-2.0 * np.log(max(R, 1e-9)), 0.0))) / 2.0)
            if R > 1e-9:
                s_k_n, c_k_n = s_mean / R, c_mean / R
            else:
                s_k_n, c_k_n = 0.0, 1.0
            dot = float(np.clip(s_k_n * s_g_n + c_k_n * c_g_n, -1.0, 1.0))
            ang_dist_2t = float(np.arccos(dot))
            ang_dist_deg = float(np.degrees(ang_dist_2t) / 2.0)
        else:
            R, mean_deg, std_deg, ang_dist_deg = 0.0, float('nan'), float('nan'), 0.0
        size_frac = n / max(total, 1)
        score = size_frac * R * (ang_dist_deg ** 2)
        cluster_masks.append(cm)
        all_info.append({
            'k': k, 'size': n, 'size_frac': size_frac,
            'R': R, 'mean_deg': mean_deg, 'std_deg': std_deg,
            'ang_dist_deg': ang_dist_deg, 'score': score,
        })

    winner_idx = int(np.argmax([info['score'] for info in all_info]))
    return cluster_masks, all_info, winner_idx


def cluster_umap_hdbscan_by_aolp(embedding, aolp_deg, valid_indices, S0_shape,
                                  min_cluster_size=100, min_samples=None):
    """HDBSCAN sull'embedding UMAP. Cluster formati senza guardare AoLP.

    Dopo clustering, calcola statistica AoLP per cluster e score generico
    `size_frac × R × ang_dist_deg²` (vedi `cluster_aolp_kmeans`). Cluster
    'rumore' di HDBSCAN (label -1) escluso dallo scoring.

    Restituisce:
      cluster_masks: list di bool array shape=S0_shape, uno per cluster
                     (incluso noise -1 come primo se presente).
      all_info: list di dict {label, size, size_frac, R, mean_deg, std_deg,
                              ang_dist_deg, score}.
      winner_idx: int, index del cluster con score massimo (escluso noise).
      labels: array (n_emb,) di label HDBSCAN per ogni punto embedding.
    Se troppo pochi punti: (None, [], None, None).
    """
    from sklearn.cluster import HDBSCAN

    if embedding.shape[0] < min_cluster_size:
        return None, [], None, None

    clusterer = HDBSCAN(min_cluster_size=min_cluster_size,
                        min_samples=min_samples)
    labels = clusterer.fit_predict(embedding)

    aolp_flat = aolp_deg.ravel()
    aolp_at_emb = aolp_flat[valid_indices]
    aolp_rad2 = np.deg2rad(2.0 * aolp_at_emb)
    X = np.column_stack([np.sin(aolp_rad2), np.cos(aolp_rad2)])

    # centroide globale escludendo noise
    not_noise = labels != -1
    if not_noise.any():
        s_g = float(X[not_noise, 0].mean())
        c_g = float(X[not_noise, 1].mean())
    else:
        s_g, c_g = 0.0, 1.0
    R_g = float(np.sqrt(s_g ** 2 + c_g ** 2))
    if R_g > 1e-9:
        s_g_n, c_g_n = s_g / R_g, c_g / R_g
    else:
        s_g_n, c_g_n = 0.0, 1.0

    unique_labels = sorted(set(labels.tolist()))
    total = embedding.shape[0]
    cluster_masks = []
    all_info = []
    valid_idx_arr = np.asarray(valid_indices, dtype=np.int64)
    for lbl in unique_labels:
        sel = labels == lbl
        n = int(sel.sum())
        cm = np.zeros(S0_shape, dtype=bool)
        if n > 0:
            idx_in_image = valid_idx_arr[sel]
            ys, xs = np.unravel_index(idx_in_image, S0_shape)
            cm[ys, xs] = True
            s_mean = float(X[sel, 0].mean())
            c_mean = float(X[sel, 1].mean())
            R = float(np.sqrt(s_mean ** 2 + c_mean ** 2))
            mean_deg = float(np.degrees(np.arctan2(s_mean, c_mean)) / 2.0)
            median_deg = float(np.median(aolp_at_emb[sel]))
            std_deg = float(np.degrees(np.sqrt(max(-2.0 * np.log(max(R, 1e-9)), 0.0))) / 2.0)
            if R > 1e-9:
                s_k_n, c_k_n = s_mean / R, c_mean / R
            else:
                s_k_n, c_k_n = 0.0, 1.0
            dot = float(np.clip(s_k_n * s_g_n + c_k_n * c_g_n, -1.0, 1.0))
            ang_dist_deg = float(np.degrees(np.arccos(dot)) / 2.0)
        else:
            R, mean_deg, median_deg, std_deg, ang_dist_deg = 0.0, float('nan'), float('nan'), float('nan'), 0.0
        size_frac = n / max(total, 1)
        score = size_frac * R * (ang_dist_deg ** 2) if lbl != -1 else 0.0
        cluster_masks.append(cm)
        all_info.append({
            'label': int(lbl), 'size': n, 'size_frac': size_frac,
            'R': R, 'mean_deg': mean_deg, 'median_deg': median_deg, 'std_deg': std_deg,
            'ang_dist_deg': ang_dist_deg, 'score': score,
        })

    scores = [info['score'] for info in all_info]
    if any(s > 0 for s in scores):
        winner_idx = int(np.argmax(scores))
    else:
        winner_idx = -1
    return cluster_masks, all_info, winner_idx, labels


def cluster_umap_hdbscan_by_delta(embedding, delta_deg, valid_indices, S0_shape,
                                   min_cluster_size=100, min_samples=None):
    """HDBSCAN sull'embedding UMAP, stats su retardance δ in [0°, 360°).

    Mirror di `cluster_umap_hdbscan_by_aolp` ma δ è già ciclica su giro intero
    (no doppio angolo: sin(δ), cos(δ) diretti). Score generico
    `size_frac × R × ang_dist_deg²` con `ang_dist_deg ∈ [0°, 180°]`.
    Median calcolata in frame locale (mean_dir ± π) per gestire wrap a 0°/360°.

    Restituisce:
      cluster_masks: list di bool array shape=S0_shape, uno per cluster.
      all_info: dict {label, size, size_frac, R, mean_deg ∈ [0°, 360°),
                      median_deg ∈ [0°, 360°), std_deg, ang_dist_deg, score}.
      winner_idx: int, index del cluster con score massimo (escluso noise -1).
      labels: array (n_emb,) di label HDBSCAN.
    Se troppo pochi punti: (None, [], None, None).
    """
    from sklearn.cluster import HDBSCAN

    if embedding.shape[0] < min_cluster_size:
        return None, [], None, None

    clusterer = HDBSCAN(min_cluster_size=min_cluster_size,
                        min_samples=min_samples)
    labels = clusterer.fit_predict(embedding)

    delta_flat = delta_deg.ravel()
    delta_at_emb = delta_flat[valid_indices]
    delta_rad = np.deg2rad(delta_at_emb)
    X = np.column_stack([np.sin(delta_rad), np.cos(delta_rad)])

    not_noise = labels != -1
    if not_noise.any():
        s_g = float(X[not_noise, 0].mean())
        c_g = float(X[not_noise, 1].mean())
    else:
        s_g, c_g = 0.0, 1.0
    R_g = float(np.sqrt(s_g ** 2 + c_g ** 2))
    if R_g > 1e-9:
        s_g_n, c_g_n = s_g / R_g, c_g / R_g
    else:
        s_g_n, c_g_n = 0.0, 1.0

    unique_labels = sorted(set(labels.tolist()))
    total = embedding.shape[0]
    cluster_masks = []
    all_info = []
    valid_idx_arr = np.asarray(valid_indices, dtype=np.int64)
    for lbl in unique_labels:
        sel = labels == lbl
        n = int(sel.sum())
        cm = np.zeros(S0_shape, dtype=bool)
        if n > 0:
            idx_in_image = valid_idx_arr[sel]
            ys, xs = np.unravel_index(idx_in_image, S0_shape)
            cm[ys, xs] = True
            s_mean = float(X[sel, 0].mean())
            c_mean = float(X[sel, 1].mean())
            R = float(np.sqrt(s_mean ** 2 + c_mean ** 2))
            mean_dir_rad = float(np.arctan2(s_mean, c_mean))
            mean_deg = float(np.degrees(mean_dir_rad)) % 360.0
            diffs = np.angle(np.exp(1j * (delta_rad[sel] - mean_dir_rad)))
            med_diff = float(np.median(diffs))
            median_deg = float(np.degrees(mean_dir_rad + med_diff)) % 360.0
            std_deg = float(np.degrees(np.sqrt(max(-2.0 * np.log(max(R, 1e-9)), 0.0))))
            if R > 1e-9:
                s_k_n, c_k_n = s_mean / R, c_mean / R
            else:
                s_k_n, c_k_n = 0.0, 1.0
            dot = float(np.clip(s_k_n * s_g_n + c_k_n * c_g_n, -1.0, 1.0))
            ang_dist_deg = float(np.degrees(np.arccos(dot)))
        else:
            R, mean_deg, median_deg, std_deg, ang_dist_deg = 0.0, float('nan'), float('nan'), float('nan'), 0.0
        size_frac = n / max(total, 1)
        score = size_frac * R * (ang_dist_deg ** 2) if lbl != -1 else 0.0
        cluster_masks.append(cm)
        all_info.append({
            'label': int(lbl), 'size': n, 'size_frac': size_frac,
            'R': R, 'mean_deg': mean_deg, 'median_deg': median_deg, 'std_deg': std_deg,
            'ang_dist_deg': ang_dist_deg, 'score': score,
        })

    scores = [info['score'] for info in all_info]
    if any(s > 0 for s in scores):
        winner_idx = int(np.argmax(scores))
    else:
        winner_idx = -1
    return cluster_masks, all_info, winner_idx, labels


def compute_or_load_umap_cache(ch, sd, dataset, cache_dir='./outputs',
                                n_target=UMAP_RANDOM_SAMPLE_N,
                                channel_seed_offset=None):
    """Compute UMAP embedding for one channel or load from `.npz` cache.

    sd: dict con chiavi S0, S1, S2, S3, DoLP, AoLP, delta, theta, bg_mask,
        sat_mask (opzionale). dataset: nome dataset usato nel filename cache.
    Cache layout: `{cache_dir}/umap_{dataset}_{ch}_nobg_cache.npz`. Schema v3
    (axis_conf_min + sample_n) invalidato automaticamente se i parametri
    correnti differiscono.

    Restituisce (embedding, AoLP_2D, delta_2D, valid_indices, S0_shape) o
    None se troppo pochi pixel validi (<100).
    """
    import os
    import time as _time

    if channel_seed_offset is None:
        channel_seed_offset = {'R': 0, 'G': 1, 'B': 2}
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"umap_{dataset}_{ch}_nobg_cache.npz")

    if os.path.exists(cache_path):
        with np.load(cache_path) as d:
            ok = ('delta_deg' in d.files and 'axis_conf_min' in d.files
                  and 'sample_n' in d.files
                  and float(d['axis_conf_min']) == UMAP_AXIS_CONFIDENCE_MIN
                  and int(d['sample_n']) == n_target)
            if ok:
                print(f"[cache] carico {cache_path}")
                return (d['embedding'].copy(),
                        d['aolp_deg'].copy(),
                        d['delta_deg'].copy(),
                        d['valid_indices'].copy(),
                        tuple(int(x) for x in d['S0_shape']))
        print(f"[cache] {cache_path} obsoleto, ricomputo")

    S0 = sd['S0']; S1 = sd['S1']; S2 = sd['S2']; S3 = sd['S3']
    DoLP = sd['DoLP']; AoLP = sd['AoLP']
    delta = sd['delta']; theta = sd['theta']
    sat_mask = sd.get('sat_mask')
    base_valid = build_validity_mask(
        S0, DoLP, bg_mask=None, sat_mask=sat_mask, theta_deg=theta)
    valid_mask = random_sample_mask(
        S0.shape, base_valid, n_target=n_target,
        seed=RANDOM_STATE + channel_seed_offset.get(ch, 0))
    features, valid_indices = build_feature_matrix(
        S0, S1, S2, S3, DoLP, valid_mask, feature_mode='no_delta')
    print(f"  pixel validi: {features.shape[0]}")
    if features.shape[0] < 100:
        print("  too few valid pixels, skip")
        return None
    t0 = _time.time()
    embedding = fit_umap(features)
    print(f"  UMAP fit: {_time.time() - t0:.1f}s")
    np.savez_compressed(
        cache_path, embedding=embedding, aolp_deg=AoLP,
        delta_deg=delta, valid_indices=valid_indices,
        S0_shape=np.array(S0.shape, dtype=np.int64),
        axis_conf_min=np.float32(UMAP_AXIS_CONFIDENCE_MIN),
        sample_n=np.int32(n_target))
    print(f"[cache] salvato {cache_path}")
    return embedding, AoLP, delta, valid_indices, S0.shape


def export_umap_panels(spec, embedding, valid_indices, S0_shape,
                       dataset_label, channel_label, output_dir,
                       save_plots=True, hist_bins=180, bg_mask=None):
    """Esporta 3 pannelli pubblicabili (mappa, scatter UMAP, istogramma).

    spec viene da `color_spec(color_by, ...)`. Cartella output:
        `{output_dir}/{dataset_label}/{spec['export_subdir']}/{channel_label}/`
    File: `{export_map_file}`, `umap_scatter.pdf`, `{export_hist_file}`.

    Se `bg_mask` fornita, l'istogramma è ristretto ai pixel sample
    (`~bg_mask`) anziché a tutti i pixel validi. Mappa e scatter non
    vengono filtrati (servono per debug visivo dell'intero campo).
    """
    import os
    import matplotlib.pyplot as plt
    from .plotting import save_and_show

    out = os.path.join(output_dir, dataset_label,
                       spec['export_subdir'], channel_label)
    os.makedirs(out, exist_ok=True)
    cmap = spec['cmap']
    vmin, vmax = spec['vmin'], spec['vmax']
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    H, W = S0_shape
    value_map = spec['value_map']
    value_valid = spec['value_valid']
    extend = spec['cbar_extend']

    aspect_img = H / W
    fig_w = 3.35
    fig_h = fig_w * aspect_img
    fig, ax = plt.subplots(figsize=(fig_w + 0.7, fig_h))
    im = ax.imshow(value_map, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    ax.set_title(spec['map_title_short'], pad=6)
    ax.axis('off')
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, extend=extend)
    cb.set_label(spec['unit_label'])
    save_and_show(fig, os.path.join(out, spec['export_map_file']),
                  show=save_plots)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.35 + 0.7, 3.35))
    ax.scatter(embedding[:, 0], embedding[:, 1],
               c=value_valid, cmap=cmap, vmin=vmin, vmax=vmax,
               s=2.0, alpha=0.85, rasterized=True)
    ax.set_xlabel('UMAP 1'); ax.set_ylabel('UMAP 2')
    ax.set_title('UMAP embedding', pad=6)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                      ax=ax, fraction=0.046, pad=0.03, extend=extend)
    cb.set_label(spec['unit_label'])
    save_and_show(fig, os.path.join(out, 'umap_scatter.pdf'), show=save_plots)
    plt.close(fig)

    hmin, hmax = spec['hist_range']
    fig, ax = plt.subplots(figsize=(3.35, 2.2))
    if bg_mask is not None:
        sample_at_emb = ~bg_mask.ravel()[valid_indices]
        hist_vals = value_valid[sample_at_emb & np.isfinite(value_valid)]
        hist_ylabel = '# pixel sample'
    else:
        hist_vals = value_valid[np.isfinite(value_valid)]
        hist_ylabel = '# pixel validi'
    counts, edges = np.histogram(hist_vals, bins=hist_bins, range=(hmin, hmax))
    centers = 0.5 * (edges[:-1] + edges[1:])
    widths = np.diff(edges)
    bar_colors = [cmap(norm(c)) for c in centers]
    ax.bar(centers, counts, width=widths, color=bar_colors,
           edgecolor='none', align='center')
    edge = spec['hist_edge_exclude']
    if edge > 0.0:
        inner = (centers > hmin + edge) & (centers < hmax - edge)
        ymax = (float(counts[inner].max())
                if (inner.any() and counts[inner].size)
                else (float(counts.max()) if counts.size else 1.0))
        ax.axvspan(hmin, hmin + edge, color='gray', alpha=0.08)
        ax.axvspan(hmax - edge, hmax, color='gray', alpha=0.08)
        ax.set_ylim(0, ymax * 1.25)
    else:
        ymax = float(np.percentile(counts, 99)) if counts.size else 1.0
        ax.set_ylim(0, ymax * 1.15)
    ax.set_xlim(hmin, hmax)
    ax.set_xlabel(spec['unit_label'])
    ax.set_ylabel(hist_ylabel)
    ax.set_title(spec['hist_title'].replace('(c) ', ''), pad=6)
    ax.grid(True, axis='y', linestyle=':', alpha=0.4)
    save_and_show(fig, os.path.join(out, spec['export_hist_file']),
                  show=save_plots)
    plt.close(fig)
    return out


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
