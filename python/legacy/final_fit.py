import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Import shared functions and configs
import final_utils as utils

try:
    matplotlib.use('TkAgg')
except:
    pass


# =============================================================================
# INTERACTIVE DEBUGGER
# =============================================================================

def run_interactive_debug(angles_rad_2x, image_stack, S0, S1, S2):
    """Launches the interactive window for pixel fit debugging with Stokes Ellipse."""
    print("Avvio del Debugger Interattivo...")

    num_frames, H, W = image_stack.shape
    selected_pixel = [W // 2, H // 2]  # Start at the center

    # Increased figure width to accommodate 3 subplots
    fig = plt.figure(figsize=(18, 6), num="Interactive Pixel Debugger")

    ax_img = fig.add_subplot(131)
    ax_plot = fig.add_subplot(132)
    ax_ellipse = fig.add_subplot(133)

    # --- Setup Left: Image ---
    vmax = np.percentile(image_stack, 99)
    img_display = ax_img.imshow(image_stack[0], cmap='gray', vmin=0, vmax=vmax)
    ax_img.set_title(f"Clicca per selezionare un pixel\nRisoluzione: {W}x{H}")
    ax_img.axis('off')

    # Marker for selected pixel
    pixel_marker, = ax_img.plot(selected_pixel[0], selected_pixel[1], 'r+', markersize=12, markeredgewidth=2)

    # --- Setup Middle: Cartesian Fit Plot ---
    analyzer_angles_deg = np.degrees(angles_rad_2x) / 2.0
    plot_limit_angle = max(180, np.max(analyzer_angles_deg) if len(analyzer_angles_deg) > 0 else 180)

    meas_scatter, = ax_plot.plot([], [], 'ro', label='Intensità Misurata', zorder=5)
    fit_line, = ax_plot.plot([], [], 'b-', label='Fit: 0.5*(S0 + S1cos2A + S2sin2A)', linewidth=2, zorder=4)
    current_indicator, = ax_plot.plot([], [], 'yo', markersize=10, markeredgecolor='black', label='Frame Corrente',
                                      zorder=10)

    ax_plot.set_xlabel("Angolo Analizzatore (Gradi)")
    ax_plot.set_ylabel("Intensità (DN)")
    ax_plot.legend(loc='upper right')
    ax_plot.grid(True, linestyle='--', alpha=0.5)

    # --- Setup Right: Stokes Ellipse ---
    ellipse_line, = ax_ellipse.plot([], [], 'g-', linewidth=2, label='Polarization Ellipse', zorder=4)
    major_axis_line, = ax_ellipse.plot([], [], 'r--', linewidth=1.5, label='AoLP Axis', zorder=5)

    ax_ellipse.set_aspect('equal', adjustable='box')
    ax_ellipse.grid(True, linestyle='--', alpha=0.5)
    ax_ellipse.legend(loc='upper right')
    ax_ellipse.set_xlabel("X Intensity")
    ax_ellipse.set_ylabel("Y Intensity")

    def update_pixel_data(x, y):
        selected_pixel[0], selected_pixel[1] = x, y
        pixel_marker.set_data([x], [y])

        # 1. Update Intensity Fit Plot
        intensities = image_stack[:, y, x]
        meas_scatter.set_data(analyzer_angles_deg, intensities)

        s0_val, s1_val, s2_val = S0[y, x], S1[y, x], S2[y, x]
        dense_x_deg = np.linspace(0, plot_limit_angle, 200)
        dense_x_rad_2 = np.deg2rad(dense_x_deg * 2)
        fit_y = 0.5 * (s0_val + s1_val * np.cos(dense_x_rad_2) + s2_val * np.sin(dense_x_rad_2))
        fit_line.set_data(dense_x_deg, fit_y)

        ax_plot.set_title(f"Pixel ({x}, {y}) | S0={s0_val:.0f}, S1={s1_val:.0f}, S2={s2_val:.0f}")

        y_max = max(np.max(intensities), np.max(fit_y)) * 1.1
        ax_plot.set_xlim(-5, plot_limit_angle + 5)
        ax_plot.set_ylim(0, y_max)

        # 2. Update Stokes Ellipse Plot
        # Calculate Polarization parameters
        s0_safe = s0_val if s0_val > 0 else 1e-8
        dolp = np.clip(np.sqrt(s1_val ** 2 + s2_val ** 2) / s0_safe, 0, 1)
        aolp_rad = 0.5 * np.arctan2(s2_val, s1_val)

        # Semi-major (A) and semi-minor (B) axes for partial polarization representation
        A = np.sqrt(0.5 * s0_safe * (1 + dolp))
        B = np.sqrt(0.5 * s0_safe * (1 - dolp))

        # Parametric equations for the rotated ellipse
        t = np.linspace(0, 2 * np.pi, 150)
        x_ell = A * np.cos(t) * np.cos(aolp_rad) - B * np.sin(t) * np.sin(aolp_rad)
        y_ell = A * np.cos(t) * np.sin(aolp_rad) + B * np.sin(t) * np.cos(aolp_rad)

        ellipse_line.set_data(x_ell, y_ell)

        # Draw the major axis line to visually indicate AoLP
        x_maj = [-A * np.cos(aolp_rad), A * np.cos(aolp_rad)]
        y_maj = [-A * np.sin(aolp_rad), A * np.sin(aolp_rad)]
        major_axis_line.set_data(x_maj, y_maj)

        # Dynamically scale the ellipse viewport based on total intensity
        lim = np.sqrt(s0_safe) * 1.1 + 1e-5
        ax_ellipse.set_xlim(-lim, lim)
        ax_ellipse.set_ylim(-lim, lim)

        ax_ellipse.set_title(f"DoLP: {dolp:.2%} | AoLP: {np.degrees(aolp_rad):.1f}°")

        fig.canvas.draw_idle()

    def update_animation(frame):
        idx = frame % num_frames
        img_display.set_data(image_stack[idx])

        cur_ang_deg = np.degrees(angles_rad_2x[idx]) / 2.0
        x, y = selected_pixel
        s0, s1, s2 = S0[y, x], S1[y, x], S2[y, x]
        cur_ang_rad_2 = angles_rad_2x[idx]
        cur_intensity = 0.5 * (s0 + s1 * np.cos(cur_ang_rad_2) + s2 * np.sin(cur_ang_rad_2))

        current_indicator.set_data([cur_ang_deg], [cur_intensity])
        return img_display, current_indicator, pixel_marker

    def onclick(event):
        if event.inaxes == ax_img:
            x = int(np.clip(event.xdata, 0, W - 1))
            y = int(np.clip(event.ydata, 0, H - 1))
            update_pixel_data(x, y)

    # Initialize with the central pixel
    update_pixel_data(W // 2, H // 2)

    anim = FuncAnimation(fig, update_animation, frames=range(20000), interval=200, blit=False, cache_frame_data=False)
    fig.canvas.mpl_connect('button_press_event', onclick)

    return anim


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("--- Avvio Fit Interattivo ---")

    # Now using DOWNSAMPLE_FACTOR from utils instead of hardcoded 1
    angles, stack = utils.load_rotation_sequence(
        utils.POL_SUBFOLDER,
        utils.TARGET_CHANNEL_IDX,
        downsample_factor=utils.DOWNSAMPLE_FACTOR,
        invert_angles=False
    )

    if stack is None or angles is None:
        print("Interruzione: Dati non caricati correttamente.")
        return

    S0, S1, S2 = utils.calculate_linear_stokes(angles, stack)

    # Global reference to prevent garbage collection
    global anim
    anim = run_interactive_debug(angles, stack, S0, S1, S2)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()