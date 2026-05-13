"""Stokes parameters: linear pseudo-inverse fit, S3 from waveplate, quartz dispersion."""
import os

import numpy as np

from . import config
from .io_raw import load_raw_image

_WAV_INTENSITY_CACHE = None


def get_wav_intensity_cache():
    """Returns I(+45)+I(-45) populated by the last calculate_s3() call, or None."""
    return _WAV_INTENSITY_CACHE


def reset_wav_intensity_cache():
    global _WAV_INTENSITY_CACHE
    _WAV_INTENSITY_CACHE = None


def calculate_linear_stokes(angles_rad_2x, image_stack):
    print("Calculating linear Stokes parameters (S0, S1, S2)...")
    N, H, W = image_stack.shape
    ones = np.ones(N, dtype=np.float32)
    cos_2a = np.cos(angles_rad_2x).astype(np.float32)
    sin_2a = np.sin(angles_rad_2x).astype(np.float32)

    M = np.vstack([ones, cos_2a, sin_2a]).T
    M_pinv = np.linalg.pinv(M)
    pixel_data = image_stack.reshape(N, -1)
    params = M_pinv @ pixel_data

    S0 = (2 * params[0]).reshape(H, W)
    S1 = (2 * params[1]).reshape(H, W)
    S2 = (2 * params[2]).reshape(H, W)
    return S0, S1, S2


def quartz_birefringence(wavelength_nm):
    """Delta_n = n_e - n_o di alpha-quarzo via Ghosh (1999), 200 nm - 2 um."""
    lam_um = wavelength_nm / 1000.0
    lam2 = lam_um ** 2
    n_o_sq = (1.28604141
              + 1.07044083 * lam2 / (lam2 - 0.0100585997)
              + 1.10202242 * lam2 / (lam2 - 100.0))
    n_e_sq = (1.28851804
              + 1.09509924 * lam2 / (lam2 - 0.0102101864)
              + 1.15662475 * lam2 / (lam2 - 100.0))
    return np.sqrt(n_e_sq) - np.sqrt(n_o_sq)


def waveplate_retardance(wavelength_nm,
                         design_wavelength_nm=config.DEFAULT_DESIGN_WAVELENGTH_NM,
                         order=config.DEFAULT_WAVEPLATE_ORDER):
    """Retardance (rad) di zero-order quartz waveplate fuori design wavelength."""
    delta_design = 2.0 * np.pi * order
    dn_ratio = quartz_birefringence(wavelength_nm) / quartz_birefringence(design_wavelength_nm)
    lam_ratio = design_wavelength_nm / wavelength_nm
    return delta_design * dn_ratio * lam_ratio


def calculate_s3(wav_dir, channel_index, downsample_factor=1,
                 wavelength=config.DEFAULT_DESIGN_WAVELENGTH_NM,
                 dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
                 use_raw_bayer=config.USE_RAW_BAYER):
    global _WAV_INTENSITY_CACHE
    print(f"\nLoading waveplate images from: {wav_dir}")

    path_45 = os.path.join(wav_dir, 'wav45.dng')
    path_minus_45 = os.path.join(wav_dir, 'wav-45.dng')
    if not os.path.exists(path_minus_45):
        typo = os.path.join(wav_dir, 'wav-45dng')
        if os.path.exists(typo):
            path_minus_45 = typo

    img_45_orig = load_raw_image(path_45, channel_index, downsample_factor,
                                 dark_frame_path=dark_frame_path,
                                 use_raw_bayer=use_raw_bayer)
    img_minus_45_orig = load_raw_image(path_minus_45, channel_index, downsample_factor,
                                       dark_frame_path=dark_frame_path,
                                       use_raw_bayer=use_raw_bayer)

    if img_45_orig is None or img_minus_45_orig is None:
        print("Error: Could not find or load both wav45.dng and wav-45.dng.")
        return None

    # Angle inversion: original -45 -> I(+45), original +45 -> I(-45)
    I_45 = img_minus_45_orig
    I_minus_45 = img_45_orig

    _WAV_INTENSITY_CACHE = I_45 + I_minus_45

    delta = waveplate_retardance(wavelength)
    correction_factor = np.sin(delta)
    dn_ratio = (quartz_birefringence(wavelength)
                / quartz_birefringence(config.DEFAULT_DESIGN_WAVELENGTH_NM))

    print(f"Calculating S3... (lambda = {wavelength:.1f} nm, "
          f"Delta_n ratio = {dn_ratio:.4f}, "
          f"delta = {np.degrees(delta):.2f} deg, "
          f"1/sin(delta) = {1/correction_factor:.3f})")

    S3 = (I_45 - I_minus_45) / correction_factor
    return S3
