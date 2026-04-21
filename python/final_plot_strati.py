import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

import final_utils as utils

# =============================================================================
# GESTIONE PERCORSI (Coerente con la struttura del progetto)
# =============================================================================
# Risale di un livello rispetto alla posizione dello script (es. da /python/ a /)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'Images', 'generated', 'strati_fit')
os.makedirs(OUT_DIR, exist_ok=True)
WAVELENGTHS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'outputs', 'rgb_wavelengths.csv')

# =============================================================================
# STILE PUBBLICAZIONE (Coerente con final_thesis_figure.py)
# =============================================================================
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'text.usetex': False,
    'mathtext.fontset': 'cm',
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'image.interpolation': 'none',
})

# =============================================================================
# DATI DI INPUT
# =============================================================================
# Numero di strati di nastro adesivo per ciascun punto di misura.
n_strati = np.array([1, 2, 3, 4, 5, 4, 3, 2, 1])

# Fasi srotolate misurate sulle mappe di retardance (gradi).
# NOTA: questi valori vanno rimisurati manualmente dalle mappe prodotte dalla
# pipeline arctan2 [0, 360) (B1). I numeri qui sotto sono placeholder derivati
# dalla vecchia pipeline arccos e NON devono essere usati per conclusioni.
delta_unwrap_R = np.array([229, 463, 720, 959, 1205, 964, 720, 488, 238])
delta_unwrap_G = np.array([274, 559, 825, 1129, 1415, 1140, 841, 544, 280])
delta_unwrap_B = np.array([328, 652, 947, 1249, 1576, 1258, 991, 677, 336])

# Lunghezze d'onda centroide dei canali RGB (nm), lette da outputs/rgb_wavelengths.csv.
lambda_R = utils.get_channel_wavelength(WAVELENGTHS_CSV, 0)
lambda_G = utils.get_channel_wavelength(WAVELENGTHS_CSV, 1)
lambda_B = utils.get_channel_wavelength(WAVELENGTHS_CSV, 2)
lambdas = np.array([lambda_R, lambda_G, lambda_B])


# =============================================================================
# FUNZIONI DI FIT
# =============================================================================
def linear_fit_zero_intercept(x, m):
    return m * x


def inverse_fit(x, k):
    return k / x


def format_scientific(value):
    """Formatta un numero in notazione scientifica per LaTeX (1 cifra decimale)."""
    exponent = int(np.floor(np.log10(abs(value))))
    coeff = value / (10 ** exponent)
    return rf"{coeff:.1f} \cdot 10^{{{exponent}}}"


# =============================================================================
# GENERAZIONE GRAFICI
# =============================================================================

def generate_fit_strati():
    """Genera il plot dei fit lineari per i tre canali."""
    fig, ax = plt.subplots(figsize=(3.35, 3.35))
    colors = {'R': 'tab:red', 'G': 'tab:green', 'B': 'tab:blue'}
    slopes = []

    datasets = [
        ('R', delta_unwrap_R, colors['R']),
        ('G', delta_unwrap_G, colors['G']),
        ('B', delta_unwrap_B, colors['B'])
    ]

    for label, y_data, color in datasets:
        popt, _ = curve_fit(linear_fit_zero_intercept, n_strati, y_data)
        slope = popt[0]
        slopes.append(slope)

        ax.scatter(n_strati, y_data, color=color, s=15, zorder=3, alpha=0.8)

        x_fit = np.linspace(0, 5.5, 100)
        y_fit = linear_fit_zero_intercept(x_fit, slope)
        ax.plot(x_fit, y_fit, color=color, linestyle='--', linewidth=1.2,
                label=rf'{label}: $\delta_{label} \approx {slope:.1f}^\circ/n$', zorder=2)

    ax.set_xlabel('Numero di strati $n$')
    ax.set_ylabel(r'Ritardo di fase srotolato $\delta_{unwrap}$ (°)')
    ax.set_xlim(0, 5.5)
    ax.set_ylim(0, 1900)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left')

    out_path = os.path.join(OUT_DIR, 'fit_strati_linear.pdf')
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Salvato: {out_path}")
    return np.array(slopes)


def generate_fit_lambda(slopes):
    """Genera il plot del fit 1/lambda con k in notazione scientifica."""
    fig, ax = plt.subplots(figsize=(3.35, 3.35))

    popt, _ = curve_fit(inverse_fit, lambdas, slopes)
    k = popt[0]
    k_str = format_scientific(k)

    # Plot dei punti RGB
    ax.scatter(lambdas[0], slopes[0], color='tab:red', s=25, zorder=3, label='R')
    ax.scatter(lambdas[1], slopes[1], color='tab:green', s=25, zorder=3, label='G')
    ax.scatter(lambdas[2], slopes[2], color='tab:blue', s=25, zorder=3, label='B')

    # Plot curva di fit
    x_fit = np.linspace(150, 1100, 500)
    y_fit = inverse_fit(x_fit, k)

    ax.plot(x_fit, y_fit, color='black', linestyle='--', linewidth=1.2,
            label=rf'Fit: $\delta(\lambda) = \frac{{{k_str}}}{{\lambda}}$', zorder=2)

    ax.set_xlabel(r'Lunghezza d\'onda $\lambda$ (nm)')
    ax.set_ylabel(r'Ritardo specifico $\delta$ (°/strato)')
    ax.set_xlim(0, 1100)
    ax.set_ylim(0, 1050)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right')

    out_path = os.path.join(OUT_DIR, 'fit_lambda_inverse.pdf')
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Salvato: {out_path}")


if __name__ == '__main__':
    print(f"Cartella di output: {OUT_DIR}")
    computed_slopes = generate_fit_strati()
    generate_fit_lambda(computed_slopes)