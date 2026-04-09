"""
Stokes Parameter Fit from RAW Images
Calculates the full Stokes vector (S0, S1, S2, S3), DoLP, AoLP, Retardance, and Fast Axis.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Import shared functions and configs
import final_utils as utils

try:
    matplotlib.use('TkAgg')
except:
    pass

# =============================================================================
# PLOTTING
# =============================================================================

def plot_all_parameters(S0, S1, S2, S3, DoLP, AoLP, delta, theta, bg_mask, channel_idx):
    """Plots all 9 parameters in a 3x3 grid."""
    print("\nGenerating plots...")

    # Set colormap for S0 based on target channel (0: Red, 1: Green, 2: Blue)
    if channel_idx == 0:
        cmap_s0 = LinearSegmentedColormap.from_list('black_red', ['black', 'red'])
    elif channel_idx == 1:
        cmap_s0 = LinearSegmentedColormap.from_list('black_green', ['black', 'green'])
    elif channel_idx == 2:
        cmap_s0 = LinearSegmentedColormap.from_list('black_blue', ['black', 'blue'])
    else:
        cmap_s0 = 'gray'

    # Adjusted to a 3x3 grid to gracefully accommodate the mask
    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    fig.suptitle("Full Stokes, Polarization, & Retardance Parameters", fontsize=16)

    # --- ROW 1: S0, S1, S2 ---
    im0 = axes[0, 0].imshow(S0, cmap=cmap_s0)
    axes[0, 0].set_title('S0 (Total Intensity)')
    axes[0, 0].axis('off')
    fig.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04)

    s1_max = np.percentile(np.abs(S1), 99)
    im1 = axes[0, 1].imshow(S1, cmap='bwr', vmin=-s1_max, vmax=s1_max)
    axes[0, 1].set_title('S1 (Horizontal/Vertical)')
    axes[0, 1].axis('off')
    fig.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)

    s2_max = np.percentile(np.abs(S2), 99)
    im2 = axes[0, 2].imshow(S2, cmap='bwr', vmin=-s2_max, vmax=s2_max)
    axes[0, 2].set_title('S2 (±45° Diagonal)')
    axes[0, 2].axis('off')
    fig.colorbar(im2, ax=axes[0, 2], fraction=0.046, pad=0.04)

    # --- ROW 2: S3, DoLP, AoLP ---
    if S3 is not None:
        s3_max = np.percentile(np.abs(S3), 99)
        im3 = axes[1, 0].imshow(S3, cmap='bwr', vmin=-s3_max, vmax=s3_max)
        axes[1, 0].set_title('S3 (Circular Left/Right)')
        axes[1, 0].axis('off')
        fig.colorbar(im3, ax=axes[1, 0], fraction=0.046, pad=0.04)
    else:
        axes[1, 0].text(0.5, 0.5, 'S3 Data Missing', ha='center', va='center')
        axes[1, 0].axis('off')

    im_dolp = axes[1, 1].imshow(DoLP, cmap='viridis', vmin=0, vmax=1)
    axes[1, 1].set_title('DoLP (Linear Polarization %)')
    axes[1, 1].axis('off')
    fig.colorbar(im_dolp, ax=axes[1, 1], fraction=0.046, pad=0.04)

    im_aolp = axes[1, 2].imshow(AoLP, cmap='twilight', vmin=-90, vmax=90)
    axes[1, 2].set_title('AoLP (Linear Angle)')
    axes[1, 2].axis('off')
    fig.colorbar(im_aolp, ax=axes[1, 2], fraction=0.046, pad=0.04, label='Degrees')

    # --- ROW 3: Fast Axis (Theta), Retardance (Delta), Mask ---
    if theta is not None and delta is not None:
        im_theta = axes[2, 0].imshow(theta, cmap='twilight', vmin=-90, vmax=90)
        axes[2, 0].set_title('Fast Axis (Theta)')
        axes[2, 0].axis('off')
        fig.colorbar(im_theta, ax=axes[2, 0], fraction=0.046, pad=0.04, label='Degrees')

        im_delta = axes[2, 1].imshow(delta, cmap='twilight', vmin=-180, vmax=180)
        axes[2, 1].set_title('Retardance (Delta)')
        axes[2, 1].axis('off')
        fig.colorbar(im_delta, ax=axes[2, 1], fraction=0.046, pad=0.04, label='Degrees')
    else:
        axes[2, 0].text(0.5, 0.5, 'Requires S3', ha='center', va='center')
        axes[2, 0].axis('off')
        axes[2, 1].text(0.5, 0.5, 'Requires S3', ha='center', va='center')
        axes[2, 1].axis('off')

    # Create the debug mask: Normalize S0 to 0-1 range
    S0_norm = (S0 - np.min(S0)) / (np.max(S0) - np.min(S0) + 1e-8)

    # Put 0.0 (black) where bg_mask is False (excluded from average), otherwise show S0_norm
    debug_mask_img = np.where(bg_mask, S0_norm, 0.0)

    im_mask = axes[2, 2].imshow(debug_mask_img, cmap='gray', vmin=0, vmax=1)
    axes[2, 2].set_title('Safe Background Mask (Debug)')
    axes[2, 2].axis('off')
    fig.colorbar(im_mask, ax=axes[2, 2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.show()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("--- Starting Stokes Fit ---")

    # 1. Linear Stokes Parameters (S0, S1, S2)
    angles, stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER,
        utils.TARGET_CHANNEL_IDX,
        downsample_factor=utils.DOWNSAMPLE_FACTOR,
        invert_angles=True
    )

    if stack is None or angles is None:
        print("Interruption: Linear polarization data could not be loaded.")
        return

    S0, S1, S2 = utils.calculate_linear_stokes(angles, stack)

    # 2. Extract Wavelength for the active channel
    wavelength = utils.get_channel_wavelength(utils.WAVELENGTHS_CSV, utils.TARGET_CHANNEL_IDX)

    # 3. Circular Stokes Parameter (S3) with Wavelength Correction
    S3 = utils.calculate_s3(utils.WAV_SUBFOLDER, utils.TARGET_CHANNEL_IDX, utils.DOWNSAMPLE_FACTOR, wavelength)

    # 4. Generate Mask and Correct Math
    # Dynamically find the background by expanding an object mask based on S0 and the S3 waveplate circle
    bg_mask = utils.generate_background_mask(S0, S3)

    # Align the reference frame to compensate for the input offset using the mask
    S1_aligned, S2_aligned = utils.align_reference_frame(S1, S2, bg_mask)

    # 5. Polarization & Retardance Math (using aligned data and background mask)
    DoLP, AoLP = utils.calculate_dolp_aolp(S0, S1_aligned, S2_aligned)
    delta_degrees, theta_degrees = utils.calculate_retardance_and_fast_axis(S0, S1_aligned, S2_aligned, S3, bg_mask)

    # 6. Plotting - Pass the channel index for S0 coloring
    plot_all_parameters(S0, S1_aligned, S2_aligned, S3, DoLP, AoLP, delta_degrees, theta_degrees, bg_mask, utils.TARGET_CHANNEL_IDX)

    print("--- Finished ---")

if __name__ == "__main__":
    main()