"""Costanti, default e mappature dataset per il package polarimetro."""
import csv
import os

# Sensor / saturation
SENSOR_WHITE_LEVEL = 4095
SATURATION_FRACTION = 0.98

# Poincare ellipticity rebasing
WAV_HOLDER_THRESHOLD = 0.50

# Background mask (Canny + dark prior + flood-fill)
DARK_THRESH = 0.30
CANNY_SIGMA = 1.5
CANNY_LOW = 0.05
CANNY_HIGH = 0.15
COMPACTNESS_WARN = 0.05
EROSION_NATIVE_PX = 100
POINCARE_DILATE_NATIVE_PX = 150

# Defaults overridable
DEFAULT_DOWNSAMPLE_FACTOR = 4
DEFAULT_TARGET_CHANNEL_IDX = 2
DEFAULT_DARK_FRAME_PATH = './raw/dark.dng'
DEFAULT_WAVELENGTHS_CSV = './outputs/rgb_wavelengths.csv'
DEFAULT_DESIGN_WAVELENGTH_NM = 633.0
DEFAULT_WAVEPLATE_ORDER = 0.25
ENABLE_BACKGROUND_ALIGNMENT = True
USE_RAW_BAYER = True

# Output paths
THESIS_FIGURES_DIR = '../Images/generated'
THESIS_FIGURE_PARAMS = "all"

# Punti di ancoraggio di design per fit δ(λ) = k/λ su lamine d'onda.
# Quartzo zero-order: δ = 2π · Δn · d / λ → δ ∝ 1/λ.
# Valori nominali al picco di taratura (633 nm).
WAVEPLATE_DESIGN_ANCHOR = {
    'lambdamezzi_50deg':  {'wavelength_nm': 633.0, 'delta_deg': 180.0},
    'lambdaquarti_50deg': {'wavelength_nm': 633.0, 'delta_deg':  90.0},
}


def get_channel_wavelength(csv_path, channel_index):
    """Reads centroid wavelength (nm) for the given channel index (0:R, 1:G, 2:B)."""
    channel_map = {0: 'R', 1: 'G', 2: 'B'}
    target_char = channel_map.get(channel_index, 'G')

    if not os.path.exists(csv_path):
        print(f"Warning: Wavelength CSV not found at {csv_path}. Defaulting to 532.0 nm.")
        return 532.0

    try:
        with open(csv_path, mode='r') as infile:
            reader = csv.reader(infile)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[0].strip().upper() == target_char:
                    return float(row[1].strip())
    except Exception as e:
        print(f"Error reading {csv_path}: {e}. Defaulting to 532.0 nm.")
        return 532.0

    print(f"Warning: Channel {target_char} not found in {csv_path}. Defaulting to 532.0 nm.")
    return 532.0
