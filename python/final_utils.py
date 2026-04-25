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
DOWNSAMPLE_FACTOR = 1

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

# Cache for the cleaned bg mask used in the Poincare ellipticity rebasing
# (bg_mask intersected with wav-bright pixels). Exposed to plotting code so the
# debug figure can overlay the actual mask used for the beta fit.
_POINCARE_BG_MASK_CACHE = None

# Threshold (fraction of bg median) on the wav intensity used to mask out
# the dark holder/aperture region before the beta polynomial fit. Lower
# values keep more bg pixels for the fit (better spatial constraint) at
# the cost of including pixels closer to the holder transition where the
# wav numerator is degenerate. Default 0.7 trades off the two.
WAV_HOLDER_THRESHOLD = 0.7

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
    Segmenta il sample via Canny + dark-pixel prior + circle expansion +
    flood-fill del bg dal bordo foto, restituisce il complemento.

    Progetto scale-invariant: tutti i parametri geometrici sono espressi in
    frazione di ``max(H, W)`` oppure di ``H*W``.

    Strategia:
      * **Canny con soglie assolute** (low=29/255, high=148/255): hysteresis
        tarata per catturare anche bordi semi-trasparenti senza generare
        random walk da rumore.
      * **Dark-pixel prior**: ogni pixel al di sotto di ``DARK_THRESH`` (30%
        del range) viene marcato come sample per definizione. Cattura
        holder neri e monture anche quando il bordo sfuma.
      * **Circle expansion**: dilation con disco proporzionale per cucire
        edge vicini ma non perfettamente allineati.
      * **Flood-fill del bg dal bordo foto**: il bg e' l'unica componente
        connessa del complemento del barrier che tocchi almeno un lato
        dell'immagine. Piu' robusto di "largest + brightest" che puo'
        scegliere regioni luminose enclosed (es. cerchio interno della
        montatura lambda/4).
      * **Fill holes del sample**: buchi interni al sample (bg intrappolato
        dentro il campione) vengono tappati con ``binary_fill_holes``.
      * **Auto error detection via compactness**: misura
        ``4*pi*A/perimetro^2`` sulla componente sample piu' grande; se il
        contorno risulta troppo frastagliato, emette warning.
    """
    from skimage.feature import canny
    from skimage.morphology import disk, closing, opening, dilation

    DARK_THRESH = 0.30        # nero >= 70% -> sample
    CANNY_SIGMA = 1.5         # scelto su sweep strati_v2/B (2026-04-24)
    CANNY_LOW = 0.05          # soglia bassa su gradiente [0, 1]
    CANNY_HIGH = 0.15         # soglia alta su gradiente [0, 1]
    COMPACTNESS_WARN = 0.05   # sotto questa soglia: warning "frastagliato"

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

    # 1) normalizzazione in [0, 1]
    s_ptp = float(np.ptp(S0))
    if s_ptp < 1e-8:
        return _brightness_fallback("S0 costante (ptp ~ 0)")
    S0_norm = (S0 - np.min(S0)) / s_ptp

    # 2) dark prior
    dark_mask = S0_norm < DARK_THRESH
    print(f"  dark_mask (<{DARK_THRESH:.2f}): "
          f"frac={dark_mask.sum() / dark_mask.size:.4f}")

    # 3) Canny con sigma fisso e soglie assolute scelte via parameter sweep
    #    su strati_v2/B (dataset piu' challenging: mistilinee ravvicinate
    #    con bordi trasparenti). Sigma basso (1.5 px) preserva bordi fini
    #    senza lasciare troppo rumore, soglie moderate catturano bordi
    #    deboli senza random walk.
    edges = canny(
        S0_norm, sigma=CANNY_SIGMA,
        low_threshold=CANNY_LOW, high_threshold=CANNY_HIGH,
        use_quantiles=False,
    )
    frac_edges = edges.sum() / edges.size
    print(f"  Canny: sigma={CANNY_SIGMA:.2f} px, "
          f"low={CANNY_LOW:.3f}, high={CANNY_HIGH:.3f}, "
          f"edges_frac={frac_edges:.4f}")
    if frac_edges < 1e-5 and not dark_mask.any():
        return _brightness_fallback(
            "Canny vuoto e nessun pixel scuro sotto soglia")

    # 4) circle expansion: dilation con disco proporzionale per fondere
    #    edge vicini in un unico barrier. Raggio ~0.004 * dim -> ~15 px
    #    native, ~4 px DS=20. Piu' aggressivo di un semplice closing perche'
    #    dilata prima del complemento.
    expand_r = max(4, int(dim * 0.004))
    edges_expanded = dilation(edges, disk(expand_r))

    # 5) barrier = edge expansi + dark prior, piu' closing di 1-2 px
    #    per cucire gap residui sottili
    barrier = edges_expanded | dark_mask
    closing_r = max(2, int(dim * 0.002))
    barrier = closing(barrier, disk(closing_r))

    # 6) etichetta componenti del complemento del barrier (4-conn)
    labeled, n_feat = ndimage.label(~barrier, structure=struct4)
    if n_feat == 0:
        return _brightness_fallback("nessuna componente bg candidata")

    # 7) bg = componente piu' grande che tocca il bordo foto (true
    #    "outside"). Evita che interni luminosi enclosed (es. cerchio
    #    montatura lambda/4) vengano scambiati per bg.
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
    label_best = max(border_sizes, key=border_sizes.get)
    bg_flood = (labeled == label_best)
    print(f"  bg flood-fill (border-touching): label={label_best} "
          f"di {n_feat} tot, size_frac={bg_flood.sum() / bg_flood.size:.4f}, "
          f"mean_brightness={float(S0_norm[bg_flood].mean()):.3f}")

    # 8) sample = ~bg, fill holes interni (buchi di bg intrappolato dentro
    #    il campione vengono tappati)
    sample_mask = ~bg_flood
    sample_mask = ndimage.binary_fill_holes(sample_mask)
    if sample_mask is None:
        return _brightness_fallback("fill_holes sul sample ha fallito")

    # 9) opening per ammorbidire zigrini residui
    opening_r = max(2, int(dim * 0.0015))
    sample_mask = opening(sample_mask, disk(opening_r))

    # 10) auto error detection: compactness della componente sample piu'
    #     grande. Sample fisici hanno contorni regolari (rettangoli,
    #     dischi, mistilinee a tratti lunghi) -> compactness >= 0.1 ok,
    #     < 0.05 probabilmente segmentazione fallita.
    lbl_s, n_s = ndimage.label(sample_mask, structure=struct4)
    if n_s > 0:
        sizes_s = ndimage.sum(sample_mask, lbl_s,
                              index=range(1, n_s + 1))
        largest_s = int(np.argmax(sizes_s)) + 1
        sample_largest = (lbl_s == largest_s)
        area = int(sample_largest.sum())
        perim_mask = ndimage.binary_dilation(
            sample_largest, structure=struct4) & (~sample_largest)
        perim = int(perim_mask.sum())
        if area > 0 and perim > 0:
            compactness = 4.0 * np.pi * area / (perim ** 2)
            status = "OK" if compactness >= COMPACTNESS_WARN else "WARN"
            print(f"  compactness sample piu' grande = {compactness:.3f} "
                  f"(1=cerchio, 0=frastagliato) [{status}]")
            if compactness < COMPACTNESS_WARN:
                print("  [bg_mask] WARNING: contorno del sample molto "
                      "frastagliato; segmentazione probabilmente sporca.")

    # 11) bg finale + erosione di sicurezza
    bg_mask = ~sample_mask
    erosion_r = max(5, int(dim * 0.005))
    bg_mask = ndimage.binary_erosion(
        bg_mask, structure=disk(erosion_r), iterations=1)

    frac_bg = bg_mask.sum() / bg_mask.size
    if frac_bg < 0.01 or frac_bg > 0.995:
        return _brightness_fallback(f"bg_frac degenere={frac_bg:.4f}")

    print(f"  bg_frac={frac_bg:.4f} (sample_frac={1-frac_bg:.4f})")
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


def align_poincare_ellipticity(S0, S1, S3, bg_mask,
                               enable=ENABLE_BACKGROUND_ALIGNMENT):
    """Rotates the Stokes basis around the S2 axis so that the background input
    state sits on the pure-linear equator (s3/s0 -> 0 on bg).

    Complements ``align_reference_frame`` which rotates around S3 to cancel
    s2_bg. The combined rotation brings the bg Stokes vector to (1, 0, 0),
    matching the linear-input assumption of the retarder inversion.

    The bg statistics used to compute the rotation angle exclude
    waveplate-holder dark pixels (visible in the wav frames as black corners
    of the lamda/4 mount) using the cached wav intensity; those pixels pass
    the S0-based bg_mask but carry noisy S3 because the wav numerator
    I_+45 - I_-45 is tiny there.

    Physically the rotation rebases the Poincaree sphere to absorb residual
    ellipticity in the illumination (LCD imperfection, optics birefringence).
    Retardance delta is invariant under this rotation, so downstream formulas
    recover it correctly to first order in beta.
    """
    global _POINCARE_BG_MASK_CACHE
    _POINCARE_BG_MASK_CACHE = None

    if not enable:
        print("Poincare ellipticity rebasing disabled. Skipping.")
        return S1, S3

    print("Rebasing Poincare sphere around S2 axis (ellipticity correction)...")

    if not np.any(bg_mask):
        print("  Warning: bg mask empty. Skipping.")
        return S1, S3

    # Build the s3-specific bg mask: exclude wav-dark holder pixels. Threshold
    # is WAV_HOLDER_THRESHOLD * median(wav intensity on bg). Lower values keep
    # more bg pixels for the beta fit at the cost of including pixels closer
    # to the holder transition where the wav numerator is degenerate.
    bg_mask_s3 = bg_mask
    if _WAV_INTENSITY_CACHE is not None \
            and _WAV_INTENSITY_CACHE.shape == bg_mask.shape:
        wav_bg_med = float(np.median(_WAV_INTENSITY_CACHE[bg_mask]))
        wav_bright = _WAV_INTENSITY_CACHE > WAV_HOLDER_THRESHOLD * wav_bg_med
        struct = ndimage.generate_binary_structure(2, 2)
        wav_bright = ndimage.binary_erosion(
            wav_bright, structure=struct,
            iterations=max(3, int(max(bg_mask.shape) * 0.01)))
        candidate = bg_mask & wav_bright
        if candidate.sum() < 0.1 * bg_mask.sum():
            print("  WARNING: wav holder mask too aggressive, using full bg.")
        else:
            bg_mask_s3 = candidate
            n_excl = int(bg_mask.sum() - bg_mask_s3.sum())
            print(f"  Wav-dark holder pixels excluded "
                  f"(threshold {WAV_HOLDER_THRESHOLD:.2f}x med): "
                  f"{n_excl} ({100*n_excl/max(1,bg_mask.sum()):.1f}%)")

    _POINCARE_BG_MASK_CACHE = bg_mask_s3.copy()

    # Fit s1_in and s3_in as 2D degree-2 polynomial surfaces on the cleaned bg
    # so the rotation angle beta(x, y) can track the spatial variation of the
    # residual ellipticity. Same basis as align_reference_frame (1, x, y, x^2,
    # xy, y^2). Tens of thousands of bg pixels make degree 2 stable; higher
    # degree risks overfitting sample-edge seepage.
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

    # Diagnostics: before/after residual on the cleaned bg.
    s3_bg_med_pre = float(np.median(s3_vals))
    s3_bg_std_pre = float(np.std(s3_vals))
    s3_fit_bg = s3_fit[bg_mask_s3]
    s3_resid_std = float(np.std(s3_vals - s3_fit_bg))
    print(f"  s3_bg (cleaned) pre: median={s3_bg_med_pre:+.4f}, "
          f"std={s3_bg_std_pre:.4f}")
    print(f"  s3_bg deg-2 fit: residual std={s3_resid_std:.4f} "
          f"(ratio resid/raw = {s3_resid_std/max(1e-8,s3_bg_std_pre):.2f})")

    # Pixel-wise rotation angle beta(x, y) from the fitted input state.
    beta_map = np.arctan2(s3_fit, s1_fit)
    cos_b = np.cos(beta_map)
    sin_b = np.sin(beta_map)

    # Rotation acts linearly on absolute Stokes components (S0 unchanged).
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

    return S1_rot, S3_rot


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

    # STEP 2: Background input state from unobstructed (mask) region.
    # Assumes Poincare basis is already rebased via align_poincare_ellipticity
    # (callers: S1, S3 already rotated around S2 so s3_bg ~ 0).
    if np.any(bg_mask):
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
            [np.ones(s3.size), x_norm.ravel(), y_norm.ravel(),
             x_norm.ravel() ** 2, x_norm.ravel() * y_norm.ravel(),
             y_norm.ravel() ** 2])

        # --- FIT S1 su bg (necessario per calcolo di delta: baseline di s1
        # lineare orizzontale). S3 non sottratto: rotazione Poincare gestisce
        # l'ellitticita' residua dell'input.
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

    # STEP 3: Spatial smoothing — trades spatial resolution for noise robustness
    if smooth_sigma > 0:
        s1 = ndimage.gaussian_filter(s1, sigma=smooth_sigma)
        s2 = ndimage.gaussian_filter(s2, sigma=smooth_sigma)
        s3 = ndimage.gaussian_filter(s3, sigma=smooth_sigma)

    # STEP 4: S3 usato direttamente (senza sottrazione di baseline).
    s3_corrected = s3

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