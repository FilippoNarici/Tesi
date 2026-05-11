"""RAW loading, dark subtraction, downsampling, saturation accumulator."""
import glob
import os
import re

import numpy as np
import rawpy
from tqdm import tqdm

from . import config

_SATURATION_ACCUMULATOR = None
_DARK_FRAME_CACHE = {}


def downsample_image(img, factor):
    if factor <= 1:
        return img
    H, W = img.shape
    new_H = H - (H % factor)
    new_W = W - (W % factor)
    img_cropped = img[:new_H, :new_W]
    return img_cropped.reshape(new_H // factor, factor,
                               new_W // factor, factor).mean(axis=(1, 3))


def _read_raw_channel_fullres(path, channel_index,
                              track_saturation=True,
                              use_raw_bayer=config.USE_RAW_BAYER):
    global _SATURATION_ACCUMULATOR
    with rawpy.imread(path) as raw:
        if use_raw_bayer:
            ri = raw.raw_image_visible
            if ri.ndim != 3 or ri.shape[2] < 3:
                raise RuntimeError(
                    f"Expected 4-plane RGBG raw layout, got shape {ri.shape}. "
                    "Disable use_raw_bayer to fall back to the postprocess path."
                )
            plane_map = {0: 0, 1: 1, 2: 2}
            data = ri[:, :, plane_map[channel_index]].astype(np.float32)
        else:
            rgb = raw.postprocess(
                use_camera_wb=False,
                user_wb=[1.0, 1.0, 1.0, 1.0],
                no_auto_bright=True,
                gamma=(1, 1),
                output_bps=16,
            )
            data = rgb[:, :, channel_index].astype(np.float32)

    if track_saturation and _SATURATION_ACCUMULATOR is not None:
        if use_raw_bayer:
            threshold = config.SENSOR_WHITE_LEVEL * config.SATURATION_FRACTION
        else:
            threshold = 65535.0 * config.SATURATION_FRACTION
        frame_sat = data >= threshold
        if _SATURATION_ACCUMULATOR.shape != frame_sat.shape:
            _SATURATION_ACCUMULATOR = frame_sat.copy()
        else:
            np.logical_or(_SATURATION_ACCUMULATOR, frame_sat,
                          out=_SATURATION_ACCUMULATOR)
    return data


def reset_saturation_accumulator():
    global _SATURATION_ACCUMULATOR
    _SATURATION_ACCUMULATOR = np.zeros((1, 1), dtype=bool)


def get_saturation_mask(downsample_factor=1):
    if _SATURATION_ACCUMULATOR is None or _SATURATION_ACCUMULATOR.size == 1:
        return None
    sat = _SATURATION_ACCUMULATOR
    if downsample_factor <= 1:
        return sat.copy()
    H, W = sat.shape
    new_H = H - (H % downsample_factor)
    new_W = W - (W % downsample_factor)
    sat = sat[:new_H, :new_W]
    sat = sat.reshape(new_H // downsample_factor, downsample_factor,
                      new_W // downsample_factor, downsample_factor)
    return sat.any(axis=(1, 3))


def load_dark_frame(channel_index,
                    dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
                    use_raw_bayer=config.USE_RAW_BAYER):
    key = (channel_index, use_raw_bayer, dark_frame_path)
    if key in _DARK_FRAME_CACHE:
        return _DARK_FRAME_CACHE[key]
    if not os.path.exists(dark_frame_path):
        print(f"Warning: dark frame not found at {dark_frame_path}. "
              "Skipping bias subtraction.")
        _DARK_FRAME_CACHE[key] = None
        return None
    try:
        dark = _read_raw_channel_fullres(dark_frame_path, channel_index,
                                         track_saturation=False,
                                         use_raw_bayer=use_raw_bayer)
    except Exception as e:
        print(f"Error reading dark frame {dark_frame_path}: {e}. "
              "Skipping bias subtraction.")
        _DARK_FRAME_CACHE[key] = None
        return None
    _DARK_FRAME_CACHE[key] = dark
    print(f"Loaded dark frame ({('raw Bayer' if use_raw_bayer else 'postprocess')}, "
          f"channel {channel_index}): mean={dark.mean():.2f}, max={dark.max():.0f}")
    return dark


def load_raw_image(path, channel_index, downsample_factor=1,
                   subtract_dark=True,
                   dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
                   use_raw_bayer=config.USE_RAW_BAYER):
    if not os.path.exists(path):
        return None
    try:
        data = _read_raw_channel_fullres(path, channel_index,
                                         use_raw_bayer=use_raw_bayer)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None
    if subtract_dark:
        dark = load_dark_frame(channel_index, dark_frame_path=dark_frame_path,
                               use_raw_bayer=use_raw_bayer)
        if dark is not None:
            data = data - dark
    return downsample_image(data, downsample_factor)


def load_rotation_sequence(pol_dir, channel_index,
                           downsample_factor=1, invert_angles=False,
                           dark_frame_path=config.DEFAULT_DARK_FRAME_PATH,
                           use_raw_bayer=config.USE_RAW_BAYER):
    print(f"Loading linear polarization images from: {pol_dir}")
    search_pattern = os.path.join(pol_dir, 'pol*.dng')
    file_paths = glob.glob(search_pattern)

    if not file_paths:
        print("No 'pol*.dng' files found in the specified folder.")
        return None, None

    angle_file_pairs = []
    for fpath in file_paths:
        match = re.search(r'pol(\d+)\.dng', os.path.basename(fpath), re.IGNORECASE)
        if match:
            orig_angle = int(match.group(1))
            angle = (360 - orig_angle) % 360 if invert_angles else orig_angle
            angle_file_pairs.append((angle, fpath))

    if not angle_file_pairs:
        return None, None

    angle_file_pairs.sort()
    angles_rad_2x = np.deg2rad(2.0 * np.array([p[0] for p in angle_file_pairs]))

    images = []
    print(f"Found {len(angle_file_pairs)} images. Processing (Downsample: {downsample_factor}x)...")
    for _ang, fpath in tqdm(angle_file_pairs):
        img = load_raw_image(fpath, channel_index, downsample_factor,
                             dark_frame_path=dark_frame_path,
                             use_raw_bayer=use_raw_bayer)
        if img is not None:
            images.append(img)

    return angles_rad_2x, np.stack(images, axis=0)
