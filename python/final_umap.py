"""
UMAP visualisation of the polarimetric Stokes maps.

Each valid pixel is represented by its raw 4-D Stokes vector
(S0, S1, S2, S3) and projected to two dimensions by UMAP. Intensity
therefore participates in the embedding alongside the three
polarization components, so pixels separate not only by polarization
state but also by absolute brightness. No clustering is performed:
both the spatial retardance map and the UMAP scatter are coloured by
the same retardance value, so the viewer can read across panels by
eye. When the two panels share the same colour, the corresponding
spatial region belongs to the same polarimetric regime.

Nothing is averaged or blurred on top of the Stokes fit: the retardance is
computed with ``smooth_sigma=0`` and the embedding is fed the raw per-pixel
Stokes components so that any structure visible in the embedding comes from
the measurement, not from a post-processing filter.
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

UMAP_FIT_SAMPLE = 20000
UMAP_N_NEIGHBORS = 80
UMAP_MIN_DIST = 0.008
UMAP_METRIC = 'euclidean'

DOLP_MIN = 0.05
RANDOM_STATE = 42

# =============================================================================
# FEATURE EXTRACTION
# =============================================================================

def _build_feature_matrix(S0, S1, S2, S3, valid_mask):
    S3_col = S3 if S3 is not None else np.zeros_like(S0)
    flat_valid = valid_mask.ravel()
    features = np.column_stack([
        S0.ravel(), S1.ravel(), S2.ravel(), S3_col.ravel()
    ])[flat_valid]
    valid_indices = np.flatnonzero(flat_valid)
    return features.astype(np.float32), valid_indices

def _build_validity_mask(S0, DoLP, bg_mask):
    sample_mask = ~bg_mask
    finite = np.isfinite(S0) & np.isfinite(DoLP)
    bright_enough = DoLP >= DOLP_MIN
    return sample_mask & finite & bright_enough

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

def plot_retardance_and_umap(embedding, delta_deg, valid_indices, S0,
                             sample_name=''):
    """Two-panel figure.

    Left  : full spatial retardance map (cyclic twilight colormap, 0-360 deg).
    Right : UMAP 2-D embedding, each point coloured by the retardance of the
            same pixel so that colours carry across the two panels and the
            viewer can follow a region from geometry space into polarimetric
            space.
    """
    fig, (ax_map, ax_umap) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f"Polarimetric UMAP - {sample_name}", fontsize=14)

    im_delta = ax_map.imshow(delta_deg, cmap='twilight', vmin=0, vmax=360)
    ax_map.set_title(r"(a) Retardance $\delta$ (deg)")
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

def run(sample_name=None, show=True, save_path=None):
    if sample_name is None:
        sample_name = os.path.basename(os.path.normpath(utils.TARGET_FOLDER))

    print("--- Polarimetric pipeline ---")
    utils.reset_saturation_accumulator()

    angles, stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
        downsample_factor=utils.DOWNSAMPLE_FACTOR, invert_angles=True)
    if stack is None or angles is None:
        return None

    S0, S1, S2 = utils.calculate_linear_stokes(angles, stack)
    wavelength = utils.get_channel_wavelength(utils.WAVELENGTHS_CSV,
                                              utils.TARGET_CHANNEL_IDX)
    S3 = utils.calculate_s3(utils.WAV_SUBFOLDER, utils.TARGET_CHANNEL_IDX,
                            utils.DOWNSAMPLE_FACTOR, wavelength)

    bg_mask = utils.generate_background_mask(S0)
    S1_al, S2_al = utils.align_reference_frame(S1, S2, bg_mask)
    DoLP, _ = utils.calculate_dolp_aolp(S0, S1_al, S2_al)
    # smooth_sigma=0: no spatial Gaussian blur on top of the Stokes fit, so
    # the UMAP sees exactly the per-pixel polarimetric response.
    delta_deg, theta_deg = utils.calculate_retardance_and_fast_axis(
        S0, S1_al, S2_al, S3, bg_mask, smooth_sigma=0)

    sat_mask = utils.get_saturation_mask(utils.DOWNSAMPLE_FACTOR)
    if sat_mask is not None and sat_mask.any():
        for arr in (DoLP, delta_deg, theta_deg):
            if arr is not None:
                arr[sat_mask] = np.nan

    print("--- UMAP ---")
    valid_mask = _build_validity_mask(S0, DoLP, bg_mask)
    if sat_mask is not None:
        valid_mask &= ~sat_mask

    features, valid_indices = _build_feature_matrix(S0, S1_al, S2_al, S3,
                                                    valid_mask)
    print(f"  Valid pixels: {features.shape[0]} / {S0.size} "
          f"({100.0 * features.shape[0] / S0.size:.1f}%)")

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
        S0=S0,
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
