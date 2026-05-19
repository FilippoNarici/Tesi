"""Confronto fotoelastico barra acrilica caricata vs scarica (cella I).

Pipeline (su S0 unificato RGB):
    1. Allineamento globale via phase-correlation FFT su ROI del solo
       supporto destro (la parte flessa non deve dominare il fit traslazionale).
    2. Tracking della centerline pixel-per-pixel sulla barra: per ogni colonna
       x trova i due picchi negativi (bordi superiore/inferiore) e ne prende
       la media → y_mid(x).
    3. Fit polinomiale di grado 2 sulla centerline per regolarizzare il rumore.
    4. Costruzione del campo di warp Δy(x) = y_off_fit(x) − y_on_fit(x):
       deforma `barraon` finché la centerline coincide con `barraoff`.
       Solo nel range della barra; supporto a destra rimane invariato.
    5. ΔS3 = S3_warped(on) − S3(off) per canale.

`barraon_v2` carica la cache di `barraoff_v2` (deve essere pre-computata).
Modifica `_other_data` in-place applicando lo shift FFT a tutti i campi 2D
+ maschere.
"""
import numpy as np
from scipy.ndimage import (
    map_coordinates as _map_coords,
    shift as _ndi_shift,
    uniform_filter1d as _uniform,
)
from scipy.signal import find_peaks as _find_peaks


PHASE_CORR_EPS = 1e-12


def phase_correlation(ref, mov):
    """Phase correlation FFT con finestra di Hanning e interpolazione parabolica.

    Restituisce (dy, dx, err) con shift sub-pixel. `err` ∈ [0, 1] proxy del
    rumore: vicino a 0 = picco netto, vicino a 1 = picco diffuso. Pre-condizione:
    ref e mov senza NaN (usare `np.nan_to_num` prima della chiamata).
    """
    ref = ref.astype(np.float64) - ref.mean()
    mov = mov.astype(np.float64) - mov.mean()
    H, W = ref.shape
    win = np.hanning(H)[:, None] * np.hanning(W)[None, :]
    F_ref = np.fft.fft2(ref * win)
    F_mov = np.fft.fft2(mov * win)
    cross = F_ref * np.conj(F_mov)
    c = np.fft.ifft2(cross / (np.abs(cross) + PHASE_CORR_EPS)).real
    py, px = np.unravel_index(np.argmax(c), c.shape)
    peak_val = float(c[py, px])

    def _parab(y, idx, N):
        ip = (idx + 1) % N; im = (idx - 1) % N
        num = y[im] - y[ip]
        den = 2 * (y[im] - 2 * y[idx] + y[ip])
        return idx + (num / den if abs(den) > PHASE_CORR_EPS else 0.0)

    sy = _parab(c[:, px], py, H)
    sx = _parab(c[py, :], px, W)
    if sy > H / 2: sy -= H
    if sx > W / 2: sx -= W
    err = max(0.0, min(1.0, float(1.0 - peak_val / (np.std(c) * 5 + PHASE_CORR_EPS))))
    return float(sy), float(sx), err


def shift_dict_inplace(data_dict, shift_yx, fields_2d, mask_fields):
    """Applica `shift_yx = (dy, dx)` a tutti i canali di `data_dict` in-place.

    `fields_2d`: tuple di chiavi float 2D (S0, S1, ...) — interpolazione bilineare.
    `mask_fields`: tuple di chiavi bool 2D (bg_mask, ...) — nearest + threshold.
    Per-canale: data_dict[ch][k]. Salta chiavi assenti o None.
    """
    for ch in data_dict:
        d = data_dict[ch]
        for k in fields_2d:
            arr = d.get(k)
            if arr is None:
                continue
            d[k] = _ndi_shift(arr.astype(np.float32), shift=shift_yx,
                               order=1, mode='nearest').astype(arr.dtype)
        for k in mask_fields:
            arr = d.get(k)
            if arr is None:
                continue
            shifted = _ndi_shift(arr.astype(np.float32), shift=shift_yx,
                                  order=0, mode='constant', cval=0.0)
            d[k] = (shifted > 0.5)


def normalize_for_display(x, lo_pct=1.0, hi_pct=99.0):
    """Normalizza array a [0, 1] via percentili (robusto a outlier)."""
    lo = float(np.nanpercentile(x, lo_pct))
    hi = float(np.nanpercentile(x, hi_pct))
    return np.clip((x - lo) / (hi - lo + 1e-9), 0.0, 1.0)


def composite_rgb(channel_red, channel_blue):
    """Sovrappone due array 2D in canali R + B (G = 0). Utile per overlay debug."""
    rgb = np.zeros((*channel_red.shape, 3), dtype=np.float32)
    rgb[..., 0] = channel_red
    rgb[..., 2] = channel_blue
    return rgb


def trace_centerline(img, x_range_frac=(0.17, 0.80), prom_frac=0.10,
                     smooth_half=3):
    """Traccia centerline come media dei due picchi negativi più prominenti per colonna.

    `img` viene smussato lungo x (uniform_filter1d) prima del peak detection.
    Restituisce (xs, y_top, y_bot, y_mid): `xs` indici di colonna nel range,
    le tre y sono shape (xs.size,) con NaN dove < 2 picchi trovati.
    """
    H, W = img.shape
    img_s = _uniform(np.nan_to_num(img.astype(np.float64), nan=0.0),
                      size=2 * smooth_half + 1, axis=1, mode='nearest')
    x0 = int(round(x_range_frac[0] * W))
    x1 = int(round(x_range_frac[1] * W))
    xs = np.arange(x0, x1)
    y_top = np.full(xs.size, np.nan)
    y_bot = np.full(xs.size, np.nan)
    y_mid = np.full(xs.size, np.nan)
    for i, x in enumerate(xs):
        col = img_s[:, x]
        inv = col.max() - col
        prom = prom_frac * (col.max() - col.min())
        peaks, props = _find_peaks(inv, prominence=prom)
        if peaks.size < 2:
            continue
        order = np.argsort(-props['prominences'])[:2]
        two = np.sort(peaks[order])
        y_top[i] = float(two[0]); y_bot[i] = float(two[1])
        y_mid[i] = 0.5 * (two[0] + two[1])
    return xs, y_top, y_bot, y_mid


def polyfit_centerline(xs, y_mid, degree=2):
    """Fit polinomiale di `y_mid(xs)` di grado `degree`, ignorando NaN.

    Restituisce (coeffs, y_fit) o (None, None) se troppi NaN.
    """
    ok = np.isfinite(y_mid)
    if int(ok.sum()) < degree + 1:
        return None, None
    coeffs = np.polyfit(xs[ok].astype(np.float64),
                         y_mid[ok].astype(np.float64), degree)
    return coeffs, np.polyval(coeffs, xs.astype(np.float64))


def rms_residual(y, y_fit):
    """RMS dei residui `y - y_fit`, ignorando NaN."""
    ok = np.isfinite(y) & np.isfinite(y_fit)
    return float(np.sqrt(np.mean((y[ok] - y_fit[ok]) ** 2))) if ok.any() else float('nan')


def build_warp_field(W, xs, coeff_on, coeff_off):
    """Costruisce array Δy(x) di shape (W,) per warp colonna-per-colonna.

    `coeff_*`: coefficienti polinomiali da `polyfit_centerline`. Solo il range
    [0, xs[-1]] viene popolato da `polyval(off) - polyval(on)`. Oltre xs[-1]
    Δy resta zero (preserva supporto). Restituisce array float64 o None se
    coefficienti mancanti.
    """
    if coeff_on is None or coeff_off is None:
        return None
    delta_y = np.zeros(W, dtype=np.float64)
    x_extrap = np.arange(0, int(xs[-1]) + 1, dtype=np.float64)
    delta_y[:x_extrap.size] = (np.polyval(coeff_off, x_extrap)
                                - np.polyval(coeff_on, x_extrap))
    return delta_y


def warp_image(img, delta_y):
    """Deforma `img` colonna-per-colonna con shift verticale `delta_y(x)`.

    Pixel sorgente: (y - Δy(x), x). NaN nell'originale → NaN nel warped
    (propagati via mask separata). Restituisce array float32 stessa shape.
    """
    H, W = img.shape
    y_grid, x_grid = np.mgrid[0:H, 0:W]
    y_src = y_grid - delta_y[None, :]
    coords = np.stack([y_src.ravel(), x_grid.ravel()], axis=0)

    img_clean = np.nan_to_num(img, nan=0.0).astype(np.float32)
    warped = _map_coords(img_clean, coords, order=1, mode='nearest').reshape(H, W)

    nan_mask = ~np.isfinite(img)
    if nan_mask.any():
        nan_w = _map_coords(nan_mask.astype(np.float32), coords,
                              order=0, mode='nearest').reshape(H, W) > 0.5
        warped[nan_w] = np.nan
    return warped
