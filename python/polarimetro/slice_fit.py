"""Slice diagonale + plateau detection + fit retardance-vs-strati.

Mattoni atomici per la cella F del notebook (strati_v2). La composizione del
plot 3-pannelli + export PDF/HTML resta nella cella; qui solo l'algoritmo.

Pipeline tipica:
    t_vals, X, Y, center = build_slice_grid(...)
    profile, circ_std = sample_thick_delta(delta_map, X, Y)
    crop_idx = find_auto_crop(profile, t_vals, ds, margin, ignore_native)
    plateaus = detect_plateaus(profile, t_vals, ds, crop_idx, sigma, grad_th,
                                min_len_native, labels)
    fit = fit_layers(plateaus)
"""
import numpy as np
from scipy import ndimage as _ndimage


def build_slice_grid(shape, anchor_native, angle_deg, ds, hw_native,
                     step_native):
    """Costruisce griglia (T, U) di campionamento per slice diagonale spessa.

    shape: (H, W) della mappa downsampled. anchor_native: (x_n, y_n) px nativi
    del centro della slice. angle_deg: direzione in gradi. ds: downsample.
    hw_native: semi-larghezza banda (px nativi). step_native: passo lungo
    slice (px nativi).

    Restituisce (t_vals, X, Y, (cx, cy)) con X, Y shape (n_t, 2*n_perp+1) in
    coordinate downsampled, pronti per scipy.ndimage.map_coordinates.
    """
    H, W = shape
    cx_ds = anchor_native[0] / ds
    cy_ds = anchor_native[1] / ds
    half_ds = hw_native / ds
    step_ds = step_native / ds
    theta = np.deg2rad(angle_deg)
    dx, dy = np.cos(theta), -np.sin(theta)

    def _t_to_edge(c, d, lim):
        if d > 1e-12:
            return (lim - 1 - c) / d
        if d < -1e-12:
            return -c / d
        return np.inf

    t_pos = min(_t_to_edge(cx_ds, dx, W), _t_to_edge(cy_ds, dy, H))
    t_neg = min(_t_to_edge(cx_ds, -dx, W), _t_to_edge(cy_ds, -dy, H))
    t_vals = np.arange(-t_neg, t_pos + step_ds, step_ds)
    nx, ny = -dy, dx
    n_perp = max(0, int(np.floor(half_ds)))
    offsets = np.arange(-n_perp, n_perp + 1)
    T, U = np.meshgrid(t_vals, offsets, indexing='ij')
    X = cx_ds + T * dx + U * nx
    Y = cy_ds + T * dy + U * ny
    return t_vals, X, Y, (cx_ds, cy_ds)


def sample_thick_delta(delta_map, X, Y):
    """Campiona delta_map (in gradi, ciclica 0-360) lungo slice spessa.

    Media circolare (atan2(sin, cos)) sulla larghezza U per ogni t. Restituisce
    (delta_mean, circ_std), entrambi 1D di lunghezza n_t. NaN dove la banda è
    interamente fuori da pixel validi.
    """
    valid_in = np.isfinite(delta_map)
    delta_filled = np.where(valid_in, delta_map, 0.0)
    rad = np.deg2rad(delta_filled)
    coords = np.stack([Y.ravel(), X.ravel()], axis=0)
    sin_s = _ndimage.map_coordinates(np.sin(rad), coords, order=1, mode='constant', cval=0.0)
    cos_s = _ndimage.map_coordinates(np.cos(rad), coords, order=1, mode='constant', cval=0.0)
    valid_s = _ndimage.map_coordinates(valid_in.astype(np.float32), coords, order=1, mode='constant', cval=0.0)
    sin_s = sin_s.reshape(X.shape)
    cos_s = cos_s.reshape(X.shape)
    w = (valid_s.reshape(X.shape) > 0.5).astype(np.float32)
    w_sum = w.sum(axis=1)
    w_safe = np.maximum(w_sum, 1.0)
    sin_m = (sin_s * w).sum(axis=1) / w_safe
    cos_m = (cos_s * w).sum(axis=1) / w_safe
    delta_mean = np.degrees(np.arctan2(sin_m, cos_m)) % 360.0
    delta_mean = np.where(w_sum > 0.5, delta_mean, np.nan)
    R = np.sqrt(sin_m ** 2 + cos_m ** 2)
    circ_std = np.degrees(np.sqrt(np.maximum(-2.0 * np.log(np.clip(R, 1e-9, 1.0)), 0.0)))
    circ_std = np.where(w_sum > 0.5, circ_std, np.nan)
    return delta_mean, circ_std


def find_auto_crop(profile, t_vals, ds, margin, ignore_native):
    """Trova indici crop (start, end) lungo slice escludendo bordi + δ vicini a 0/360.

    Esclude `ignore_native` px nativi ai due estremi dell'arc, poi richiede
    profilo finito e δ ∈ [margin, 360-margin].
    """
    n = len(profile)
    if n == 0:
        return 0, 0
    arc = t_vals * ds
    arc_min = float(arc[0]) + ignore_native
    arc_max = float(arc[-1]) - ignore_native
    in_range = (arc >= arc_min) & (arc <= arc_max)
    in_win = (np.isfinite(profile)
              & (profile >= margin)
              & (profile <= 360.0 - margin)
              & in_range)
    idx = np.where(in_win)[0]
    if idx.size == 0:
        r = np.where(in_range)[0]
        return (int(r[0]), int(r[-1])) if r.size else (0, n - 1)
    return int(idx[0]), int(idx[-1])


def detect_plateaus(profile, t_vals, ds, crop_idx, sigma, grad_th,
                    min_len_native, labels):
    """Rileva plateau lungo profilo δ via gradient threshold dopo gauss blur.

    Restituisce lista di dict per ogni plateau con keys: label, idx_start,
    idx_end, arc_start, arc_end, arc_mid, delta_med (mediana circolare),
    delta_std, n_samples.
    """
    s, e = crop_idx
    if e <= s:
        return []
    seg = profile[s:e + 1]
    valid = np.isfinite(seg)
    if valid.sum() < 3:
        return []
    seg_for_smooth = np.where(valid, seg, np.nanmean(seg) if valid.any() else 0.0)
    smooth = _ndimage.gaussian_filter1d(seg_for_smooth, sigma=sigma, mode='nearest')
    grad = np.abs(np.gradient(smooth))
    flat = (grad < grad_th) & valid
    step_native = (t_vals[1] - t_vals[0]) * ds if len(t_vals) > 1 else 1.0
    min_run = max(1, int(np.ceil(min_len_native / max(step_native, 1e-6))))
    padded = np.concatenate(([False], flat, [False]))
    diffs = np.diff(padded.astype(np.int8))
    starts = np.where(diffs == 1)[0]
    ends_excl = np.where(diffs == -1)[0]
    runs = [(int(a), int(b - 1)) for a, b in zip(starts, ends_excl)
            if (b - a) >= min_run]
    if not runs:
        return []
    n_exp = len(labels)
    if len(runs) > n_exp:
        runs = sorted(runs, key=lambda r: -(r[1] - r[0]))[:n_exp]
    runs = sorted(runs, key=lambda r: r[0])
    arc = t_vals * ds
    seg_arc = arc[s:e + 1]
    plateaus = []
    seg_filled = np.where(valid, seg, np.nan)
    for i, (a, b) in enumerate(runs):
        lbl = labels[i] if len(runs) == n_exp else f"P{i+1}"
        block = seg_filled[a:b + 1]
        block = block[np.isfinite(block)]
        if block.size == 0:
            continue
        rad = np.deg2rad(block)
        med = np.degrees(np.arctan2(np.sin(rad).mean(), np.cos(rad).mean())) % 360.0
        plateaus.append({
            'label': lbl,
            'idx_start': s + a, 'idx_end': s + b,
            'arc_start': float(seg_arc[a]), 'arc_end': float(seg_arc[b]),
            'arc_mid': 0.5 * (float(seg_arc[a]) + float(seg_arc[b])),
            'delta_med': float(med), 'delta_std': float(np.std(block)),
            'n_samples': int(b - a + 1),
        })
    return plateaus


def _unwrap_along_n(items):
    """Unwrap monotono lungo lista [(n, lbl, delta), ...] aggiungendo 360°."""
    if not items:
        return []
    out = [(items[0][0], items[0][1], items[0][2])]
    offset = 0.0
    prev = items[0][2]
    for n, lbl, y in items[1:]:
        y_adj = y + offset
        while y_adj < prev:
            offset += 360.0
            y_adj += 360.0
        out.append((n, lbl, y_adj))
        prev = y_adj
    return out


def fit_layers(plateaus):
    """Fit lineare attraverso origine δ = m·n da plateaus.

    Unwrap separato per lato L e R (entrambi includono centro). Restituisce
    dict {slope, r2, rms, x, y, y_raw, labels, n_unwrapped} o None se input
    insufficiente.
    """
    L, R, C = [], [], []
    for p in plateaus:
        lbl = p['label']
        y = float(p['delta_med'])
        if lbl.endswith('L'):
            try:
                n = int(lbl[:-1])
            except ValueError:
                continue
            L.append((n, lbl, y))
        elif lbl.endswith('R'):
            try:
                n = int(lbl[:-1])
            except ValueError:
                continue
            R.append((n, lbl, y))
        else:
            try:
                n = int(lbl)
            except ValueError:
                continue
            C.append((n, lbl, y))
    if not (L or R or C):
        return None
    L_seq = sorted(L + C, key=lambda t: t[0])
    R_seq = sorted(R + C, key=lambda t: t[0])
    L_unw = _unwrap_along_n(L_seq)
    R_unw = _unwrap_along_n(R_seq)
    unwrapped = {}
    for _, lbl, y in L_unw:
        unwrapped.setdefault(lbl, []).append(y)
    for _, lbl, y in R_unw:
        unwrapped.setdefault(lbl, []).append(y)
    pts = []
    for p in plateaus:
        lbl = p['label']
        if lbl not in unwrapped:
            continue
        try:
            n = int(lbl.rstrip('LR'))
        except ValueError:
            continue
        y_unw = float(np.mean(unwrapped[lbl]))
        pts.append((n, y_unw, lbl, float(p['delta_med'])))
    if not pts:
        return None
    x = np.array([q[0] for q in pts], dtype=float)
    y = np.array([q[1] for q in pts], dtype=float)
    y_raw = np.array([q[3] for q in pts], dtype=float)
    denom = float((x * x).sum())
    if denom <= 0:
        return None
    m = float((x * y).sum() / denom)
    y_pred = m * x
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 0 else float('nan')
    rms = float(np.sqrt(ss_res / max(len(y), 1)))
    # errore standard statistico della pendenza (fit through-origin):
    # sigma_m^2 = ss_res / (N-1) / sum(x^2)
    n_pts = len(y)
    slope_err = (float(np.sqrt(ss_res / (n_pts - 1) / denom))
                 if n_pts > 1 else float('nan'))
    n_unw = int(np.sum(np.abs(y - y_raw) > 1e-6))
    return {'slope': m, 'slope_err': slope_err, 'r2': r2, 'rms': rms,
            'x': x, 'y': y,
            'y_raw': y_raw, 'labels': [q[2] for q in pts],
            'n_unwrapped': n_unw}
