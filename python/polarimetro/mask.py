"""Background segmentation: Canny + dark prior + flood-fill multi-component."""
import numpy as np
import scipy.ndimage as ndimage

from . import config


def generate_background_mask(S0, S3=None, downsample_factor=config.DEFAULT_DOWNSAMPLE_FACTOR):
    """Segmenta sample via Canny + dark prior + circle expansion + flood-fill bg.

    Restituisce maschera booleana del background (True = background).
    Pipeline (vedi CLAUDE.md insidie): Canny abs thresholds -> dark prior
    (S0_norm < DARK_THRESH) -> dilation disco -> closing -> label complemento ->
    union componenti border-touching size >= 20% del max -> fill_holes sample ->
    opening -> erosione di sicurezza scalata 100/DS px nativi.
    """
    from skimage.feature import canny
    from skimage.morphology import closing, dilation, disk, opening

    print("Generating background mask (Canny + dark + expand + flood)...")
    H, W = S0.shape
    dim = max(H, W)
    struct4 = ndimage.generate_binary_structure(2, 1)

    def _brightness_fallback(reason):
        print(f"  [bg_mask] fallback brightness: {reason}")
        S0_smooth = ndimage.gaussian_filter(S0, sigma=dim * 0.005)
        bg = S0_smooth > np.mean(S0_smooth) * 0.5
        eros = max(3, int(dim * 0.005))
        return ndimage.binary_erosion(
            bg, structure=ndimage.generate_binary_structure(2, 2),
            iterations=eros)

    s_ptp = float(np.ptp(S0))
    if s_ptp < 1e-8:
        return _brightness_fallback("S0 costante (ptp ~ 0)")
    S0_norm = (S0 - np.min(S0)) / s_ptp

    dark_mask = S0_norm < config.DARK_THRESH
    print(f"  dark_mask (<{config.DARK_THRESH:.2f}): "
          f"frac={dark_mask.sum() / dark_mask.size:.4f}")

    edges = canny(
        S0_norm, sigma=config.CANNY_SIGMA,
        low_threshold=config.CANNY_LOW, high_threshold=config.CANNY_HIGH,
        use_quantiles=False,
    )
    frac_edges = edges.sum() / edges.size
    print(f"  Canny: sigma={config.CANNY_SIGMA:.2f} px, "
          f"low={config.CANNY_LOW:.3f}, high={config.CANNY_HIGH:.3f}, "
          f"edges_frac={frac_edges:.4f}")
    if frac_edges < 1e-5 and not dark_mask.any():
        return _brightness_fallback("Canny vuoto e nessun pixel scuro sotto soglia")

    expand_r = max(4, int(dim * 0.004))
    edges_expanded = dilation(edges, disk(expand_r))

    barrier = edges_expanded | dark_mask
    closing_r = max(2, int(dim * 0.002))
    barrier = closing(barrier, disk(closing_r))

    labeled, n_feat = ndimage.label(~barrier, structure=struct4)
    if n_feat == 0:
        return _brightness_fallback("nessuna componente bg candidata")

    border_labels = set()
    border_labels.update(np.unique(labeled[0, :]).tolist())
    border_labels.update(np.unique(labeled[-1, :]).tolist())
    border_labels.update(np.unique(labeled[:, 0]).tolist())
    border_labels.update(np.unique(labeled[:, -1]).tolist())
    border_labels.discard(0)
    if not border_labels:
        return _brightness_fallback(
            "nessuna componente del complemento tocca il bordo foto")

    border_sizes = {int(lbl): int((labeled == lbl).sum())
                    for lbl in border_labels}
    largest_sz = max(border_sizes.values())
    keep_labels = [lbl for lbl, sz in border_sizes.items()
                   if sz >= 0.20 * largest_sz]
    bg_flood = np.isin(labeled, keep_labels)
    print(f"  bg flood-fill (border-touching): kept {len(keep_labels)}/"
          f"{len(border_sizes)} comp, size_frac={bg_flood.sum() / bg_flood.size:.4f}, "
          f"mean_brightness={float(S0_norm[bg_flood].mean()):.3f}")

    sample_mask = ~bg_flood
    sample_mask = ndimage.binary_fill_holes(sample_mask)
    if sample_mask is None:
        return _brightness_fallback("fill_holes sul sample ha fallito")

    opening_r = max(2, int(dim * 0.0015))
    sample_mask = opening(sample_mask, disk(opening_r))

    lbl_s, n_s = ndimage.label(sample_mask, structure=struct4)
    if n_s > 0:
        sizes_s = ndimage.sum(sample_mask, lbl_s, index=range(1, n_s + 1))
        largest_s = int(np.argmax(sizes_s)) + 1
        sample_largest = (lbl_s == largest_s)
        area = int(sample_largest.sum())
        perim_mask = ndimage.binary_dilation(
            sample_largest, structure=struct4) & (~sample_largest)
        perim = int(perim_mask.sum())
        if area > 0 and perim > 0:
            compactness = 4.0 * np.pi * area / (perim ** 2)
            status = "OK" if compactness >= config.COMPACTNESS_WARN else "WARN"
            print(f"  compactness sample piu' grande = {compactness:.3f} "
                  f"(1=cerchio, 0=frastagliato) [{status}]")
            if compactness < config.COMPACTNESS_WARN:
                print("  [bg_mask] WARNING: contorno del sample molto "
                      "frastagliato; segmentazione probabilmente sporca.")

    bg_mask = ~sample_mask
    erosion_r = max(1, config.EROSION_NATIVE_PX // max(1, downsample_factor))
    bg_mask = ndimage.binary_erosion(
        bg_mask, structure=disk(erosion_r), iterations=1)

    frac_bg = bg_mask.sum() / bg_mask.size
    if frac_bg < 0.01 or frac_bg > 0.995:
        return _brightness_fallback(f"bg_frac degenere={frac_bg:.4f}")

    print(f"  bg_frac={frac_bg:.4f} (sample_frac={1-frac_bg:.4f})")
    return bg_mask
