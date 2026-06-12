# Riscontro polimeri vs quarzo per la dispersione della lamina lambda/4 (journal, NON tesi).
# Domanda (utente 2026-06-12): il riscontro col quarzo ha senso se la lamina e' quasi
# certamente un polimero? Proviamo PMMA e polimeri comuni da film ritardatori.
#
# Modello: lamina singolo-ordine  delta(lambda) = A * Dn_rel(lambda) / lambda
#   - "anchored": A fissata dal design (delta=90 @ 633 nm)
#   - "free k":   A fittata ai 3 punti misurati (confronto di sola FORMA della dispersione)
# Dn_rel per i polimeri: Cauchy a 1 parametro  Dn(l) = 1 + b/l^2  calibrata sul
# rapporto di letteratura R450 = Dn(450)/Dn(550) (convenzione film ritardatori LCD).
# Quarzo: Sellmeier di Ghosh esatto (polarimetro.stokes.quartz_birefringence).

import numpy as np
import sys

sys.path.insert(0, '.')
from polarimetro.stokes import quartz_birefringence

LAMBDAS = np.array([626.0, 536.0, 466.0])      # nm, centroidi R/G/B
MEASURED = np.array([88.4, 111.0, 130.8])      # deg, delta_a self-ref (S3_CALIBRATION.md)
DESIGN_L, DESIGN_D = 633.0, 90.0

# R450 = Dn(450)/Dn(550): PC 1.08 (lett., bisfenolo-A); COP ~1.005 (piatto, Zeonor);
# PMMA ~1.03 (debole, approssimativo); PS ~1.10 (aromatico, approssimativo);
# 'geometrico' = nessuna dispersione (solo 1/lambda).
MATERIALS = {
    'geometrico (Dn piatto)': None,
    'COP / Zeonor (R450~1.005)': 1.005,
    'PMMA (R450~1.03 appr.)': 1.03,
    'quarzo (Ghosh esatto)': 'quartz',
    'PC bisfenolo-A (R450=1.08)': 1.08,
    'PS (R450~1.10 appr.)': 1.10,
}


def cauchy_b_from_r450(r450):
    """b tale che (1+b/450^2)/(1+b/550^2) = r450."""
    num = r450 - 1.0
    den = 1.0 / 450.0**2 - r450 / 550.0**2
    return num / den


def dn_rel(lam, spec):
    if spec is None:
        return np.ones_like(np.asarray(lam, dtype=float))
    if spec == 'quartz':
        return np.array([quartz_birefringence(l) for l in np.atleast_1d(lam)])
    b = cauchy_b_from_r450(spec)
    return 1.0 + b / np.asarray(lam, dtype=float) ** 2


def predict(lam, spec, amplitude):
    return amplitude * dn_rel(lam, spec) / np.asarray(lam, dtype=float)


print(f"misurato (R/G/B): {MEASURED}")
print(f"{'materiale':28s} {'delta R/G/B anchored':>24s} {'RMS_anch':>8s} {'RMS_freek':>9s}")
for name, spec in MATERIALS.items():
    # anchored al design 90 @ 633
    A_anch = DESIGN_D * DESIGN_L / dn_rel(np.array([DESIGN_L]), spec)[0]
    d_anch = predict(LAMBDAS, spec, A_anch)
    rms_anch = np.sqrt(np.mean((d_anch - MEASURED) ** 2))
    # free k: least squares su A (lineare)
    base = dn_rel(LAMBDAS, spec) / LAMBDAS
    A_free = np.sum(base * MEASURED) / np.sum(base ** 2)
    d_free = predict(LAMBDAS, spec, A_free)
    rms_free = np.sqrt(np.mean((d_free - MEASURED) ** 2))
    d_str = '/'.join(f'{v:6.1f}' for v in d_anch)
    print(f"{name:28s} {d_str:>24s} {rms_anch:8.2f} {rms_free:9.2f}")

# rapporti di dispersione impliciti nei dati (Dn ~ delta*lambda)
dn_meas = MEASURED * LAMBDAS
dn_meas = dn_meas / dn_meas[0]
print(f"\nDn_rel implicito misurato (R=1): G/R={dn_meas[1]:.4f}  B/R={dn_meas[2]:.4f}")
for name, spec in MATERIALS.items():
    d = dn_rel(LAMBDAS, spec)
    print(f"  {name:28s} G/R={d[1]/d[0]:.4f}  B/R={d[2]/d[0]:.4f}")
