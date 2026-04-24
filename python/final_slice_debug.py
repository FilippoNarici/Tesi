"""
Diagnostic: retardance map + thick diagonal slice across the strati sample.

Runs the standard polarimeter pipeline (Stokes -> S3 -> 2D alignment ->
Poincare ellipticity rebasing -> retardance) for the channel and dataset
configured in ``final_utils.py``, then extracts ``delta`` along a user-defined
straight slice that crosses every tape layer. The slice is integrated over a
band of parallel lines (configurable half-width) and averaged in the
sin/cos domain so the [0, 360) wrap does not corrupt the mean.

Output: PNG with the retardance map (slice band overlaid) plus the 1D
profile of delta along the slice. Useful for inspecting left/right
asymmetries inside individual layers without committing to a code change.
"""

import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.ndimage as ndimage

import final_utils as utils

if 'MPLBACKEND' not in os.environ:
    try:
        matplotlib.use('TkAgg')
    except Exception:
        pass


# =============================================================================
# SLICE CONFIGURATION
# =============================================================================

# Anchor point on the slice line, in NATIVE (un-downsampled) image pixels.
SLICE_POINT_NATIVE_XY = (767, 422)

# Slope of the slice in degrees, goniometric convention: counter-clockwise
# from the +x axis with y treated as up (the natural reading off a protractor
# placed on the displayed image). Internally converted to pixel frame
# (where y increases downward) by flipping the y-component.
SLICE_ANGLE_DEG = 141.0

# Half-width of the thick band, perpendicular to the slice axis, in NATIVE
# (un-downsampled) pixels. Each output sample averages over the parallel
# lines that fit inside the band at the current downsample factor. Native
# units keep the physical band size constant across changes of
# utils.DOWNSAMPLE_FACTOR.
SLICE_HALF_WIDTH_NATIVE_PX = 200.0

# Sampling step along the slice, in NATIVE pixels. Converted to the analysis
# grid internally; with DOWNSAMPLE_FACTOR = 5 a value of 5 reproduces the
# previous one-sample-per-ds-pixel resolution.
SLICE_STEP_NATIVE_PX = 5.0

# Auto-crop the 1D profile to the central region where the band-averaged
# delta sits well away from the [0, 360) wrap edges. The bg pixels and the
# saturation-fallback regions snap to delta ~ 0 or ~ 360, so requiring
# delta to be at least AUTO_CROP_EDGE_MARGIN_DEG away from both endpoints
# isolates the genuine sample signal without needing a binary mask.
AUTO_CROP_TO_SAMPLE = True

# Minimum angular distance from 0 deg and 360 deg for a slice sample to
# count as "inside the sample". Set in degrees of retardance.
AUTO_CROP_EDGE_MARGIN_DEG = 15.0

# Hard ignore band at each end of the slice, in NATIVE pixels. Samples
# falling within this distance of either slice extremity are excluded from
# the crop search even if they pass the angular threshold (suppresses spikes
# from image-edge artefacts and bg holder regions far from the sample).
AUTO_CROP_IGNORE_NATIVE_PX = 1500.0

# =============================================================================
# PLATEAU AUTO-MEASUREMENT
# =============================================================================

# Detect the flat plateaus inside the cropped slice, label them by position
# (1L outermost-left ... 5 centre ... 1R outermost-right) and overlay the
# fitted retardance value on the 1D plot. Order is left-to-right along the
# slice; assignment assumes the funnel shape with a single central plateau.
PLATEAU_DETECT = True

# Ordered labels (innermost = '5'). Length must equal the expected number
# of plateaus; the script picks the longest matching number of detected
# runs and sorts them by arc-length position before assigning labels.
PLATEAU_LABELS = ['1L', '2L', '3L', '4L', '5', '4R', '3R', '2R', '1R']

# Smoothing applied to delta before computing the gradient, in samples
# (one sample = SLICE_STEP_NATIVE_PX native pixels). Suppresses single-sample
# spikes that would otherwise break a long flat run.
PLATEAU_SMOOTH_SIGMA_SAMPLES = 1.5

# Maximum |d delta / d sample| (degrees per slice sample) tolerated inside
# a plateau. Steps between layers easily exceed 5 deg/sample, so a tight
# threshold cleanly separates plateaus from transitions.
PLATEAU_GRADIENT_THRESH_DEG = 1

# Minimum length of a plateau, in NATIVE pixels. Shorter flat runs are
# discarded as noise excursions inside transition regions.
PLATEAU_MIN_LENGTH_NATIVE_PX = 30.0

# Through-origin linear fit delta = m * n over the labelled plateaus, using
# layer number n parsed from the label (e.g. '3L' -> 3, '5' -> 5). Reports
# the slope (deg per added layer), R^2, and per-point residuals.
LAYER_FIT_THROUGH_ORIGIN = True

OUTPUT_DIR = './outputs'


# =============================================================================
# PIPELINE (mirrors final_polarimeter.py)
# =============================================================================

def run_pipeline():
    utils.reset_saturation_accumulator()

    wavelength = utils.get_channel_wavelength(
        utils.WAVELENGTHS_CSV, utils.TARGET_CHANNEL_IDX)

    angles_rad_2x, image_stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
        utils.DOWNSAMPLE_FACTOR, invert_angles=True)
    if angles_rad_2x is None:
        raise RuntimeError("Failed to load rotation sequence.")

    S0, S1, S2 = utils.calculate_linear_stokes(angles_rad_2x, image_stack)
    S3 = utils.calculate_s3(utils.WAV_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
                            utils.DOWNSAMPLE_FACTOR, wavelength=wavelength)

    bg_mask = utils.generate_background_mask(S0, S3)
    S1, S2 = utils.align_reference_frame(S1, S2, bg_mask)
    S1, S3 = utils.align_poincare_ellipticity(S0, S1, S3, bg_mask)

    delta, _theta = utils.calculate_retardance_and_fast_axis(
        S0, S1, S2, S3, bg_mask)

    sat_mask = utils.get_saturation_mask(utils.DOWNSAMPLE_FACTOR)
    if sat_mask is not None and sat_mask.shape == delta.shape:
        delta = np.where(sat_mask, np.nan, delta)

    return delta, S0, bg_mask, wavelength


# =============================================================================
# SLICE GEOMETRY + SAMPLING
# =============================================================================

def build_slice_grid(map_shape, point_native_xy, angle_deg,
                     downsample_factor,
                     half_width_native_px, step_native_px):
    """Returns the (X, Y) coordinate grids in downsampled pixel frame for
    every sample of the thick slice.

    Shape of X, Y is (n_along, 2 * floor(half_width_ds) + 1).
    Inputs are expressed in NATIVE pixels and converted to the analysis grid
    via ``downsample_factor``, so the physical extent of the slice does not
    drift when the user changes the downsampling.
    """
    H, W = map_shape
    cx_ds = point_native_xy[0] / downsample_factor
    cy_ds = point_native_xy[1] / downsample_factor

    half_width_ds = half_width_native_px / downsample_factor
    step_ds = step_native_px / downsample_factor

    # Goniometric -> pixel frame: y axis is flipped on screen.
    theta = np.deg2rad(angle_deg)
    dx = np.cos(theta)
    dy = -np.sin(theta)

    # Find the longest signed arc length that keeps the centerline inside
    # the image bounds (0 <= x <= W-1, 0 <= y <= H-1).
    def t_to_edge(c, d, lim):
        if d > 1e-12:
            return (lim - 1 - c) / d
        if d < -1e-12:
            return -c / d
        return np.inf

    t_pos = min(t_to_edge(cx_ds, dx, W), t_to_edge(cy_ds, dy, H))
    t_neg = min(t_to_edge(cx_ds, -dx, W), t_to_edge(cy_ds, -dy, H))

    t_vals = np.arange(-t_neg, t_pos + step_ds, step_ds)

    # Perpendicular direction (left-hand normal in pixel frame).
    nx, ny = -dy, dx

    n_perp = max(0, int(np.floor(half_width_ds)))
    offsets = np.arange(-n_perp, n_perp + 1)
    T, U = np.meshgrid(t_vals, offsets, indexing='ij')

    X = cx_ds + T * dx + U * nx
    Y = cy_ds + T * dy + U * ny

    return t_vals, X, Y, (cx_ds, cy_ds), (dx, dy), (nx, ny)


def find_sample_crop(delta_slice, t_vals, downsample_factor,
                     edge_margin_deg, ignore_native_px):
    """Returns inclusive (start, end) indices into ``delta_slice`` bracketing
    the central region where the band-averaged retardance sits at least
    ``edge_margin_deg`` away from both 0 deg and 360 deg, after discarding
    ``ignore_native_px`` of slice on each end.

    Scans inward from each end of the surviving range and stops at the first
    qualifying sample, so the crop tracks the actual sample-vs-background
    transition where the profile rises off the wrap edges. Falls back to the
    full slice (or the ignore-trimmed range) if no sample qualifies.
    """
    n = len(delta_slice)
    if n == 0:
        return 0, 0

    arc_native = t_vals * downsample_factor
    arc_min = float(arc_native[0]) + ignore_native_px
    arc_max = float(arc_native[-1]) - ignore_native_px
    in_range = (arc_native >= arc_min) & (arc_native <= arc_max)

    in_window = (np.isfinite(delta_slice)
                 & (delta_slice >= edge_margin_deg)
                 & (delta_slice <= 360.0 - edge_margin_deg)
                 & in_range)
    idx = np.where(in_window)[0]
    if idx.size == 0:
        range_idx = np.where(in_range)[0]
        if range_idx.size == 0:
            return 0, n - 1
        return int(range_idx[0]), int(range_idx[-1])

    return int(idx[0]), int(idx[-1])


def sample_thick_slice(delta_map, X, Y):
    """Averages delta across the band in the sin/cos domain to respect the
    [0, 360) wrap. Returns the 1D mean profile and the per-sample circular
    standard deviation across the band (useful as an envelope on the plot).
    """
    valid_input = np.isfinite(delta_map)
    delta_filled = np.where(valid_input, delta_map, 0.0)

    rad = np.deg2rad(delta_filled)
    coords = np.stack([Y.ravel(), X.ravel()], axis=0)

    sin_samp = ndimage.map_coordinates(np.sin(rad), coords, order=1,
                                        mode='constant', cval=0.0)
    cos_samp = ndimage.map_coordinates(np.cos(rad), coords, order=1,
                                        mode='constant', cval=0.0)
    valid_samp = ndimage.map_coordinates(valid_input.astype(np.float32),
                                          coords, order=1,
                                          mode='constant', cval=0.0)

    sin_samp = sin_samp.reshape(X.shape)
    cos_samp = cos_samp.reshape(X.shape)
    weights = (valid_samp.reshape(X.shape) > 0.5).astype(np.float32)

    w_sum = weights.sum(axis=1)
    w_sum_safe = np.maximum(w_sum, 1.0)
    sin_mean = (sin_samp * weights).sum(axis=1) / w_sum_safe
    cos_mean = (cos_samp * weights).sum(axis=1) / w_sum_safe

    delta_mean = np.degrees(np.arctan2(sin_mean, cos_mean)) % 360.0
    delta_mean = np.where(w_sum > 0.5, delta_mean, np.nan)

    R = np.sqrt(sin_mean ** 2 + cos_mean ** 2)
    circ_std_deg = np.degrees(np.sqrt(np.maximum(-2.0 * np.log(np.clip(R, 1e-9, 1.0)),
                                                  0.0)))
    circ_std_deg = np.where(w_sum > 0.5, circ_std_deg, np.nan)

    return delta_mean, circ_std_deg


# =============================================================================
# PLATEAU DETECTION
# =============================================================================

def detect_plateaus(delta_slice, t_vals, downsample_factor, crop_idx,
                    smooth_sigma_samples, gradient_thresh_deg,
                    min_length_native_px, expected_labels):
    """Identifies the flat plateaus inside the cropped slice and labels them
    in arc-length order using ``expected_labels``.

    The detector smooths delta with a small Gaussian, marks samples whose
    absolute first derivative falls below the threshold, gathers contiguous
    "flat" runs longer than ``min_length_native_px``, then takes the
    ``len(expected_labels)`` longest runs (most plausible plateaus) and
    sorts them by arc position. Labels are assigned positionally.

    Returns a list of dicts with keys: label, idx_start, idx_end, arc_start,
    arc_end, arc_mid, delta_med (circular mean), delta_std, n_samples.
    Indices are absolute (into ``delta_slice`` / ``t_vals``).
    """
    s, e = crop_idx
    if e <= s:
        return []

    seg_delta = delta_slice[s:e + 1]
    arc_native = t_vals * downsample_factor
    seg_arc = arc_native[s:e + 1]
    valid = np.isfinite(seg_delta)
    if valid.sum() < 3:
        return []

    # Gaussian smoothing on the raw delta is fine here: the cropped region
    # already excludes the [0, 360) wrap edges, so plain arithmetic does
    # not jump across the discontinuity.
    seg_filled = np.where(valid, seg_delta, np.nan)
    nan_mask = ~valid
    seg_for_smooth = np.where(valid, seg_delta,
                              np.nanmean(seg_delta) if valid.any() else 0.0)
    smooth = ndimage.gaussian_filter1d(seg_for_smooth,
                                        sigma=smooth_sigma_samples,
                                        mode='nearest')

    grad = np.abs(np.gradient(smooth))
    flat = (grad < gradient_thresh_deg) & valid

    step_native = ((t_vals[1] - t_vals[0]) * downsample_factor
                   if len(t_vals) > 1 else 1.0)
    min_run = max(1, int(np.ceil(min_length_native_px / max(step_native, 1e-6))))

    padded = np.concatenate(([False], flat, [False]))
    diffs = np.diff(padded.astype(np.int8))
    starts = np.where(diffs == 1)[0]
    ends_excl = np.where(diffs == -1)[0]
    runs = [(int(a), int(b - 1)) for a, b in zip(starts, ends_excl)
            if (b - a) >= min_run]

    if not runs:
        return []

    n_expected = len(expected_labels)
    if len(runs) > n_expected:
        runs = sorted(runs, key=lambda r: -(r[1] - r[0]))[:n_expected]
    runs = sorted(runs, key=lambda r: r[0])

    plateaus = []
    for i, (a, b) in enumerate(runs):
        if len(runs) == n_expected:
            label = expected_labels[i]
        else:
            label = f'P{i + 1}'
        seg = seg_filled[a:b + 1]
        seg = seg[np.isfinite(seg)]
        if seg.size == 0:
            continue
        rad = np.deg2rad(seg)
        med = (np.degrees(np.arctan2(np.sin(rad).mean(),
                                      np.cos(rad).mean())) % 360.0)
        plateaus.append({
            'label': label,
            'idx_start': s + a,
            'idx_end': s + b,
            'arc_start': float(seg_arc[a]),
            'arc_end': float(seg_arc[b]),
            'arc_mid': 0.5 * (float(seg_arc[a]) + float(seg_arc[b])),
            'delta_med': float(med),
            'delta_std': float(np.std(seg)),
            'n_samples': int(b - a + 1),
        })
    return plateaus


# =============================================================================
# LAYER FIT
# =============================================================================

def _unwrap_along_n(items):
    """Cumulative 360 deg unwrap along ``items`` sorted by layer n.

    Walks the sequence in order; if the next value is less than the
    previous unwrapped value, adds 360 deg (and accumulates the offset for
    the rest of the sequence). Pure additive — never flips sign — so a
    physical retardance that wraps past 360 within the layer stack gets
    its monotonic ascent restored.

    ``items`` is ``[(n, label, y_raw), ...]`` sorted by n.
    Returns the same triples with y replaced by the unwrapped value.
    """
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


def fit_layers_through_origin(plateaus):
    """Through-origin least-squares fit ``delta = m * n`` over plateaus.

    Labels are parsed as ``<n><L|R>`` (e.g. '3L' -> n=3, side=L) or as a
    bare integer for the central plateau. The L and R sequences are each
    unwrapped independently (with the central n included as the terminus),
    so a physical retardance wrap inside the layer stack is restored to a
    monotonic ascent in n. Both unwraps converge on the central plateau,
    whose final value is the average of the two side estimates.

    Returns ``None`` if no plateau parses or the design matrix is degenerate.
    """
    L_items, R_items, C_items = [], [], []
    for p in plateaus:
        lbl = p['label']
        y = float(p['delta_med'])
        if lbl.endswith('L'):
            try:
                n = int(lbl[:-1])
            except ValueError:
                continue
            L_items.append((n, lbl, y))
        elif lbl.endswith('R'):
            try:
                n = int(lbl[:-1])
            except ValueError:
                continue
            R_items.append((n, lbl, y))
        else:
            try:
                n = int(lbl)
            except ValueError:
                continue
            C_items.append((n, lbl, y))

    if not (L_items or R_items or C_items):
        return None

    L_items.sort(key=lambda t: t[0])
    R_items.sort(key=lambda t: t[0])
    C_items.sort(key=lambda t: t[0])

    L_seq = sorted(L_items + C_items, key=lambda t: t[0])
    R_seq = sorted(R_items + C_items, key=lambda t: t[0])

    L_unw = _unwrap_along_n(L_seq)
    R_unw = _unwrap_along_n(R_seq)

    unwrapped = {}
    for n, lbl, y in L_unw:
        unwrapped.setdefault(lbl, []).append(y)
    for n, lbl, y in R_unw:
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
    resid = y - y_pred
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 0 else float('nan')
    rms = float(np.sqrt(ss_res / max(len(y), 1)))

    n_unwrapped = int(np.sum(np.abs(y - y_raw) > 1e-6))

    return {
        'slope': m,
        'r2': r2,
        'rms': rms,
        'x': x,
        'y': y,
        'y_raw': y_raw,
        'resid': resid,
        'labels': [q[2] for q in pts],
        'n_unwrapped': n_unwrapped,
    }


# =============================================================================
# PLOT
# =============================================================================

def make_plot(delta, t_vals, delta_slice, circ_std, X, Y,
              center_ds, dirs, dataset_name, channel_char, wavelength,
              crop_idx, plateaus=None, fit=None):
    cx_ds, cy_ds = center_ds
    crop_s, crop_e = crop_idx

    if fit is not None:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6),
                                 gridspec_kw={'width_ratios': [1.0, 1.4, 0.7]})
    else:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                                 gridspec_kw={'width_ratios': [1.0, 1.2]})

    im = axes[0].imshow(delta, cmap='twilight', vmin=0, vmax=360,
                        origin='upper')
    fig.colorbar(im, ax=axes[0], label='delta [deg]')

    mid_col = X.shape[1] // 2

    # Full slice in faint gray; cropped portion overlaid in bold red.
    axes[0].plot(X[:, mid_col], Y[:, mid_col], '-', color='gray',
                 lw=0.6, alpha=0.5)
    axes[0].plot(X[:, 0], Y[:, 0], 'w-', lw=0.4, alpha=0.4)
    axes[0].plot(X[:, -1], Y[:, -1], 'w-', lw=0.4, alpha=0.4)

    sl = slice(crop_s, crop_e + 1)
    axes[0].plot(X[sl, mid_col], Y[sl, mid_col], 'r-', lw=1.2)
    axes[0].plot(X[sl, 0], Y[sl, 0], 'y-', lw=0.7, alpha=0.9)
    axes[0].plot(X[sl, -1], Y[sl, -1], 'y-', lw=0.7, alpha=0.9)
    axes[0].plot(cx_ds, cy_ds, 'r+', mew=2, ms=12)

    axes[0].set_xlim(0, delta.shape[1] - 1)
    axes[0].set_ylim(delta.shape[0] - 1, 0)
    axes[0].set_title(f'{dataset_name}, channel {channel_char} '
                      f'(lambda = {wavelength:.0f} nm)')
    axes[0].set_xlabel('x [downsampled px]')
    axes[0].set_ylabel('y [downsampled px]')

    arc_native = t_vals * utils.DOWNSAMPLE_FACTOR
    axes[1].plot(arc_native[sl], delta_slice[sl], 'k-', lw=1.3,
                 label='band-averaged delta')
    axes[1].fill_between(arc_native[sl],
                         delta_slice[sl] - circ_std[sl],
                         delta_slice[sl] + circ_std[sl],
                         color='gray', alpha=0.3,
                         label='+/- circular std across band')
    axes[1].axhline(0, color='lightgray', lw=0.5)
    axes[1].axhline(360, color='lightgray', lw=0.5)

    if plateaus:
        for p in plateaus:
            axes[1].plot([p['arc_start'], p['arc_end']],
                         [p['delta_med'], p['delta_med']],
                         color='tab:red', lw=2.5, solid_capstyle='butt',
                         zorder=5)
            axes[1].axvspan(p['arc_start'], p['arc_end'],
                            color='tab:red', alpha=0.06, zorder=0)
            axes[1].annotate(
                f"{p['label']}: {p['delta_med']:.1f}°\n"
                f"σ={p['delta_std']:.1f}°",
                xy=(p['arc_mid'], p['delta_med']),
                xytext=(0, 12), textcoords='offset points',
                ha='center', va='bottom', fontsize=8, color='tab:red',
                bbox=dict(boxstyle='round,pad=0.25', fc='white',
                          ec='tab:red', lw=0.5, alpha=0.85),
                zorder=6)
        axes[1].plot([], [], color='tab:red', lw=2.5,
                     label='detected plateau (median delta)')

    axes[1].set_xlabel('arc length along slice [native px]')
    axes[1].set_ylabel('delta [deg]')
    axes[1].set_ylim(-10, 370)
    axes[1].grid(alpha=0.3)
    axes[1].legend(loc='best', fontsize=9)
    axes[1].set_title(
        f'Slice through ({SLICE_POINT_NATIVE_XY[0]}, '
        f'{SLICE_POINT_NATIVE_XY[1]}) at {SLICE_ANGLE_DEG:.0f} deg, '
        f'half-width = {SLICE_HALF_WIDTH_NATIVE_PX:.0f} native px')

    if fit is not None:
        ax_fit = axes[2]
        x_fit = fit['x']
        y_fit = fit['y']
        slope = fit['slope']

        # Group L vs R vs central by label suffix for distinct markers.
        for xi, yi, lbl in zip(x_fit, y_fit, fit['labels']):
            if lbl.endswith('L'):
                marker, color = 'o', 'tab:blue'
            elif lbl.endswith('R'):
                marker, color = 's', 'tab:orange'
            else:
                marker, color = 'D', 'tab:green'
            ax_fit.plot(xi, yi, marker=marker, color=color, ms=7,
                         markeredgecolor='k', markeredgewidth=0.5,
                         linestyle='none', zorder=3)
            ax_fit.annotate(lbl, (xi, yi), xytext=(4, 4),
                             textcoords='offset points', fontsize=7)

        x_max = float(x_fit.max())
        xs = np.array([0.0, x_max + 0.3])
        ax_fit.plot(xs, slope * xs, 'k--', lw=1.2,
                     label=f'fit: δ = {slope:.2f}° × n')

        # Show the raw (pre-unwrap) value too as a faint marker so the
        # +360 jumps are visible.
        n_unw = int(fit.get('n_unwrapped', 0))
        if n_unw:
            ax_fit.plot(x_fit, fit['y_raw'], 'x', color='gray', ms=6,
                         alpha=0.5, zorder=2, label='raw (pre-unwrap)')

        ax_fit.set_xlim(0, x_max + 0.5)
        ymax = max(float(y_fit.max()) * 1.05,
                   slope * (x_max + 0.3) * 1.05, 360.0)
        ax_fit.set_ylim(0, ymax)
        ax_fit.set_xlabel('layer number n')
        ax_fit.set_ylabel('delta unwrapped [deg]' if n_unw else 'delta [deg]')
        ax_fit.grid(alpha=0.3)
        unw_note = f"  ({n_unw} pt unwrapped +360)" if n_unw else ""
        ax_fit.set_title(
            f'Through-origin fit{unw_note}\n'
            f'slope = {slope:.2f}°/layer  R² = {fit["r2"]:.3f}  '
            f'RMS = {fit["rms"]:.2f}°')
        ax_fit.legend(loc='lower right', fontsize=8)

        # Marker legend (L/R/center) without duplicating per-point entries.
        from matplotlib.lines import Line2D
        handles = [
            Line2D([], [], marker='o', color='tab:blue', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='L side'),
            Line2D([], [], marker='s', color='tab:orange', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='R side'),
            Line2D([], [], marker='D', color='tab:green', linestyle='none',
                   markeredgecolor='k', markeredgewidth=0.5, label='center'),
            Line2D([], [], color='k', linestyle='--', label=f'fit'),
        ]
        ax_fit.legend(handles=handles, loc='lower right', fontsize=7)

    fig.tight_layout()
    return fig


# =============================================================================
# ENTRY
# =============================================================================


def main():
    delta, _S0, _bg_mask, wavelength = run_pipeline()

    channel_map = {0: 'R', 1: 'G', 2: 'B'}
    channel_char = channel_map.get(utils.TARGET_CHANNEL_IDX, '?')
    dataset_name = os.path.basename(utils.TARGET_FOLDER.rstrip('/').rstrip('\\'))

    t_vals, X, Y, center_ds, dir_pix, perp_pix = build_slice_grid(
        delta.shape,
        SLICE_POINT_NATIVE_XY,
        SLICE_ANGLE_DEG,
        utils.DOWNSAMPLE_FACTOR,
        SLICE_HALF_WIDTH_NATIVE_PX,
        SLICE_STEP_NATIVE_PX,
    )

    delta_slice, circ_std = sample_thick_slice(delta, X, Y)

    if AUTO_CROP_TO_SAMPLE:
        crop_idx = find_sample_crop(delta_slice, t_vals,
                                    utils.DOWNSAMPLE_FACTOR,
                                    AUTO_CROP_EDGE_MARGIN_DEG,
                                    AUTO_CROP_IGNORE_NATIVE_PX)
        s, e = crop_idx
        t_native = t_vals * utils.DOWNSAMPLE_FACTOR
        print(f"Auto-crop (delta in [{AUTO_CROP_EDGE_MARGIN_DEG:.0f}, "
              f"{360 - AUTO_CROP_EDGE_MARGIN_DEG:.0f}] deg, "
              f"ignore {AUTO_CROP_IGNORE_NATIVE_PX:.0f} px / side): "
              f"indices [{s}, {e}] of {len(t_vals)} -> "
              f"arc [{t_native[s]:.0f}, {t_native[e]:.0f}] native px "
              f"(span {t_native[e] - t_native[s]:.0f} px)")
    else:
        crop_idx = (0, len(t_vals) - 1)

    plateaus = []
    if PLATEAU_DETECT:
        plateaus = detect_plateaus(delta_slice, t_vals,
                                    utils.DOWNSAMPLE_FACTOR, crop_idx,
                                    PLATEAU_SMOOTH_SIGMA_SAMPLES,
                                    PLATEAU_GRADIENT_THRESH_DEG,
                                    PLATEAU_MIN_LENGTH_NATIVE_PX,
                                    PLATEAU_LABELS)
        if plateaus:
            n_found = len(plateaus)
            n_expected = len(PLATEAU_LABELS)
            if n_found != n_expected:
                print(f"WARNING: detected {n_found} plateaus, expected "
                      f"{n_expected}. Labels assigned as P1..P{n_found}; "
                      "tune PLATEAU_GRADIENT_THRESH_DEG / "
                      "PLATEAU_MIN_LENGTH_NATIVE_PX to recover.")
            print(f"\nPlateaus ({n_found} detected):")
            print(f"  {'label':>5} {'delta [deg]':>12} {'sigma':>8} "
                  f"{'arc range [native px]':>26} {'samples':>8}")
            for p in plateaus:
                print(f"  {p['label']:>5} {p['delta_med']:>12.2f} "
                      f"{p['delta_std']:>8.2f} "
                      f"[{p['arc_start']:>+8.0f}, {p['arc_end']:>+8.0f}] "
                      f"{p['n_samples']:>8d}")
        else:
            print("No plateaus detected (relax thresholds).")

    fit = None
    if LAYER_FIT_THROUGH_ORIGIN and plateaus:
        fit = fit_layers_through_origin(plateaus)
        if fit is not None:
            n_unw = int(fit.get('n_unwrapped', 0))
            print(f"\nThrough-origin fit  delta = m * n :")
            print(f"  slope m = {fit['slope']:.3f} deg / layer")
            print(f"  R^2     = {fit['r2']:.4f}")
            print(f"  RMS res = {fit['rms']:.3f} deg")
            if n_unw:
                print(f"  unwrap  : {n_unw} point(s) shifted by +360 deg "
                      "(per-side cumulative)")
            print(f"  {'label':>5} {'n':>3} {'raw':>8} {'unwrap':>8} "
                  f"{'fit':>8} {'resid':>8}")
            for lbl, xi, yr, yi, ri in zip(fit['labels'], fit['x'],
                                            fit['y_raw'], fit['y'],
                                            fit['resid']):
                print(f"  {lbl:>5} {int(xi):>3d} {yr:>8.2f} {yi:>8.2f} "
                      f"{fit['slope'] * xi:>8.2f} {ri:>+8.2f}")
        else:
            print("Layer fit skipped (no plateau labels parsed as integers).")

    fig = make_plot(delta, t_vals, delta_slice, circ_std,
                    X, Y, center_ds, (dir_pix, perp_pix),
                    dataset_name, channel_char, wavelength,
                    crop_idx, plateaus=plateaus, fit=fit)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(
        OUTPUT_DIR,
        f'slice_delta_{dataset_name}_{channel_char}.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved {out_path}")

    backend = matplotlib.get_backend().lower()
    if backend not in ('agg', 'pdf', 'ps', 'svg', 'cairo'):
        plt.show()
    else:
        plt.close(fig)


if __name__ == '__main__':
    main()
