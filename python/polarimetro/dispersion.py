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


def fit_multiorder_waveplate(lambdas_nm, deltas_deg, dn_func,
                             design_wavelength_nm=633.0,
                             d_min_nm=5.0e3, d_max_nm=2.0e6, d_step_nm=20.0):
    """Fit brute-force dello spessore `d` di una lamina d'onda multi-ordine.

    Modello: la ritardanza totale e' `delta_tot(lambda) = 360 * dn(lambda) * d
    / lambda` (gradi), mentre la misura restituisce il solo residuo
    `delta_tot mod 360`. Si scandisce `d` in `[d_min_nm, d_max_nm]` con passo
    `d_step_nm` e si minimizza il residuo circolare RMS fra il predetto avvolto
    e i `deltas_deg` misurati.

    `dn_func(lambda_nm)` restituisce la birifrangenza Delta_n alla lunghezza
    d'onda data (es. `polarimetro.quartz_birefringence`).

    Restituisce dict: `d_nm`, `order` (ordine a `design_wavelength_nm`),
    `rms_deg`, `pred_deg` (predetto avvolto ai lambda misurati), `lambdas`,
    `deltas`, `dn`, `design_wavelength_nm`.
    """
    lambdas = np.asarray(lambdas_nm, dtype=float)
    meas = np.asarray(deltas_deg, dtype=float)
    if lambdas.size < 2:
        return {'d_nm': float('nan'), 'order': float('nan'),
                'rms_deg': float('nan'), 'pred_deg': None,
                'lambdas': lambdas, 'deltas': meas, 'dn': None,
                'design_wavelength_nm': design_wavelength_nm}
    dn = np.array([dn_func(float(l)) for l in lambdas])
    dn0 = dn_func(float(design_wavelength_nm))
    ds = np.arange(d_min_nm, d_max_nm, d_step_nm)

    def _circ_dist(a, b):
        return np.abs((a - b + 180.0) % 360.0 - 180.0)

    best_d, best_rms, best_pred = float('nan'), float('inf'), None
    for d in ds:
        pred = (360.0 * dn * d / lambdas) % 360.0
        rms = float(np.sqrt(np.mean(_circ_dist(pred, meas) ** 2)))
        if rms < best_rms:
            best_d, best_rms, best_pred = float(d), rms, pred
    order = 360.0 * dn0 * best_d / float(design_wavelength_nm) / 360.0
    return {
        'd_nm': best_d, 'order': order, 'rms_deg': best_rms,
        'pred_deg': best_pred, 'lambdas': lambdas, 'deltas': meas,
        'dn': dn, 'design_wavelength_nm': float(design_wavelength_nm),
    }


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
        ax.set_ylim(0, max(all_vals) * y_pad_frac)
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
