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

TARGET_FOLDER = './raw/zucchero'
POL_SUBFOLDER = os.path.join(TARGET_FOLDER, 'pol')
WAV_SUBFOLDER = os.path.join(TARGET_FOLDER, 'wav')
WAVELENGTHS_CSV = './outputs/rgb_wavelengths.csv'

# Sensor channels: 0: Red, 1: Green, 2: Blue
TARGET_CHANNEL_IDX = 0

# Default downsampling factor for the full polarimeter mapping
DOWNSAMPLE_FACTOR = 10

# =============================================================================
# THESIS FIGURE CONFIGURATION
# =============================================================================

# Which parameter to plot (one of: S0, S1, S2, S3, DoLP, AoLP, delta, theta, mask)
THESIS_FIGURE_PARAM = 'AoLP'

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

def load_raw_image(path, channel_index, downsample_factor=1):
    """Loads a RAW image, extracts the 16-bit color channel, and downsamples."""
    if not os.path.exists(path):
        return None
    try:
        with rawpy.imread(path) as raw:
            rgb = raw.postprocess(
                use_camera_wb=True,
                no_auto_bright=True,
                gamma=(1, 1),
                output_bps=16
            )
        channel_data = rgb[:, :, channel_index].astype(np.float32)
        return downsample_image(channel_data, downsample_factor)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None

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

def calculate_s3(wav_dir, channel_index, downsample_factor=1, wavelength=633.0):
    """Loads wav images, applies angle inversion, and calculates wavelength-corrected S3."""
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

    # Wavelength correction for zero-order 633nm lambda/4 waveplate
    delta = (np.pi / 2.0) * (633.0 / wavelength)
    correction_factor = np.sin(delta)

    print(f"Calculating S3... (Applying correction for {wavelength}nm, factor: 1/sin({np.degrees(delta):.1f}°) = {1/correction_factor:.3f})")

    # S3 = (I(45) - I(-45)) / sin(delta)
    S3 = (I_45 - I_minus_45) / correction_factor

    return S3


def generate_background_mask(S0, S3=None):
    """
    Creates a 'smart select' background mask. Uses local adaptive thresholding,
    keeps only the single largest connected component to filter artifacts.
    If S3 is provided, further constrains the background to the active waveplate circle.
    """
    print("Generating smart background mask...")
    H, W = S0.shape

    # 1. Create a local illumination profile
    blur_sigma = max(H, W) * 0.02
    bg_profile = ndimage.gaussian_filter(S0, sigma=blur_sigma)

    # 2. Extract features: slightly more forgiving threshold to catch edges
    features = S0 < (bg_profile * 0.95)

    # 3. Dilate slightly MORE to ensure the loop around the holder seals shut
    close_px = max(3, int(max(H, W) * 0.025))
    struct = ndimage.generate_binary_structure(2, 2)
    closed_edges = ndimage.binary_dilation(features, structure=struct, iterations=close_px)

    # 4. Fill the holes
    filled_object = ndimage.binary_fill_holes(closed_edges)

    # 5. KEEP ONLY LARGEST COMPONENT: This deletes the bottom blocks & random dust!
    labeled_array, num_features = ndimage.label(filled_object)
    if num_features > 0:
        # Measure size of each labeled cluster
        sizes = ndimage.sum(filled_object, labeled_array, range(1, num_features + 1))
        # Find the ID of the largest cluster
        largest_label = np.argmax(sizes) + 1
        main_object = (labeled_array == largest_label)
    else:
        main_object = filled_object

    # 6. Expand outward by ~2% for the safe background margin
    safe_margin_px = max(2, int(max(H, W) * 0.02))
    final_object = ndimage.binary_dilation(main_object, structure=struct, iterations=safe_margin_px)

    # 7. Background is the inverse
    bg_mask = ~final_object

    # 8. If S3 is provided, isolate the active waveplate circle
    if S3 is not None:
        print("Refining mask to include only the active waveplate area from S3...")

        # Calculate the magnitude of S3 and blur it less to keep edges sharper
        s3_mag = ndimage.gaussian_filter(np.abs(S3), sigma=max(H, W) * 0.01)

        # Relax the threshold so it includes more of the waveplate area
        threshold = np.mean(s3_mag) * 0.25
        valid_s3_area = s3_mag > threshold

        # Fill holes (like the zero-crossing line across the middle of the waveplate)
        valid_s3_area = ndimage.binary_fill_holes(valid_s3_area)

        # Ensure we only pick up the main circle, ignore noisy stray pixels
        labeled_s3, num_s3_features = ndimage.label(valid_s3_area)
        if num_s3_features > 0:
            sizes = ndimage.sum(valid_s3_area, labeled_s3, range(1, num_s3_features + 1))
            largest_s3_label = np.argmax(sizes) + 1
            valid_s3_area = (labeled_s3 == largest_s3_label)

        # Erode the mask much less aggressively (0.5% instead of 1.5%)
        erosion_px = max(1, int(max(H, W) * 0.005))
        valid_s3_area = ndimage.binary_erosion(valid_s3_area, structure=struct, iterations=erosion_px)

        # Intersect our object-background mask with the valid waveplate area
        bg_mask = bg_mask & valid_s3_area

    return bg_mask

def align_reference_frame(S1, S2, bg_mask):
    """
    Mathematically rotates the S1/S2 reference frame so the background input
    light represents perfectly horizontal polarization (AoLP = 0).
    """
    print(f"Aligning reference frame to compensate for LCD offset angle...")

    if not np.any(bg_mask):
        print("Warning: Background mask is empty. Skipping alignment.")
        return S1, S2

    bg_s1 = np.median(S1[bg_mask])
    bg_s2 = np.median(S2[bg_mask])

    alpha_bg = 0.5 * np.arctan2(bg_s2, bg_s1)
    print(f"Detected background offset angle (from masked area): {np.degrees(alpha_bg):.2f}°")

    cos_2a = np.cos(2 * alpha_bg)
    sin_2a = np.sin(2 * alpha_bg)

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

def calculate_retardance_and_fast_axis(S0, S1, S2, S3, bg_mask):
    """Calculates Retardance (Delta) and Fast Axis (Theta) using real input parameters."""
    print("Calculating Retardance and Fast Axis (Corrected for true input)...")
    if S3 is None:
        print("Warning: S3 is required to calculate retardance. Returning None.")
        return None, None

    # STEP 1: Normalize
    S0_safe = np.where(S0 == 0, 1e-8, S0)
    s1 = S1 / S0_safe
    s2 = S2 / S0_safe
    s3 = S3 / S0_safe

    # STEP 2: Extract real background input states
    if np.any(bg_mask):
        s1_in = np.median(s1[bg_mask])
        s3_in = np.median(s3[bg_mask])
    else:
        s1_in = 1.0
        s3_in = 0.0

    # Compensate for circular background offset
    s3_corrected = s3 - s3_in

    # STEP 3: Fast Axis Angle (Theta) - Use real s1_in
    theta = 0.5 * np.arctan2(s1_in - s1, s2)

    # STEP 4: Retardance Magnitude (Delta)
    sin_2theta_sq = np.sin(2 * theta)**2

    # Numerical Safety Check
    safe_mask = sin_2theta_sq > 0.02

    cos_delta = np.ones_like(s1)
    # Use s1_in for the amplitude normalization
    cos_delta[safe_mask] = 1 - ((s1_in - s1[safe_mask]) / (s1_in * sin_2theta_sq[safe_mask]))

    # Clip to valid arccos range to prevent NaNs
    cos_delta = np.clip(cos_delta, -1.0, 1.0)
    delta_magnitude = np.arccos(cos_delta)

    # STEP 5: Apply Sign Correction using the corrected S3
    sign_checker = s3_corrected * np.sin(2 * theta)
    delta_signed = np.where(sign_checker < 0, -delta_magnitude, delta_magnitude)

    # STEP 6: Convert to Degrees
    delta_degrees = np.degrees(delta_signed)
    theta_degrees = np.degrees(theta)

    return delta_degrees, theta_degrees