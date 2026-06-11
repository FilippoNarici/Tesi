"""delta_a(lambda) PUNTO FISSO, pipeline-consistente, depol-unbiased.

La piu' rigorosa: il delta_a corretto e' quello AUTO-COERENTE con la pipeline
ESATTA usata su tutti i dataset (ellitticita' LCD via rotazione di Poincare,
NON sottrazione), letto con stima depol-UNBIASED (direzione del vettore di
Stokes, robusta alla depol scalare). sample==analizzatore => delta=delta_a.

Iterazione per canale (input (1,0,0) dopo gli allineamenti):
  delta_a -> S3_c = S3_raw / sin(delta_a)
          -> align_reference_frame(S1,S2)            (ruota S1<->S2)
          -> align_poincare_ellipticity(S1,S3_c)     (ruota S1<->S3, toglie LCD)
          -> mediana ROI vincente di (s1,s2,s3)
          -> delta dalla DIREZIONE u=s/|s| (depol-unbiased)
          -> nuovo delta_a. Ripeti a convergenza (punto fisso).

beta di Poincare e' ~indipendente da delta_a (sfondo: il fattore sin(delta_a)
si cancella, lo sfondo non ha ritardatore) -> il punto fisso converge in pochi
passi. Confronto col modello quarzo (che NON entra nell'iterazione).

SCRIPT DI CALIBRAZIONE (mantenuto). Provenienza dei valori hardcodati in
`config.MEASURED_S3_RETARDANCE_DEG`. Rieseguire SOLO se cambia l'hardware
(lamina, sorgente, sensore) o le lunghezze d'onda effettive dei canali, poi
copiare i delta_a stampati in `config.MEASURED_S3_RETARDANCE_DEG`. Richiede la
cache UMAP di `lambdaquarti_50deg` (ROI del cluster vincente). Vedi
`python/S3_CALIBRATION.md` per il contesto completo.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polarimetro import (
    stokes as st,
    align as al,
    mask as mk,
    umap_runner as um,
    reset_saturation_accumulator,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
RAWROOT = os.path.join(HERE, "raw")
DATASET = "lambdaquarti_50deg"
DS = 4
CH_IDX = {"R": 0, "G": 1, "B": 2}
LAMBDA = {0: 626.0, 1: 536.0, 2: 466.0}
DESIGN = 633.0
DARK = os.path.join(RAWROOT, "dark.dng")


def winner_roi(ch, S0_shape):
    d = np.load(os.path.join(OUT, f"umap_{DATASET}_{ch}_nobg_cache.npz"),
                allow_pickle=False)
    cm, info, wi, _ = um.cluster_umap_hdbscan_by_delta(
        d["embedding"], d["delta_deg"], d["valid_indices"],
        tuple(int(x) for x in d["S0_shape"]), min_cluster_size=100)
    d.close()
    return cm[wi]


def direction_delta(s1, s2, s3):
    """delta dalla DIREZIONE (depol-unbiased) da componenti mediane. [0,180]."""
    norm = np.sqrt(s1**2 + s2**2 + s3**2)
    u1, u2, u3 = s1 / norm, s2 / norm, s3 / norm
    two_t = np.arctan2(1.0 - u1, u2)
    s2t = np.sin(two_t)
    cosd = np.clip(1.0 - (1.0 - u1) / max(s2t**2, 1e-6), -1.0, 1.0)
    sind = np.clip(u3 / (s2t if abs(s2t) > 1e-3 else np.sign(s2t) * 1e-3),
                   -1.0, 1.0)
    d = np.degrees(np.arctan2(sind, cosd)) % 360.0
    return 360.0 - d if d > 180.0 else d


def main():
    reset_saturation_accumulator()
    pol = os.path.join(RAWROOT, DATASET, "pol")
    wav = os.path.join(RAWROOT, DATASET, "wav")
    ch_list = [0, 1, 2]

    angles, lin_rgb = st.calculate_linear_stokes_rgb_streaming(
        pol, channel_indices=ch_list, downsample_factor=DS,
        invert_angles=False, dark_frame_path=DARK)
    s3_rgb = st.calculate_s3_rgb(
        wav, channel_indices=ch_list, downsample_factor=DS,
        wavelengths_per_ch=LAMBDA, dark_frame_path=DARK)
    S0_mean = np.mean([lin_rgb[ci][0] for ci in ch_list], axis=0)
    bg = mk.generate_background_mask(S0_mean, downsample_factor=DS)

    print("\n" + "=" * 92)
    print("delta_a PUNTO FISSO (pipeline-consistente, Poincare reale, depol-unbiased)")
    print("Iterazione self-consistent; quarzo mostrato solo per confronto (non entra).")
    print("=" * 92)
    print(f"{'ch':>3}{'lam':>5} | {'iter (delta_a per passo)':<34} | "
          f"{'d_a*':>7}{'1/sin':>7} | {'d_quar':>7}{'1/sinQ':>7} | {'DoP':>5}")
    print("-" * 92)

    final = {}
    for ch, ci in CH_IDX.items():
        S0, S1, S2 = lin_rgb[ci]
        S3_q, wav_int = s3_rgb[ci]
        lam = LAMBDA[ci]
        dq = float(np.degrees(st.waveplate_retardance(lam, DESIGN, order=0.25)))
        S3_raw = S3_q * np.sin(np.radians(dq))

        roi = winner_roi(ch, S0.shape)
        S0s = np.where(S0 == 0, 1e-8, S0)
        S1_a, S2_a = al.align_reference_frame(S1, S2, bg)
        s2 = float(np.median((S2_a / S0s)[roi]))
        dop = float(np.median(
            np.sqrt((S1_a/S0s)**2 + (S2_a/S0s)**2 + (S3_raw/S0s)**2)[roi]))

        d_a = dq  # innesco
        hist = []
        for _ in range(25):
            sin_da = np.sin(np.radians(d_a))
            if abs(sin_da) < 1e-3:
                sin_da = np.sign(sin_da) * 1e-3
            S3_c = S3_raw / sin_da
            S1_b, S3_b, _ = al.align_poincare_ellipticity(
                S0, S1_a, S3_c, bg, downsample_factor=DS,
                wav_intensity=wav_int, return_mask=True)
            s1 = float(np.median((S1_b / S0s)[roi]))
            s3 = float(np.median((S3_b / S0s)[roi]))
            d_new = direction_delta(s1, s2, s3)
            hist.append(d_new)
            if abs(d_new - d_a) < 0.02:
                d_a = d_new
                break
            d_a = 0.5 * d_a + 0.5 * d_new  # damping
        final[ch] = d_a
        corr = 1.0 / np.sin(np.radians(d_a))
        corrq = 1.0 / np.sin(np.radians(dq))
        itxt = " ".join(f"{h:.1f}" for h in hist[:6])
        print(f"{ch:>3}{lam:>5.0f} | {itxt:<34} | {d_a:>7.1f}{corr:>7.3f} | "
              f"{dq:>7.1f}{corrq:>7.3f} | {dop:>5.2f}")

    print("-" * 92)
    print("Da hardcodare in stokes.py (calculate_s3 / calculate_s3_rgb):")
    for ch in ("R", "G", "B"):
        print(f"  {ch} ({LAMBDA[CH_IDX[ch]]:.0f} nm): delta_a = {final[ch]:.1f} deg, "
              f"1/sin = {1.0/np.sin(np.radians(final[ch])):.4f}")


if __name__ == "__main__":
    main()
