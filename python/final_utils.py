"""
Utility functions and common configurations for Stokes parameter calculations.
"""

import os
import re
import glob
import csv
import numpy as np
import rawpy
import scipy.ndimage as ndimage
from tqdm import tqdm

# =============================================================================
# COMMON CONFIGURATION
# =============================================================================

TARGET_FOLDER = './raw/strati_v2'
POL_SUBFOLDER = os.path.join(TARGET_FOLDER, 'pol')
WAV_SUBFOLDER = os.path.join(TARGET_FOLDER, 'wav')
WAVELENGTHS_CSV = './outputs/rgb_wavelengths.csv'

# Sensor channels: 0: Red, 1: Green, 2: Blue
TARGET_CHANNEL_IDX = 2

# Default downsampling factor for the full polarimeter mapping
DOWNSAMPLE_FACTOR = 20

# Toggle per la correzione dell'inclinazione dello sfondo (allineamento S1/S2)
ENABLE_BACKGROUND_ALIGNMENT = True

# Raw Bayer extraction mode.
# True  : read raw_image_visible directly, pick the Bayer plane for the target channel.
#         Avoids the camera-colour-matrix crosstalk that raw.postprocess mixes into each
#         channel and keeps the intensity strictly proportional to the sensor count.
# False : legacy path through rawpy.postprocess with WB disabled and linear gamma.
USE_RAW_BAYER = True

# Bias/dark frame captured with the sensor capped. Subtracted from every pol/wav image
# before Stokes fitting to remove the CMOS pedestal.
DARK_FRAME_PATH = './raw/dark.dng'

# Hardware calibration: the lambda-mezzi dataset was acquired with the waveplate mounted
# rotated 90 degrees (fast/slow axes physically swapped). Setting this flag applies the
# equivalent Poincare-sphere transformation (delta -> 360 - delta, theta -> theta - 90)
# at the end of the retardance calculation, restoring the correct physical parameters.
WAVEPLATE_AXES_SWAPPED = "lambdamezzi_50deg" in TARGET_FOLDER.lower()

# Cache to hold the wav intensity so the mask generator can find the exact vignette
_WAV_INTENSITY_CACHE = None

# Cache for the dark frame at full native resolution (keyed by channel index)
_DARK_FRAME_CACHE = {}

# Saturation threshold: pixels reaching or exceeding this fraction of the sensor
# white level are flagged as clipped. The DNG metadata reports white_level=4095
# (12-bit linear read-out), so the default threshold corresponds to ~4013 counts.
SENSOR_WHITE_LEVEL = 4095
SATURATION_FRACTION = 0.98

# Module-level OR-accumulator of saturated photosites across every RAW frame
# loaded since reset_saturation_accumulator() was last called. Stored at the
# native sensor resolution so saturation inside a single photosite is preserved
# even after aggressive block downsampling.
_SATURATION_ACCUMULATOR = None

# =============================================================================
# THESIS FIGURE CONFIGURATION
# =============================================================================

# Which parameters to plot.
# Can be a single string, a list like ['AoLP', 'DoLP'], or 'all' to export everything.
THESIS_FIGURE_PARAMS = "all"

# Output directory base (subfolder named after sample is created automatically)
THESIS_FIGURES_DIR = '../Images/generated'

# =============================================================================
# LOADING & PROCESSING FUNCTIONS
# =============================================================================

def get_channel_wavelength(csv_path, channel_index):
    """Reads the centroid wavelength for the given channel index (0:R, 1:G, 2:B)."""
    channel_map = {0: 'R', 1: 'G', 2: 'B'}
    target_char = channel_map.get(channel_index, 'G')

    if not os.path.exists(csv_path):
        print(f"Warning: Wavelength CSV not found at {csv_path}. Defaulting to 532.0 nm.")
        return 532.0

    try:
        with open(csv_path, mode='r') as infile:
            reader = csv.reader(infile)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2 and row[0].strip().upper() == target_char:
                    return float(row[1].strip())
    except Exception as e:
        print(f"Error reading {csv_path}: {e}. Defaulting to 532.0 nm.")
        return 532.0

    print(f"Warning: Channel {target_char} not found in {csv_path}. Defaulting to 532.0 nm.")
    return 532.0

def downsample_image(img, factor):
    """Downsamples a 2D array by averaging blocks of size (factor x factor)."""
    if factor <= 1:
        return img

    H, W = img.shape
    new_H = H - (H % factor)
    new_W = W - (W % factor)
    img_cropped = img[:new_H, :new_W]

    img_downsampled = img_cropped.reshape(new_H // factor, factor, new_W // factor, factor).mean(axis=(1, 3))
    return img_downsampled

def _read_raw_channel_fullres(path, channel_index, track_saturation=True):
    """Low-level read of a single colour plane at the sensor's native resolution.

    In Bayer mode the function returns one of the four CFA planes exposed by
    rawpy as ``raw_image_visible`` (layout R, G1, B, G2). The channel mapping
    0->R, 1->G1, 2->B mirrors the convention used by the higher-level API.
    In postprocess mode the image is rendered with white balance disabled and
    a linear response curve so that the output is still a linear intensity.

    Also updates the global saturation accumulator when it has been armed by
    ``reset_saturation_accumulator()``: any photosite reaching
    ``SENSOR_WHITE_LEVEL * SATURATION_FRACTION`` in any frame is recorded so
    the downstream mask can exclude clipped pixels from the polarimetric maps.
    """
    global _SATURATION_ACCUMULATOR
    with rawpy.imread(path) as raw:
        if USE_RAW_BAYER:
            ri = raw.raw_image_visible
            if ri.ndim != 3 or ri.shape[2] < 3:
                raise RuntimeError(
                    f"Expected 4-plane RGBG raw layout, got shape {ri.shape}. "
                    "Disable USE_RAW_BAYER to fall back to the postprocess path."
                )
            # Planes: 0=R, 1=G1, 2=B, 3=G2 (G2 is identically zero on this phone)
            plane_map = {0: 0, 1: 1, 2: 2}
            data = ri[:, :, plane_map[channel_index]].astype(np.float32)
        else:
            rgb = raw.postprocess(
                use_camera_wb=False,
                user_wb=[1.0, 1.0, 1.0, 1.0],
                no_auto_bright=True,
                gamma=(1, 1),
                output_bps=16,
            )
            data = rgb[:, :, channel_index].astype(np.float32)

    if track_saturation and _SATURATION_ACCUMULATOR is not None:
        # Threshold is expressed against the native sensor range; the post-WB
        # path scales the counts to the 16-bit output but keeps proportionality,
        # so the comparison works in both modes once the scale is matched.
        if USE_RAW_BAYER:
            threshold = SENSOR_WHITE_LEVEL * SATURATION_FRACTION
        else:
            threshold = 65535.0 * SATURATION_FRACTION
        frame_sat = data >= threshold
        if _SATURATION_ACCUMULATOR.shape != frame_sat.shape:
            _SATURATION_ACCUMULATOR = frame_sat.copy()
        else:
            np.logical_or(_SATURATION_ACCUMULATOR, frame_sat,
                          out=_SATURATION_ACCUMULATOR)
    return data

def reset_saturation_accumulator():
    """Arms the global saturation accumulator for a new acquisition session."""
    global _SATURATION_ACCUMULATOR
    _SATURATION_ACCUMULATOR = np.zeros((1, 1), dtype=bool)

def get_saturation_mask(downsample_factor=1):
    """Returns the saturation mask downsampled to the analysis grid.

    A block is marked saturated whenever *any* photosite inside it clipped in
    *any* frame of the acquisition (logical OR over the 40-frame stack). The
    block-wise OR is preferred to a fractional threshold because a single
    saturated photosite already biases the mean intensity used by the Stokes
    fit, no matter how small its weight inside the block.
    """
    if _SATURATION_ACCUMULATOR is None or _SATURATION_ACCUMULATOR.size == 1:
        return None
    sat = _SATURATION_ACCUMULATOR
    if downsample_factor <= 1:
        return sat.copy()
    H, W = sat.shape
    new_H = H - (H % downsample_factor)
    new_W = W - (W % downsample_factor)
    sat = sat[:new_H, :new_W]
    sat = sat.reshape(new_H // downsample_factor, downsample_factor,
                      new_W // downsample_factor, downsample_factor)
    return sat.any(axis=(1, 3))

def load_dark_frame(channel_index):
    """Returns the full-resolution dark frame for the requested channel.

    Cached across calls. Returns ``None`` if ``DARK_FRAME_PATH`` is missing,
    in which case dark subtraction is skipped and a warning is printed once.
    """
    key = (channel_index, USE_RAW_BAYER)
    if key in _DARK_FRAME_CACHE:
        return _DARK_FRAME_CACHE[key]
    if not os.path.exists(DARK_FRAME_PATH):
        print(f"Warning: dark frame not found at {DARK_FRAME_PATH}. "
              "Skipping bias subtraction.")
        _DARK_FRAME_CACHE[key] = None
        return None
    try:
        dark = _read_raw_channel_fullres(DARK_FRAME_PATH, channel_index,
                                         track_saturation=False)
    except Exception as e:
        print(f"Error reading dark frame {DARK_FRAME_PATH}: {e}. "
              "Skipping bias subtraction.")
        _DARK_FRAME_CACHE[key] = None
        return None
    _DARK_FRAME_CACHE[key] = dark
    print(f"Loaded dark frame ({('raw Bayer' if USE_RAW_BAYER else 'postprocess')}, "
          f"channel {channel_index}): mean={dark.mean():.2f}, max={dark.max():.0f}")
    return dark

def load_raw_image(path, channel_index, downsample_factor=1, subtract_dark=True):
    """Loads a RAW image, subtracts the dark frame, and downsamples.

    Dark subtraction happens at native resolution before downsampling so the
    bias is removed on a per-photosite basis; negative residuals after
    subtraction are preserved (they average out in the Stokes fit and must
    not be clipped, otherwise the noise distribution is biased upward).
    """
    if not os.path.exists(path):
        return None
    try:
        data = _read_raw_channel_fullres(path, channel_index)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None
    if subtract_dark:
        dark = load_dark_frame(channel_index)
        if dark is not None:
            data = data - dark
    return downsample_image(data, downsample_factor)

def load_rotation_sequence(pol_dir, channel_index, downsample_factor=1, invert_angles=False):
    """Loads the pol*.dng image sequence. Optionally inverts angles."""
    print(f"Loading linear polarization images from: {pol_dir}")
    search_pattern = os.path.join(pol_dir, 'pol*.dng')
    file_paths = glob.glob(search_pattern)

    if not file_paths:
        print("No 'pol*.dng' files found in the specified folder.")
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
    angles_rad_2x = np.deg2rad(2.0 * np.array([p[0] for p in angle_file_pairs]))

    images = []
    print(f"Found {len(angle_file_pairs)} images. Processing (Downsample: {downsample_factor}x)...")
    for ang, fpath in tqdm(angle_file_pairs):
        img = load_raw_image(fpath, channel_index, downsample_factor)
        if img is not None:
            images.append(img)

    return angles_rad_2x, np.stack(images, axis=0)

# =============================================================================
# MATH & POLARIZATION CALCULATIONS
# =============================================================================

def calculate_linear_stokes(angles_rad_2x, image_stack):
    """Calculates S0, S1, S2 (fit parameters) for all pixels."""
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
    """Returns the birefringence Delta_n = n_e - n_o of crystalline alpha-quartz.

    Uses the two-term Sellmeier fit published by Ghosh (1999), valid between
    ~200 nm and ~2 um. Reproduces the literature value 0.00909 at 633 nm.
    """
    lam_um = wavelength_nm / 1000.0
    lam2 = lam_um ** 2
    # Ordinary ray
    n_o_sq = (1.28604141
              + 1.07044083 * lam2 / (lam2 - 0.0100585997)
              + 1.10202242 * lam2 / (lam2 - 100.0))
    # Extraordinary ray
    n_e_sq = (1.28851804
              + 1.09509924 * lam2 / (lam2 - 0.0102101864)
              + 1.15662475 * lam2 / (lam2 - 100.0))
    return np.sqrt(n_e_sq) - np.sqrt(n_o_sq)

def waveplate_retardance(wavelength_nm, design_wavelength_nm=633.0, order=0.25):
    """Retardance (in radians) of a zero-order quartz waveplate at a non-design wavelength.

    Scales the design retardance ``2 * pi * order`` by the ratio of the
    ``Delta_n / lambda`` products between the two wavelengths, which is the
    exact single-pass birefringent phase. ``order`` defaults to 0.25 (lambda/4).
    """
    delta_design = 2.0 * np.pi * order
    dn_ratio = quartz_birefringence(wavelength_nm) / quartz_birefringence(design_wavelength_nm)
    lam_ratio = design_wavelength_nm / wavelength_nm
    return delta_design * dn_ratio * lam_ratio

def calculate_s3(wav_dir, channel_index, downsample_factor=1, wavelength=633.0):
    """Loads wav images, applies angle inversion, and calculates wavelength-corrected S3."""
    global _WAV_INTENSITY_CACHE
    print(f"\nLoading waveplate images from: {wav_dir}")

    path_45 = os.path.join(wav_dir, 'wav45.dng')
    path_minus_45 = os.path.join(wav_dir, 'wav-45.dng')

    if not os.path.exists(path_minus_45):
        path_minus_45_typo = os.path.join(wav_dir, 'wav-45dng')
        if os.path.exists(path_minus_45_typo):
            path_minus_45 = path_minus_45_typo

    img_45_orig = load_raw_image(path_45, channel_index, downsample_factor)
    img_minus_45_orig = load_raw_image(path_minus_45, channel_index, downsample_factor)

    if img_45_orig is None or img_minus_45_orig is None:
        print("Error: Could not find or load both wav45.dng and wav-45.dng.")
        return None

    # Angle inversion logic maps original -45 -> I(45) and original 45 -> I(-45)
    I_45 = img_minus_45_orig
    I_minus_45 = img_45_orig

    # CACHE THE WAV INTENSITY for the mask generator to find the vignette!
    _WAV_INTENSITY_CACHE = I_45 + I_minus_45

    # Zero-order quartz lambda/4 waveplate: retardance at an off-design wavelength
    # scales with both 1/lambda and the (weak) chromatic dispersion of Delta_n.
    delta = waveplate_retardance(wavelength, design_wavelength_nm=633.0, order=0.25)
    correction_factor = np.sin(delta)
    dn_ratio = (quartz_birefringence(wavelength)
                / quartz_birefringence(633.0))

    print(f"Calculating S3... (lambda = {wavelength:.1f} nm, "
          f"Delta_n ratio = {dn_ratio:.4f}, "
          f"delta = {np.degrees(delta):.2f} deg, "
          f"1/sin(delta) = {1/correction_factor:.3f})")

    # S3 = (I(45) - I(-45)) / sin(delta)
    S3 = (I_45 - I_minus_45) / correction_factor

    return S3

def generate_background_mask(S0, S3=None):
    """
    Creates a universal background mask using highly sensitive Edge Detection.
    Returns the FULL background (no vignette crop) so S1 and S2 can fit the corners perfectly.
    """
    print("Generating universal background mask (Multi-Island Edge logic)...")
    H, W = S0.shape

    # 1. Very light blur for EDGE detection (preserves faint edges)
    S0_sharp = ndimage.gaussian_filter(S0, sigma=max(H, W) * 0.001)

    # 2. Stronger blur for BRIGHTNESS detection (removes noise)
    S0_smooth = ndimage.gaussian_filter(S0, sigma=max(H, W) * 0.005)

    # 3. Find "Fences" (Edges) using Sobel on the SHARP image
    sx = ndimage.sobel(S0_sharp, axis=0, mode='reflect')
    sy = ndimage.sobel(S0_sharp, axis=1, mode='reflect')
    edges = np.hypot(sx, sy)

    # Lower threshold to catch faint transparent glass edges
    edge_thresh = np.mean(edges)
    edge_mask = edges > edge_thresh

    # Dilate the edges to ensure outlines act as a solid, unbroken wall
    struct = ndimage.generate_binary_structure(2, 2)
    edge_dilation_px = max(2, int(max(H, W) * 0.015))
    edge_mask = ndimage.binary_dilation(edge_mask, structure=struct, iterations=edge_dilation_px)

    # 4. Find bright areas (Excludes the black tape and dark mounts)
    bright_thresh = np.mean(S0_smooth) * 0.5
    bright_mask = S0_smooth > bright_thresh

    # 5. The background candidates are bright areas that are NOT edges
    candidate_bg = bright_mask & (~edge_mask)

    # 6. Label the regions and keep ALL massive islands
    labeled_array, num_features = ndimage.label(candidate_bg)
    if num_features > 0:
        sizes = ndimage.sum(candidate_bg, labeled_array, range(1, num_features + 1))
        max_size = np.max(sizes)

        # Keep any background chunk that is at least 20% of the largest chunk.
        valid_labels = np.where(sizes > 0.20 * max_size)[0] + 1
        bg_mask = np.isin(labeled_array, valid_labels)
    else:
        print("Warning: Could not isolate background. Falling back to brightness.")
        bg_mask = bright_mask

    # Erode the background slightly to stay safely away from the sample edges
    erosion_px = max(2, int(max(H, W) * 0.005))
    bg_mask = ndimage.binary_erosion(bg_mask, structure=struct, iterations=erosion_px)

    # Note: We NO LONGER crop the wav vignette here!
    # This ensures S1 and S2 have data in the corners so they don't blow up.
    return bg_mask

def align_reference_frame(S1, S2, bg_mask, enable=ENABLE_BACKGROUND_ALIGNMENT):
    """
    Mathematically rotates the S1/S2 reference frame so the background input
    light represents perfectly horizontal/vertical polarization (AoLP = 0).

    Fits independent 2D polynomial surfaces to the measured S1 and S2 on the
    background region, then recovers the rotation angle from
    ``alpha = 0.5 * arctan2(S2_surface, S1_surface)``. Fitting the two Cartesian
    components separately avoids the branch cut of ``arctan2`` that appears
    when the background polarization lies near the +/- 90 deg boundary: the
    previous approach fitted the wrapped angle directly and produced a
    catastrophic jump in that regime.
    """
    if not enable:
        print("Background alignment is disabled. Skipping reference frame rotation.")
        return S1, S2

    print(f"Aligning reference frame using 2D spatial rotation...")

    if not np.any(bg_mask):
        print("Warning: Background mask is empty. Skipping alignment.")
        return S1, S2

    H, W = S1.shape
    y_idx, x_idx = np.mgrid[0:H, 0:W]

    # Normalize coordinates to [-1, 1] for mathematical stability
    x_norm = (x_idx - W / 2) / (W / 2)
    y_norm = (y_idx - H / 2) / (H / 2)

    x_bg, y_bg = x_norm[bg_mask], y_norm[bg_mask]

    M_bg = np.column_stack([np.ones(len(x_bg)), x_bg, y_bg,
                            x_bg ** 2, x_bg * y_bg, y_bg ** 2])
    M_full = np.column_stack([np.ones(S1.size), x_norm.ravel(), y_norm.ravel(),
                              x_norm.ravel() ** 2,
                              x_norm.ravel() * y_norm.ravel(),
                              y_norm.ravel() ** 2])

    # Fit each Stokes component independently on the background.
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

def calculate_dolp_aolp(S0, S1, S2):
    """Calculates Degree of Linear Polarization and Angle of Linear Polarization."""
    print("Calculating DoLP and AoLP...")

    S0_safe = np.where(S0 == 0, 1e-8, S0)
    DoLP = np.sqrt(S1**2 + S2**2) / S0_safe
    DoLP = np.clip(DoLP, 0, 1)

    AoLP_rad = 0.5 * np.arctan2(S2, S1)
    AoLP_deg = np.degrees(AoLP_rad)

    return DoLP, AoLP_deg

def calculate_retardance_and_fast_axis(S0, S1, S2, S3, bg_mask, smooth_sigma=1.0):
    """
    Calculates Retardance (Delta) and Fast Axis (Theta) for a linear retarder.

    Uses spatial Gaussian smoothing on normalized Stokes components before computation
    to maximise stability at the cost of spatial detail.  The retardance is obtained
    via arctan2(sin_delta, cos_delta) and mapped to [0°, 360°) to eliminate the
    wrapping discontinuity at ±180° present in the signed [-180, 180] convention.

    Pixels where sin²(2θ) is near zero (θ ≈ 0° or 90°) lack information about δ.
    Instead of a hard binary mask, a smooth sigmoid weight fades these pixels toward
    δ = 0, avoiding visible boundary artefacts.

    Parameters
    ----------
    smooth_sigma : float
        Standard deviation (pixels, in downsampled space) for the pre-smoothing
        Gaussian filter.  Higher values give smoother but less detailed maps.
        Default 1.  Set to 0 to disable smoothing.

    Returns
    -------
    delta_degrees : ndarray
        Retardance in degrees, range [0, 360).
    theta_degrees : ndarray
        Fast axis angle in degrees, range [0, 90].
    """
    print("Calculating Retardance and Fast Axis...")
    if S3 is None:
        print("Warning: S3 is required to calculate retardance. Returning None.")
        return None, None

    # STEP 1: Normalize Stokes components
    S0_safe = np.where(S0 == 0, 1e-8, S0)
    s1 = S1 / S0_safe
    s2 = S2 / S0_safe
    s3 = S3 / S0_safe

    # STEP 2: Background input state from unobstructed (mask) region
    if np.any(bg_mask):
        global _WAV_INTENSITY_CACHE
        # s2_in is used as a diagnostic of the alignment residual: after
        # align_reference_frame the median on the background must be close to
        # zero, otherwise the linear-horizontal assumption underlying the
        # retarder inversion no longer holds and the retardance is biased.
        s2_in = np.median(s2[bg_mask])
        if abs(s2_in) > 0.05:
            print(f"  WARNING: residual s2 on background = {s2_in:+.4f} "
                  "(> 0.05). Alignment may have failed; retardance estimate "
                  "will carry a systematic error.")

        H, W = s3.shape
        y_idx, x_idx = np.mgrid[0:H, 0:W]

        # NORMALIZE coordinates to [-1, 1] to prevent massive numerical instability
        x_norm = (x_idx - W / 2) / (W / 2)
        y_norm = (y_idx - H / 2) / (H / 2)

        M_full = np.column_stack(
            [np.ones(s3.size), x_norm.ravel(), y_norm.ravel(), x_norm.ravel() ** 2, x_norm.ravel() * y_norm.ravel(),
             y_norm.ravel() ** 2])

        # --- FIT S1 (Using the FULL mask so the corners don't blow up) ---
        x_bg, y_bg = x_norm[bg_mask], y_norm[bg_mask]
        M_bg = np.column_stack([np.ones(len(x_bg)), x_bg, y_bg, x_bg ** 2, x_bg * y_bg, y_bg ** 2])
        coeffs_s1, _, _, _ = np.linalg.lstsq(M_bg, s1[bg_mask], rcond=None)
        s1_in = (M_full @ coeffs_s1).reshape(H, W)

        # --- FIT S3 (Using a dynamically CROPPED mask to avoid the wav vignette) ---
        bg_mask_s3 = bg_mask.copy()
        if _WAV_INTENSITY_CACHE is not None:
            wav_blur = ndimage.gaussian_filter(_WAV_INTENSITY_CACHE, sigma=max(H, W) * 0.01)
            wav_thresh = np.mean(wav_blur) * 0.5
            wav_bright = wav_blur > wav_thresh
            valid_wav_area = ndimage.binary_fill_holes(wav_bright)

            generous_erosion = max(5, int(max(H, W) * 0.005))
            valid_wav_area = ndimage.binary_erosion(valid_wav_area, structure=ndimage.generate_binary_structure(2, 2),
                                                    iterations=generous_erosion)

            bg_mask_s3 = bg_mask & valid_wav_area

        if np.any(bg_mask_s3):
            x_bg_s3, y_bg_s3 = x_norm[bg_mask_s3], y_norm[bg_mask_s3]
            M_bg_s3 = np.column_stack(
                [np.ones(len(x_bg_s3)), x_bg_s3, y_bg_s3, x_bg_s3 ** 2, x_bg_s3 * y_bg_s3, y_bg_s3 ** 2])
            coeffs_s3, _, _, _ = np.linalg.lstsq(M_bg_s3, s3[bg_mask_s3], rcond=None)
            s3_in = (M_full @ coeffs_s3).reshape(H, W)
        else:
            s3_in = np.zeros((H, W))

        med_s1 = np.median(s1_in)
        med_s3 = np.median(s3_in)
    else:
        s1_in = 1.0
        s2_in = 0.0
        s3_in = 0.0
        med_s1 = 1.0
        med_s3 = 0.0

    print(f"  Background input modeled as 2D surfaces. Medians: s1={med_s1:.4f}, s2={s2_in:.4f}, s3={med_s3:.4f}")

    # STEP 3: Spatial smoothing — trades spatial resolution for noise robustness
    if smooth_sigma > 0:
        s1 = ndimage.gaussian_filter(s1, sigma=smooth_sigma)
        s2 = ndimage.gaussian_filter(s2, sigma=smooth_sigma)
        s3 = ndimage.gaussian_filter(s3, sigma=smooth_sigma)

    # STEP 4: Background-corrected S3 (remove residual circular component from source)
    s3_corrected = s3 - s3_in

    # --- THE MAGIC PLOT FIX ---
    # We modify the original S3 array in memory so that when your main script
    # plots it, it plots the beautifully flattened, corrected version!
    if S3 is not None:
        S3[:] = s3_corrected * S0_safe

    # STEP 5: Fast Axis Angle (Theta)
    # For horizontally-polarised input (s2_in=0):
    #   A = s1_in - s1 = s1_in * sin²(2θ) * (1 - cos δ)  >= 0 for a physical retarder
    #   s2           = s1_in * sin(2θ) * cos(2θ) * (1 - cos δ)
    # => arctan2(A, s2) = 2θ,  θ in [0°, 90°]
    # Clamping A to [0, ∞) enforces the physics constraint and prevents noise-driven
    # sign flips in arctan2 that would push theta into negative territory.
    A = np.maximum(s1_in - s1, 0.0)
    theta = 0.5 * np.arctan2(A, s2)

    sin_2theta = np.sin(2 * theta)
    sin_2theta_sq = sin_2theta ** 2

    # STEP 6: Smooth stability weight instead of a hard cutoff.
    # A hard mask (sin²2θ > threshold) creates a visible ring where δ snaps to 0.
    # Instead, blend smoothly from 0 (unreliable, δ→0 fallback) to 1 (fully trusted)
    # using a sigmoid-like ramp centred at sin²2θ = 0.02 with width ~0.02.
    STABILITY_CENTRE = 0.02
    STABILITY_WIDTH = 0.02
    weight = np.clip((sin_2theta_sq - STABILITY_CENTRE) / STABILITY_WIDTH, 0.0, 1.0)

    stable_frac = np.mean(weight > 0.5) * 100
    print(f"  Stability: {stable_frac:.1f}% of pixels above half-weight threshold")

    # STEP 7: cos(δ) from S1
    # cos δ = 1 - (s1_in - s1) / (s1_in * sin²(2θ))
    # Regularise the denominator to avoid division by zero, then let the weight
    # fade unreliable pixels toward the fallback (cos_delta = 1, i.e. δ = 0).
    denom_cos = s1_in * np.maximum(sin_2theta_sq, 1e-6)
    cos_delta_raw = 1.0 - A / denom_cos
    cos_delta_raw = np.clip(cos_delta_raw, -1.0, 1.0)
    cos_delta = weight * cos_delta_raw + (1.0 - weight) * 1.0  # fallback: cosδ=1

    # STEP 8: sin(δ) from S3
    # s3_corrected = s1_in * sin(2θ) * sin(δ)
    # => sin δ = s3_corrected / (s1_in * sin(2θ))
    denom_sin = s1_in * np.where(np.abs(sin_2theta) < 1e-4, np.sign(sin_2theta + 1e-12) * 1e-4, sin_2theta)
    sin_delta_raw = s3_corrected / denom_sin
    sin_delta_raw = np.clip(sin_delta_raw, -1.0, 1.0)
    sin_delta = weight * sin_delta_raw  # fallback: sinδ=0

    # STEP 9: Retardance via arctan2, mapped to [0°, 360°).
    delta = np.arctan2(sin_delta, cos_delta)
    delta = np.where(delta < 0, delta + 2.0 * np.pi, delta)

    delta_deg = np.degrees(delta)
    theta_deg = np.degrees(theta)

    # Hardware calibration for acquisitions where the waveplate was physically
    # mounted with fast/slow axes swapped (rotated 90 deg from intended). On
    # the Poincare sphere the swap is equivalent to (delta -> 2*pi - delta,
    # theta -> theta +/- 90 deg), so the correct physical parameters are
    # recovered analytically without re-measuring. Controlled by the explicit
    # WAVEPLATE_AXES_SWAPPED flag in the configuration section.
    if WAVEPLATE_AXES_SWAPPED:
        print("  -> WAVEPLATE_AXES_SWAPPED active: applying fast/slow axis "
              "correction (delta -> 360 - delta, theta -> theta - 90 deg).")
        delta_deg = (360.0 - delta_deg) % 360.0
        theta_deg = (theta_deg - 90.0 + 90.0) % 180.0 - 90.0

    return delta_deg, theta_deg