"""Fit di dispersione spettrale `f(λ) = k / λ^p` per polarimetria 2D.

Modello unico parametrico in `p`:
    * `p = 1`: ritardo di fase di lamina d'onda zero-order (quarzo Δn ≈ cost,
      δ = 2π·Δn·d / λ → δ ∝ 1/λ).
    * `p = 2`: angolo di rotazione ottica per attività ottica naturale
      (es. soluzione zuccherina, regola di Drude ψ ∝ 1/λ²).

L'utility `plot_dispersion_fit` genera una figura 1-pannello stile tesi:
scatter colorato per canale RGB (+ eventuale punto di design) e curva fit
tratteggiata; titolo con formula e R².
"""
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from .plotting import fmt_sci, save_and_show


CHANNEL_COLORS = {'R': 'tab:red', 'G': 'tab:green', 'B': 'tab:blue'}


def _inverse_power(x, k, power):
    return k / (x ** power)


def fit_inverse_lambda(lambdas_nm, values, power=1):
    """Fitta `values = k / λ^power` via least-squares non lineare.

    Restituisce dict con `k`, `k_err`, `r2`, `power`, `lambdas`, `values`,
    `n_points`. Se meno di 2 punti, `k = nan`.
    """
    lambdas = np.asarray(lambdas_nm, dtype=float)
    vals = np.asarray(values, dtype=float)
    n_points = int(lambdas.size)
    if n_points < 2:
        return {
            'k': float('nan'), 'k_err': float('nan'), 'r2': float('nan'),
            'power': int(power), 'lambdas': lambdas, 'values': vals,
            'n_points': n_points,
        }
    popt, pcov = curve_fit(
        lambda x, k: _inverse_power(x, k, power), lambdas, vals)
    k = float(popt[0])
    k_err = float(np.sqrt(pcov[0, 0]))
    pred = _inverse_power(lambdas, k, power)
    ss_res = float(np.sum((vals - pred) ** 2))
    ss_tot = float(np.sum((vals - vals.mean()) ** 2))
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 0 else float('nan')
    return {
        'k': k, 'k_err': k_err, 'r2': r2, 'power': int(power),
        'lambdas': lambdas, 'values': vals, 'n_points': n_points,
    }


def plot_s3_calibration(channel_lambdas, delta_measured_deg, quartz_func, *,
                        design_point=None,
                        out_pdf=None, show=True,
                        figsize=(4.4, 3.6),
                        lambda_range=(445.0, 650.0)):
    """Figura di calibrazione di δ_a dell'analizzatore λ/4.

    Mostra la ritardanza MISURATA per canale (punti RGB), il modello di quarzo
    come riscontro indipendente (curva tratteggiata, NON un fit ai punti) e il
    punto di design. La legenda riporta il fattore di correzione 1/sin δ_a.

    `channel_lambdas`, `delta_measured_deg`: dict {'R'/'G'/'B': valore}.
    `quartz_func`: callable λ_nm -> δ_deg (modello di quarzo).
    `design_point`: dict {'lambda_nm', 'value'} opzionale (diamond nero).
    """
    fig, ax = plt.subplots(figsize=figsize)

    x_curve = np.linspace(lambda_range[0], lambda_range[1], 400)
    y_curve = np.array([quartz_func(x) for x in x_curve])
    ax.plot(x_curve, y_curve, color='black', linestyle='--', linewidth=1.0,
            zorder=2, label='modello di quarzo (riscontro)')

    for ch in ('R', 'G', 'B'):
        if ch not in channel_lambdas or ch not in delta_measured_deg:
            continue
        lam = channel_lambdas[ch]
        d = delta_measured_deg[ch]
        corr = 1.0 / np.sin(np.radians(d))
        ax.scatter(lam, d, color=CHANNEL_COLORS[ch], s=46, marker='o',
                   zorder=4, edgecolors='black', linewidths=0.5,
                   label=f"{ch} ({lam:.0f} nm): "
                         rf"$\delta_a={d:.1f}\degree$, $1/\sin\delta_a={corr:.3f}$")

    if design_point is not None:
        ax.scatter([design_point['lambda_nm']], [design_point['value']],
                   color='black', s=46, marker='D', zorder=4,
                   edgecolors='black', linewidths=0.7,
                   label=f"design ({design_point['lambda_nm']:.0f} nm, "
                         rf"$90\degree$)")

    ax.set_xlabel(r"Lunghezza d'onda $\lambda$ (nm)")
    ax.set_ylabel(r'Ritardanza $\delta_a$ ($\degree$)')
    ax.set_title(r'Calibrazione di $\delta_a$: misura vs modello di quarzo',
                 fontsize=9, pad=4)
    ax.set_xlim(lambda_range[0], lambda_range[1])
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=7, framealpha=0.85)
    fig.tight_layout()

    if out_pdf is not None:
        os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
        save_and_show(fig, out_pdf, show=show, fmt='pdf')
    elif show:
        plt.show()
    plt.close(fig)


def plot_dispersion_fit(fit, *,
                         channel_labels,
                         design_point=None,
                         xlabel=r"Lunghezza d'onda $\lambda$ (nm)",
                         ylabel=r'valore $y$',
                         var_tex='y',
                         out_pdf=None,
                         show=True,
                         figsize=(3.5, 3.5),
                         x_curve_range=(150.0, 1100.0),
                         legend_loc='best',
                         legend_value_fmt='{:.1f}',
                         legend_value_unit='',
                         y_pad_frac=1.3,
                         x_lim=(0.0, 1100.0)):
    """Plot scatter RGB + curva fit. Titolo = `Fit: y = k/λ^p, R² = ...`.

    `fit` viene da `fit_inverse_lambda`. `channel_labels` deve essere lista
    della stessa lunghezza di `fit['lambdas']` esclusa la design anchor (che
    viene aggiunta in coda da chi compone i punti). `design_point` opzionale:
    dict {'lambda_nm', 'value', 'label'} — disegnato come diamond nero.
    """
    fig, ax = plt.subplots(figsize=figsize)
    lambdas = fit['lambdas']
    values = fit['values']

    for lam, val, lbl in zip(lambdas, values, channel_labels):
        if lbl == 'design':
            continue
        color = CHANNEL_COLORS.get(lbl, 'gray')
        legend = f"{lbl} ({lam:.0f} nm, {legend_value_fmt.format(val)}{legend_value_unit})"
        ax.scatter(lam, val, color=color, s=42, marker='o',
                   zorder=3, edgecolors='none', label=legend)

    if design_point is not None:
        ax.scatter([design_point['lambda_nm']], [design_point['value']],
                   color='black', s=42, marker='D', zorder=3,
                   edgecolors='black', linewidths=0.7,
                   label=f"design ({design_point['lambda_nm']:.0f} nm, "
                         f"{legend_value_fmt.format(design_point['value'])}"
                         f"{legend_value_unit})")

    if np.isfinite(fit['k']):
        x_curve = np.linspace(*x_curve_range, 500)
        ax.plot(x_curve, _inverse_power(x_curve, fit['k'], fit['power']),
                color='black', linestyle='--', linewidth=1.0, zorder=2)
        k_str = fmt_sci(fit['k'])
        power_tex = f"\\lambda^{{{fit['power']}}}" if fit['power'] != 1 else r"\lambda"
        title = (rf"Fit: ${var_tex}(\lambda) = {k_str}/{power_tex}$,  "
                 rf"$R^2 = {fit['r2']:.4f}$")
    else:
        title = "Fit non eseguito (<2 punti validi)"

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=9, pad=4)
    ax.set_xlim(*x_lim)
    if values.size:
        all_vals = list(values)
        if design_point is not None:
            all_vals.append(design_point['value'])
        vmin, vmax = min(all_vals), max(all_vals)
        if vmin >= 0:
            ax.set_ylim(0, vmax * y_pad_frac)
        elif vmax <= 0:
            ax.set_ylim(vmin * y_pad_frac, 0)
        else:
            pad = max(abs(vmin), abs(vmax)) * (y_pad_frac - 1.0)
            ax.set_ylim(vmin - pad, vmax + pad)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.axhline(0.0, color='gray', linewidth=0.6, alpha=0.5)
    ax.legend(loc=legend_loc, fontsize=7, framealpha=0.85)
    fig.tight_layout()

    if out_pdf is not None:
        os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
        save_and_show(fig, out_pdf, show=show, fmt='pdf')
    elif show:
        plt.show()
    plt.close(fig)
    return fit
