"""Polarimetro package: pipeline 2D Stokes per la tesi.

Public API (drop-in compatible con final_utils):
    load_rotation_sequence, calculate_linear_stokes, calculate_s3,
    generate_background_mask, align_reference_frame, align_poincare_ellipticity,
    calculate_dolp_aolp, calculate_retardance_and_fast_axis,
    reset_saturation_accumulator, get_saturation_mask,
    quartz_birefringence, waveplate_retardance.

Pipeline ordine obbligato:
    reset_saturation_accumulator()
    angles, stack = load_rotation_sequence(...)
    S0, S1, S2 = calculate_linear_stokes(angles, stack)
    S3 = calculate_s3(wav_dir, channel_index, ...)
    bg_mask = generate_background_mask(S0)
    S1, S2 = align_reference_frame(S1, S2, bg_mask)
    S1, S3 = align_poincare_ellipticity(S0, S1, S3, bg_mask, ...)
    delta, theta = calculate_retardance_and_fast_axis(S0, S1, S2, S3, bg_mask,
                                                      target_folder=...)
"""
from . import config  # noqa: F401
from .align import (
    align_poincare_ellipticity,
    align_reference_frame,
    get_poincare_bg_mask,
)
from .io_raw import (
    get_saturation_mask,
    load_dark_frame,
    load_raw_image,
    load_rotation_sequence,
    reset_saturation_accumulator,
)
from .mask import generate_background_mask
from .retardance import (
    calculate_dolp_aolp,
    calculate_retardance_and_fast_axis,
)
from .stokes import (
    calculate_linear_stokes,
    calculate_s3,
    get_wav_intensity_cache,
    quartz_birefringence,
    waveplate_retardance,
)

__all__ = [
    "load_rotation_sequence",
    "calculate_linear_stokes",
    "calculate_s3",
    "generate_background_mask",
    "align_reference_frame",
    "align_poincare_ellipticity",
    "calculate_dolp_aolp",
    "calculate_retardance_and_fast_axis",
    "reset_saturation_accumulator",
    "get_saturation_mask",
    "quartz_birefringence",
    "waveplate_retardance",
    "load_raw_image",
    "load_dark_frame",
    "get_wav_intensity_cache",
    "get_poincare_bg_mask",
    "config",
]
