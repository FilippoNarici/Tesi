"""DoLP/AoLP + retardance/fast-axis dalla pipeline pseudo-inversa + lamina lambda/4."""
import numpy as np
import scipy.ndimage as ndimage

from . import config


def calculate_dolp_aolp(S0, S1, S2):
    print("Calculating DoLP and AoLP...")
    S0_safe = np.where(S0 == 0, 1e-8, S0)
    DoLP = np.sqrt(S1**2 + S2**2) / S0_safe
    DoLP = np.clip(DoLP, 0, 1)
    AoLP_rad = 0.5 * np.arctan2(S2, S1)
    AoLP_deg = np.degrees(AoLP_rad)
    return DoLP, AoLP_deg


def calculate_retardance_and_fast_axis(S0, S1, S2, S3, bg_mask,
                                       smooth_sigma=1.0,
                                       target_folder=None):
    """Retardance delta in [0, 360) via arctan2; fast axis theta in [0, 90].

    Pipeline ordine obbligato: chiamare DOPO align_reference_frame +
    align_poincare_ellipticity. La rotazione Poincare assume input puramente
    lineare; le formule sotto richiedono s3_bg ~ 0 sul background.

    Se target_folder corrisponde a un dataset con waveplate fast/slow scambiate
    (vedi config.WAVEPLATE_SWAPPED_DATASETS) applica la correzione equivalente
    sulla sfera di Poincare (delta -> 360 - delta, theta -> theta - 90 deg).
    """
    print("Calculating Retardance and Fast Axis...")
    if S3 is None:
        print("Warning: S3 is required to calculate retardance. Returning None.")
        return None, None

    S0_safe = np.where(S0 == 0, 1e-8, S0)
    s1 = S1 / S0_safe
    s2 = S2 / S0_safe
    s3 = S3 / S0_safe

    if np.any(bg_mask):
        s2_in = np.median(s2[bg_mask])
        if abs(s2_in) > 0.05:
            print(f"  WARNING: residual s2 on background = {s2_in:+.4f} "
                  "(> 0.05). Alignment may have failed; retardance estimate "
                  "will carry a systematic error.")

        H, W = s3.shape
        y_idx, x_idx = np.mgrid[0:H, 0:W]
        x_norm = (x_idx - W / 2) / (W / 2)
        y_norm = (y_idx - H / 2) / (H / 2)

        M_full = np.column_stack(
            [np.ones(s3.size), x_norm.ravel(), y_norm.ravel(),
             x_norm.ravel() ** 2, x_norm.ravel() * y_norm.ravel(),
             y_norm.ravel() ** 2])

        x_bg, y_bg = x_norm[bg_mask], y_norm[bg_mask]
        M_bg = np.column_stack([np.ones(len(x_bg)), x_bg, y_bg,
                                x_bg ** 2, x_bg * y_bg, y_bg ** 2])
        coeffs_s1, _, _, _ = np.linalg.lstsq(M_bg, s1[bg_mask], rcond=None)
        s1_in = (M_full @ coeffs_s1).reshape(H, W)
        med_s1 = np.median(s1_in)
    else:
        s1_in = 1.0
        s2_in = 0.0
        med_s1 = 1.0

    print(f"  Background s1 surface fitted. Median s1_in={med_s1:.4f}, "
          f"residual s2 on bg={s2_in:+.4f}.")

    if smooth_sigma > 0:
        s1 = ndimage.gaussian_filter(s1, sigma=smooth_sigma)
        s2 = ndimage.gaussian_filter(s2, sigma=smooth_sigma)
        s3 = ndimage.gaussian_filter(s3, sigma=smooth_sigma)

    s3_corrected = s3

    A = np.maximum(s1_in - s1, 0.0)
    theta = 0.5 * np.arctan2(A, s2)
    sin_2theta = np.sin(2 * theta)
    sin_2theta_sq = sin_2theta ** 2

    STABILITY_CENTRE = 0.02
    STABILITY_WIDTH = 0.02
    weight = np.clip((sin_2theta_sq - STABILITY_CENTRE) / STABILITY_WIDTH, 0.0, 1.0)
    stable_frac = np.mean(weight > 0.5) * 100
    print(f"  Stability: {stable_frac:.1f}% of pixels above half-weight threshold")

    denom_cos = s1_in * np.maximum(sin_2theta_sq, 1e-6)
    cos_delta_raw = 1.0 - A / denom_cos
    cos_delta_raw = np.clip(cos_delta_raw, -1.0, 1.0)
    cos_delta = weight * cos_delta_raw + (1.0 - weight) * 1.0

    denom_sin = s1_in * np.where(np.abs(sin_2theta) < 1e-4,
                                  np.sign(sin_2theta + 1e-12) * 1e-4, sin_2theta)
    sin_delta_raw = s3_corrected / denom_sin
    sin_delta_raw = np.clip(sin_delta_raw, -1.0, 1.0)
    sin_delta = weight * sin_delta_raw

    delta = np.arctan2(sin_delta, cos_delta)
    delta = np.where(delta < 0, delta + 2.0 * np.pi, delta)

    delta_deg = np.degrees(delta)
    theta_deg = np.degrees(theta)

    if config.is_waveplate_swapped(target_folder):
        print("  -> WAVEPLATE_AXES_SWAPPED active: applying fast/slow axis "
              "correction (delta -> 360 - delta, theta -> theta - 90 deg).")
        delta_deg = (360.0 - delta_deg) % 360.0
        theta_deg = (theta_deg - 90.0 + 90.0) % 180.0 - 90.0

    return delta_deg, theta_deg
