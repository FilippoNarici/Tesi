"""Orchestratore Pass A + Pass B della pipeline Stokes.

Mattoni atomici per la cella Load+Stokes del notebook. La cella gestisce
solo lookup cache npz, threading (ThreadPoolExecutor), e logging finale.

Pass A: load RAW polarizzazione + Stokes lineari (S0/S1/S2) + S3 da lamina.
Pass B: align_reference_frame + align_poincare_ellipticity + DoLP/AoLP +
        retardance/theta. Pura, deterministica per un singolo canale.
"""
import os

import numpy as np

from . import (
    align as _align,
    config as _config,
    io_raw as _io_raw,
    mask as _mask,
    retardance as _retardance,
    stokes as _stokes,
)


def run_pass_a_unified(channels, channels_rgb, pol_subfolder, wav_subfolder,
                        downsample_factor, wavelengths_per_ch, dark_frame_path,
                        invert_angles=False):
    """Pass A streaming RGB: legge 38 file (36 pol + 2 wav) una sola volta.

    channels: lista label canali (es. ['R','G','B']).
    channels_rgb: mappa label → index (es. {'R':0,'G':1,'B':2}).
    wavelengths_per_ch: dict {ch_idx: λ_nm} usato per correzione S3.

    Restituisce raw_per_ch = {ch: {'S0','S1','S2','S3','wav_intensity','channel_idx'}}.
    """
    ch_idx_list = [channels_rgb[ch] for ch in channels]
    angles, lin_rgb = _stokes.calculate_linear_stokes_rgb_streaming(
        pol_subfolder, channel_indices=ch_idx_list,
        downsample_factor=downsample_factor, invert_angles=invert_angles,
        dark_frame_path=dark_frame_path)
    if lin_rgb is None:
        raise RuntimeError(
            f"calculate_linear_stokes_rgb_streaming fallita su {pol_subfolder}")
    s3_rgb = _stokes.calculate_s3_rgb(
        wav_subfolder, channel_indices=ch_idx_list,
        downsample_factor=downsample_factor,
        wavelengths_per_ch=wavelengths_per_ch,
        dark_frame_path=dark_frame_path)
    if s3_rgb is None:
        raise RuntimeError(f"calculate_s3_rgb fallita su {wav_subfolder}")
    raw_per_ch = {}
    for ch in channels:
        ci = channels_rgb[ch]
        S0, S1, S2 = lin_rgb[ci]
        S3, wav_int = s3_rgb[ci]
        raw_per_ch[ch] = {
            'S0': S0, 'S1': S1, 'S2': S2, 'S3': S3,
            'wav_intensity': wav_int, 'channel_idx': ci,
        }
    return raw_per_ch


def run_pass_a_per_channel(channels, channels_rgb, pol_subfolder, wav_subfolder,
                            downsample_factor, wavelengths_per_ch,
                            dark_frame_path, invert_angles=False):
    """Pass A sequenziale per-canale.

    Stessa struttura di run_pass_a_unified ma legge i file una volta per canale
    (lento, usato quando si processa un solo canale o quando non si vuole
    tenere in memoria tutti gli stack RGB simultaneamente).
    """
    raw_per_ch = {}
    for ch in channels:
        ci = channels_rgb[ch]
        print(f"\n=== Channel {ch} (idx={ci}) - Pass A: load + Stokes ===")
        angles, stack = _io_raw.load_rotation_sequence(
            pol_subfolder, ci,
            downsample_factor=downsample_factor,
            invert_angles=invert_angles,
            dark_frame_path=dark_frame_path)
        if angles is None or stack is None:
            raise RuntimeError(
                f"load_rotation_sequence fallita su {pol_subfolder}/ch{ci}")
        S0, S1, S2 = _stokes.calculate_linear_stokes(angles, stack)
        _stokes.reset_wav_intensity_cache()
        S3 = _stokes.calculate_s3(
            wav_subfolder, ci,
            downsample_factor=downsample_factor,
            wavelength=wavelengths_per_ch[ci],
            dark_frame_path=dark_frame_path)
        if S3 is None:
            raise RuntimeError(
                f"calculate_s3 fallita su {wav_subfolder}/ch{ci}")
        wav_int = _stokes.get_wav_intensity_cache()
        raw_per_ch[ch] = {
            'S0': S0, 'S1': S1, 'S2': S2, 'S3': S3,
            'wav_intensity': (wav_int.copy() if wav_int is not None else None),
            'channel_idx': ci,
        }
    return raw_per_ch


def compute_unified_bg_mask(raw_per_ch, channels, downsample_factor):
    """bg_mask unica da mean(S0) sui canali attivi (se len(channels) >= 2)."""
    S0_stack = np.stack([raw_per_ch[ch]['S0'] for ch in channels], axis=0)
    S0_mean = np.mean(S0_stack, axis=0)
    return _mask.generate_background_mask(
        S0_mean, downsample_factor=downsample_factor)


def process_channel(ch, raw_per_ch, bg_shared, downsample_factor,
                     target_folder):
    """Pass B per un canale: align (S3 + Poincaré) + DoLP/AoLP + retardance.

    raw_per_ch: dict prodotto da run_pass_a_*. bg_shared: bg_mask unificata o
    None (in tal caso ricalcolata localmente da S0). target_folder: passato a
    `calculate_retardance_and_fast_axis` (parametro riservato, inutilizzato dal
    2026-05-24: la correzione swap per-dataset e' stata rimossa).

    Restituisce (ch, processed_dict) per facile collect da ThreadPoolExecutor.
    """
    d = raw_per_ch[ch]
    bg = bg_shared if bg_shared is not None else _mask.generate_background_mask(
        d['S0'], downsample_factor=downsample_factor)
    S1_a, S2_a = _align.align_reference_frame(d['S1'], d['S2'], bg)
    S1_b, S3_b, poincare_bg = _align.align_poincare_ellipticity(
        d['S0'], S1_a, d['S3'], bg, downsample_factor=downsample_factor,
        wav_intensity=d['wav_intensity'], return_mask=True)
    DoLP, AoLP = _retardance.calculate_dolp_aolp(d['S0'], S1_b, S2_a)
    delta, theta = _retardance.calculate_retardance_and_fast_axis(
        d['S0'], S1_b, S2_a, S3_b, bg, target_folder=target_folder)
    return ch, {
        'S0': d['S0'], 'S1': S1_b, 'S2': S2_a, 'S3': S3_b,
        'bg_mask': bg, 'poincare_bg_mask': poincare_bg.copy(),
        'sat_mask': None,
        'DoLP': DoLP, 'AoLP': AoLP,
        'delta': delta, 'theta': theta,
        'wav_intensity': d['wav_intensity'],
        'channel_idx': d['channel_idx'],
    }


def apply_saturation_global(stokes_data, channels, downsample_factor):
    """Applica saturation mask globale OR (fra canali) come NaN-mask.

    Modifica `stokes_data` in place: setta NaN sui pixel saturati per S1, S2,
    S3, DoLP, AoLP, delta, theta in ogni canale, e aggiunge `sat_mask`.
    Restituisce (sat_mask, n_saturated) per logging dalla cella chiamante.
    """
    sat_mask = _io_raw.get_saturation_mask(downsample_factor)
    if sat_mask is None:
        return None, 0
    n_sat = int(sat_mask.sum())
    if n_sat == 0:
        return sat_mask, 0
    for ch in channels:
        d = stokes_data[ch]
        for k in ('S1', 'S2', 'S3', 'DoLP', 'AoLP', 'delta', 'theta'):
            d[k][sat_mask] = np.nan
        d['sat_mask'] = sat_mask
    return sat_mask, n_sat


def load_cache_npz(cache_path, dataset, downsample_factor, unified_mask,
                    channels, channels_rgb):
    """Carica stokes_data da cache npz se valida; altrimenti None.

    Schema accettato: chiavi `downsample_factor`, `dataset`, `unified_mask`,
    `{ch}_S0..S3`, `{ch}_bg_mask`, `{ch}_poincare_bg_mask`, `{ch}_DoLP`,
    `{ch}_AoLP`, `{ch}_delta`, `{ch}_theta`, opzionali `{ch}_sat_mask`,
    `{ch}_wav_intensity`. Verifica match DS + dataset + unified_mask + canali
    richiesti presenti. Restituisce dict o None.
    """
    if not os.path.exists(cache_path):
        return None
    try:
        npz = np.load(cache_path, allow_pickle=False)
    except Exception as e:
        print(f"Cache read failed ({e}); recomputing.")
        return None
    try:
        cache_unified = bool(npz['unified_mask']) if 'unified_mask' in npz.files else False
        if (int(npz['downsample_factor']) != downsample_factor
                or str(npz['dataset']) != dataset
                or cache_unified != unified_mask
                or not all(f'{ch}_S0' in npz.files for ch in channels)):
            return None
        stokes_data = {}
        for ch in channels:
            stokes_data[ch] = {
                'S0': npz[f'{ch}_S0'],
                'S1': npz[f'{ch}_S1'],
                'S2': npz[f'{ch}_S2'],
                'S3': npz[f'{ch}_S3'],
                'bg_mask': npz[f'{ch}_bg_mask'].astype(bool),
                'poincare_bg_mask': npz[f'{ch}_poincare_bg_mask'].astype(bool),
                'sat_mask': (npz[f'{ch}_sat_mask'].astype(bool)
                             if f'{ch}_sat_mask' in npz.files else None),
                'DoLP': npz[f'{ch}_DoLP'],
                'AoLP': npz[f'{ch}_AoLP'],
                'delta': npz[f'{ch}_delta'],
                'theta': npz[f'{ch}_theta'],
                'wav_intensity': (npz[f'{ch}_wav_intensity']
                                  if f'{ch}_wav_intensity' in npz.files else None),
                'channel_idx': channels_rgb[ch],
            }
        print(f"Cache loaded: {cache_path}  (dataset='{str(npz['dataset'])}', "
              f"DS={int(npz['downsample_factor'])}, unified={cache_unified}, "
              f"channels={list(channels)})")
        return stokes_data
    finally:
        npz.close()


def save_cache_npz(cache_path, stokes_data, dataset, downsample_factor,
                    unified_mask):
    """Serializza stokes_data in npz con schema standard."""
    save_dict = {
        'downsample_factor': np.int32(downsample_factor),
        'dataset': np.array(dataset),
        'unified_mask': np.bool_(unified_mask),
    }
    for ch, d in stokes_data.items():
        for k, v in d.items():
            if v is None or k == 'channel_idx':
                continue
            save_dict[f'{ch}_{k}'] = v
    np.savez_compressed(cache_path, **save_dict)
    print(f"\nCache saved: {cache_path}")
