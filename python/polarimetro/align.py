"""Background alignment: rotation around S3 axis (linear bg) + S2 axis (Poincare ellipticity)."""
import numpy as np

from . import config
from .stokes import get_wav_intensity_cache

_POINCARE_BG_MASK_CACHE = None


def get_poincare_bg_mask():
    """Returns the cleaned bg mask used by the last align_poincare_ellipticity() call."""
    return _POINCARE_BG_MASK_CACHE


def reset_poincare_bg_mask_cache():
    global _POINCARE_BG_MASK_CACHE
    _POINCARE_BG_MASK_CACHE = None


def align_reference_frame(S1, S2, bg_mask, enable=config.ENABLE_BACKGROUND_ALIGNMENT):
    """Rotazione S1/S2 attorno asse S3 (equatore Poincare) per azzerare s2_bg."""
    if not enable:
        print("Background alignment is disabled. Skipping reference frame rotation.")
        return S1, S2

    print("Aligning reference frame using 2D spatial rotation...")

    if not np.any(bg_mask):
        print("Warning: Background mask is empty. Skipping alignment.")
        return S1, S2

    H, W = S1.shape
    y_idx, x_idx = np.mgrid[0:H, 0:W]
    x_norm = (x_idx - W / 2) / (W / 2)
    y_norm = (y_idx - H / 2) / (H / 2)

    x_bg, y_bg = x_norm[bg_mask], y_norm[bg_mask]
    M_bg = np.column_stack([np.ones(len(x_bg)), x_bg, y_bg,
                            x_bg ** 2, x_bg * y_bg, y_bg ** 2])
    M_full = np.column_stack([np.ones(S1.size), x_norm.ravel(), y_norm.ravel(),
                              x_norm.ravel() ** 2,
                              x_norm.ravel() * y_norm.ravel(),
                              y_norm.ravel() ** 2])

    coeffs_s1, _, _, _ = np.linalg.lstsq(M_bg, S1[bg_mask], rcond=None)
    coeffs_s2, _, _, _ = np.linalg.lstsq(M_bg, S2[bg_mask], rcond=None)
    S1_surface = (M_full @ coeffs_s1).reshape(H, W)
    S2_surface = (M_full @ coeffs_s2).reshape(H, W)

    alpha_surface = 0.5 * np.arctan2(S2_surface, S1_surface)
    print(f"  -> Median background rotation angle: {np.degrees(np.median(alpha_surface)):.2f} deg")

    cos_2a = np.cos(2 * alpha_surface)
    sin_2a = np.sin(2 * alpha_surface)
    S1_aligned = S1 * cos_2a + S2 * sin_2a
    S2_aligned = -S1 * sin_2a + S2 * cos_2a
    return S1_aligned, S2_aligned


def align_poincare_ellipticity(S0, S1, S3, bg_mask,
                               enable=config.ENABLE_BACKGROUND_ALIGNMENT,
                               downsample_factor=config.DEFAULT_DOWNSAMPLE_FACTOR,
                               wav_holder_threshold=config.WAV_HOLDER_THRESHOLD,
                               wav_intensity=None,
                               return_mask=False):
    """Rotazione S1/S3 attorno asse S2 per azzerare s3_bg (ellitticita' residua).

    `wav_intensity`: I(+45)+I(-45) per il canale; se None, fallback al
    `_WAV_INTENSITY_CACHE` globale (thread-unsafe). Passare esplicito per
    chiamate parallele.
    `return_mask=True`: ritorna (S1_rot, S3_rot, bg_mask_s3) invece di tupla a 2.
    """
    global _POINCARE_BG_MASK_CACHE
    _POINCARE_BG_MASK_CACHE = None

    if not enable:
        print("Poincare ellipticity rebasing disabled. Skipping.")
        return (S1, S3, bg_mask) if return_mask else (S1, S3)

    print("Rebasing Poincare sphere around S2 axis (ellipticity correction)...")

    if not np.any(bg_mask):
        print("  Warning: bg mask empty. Skipping.")
        return (S1, S3, bg_mask) if return_mask else (S1, S3)

    bg_mask_s3 = bg_mask
    wav_cache = wav_intensity if wav_intensity is not None else get_wav_intensity_cache()
    if wav_cache is not None and wav_cache.shape == bg_mask.shape:
        from skimage.morphology import dilation, disk
        wav_mean = wav_cache / 2.0
        wav_bg_max = float(wav_mean[bg_mask].max())
        thresh = wav_holder_threshold * wav_bg_max
        holder = bg_mask & (wav_mean < thresh)
        dilate_r = max(1, config.POINCARE_DILATE_NATIVE_PX // max(1, downsample_factor))
        border_r = max(1, dilate_r // 2)
        border = np.zeros_like(bg_mask)
        border[:border_r, :] = True
        border[-border_r:, :] = True
        border[:, :border_r] = True
        border[:, -border_r:] = True
        holder = holder | border
        holder = dilation(holder, disk(dilate_r))
        candidate = bg_mask & ~holder
        if candidate.sum() < 0.1 * bg_mask.sum():
            print("  WARNING: wav holder mask too aggressive, using full bg.")
        else:
            bg_mask_s3 = candidate
            n_excl = int(bg_mask.sum() - bg_mask_s3.sum())
            print(f"  Wav-dark holder pixels excluded "
                  f"(< {wav_holder_threshold:.2f}x max wav in bg): "
                  f"{n_excl} ({100*n_excl/max(1,bg_mask.sum()):.1f}%)")

    _POINCARE_BG_MASK_CACHE = bg_mask_s3.copy()

    S0_safe = np.where(S0 == 0, 1e-8, S0)
    s1_ratio = S1 / S0_safe
    s3_ratio = S3 / S0_safe
    s1_vals = s1_ratio[bg_mask_s3]
    s3_vals = s3_ratio[bg_mask_s3]

    H, W = S0.shape
    y_idx, x_idx = np.mgrid[0:H, 0:W]
    xn = (x_idx - W / 2) / (W / 2)
    yn = (y_idx - H / 2) / (H / 2)
    xb, yb = xn[bg_mask_s3], yn[bg_mask_s3]
    M_bg = np.column_stack([np.ones(len(xb)), xb, yb,
                            xb ** 2, xb * yb, yb ** 2])
    M_full = np.column_stack([np.ones(xn.size), xn.ravel(), yn.ravel(),
                              xn.ravel() ** 2,
                              xn.ravel() * yn.ravel(),
                              yn.ravel() ** 2])
    c_s1, _, _, _ = np.linalg.lstsq(M_bg, s1_vals, rcond=None)
    c_s3, _, _, _ = np.linalg.lstsq(M_bg, s3_vals, rcond=None)
    s1_fit = (M_full @ c_s1).reshape(H, W)
    s3_fit = (M_full @ c_s3).reshape(H, W)

    s3_bg_med_pre = float(np.median(s3_vals))
    s3_bg_std_pre = float(np.std(s3_vals))
    s3_fit_bg = s3_fit[bg_mask_s3]
    s3_resid_std = float(np.std(s3_vals - s3_fit_bg))
    print(f"  s3_bg (cleaned) pre: median={s3_bg_med_pre:+.4f}, "
          f"std={s3_bg_std_pre:.4f}")
    print(f"  s3_bg deg-2 fit: residual std={s3_resid_std:.4f} "
          f"(ratio resid/raw = {s3_resid_std/max(1e-8,s3_bg_std_pre):.2f})")

    beta_map = np.arctan2(s3_fit, s1_fit)
    cos_b = np.cos(beta_map)
    sin_b = np.sin(beta_map)

    S1_rot = S1 * cos_b + S3 * sin_b
    S3_rot = -S1 * sin_b + S3 * cos_b

    s3_post_vals = (S3_rot / S0_safe)[bg_mask_s3]
    s3_bg_med_post = float(np.median(s3_post_vals))
    s3_bg_std_post = float(np.std(s3_post_vals))
    beta_med_deg = float(np.degrees(np.median(beta_map)))
    beta_range_deg = (float(np.degrees(beta_map.min())),
                      float(np.degrees(beta_map.max())))
    print(f"  beta(x,y): median={beta_med_deg:+.2f} deg, "
          f"range=[{beta_range_deg[0]:+.2f}, {beta_range_deg[1]:+.2f}] deg")
    print(f"  s3_bg (cleaned) post: median={s3_bg_med_post:+.4f}, "
          f"std={s3_bg_std_post:.4f}")

    return (S1_rot, S3_rot, bg_mask_s3) if return_mask else (S1_rot, S3_rot)
