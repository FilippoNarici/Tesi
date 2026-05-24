"""Stokes parameters: linear pseudo-inverse fit, S3 from waveplate, quartz dispersion."""
import glob
import os
import re

import numpy as np
from tqdm import tqdm

from . import config
from .io_raw import (
    _read_raw_rgb_fullres,
    downsample_image,
    load_dark_frame,
    load_raw_image,
)

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

    # Swap S3 globale (2026-05-23): segno assoluto di S3 = I(+45)-I(-45) dipende
    # dall'orientamento fronte/retro della w/4-di-riferimento, grado di liberta'
    # NON fissato da zucchero (S3~0) ne' da A2 (verso angoli). Lo inchioda la
    # lambdaquarti zero-order: delta deve SALIRE verso il blu (delta~1/lambda);
    # senza swap dava 273/251/230 (discendente, ramo 360-delta). Con swap ->
    # 87/109/130 (ascendente, ~90@633nm). Convenzione manuale: S3<0 destrogiro.
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


def calculate_linear_stokes_rgb_streaming(
        pol_dir, channel_indices=(0, 1, 2),
        downsample_factor=1, invert_angles=False,
        dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
        use_raw_bayer=config.USE_RAW_BAYER):
    """Carica 1 volta i 36 RAW e calcola Stokes lineari (S0,S1,S2) per 3 canali.

    Streaming: a ogni frame estrae i 3 canali e aggiorna gli accumulator
    `params[ch]` in-place. Memoria peak = 3 × params(3 × H_ds × W_ds), molto
    minore rispetto a tenere 3 stack interi in RAM.

    Restituisce: (angles_rad_2x, {ch_idx: (S0, S1, S2)}).
    """
    print(f"Loading RGB linear polarization images from: {pol_dir} "
          f"(streaming, channels={list(channel_indices)})")
    search_pattern = os.path.join(pol_dir, 'pol*.dng')
    file_paths = glob.glob(search_pattern)
    if not file_paths:
        print("No 'pol*.dng' files found.")
        return None, None

    angle_file_pairs = []
    for fpath in file_paths:
        match = re.search(r'pol(\d+)\.dng', os.path.basename(fpath), re.IGNORECASE)
        if match:
            orig_angle = int(match.group(1))
            angle = (360 - orig_angle) % 360 if invert_angles else orig_angle
            angle_file_pairs.append((angle, fpath))
    if not angle_file_pairs:
        return None, None
    angle_file_pairs.sort()
    N = len(angle_file_pairs)
    angles_rad_2x = np.deg2rad(2.0 * np.array([p[0] for p in angle_file_pairs]))

    ones = np.ones(N, dtype=np.float32)
    cos_2a = np.cos(angles_rad_2x).astype(np.float32)
    sin_2a = np.sin(angles_rad_2x).astype(np.float32)
    M = np.vstack([ones, cos_2a, sin_2a]).T
    M_pinv = np.linalg.pinv(M).astype(np.float32)  # (3, N)

    dark_per_ch = {int(ch): load_dark_frame(int(ch), dark_frame_path, use_raw_bayer)
                   for ch in channel_indices}

    params_per_ch = {int(ch): None for ch in channel_indices}
    H_ds = W_ds = None

    print(f"Found {N} pol files. Streaming (DS={downsample_factor}x)...")
    for frame_idx, (_ang, fpath) in enumerate(tqdm(angle_file_pairs)):
        rgb_full = _read_raw_rgb_fullres(fpath, channel_indices,
                                          use_raw_bayer=use_raw_bayer)
        for ch in channel_indices:
            data = rgb_full[int(ch)]
            if dark_per_ch[int(ch)] is not None:
                data = data - dark_per_ch[int(ch)]
            data_ds = downsample_image(data, downsample_factor)
            if H_ds is None:
                H_ds, W_ds = data_ds.shape
                for c in channel_indices:
                    params_per_ch[int(c)] = np.zeros((3, H_ds * W_ds), dtype=np.float32)
            flat = data_ds.ravel().astype(np.float32)
            p = params_per_ch[int(ch)]
            for k in range(3):
                p[k] += M_pinv[k, frame_idx] * flat

    out = {}
    for ch in channel_indices:
        p = params_per_ch[int(ch)]
        S0 = (2.0 * p[0]).reshape(H_ds, W_ds)
        S1 = (2.0 * p[1]).reshape(H_ds, W_ds)
        S2 = (2.0 * p[2]).reshape(H_ds, W_ds)
        out[int(ch)] = (S0, S1, S2)
    return angles_rad_2x, out


def calculate_s3_rgb(wav_dir, channel_indices=(0, 1, 2),
                     downsample_factor=1,
                     wavelengths_per_ch=None,
                     dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
                     use_raw_bayer=config.USE_RAW_BAYER):
    """Calcola S3 per 3 canali leggendo i 2 file wav UNA volta.

    `wavelengths_per_ch`: dict {ch_idx: wavelength_nm}. Default = design wavelength
    per tutti i canali.

    Restituisce dict {ch_idx: (S3, wav_intensity)}.
    """
    print(f"\nLoading RGB waveplate images from: {wav_dir} "
          f"(channels={list(channel_indices)})")
    path_45 = os.path.join(wav_dir, 'wav45.dng')
    path_minus_45 = os.path.join(wav_dir, 'wav-45.dng')
    if not os.path.exists(path_minus_45):
        typo = os.path.join(wav_dir, 'wav-45dng')
        if os.path.exists(typo):
            path_minus_45 = typo
    if not (os.path.exists(path_45) and os.path.exists(path_minus_45)):
        print("Error: missing wav45.dng or wav-45.dng.")
        return None

    if wavelengths_per_ch is None:
        wavelengths_per_ch = {int(ch): config.DEFAULT_DESIGN_WAVELENGTH_NM
                              for ch in channel_indices}

    dark_per_ch = {int(ch): load_dark_frame(int(ch), dark_frame_path, use_raw_bayer)
                   for ch in channel_indices}

    rgb_45 = _read_raw_rgb_fullres(path_45, channel_indices,
                                    use_raw_bayer=use_raw_bayer)
    rgb_m45 = _read_raw_rgb_fullres(path_minus_45, channel_indices,
                                     use_raw_bayer=use_raw_bayer)

    out = {}
    for ch in channel_indices:
        # Swap S3 globale (2026-05-23): vedi nota in calculate_s3. Segno assoluto
        # S3 fissato dalla lambdaquarti zero-order (delta deve salire verso blu).
        img_45 = rgb_m45[int(ch)]
        img_m45 = rgb_45[int(ch)]
        if dark_per_ch[int(ch)] is not None:
            img_45 = img_45 - dark_per_ch[int(ch)]
            img_m45 = img_m45 - dark_per_ch[int(ch)]
        img_45_ds = downsample_image(img_45, downsample_factor)
        img_m45_ds = downsample_image(img_m45, downsample_factor)

        wav_intensity = img_45_ds + img_m45_ds

        lam = wavelengths_per_ch[int(ch)]
        delta = waveplate_retardance(lam)
        correction = np.sin(delta)
        dn_ratio = (quartz_birefringence(lam)
                    / quartz_birefringence(config.DEFAULT_DESIGN_WAVELENGTH_NM))
        print(f"  ch={int(ch)}: lambda={lam:.1f} nm, dn_ratio={dn_ratio:.4f}, "
              f"delta={np.degrees(delta):.2f} deg, 1/sin(delta)={1/correction:.3f}")

        S3 = (img_45_ds - img_m45_ds) / correction
        out[int(ch)] = (S3, wav_intensity)
    return out
