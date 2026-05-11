"""Polarimetro package: pipeline 2D Stokes per la tesi.

Public API (drop-in compatible con final_utils):
    load_rotation_sequence, calculate_linear_stokes, calculate_s3,
    generate_background_mask, align_reference_frame, align_poincare_ellipticity,
    calculate_dolp_aolp, calculate_retardance_and_fast_axis,
    reset_saturation_accumulator, get_saturation_mask,
    quartz_birefringence, waveplate_retardance.
"""
from . import config  # noqa: F401
