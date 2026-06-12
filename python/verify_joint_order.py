# Indagine CONGIUNTA ordine+materiale per le due lamine (journal, NON tesi). 2026-06-12.
#
# Ipotesi utente da testare: ANCHE la lamba/4 e' multi-ordine (etichetta senza
# "zero-order" + stesso fornitore della lambda/2 multi-ordine).
#
# Novita' metodologica vs journal: modello a BANDA INTEGRATA con gli spettri
# reali per canale (spettri/r,g,b.csv), non monocromatico. Per una retardance
# vera delta_true(lambda) = D633 * [Dn_rel(lambda)/lambda] / [Dn_rel(633)/633]:
#   V_c = sum I_c(l) exp(i delta_true(l)) / sum I_c(l)
#   -> delta avvolta predetta = arg(V_c)  (cio' che la pipeline misura)
#   -> ritenzione di polarizzazione |V_c| (effetto banda; aliasing intra-banda)
# DoP predetta nel disco: DoP_bg * haze_c * sqrt(cos^2 2a + sin^2 2a * |V_c|^2)
# con a = angolo lamina-polarizzazione (34deg per w/4, 37deg per w/2).
# Il discriminatore: haze_c = DoP_disco / (DoP_bg * sqrt(...)) deve essere
# FISICO (<=1) e UGUALE fra le due lamine (stesso tipo di foglio).
# NB: se w/4 fosse zero-order (|V|~1) e w/2 ordine ~5, l'uguaglianza della DoP
# misurata fra le lamine richiederebbe una coincidenza; con ordini simili e'
# automatica. Questo test quantifica.

import numpy as np
import pandas as pd

CH = ('R', 'G', 'B')
LAM_EFF = {'R': 626.0, 'G': 536.0, 'B': 466.0}
DELTA_MEAS = {  # winner/self-ref, gradi avvolti [0,360)
    'q': {'R': 88.4, 'G': 111.0, 'B': 130.8},    # lambda/4 (self-ref)
    'h': {'R': 176.9, 'G': 156.8, 'B': 134.5},   # lambda/2 (winner)
}
ALPHA = {'q': 34.0, 'h': 37.0}   # angolo asse-polarizzazione (theta misurata)
DESIGN = {'q': 90.0, 'h': 180.0}

# --- spettri efficaci per canale (stesso schema della cella G0) -------------
# banda efficace = sensibilita' camera (S22 tele proxy) x spettro bianco sorgente
def load_spectra():
    cam = pd.read_csv('spettri/Samsung-Galaxy-S22-Rear-Telephoto-Camera.csv')
    src = pd.read_csv('spettri/rgb.csv', sep=';')
    src_lam = src['lambda'].values.astype(float)
    src_i = src['rgb'].values.astype(float)
    dark = np.median(src_i[src_lam < 380])
    src_i = np.clip(src_i - dark, 0, None)
    grid = np.arange(400.0, 720.0, 1.0)
    s = np.interp(grid, src_lam, src_i)
    out = {}
    for c, col in (('R', 'red'), ('G', 'green'), ('B', 'blue')):
        sens = np.interp(grid, cam['wavelength'].values.astype(float),
                         cam[col].values.astype(float))
        eff = np.clip(sens * s, 0, None)
        eff /= eff.sum()
        out[c] = (grid, eff)
    return out

SPEC = load_spectra()
for c in CH:
    g, i = SPEC[c]
    cen = (g * i).sum()
    print(f"banda {c}: centroide pieno {cen:.0f} nm")

# --- DoP misurate nel disco e nello sfondo dalle cache ----------------------
def disc_and_bg_dop(ds):
    # ~bg_mask include l'anello di sfondo eroso -> il disco va selezionato con
    # delta lontana dallo sfondo (delta_bg ~ 0/360), non con la sola maschera.
    z = np.load(f'./outputs/stokes_{ds}_DS4.npz', allow_pickle=True)
    out = {}
    for c in CH:
        S0, S1, S2, S3 = (z[f'{c}_{k}'] for k in ('S0', 'S1', 'S2', 'S3'))
        bg = z[f'{c}_bg_mask'].astype(bool)
        delta = z[f'{c}_delta']
        dop = np.sqrt(S1**2 + S2**2 + S3**2) / S0
        finite = np.isfinite(dop) & np.isfinite(S0) & np.isfinite(delta)
        bgok = bg & finite
        s0bg = np.nanmedian(S0[bgok])
        ddist = np.abs((delta + 180.0) % 360.0 - 180.0)   # distanza da 0/360
        disc = (~bg) & finite & (S0 > 0.3 * s0bg) & (ddist > 45.0)
        out[c] = (float(np.nanmedian(dop[disc])), float(np.nanmedian(dop[bgok])),
                  int(disc.sum()))
    return out

DOP = {'q': disc_and_bg_dop('lambdaquarti_50deg'),
       'h': disc_and_bg_dop('lambdamezzi_50deg')}
print('DoP misurate (disco | bg | n_pixel disco):')
for p in ('q', 'h'):
    print(' ', p, {c: f"{DOP[p][c][0]:.3f}|{DOP[p][c][1]:.3f}|{DOP[p][c][2]}" for c in CH})

# --- modello ----------------------------------------------------------------
def dn_rel(lam, b):
    return 1.0 + b / lam**2

def channel_response(b, d633_grid):
    """Per ogni canale: delta avvolta predetta e |V| su griglia di D633."""
    resp = {}
    for c in CH:
        lam, inten = SPEC[c]
        g = dn_rel(lam, b) / lam
        g = g / (dn_rel(633.0, b) / 633.0)        # g(633)=1
        ph = np.deg2rad(np.outer(d633_grid, g))   # [nD, nLam]
        V = (inten[None, :] * np.exp(1j * ph)).sum(axis=1)
        resp[c] = (np.rad2deg(np.angle(V)) % 360.0, np.abs(V))
    return resp

def ang_diff(a, b):
    return (a - b + 180.0) % 360.0 - 180.0

D_GRID = np.arange(10.0, 4400.0, 0.25)

# dispersioni candidate: b Cauchy; R450 = Dn(450)/Dn(550) equivalente.
# b NEGATIVI = dispersione INVERSA (reverse-dispersion retarder film, prodotto
# di massa per polarizzatori circolari OLED; Re450/Re550 commerciale 0.5-0.93).
B_GRID = [-150000.0, -135000.0, -120000.0, -100000.0, -75000.0, -50000.0,
          -25000.0, 0.0, 30000.0, 58475.0, 90000.0, 120000.0]

def r450(b):
    return dn_rel(450.0, b) / dn_rel(550.0, b)

# diagnostica: ritenzione di banda |V| per ordine (b=0), per canale
print('\n|V| (ritenzione banda, b=0) per ordine del ritardo a 633:')
resp0 = channel_response(0.0, np.array([360.0 * m + 180.0 for m in range(0, 9)]))
print('  ordine: ', '  '.join(f'{m}' for m in range(0, 9)))
for c in CH:
    print(f"  {c}: ", '  '.join(f"{v:.2f}" for v in resp0[c][1]))

results = []
for b in B_GRID:
    resp = channel_response(b, D_GRID)
    for p in ('q', 'h'):
        rms = np.sqrt(np.mean(
            [ang_diff(resp[c][0], DELTA_MEAS[p][c])**2 for c in CH], axis=0))
        # minimi per ramo d'ordine
        for m in range(0, 12):
            lo, hi = 360.0 * m, 360.0 * (m + 1)
            sel = (D_GRID >= lo) & (D_GRID < hi)
            if not sel.any():
                continue
            i = np.argmin(rms[sel])
            idx = np.where(sel)[0][i]
            if rms[idx] < 12.0:
                a2 = np.deg2rad(2 * ALPHA[p])
                haze = {}
                ok = True
                for c in CH:
                    Vc = resp[c][1][idx]
                    geom = np.sqrt(np.cos(a2)**2 + np.sin(a2)**2 * Vc**2)
                    dop_d, dop_bg = DOP[p][c][0], DOP[p][c][1]
                    hz = dop_d / (dop_bg * geom)
                    haze[c] = hz
                    if hz > 1.08:
                        ok = False
                results.append(dict(b=b, plate=p, m=m, D633=D_GRID[idx],
                                    rms=rms[idx], haze=haze, physical=ok,
                                    V={c: float(resp[c][1][idx]) for c in CH}))

res = pd.DataFrame(results)

print('\n=== rami d\'ordine compatibili per lamina (RMS<12; * = haze NON fisico >1.08) ===')
for p, lbl in (('q', 'lambda/4'), ('h', 'lambda/2')):
    sub = res[res.plate == p].sort_values('rms')
    print(f'\n{lbl}: misurato', DELTA_MEAS[p])
    for _, r in sub.head(14).iterrows():
        hz = '/'.join(f"{r.haze[c]:.2f}" for c in CH)
        flag = ' ' if r.physical else '*'
        print(f" {flag}b={r.b:>6.0f} (R450={r450(r.b):.3f})  ordine~{r.m:>2d}  "
              f"D633={r.D633:7.1f}  RMS={r.rms:5.2f}  haze RGB={hz}")

# --- accoppiamento: b ANCHE diverso (film stock diversi); haze uguale -------
print('\n=== soluzioni CONGIUNTE (b libero per lamina; score = RMS medio + 100*mismatch haze) ===')
joint = []
q_sols = res[(res.plate == 'q') & res.physical]
h_sols = res[(res.plate == 'h') & res.physical]
for _, rq in q_sols.iterrows():
    for _, rh in h_sols.iterrows():
        mism = np.sqrt(np.mean([(rq.haze[c] - rh.haze[c])**2 for c in CH]))
        score = 0.5 * (rq.rms + rh.rms) + 100.0 * mism
        joint.append(dict(b4=rq.b, b2=rh.b, m4=rq.m, m2=rh.m,
                          rms4=rq.rms, rms2=rh.rms,
                          D4=rq.D633, D2=rh.D633, mism=mism, score=score,
                          hq=rq.haze, hh=rh.haze))
if not joint:
    print('  (nessuna coppia fisica trovata)')
    raise SystemExit
jd = pd.DataFrame(joint).sort_values('score')
for _, r in jd.head(14).iterrows():
    hq = '/'.join(f"{r.hq[c]:.2f}" for c in CH)
    hh = '/'.join(f"{r.hh[c]:.2f}" for c in CH)
    print(f"b4={r.b4:>7.0f} b2={r.b2:>7.0f}  m4={r.m4:>2d} m2={r.m2:>2d}  "
          f"RMS {r.rms4:4.1f}/{r.rms2:4.1f}  haze q={hq} h={hh}  "
          f"mism={r.mism:.3f}  score={r.score:5.1f}  D633 {r.D4:.0f}/{r.D2:.0f}")

print('\nNota R450 equivalenti: ', {int(b): round(r450(b), 3) for b in B_GRID})

# --- chiusura loophole banda: |V| con le bande piu' STRETTE credibili --------
# (primarie pure del display r/g/b.csv, zero leakage camera). Se anche cosi'
# il multi-ordine depolarizzerebbe oltre il misurato, il rigetto e' robusto.
def load_primary(ch):
    df = pd.read_csv(f'spettri/{ch.lower()}.csv')
    lam = df.iloc[:, 0].values.astype(float)
    inten = df.iloc[:, 1].values.astype(float)
    dark = np.median(inten[lam < 380])
    inten = np.clip(inten - dark, 0, None)
    grid = np.arange(400.0, 720.0, 1.0)
    ig = np.interp(grid, lam, inten)
    ig /= ig.sum()
    return grid, ig

def fwhm(grid, inten):
    half = inten.max() / 2
    above = grid[inten >= half]
    return above.max() - above.min()

print('\nFWHM bande: modello G0 (camera x bianco) vs primarie pure:')
PRIM = {c: load_primary(c) for c in CH}
for c in CH:
    print(f"  {c}: G0 {fwhm(*SPEC[c]):.0f} nm | primaria {fwhm(*PRIM[c]):.0f} nm")

SPEC_BAK = dict(SPEC)
SPEC.update(PRIM)
respP = channel_response(0.0, np.array([360.0 * m + 180.0 for m in range(0, 9)]))
print('|V| con bande primarie (b=0), per ordine:')
print('  ordine: ', '  '.join(f'{m}' for m in range(0, 9)))
for c in CH:
    print(f"  {c}: ", '  '.join(f"{v:.2f}" for v in respP[c][1]))
SPEC.update(SPEC_BAK)
