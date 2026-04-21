"""Runner diagnostico su strati_v2:
- istogramma di delta (una volta per canale)
- UMAP senza delta nelle feature (feature_mode='no_delta')
"""
import os
import time
import matplotlib
matplotlib.use('Agg')

import final_utils as utils
import final_umap as fu

DATASET = 'strati_v2'
CHANNELS = [(0, 'R'), (1, 'G'), (2, 'B')]


def main():
    utils.TARGET_FOLDER = f'./raw/{DATASET}'
    utils.POL_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'pol')
    utils.WAV_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'wav')
    utils.WAVEPLATE_AXES_SWAPPED = False

    t_total = time.time()
    for ch_idx, ch_label in CHANNELS:
        utils.TARGET_CHANNEL_IDX = ch_idx
        t0 = time.time()
        umap_png = f'./outputs/umap_{DATASET}_{ch_label}_nodelta.png'
        hist_png = f'./outputs/hist_delta_{DATASET}_{ch_label}.png'
        print(f'\n=== {DATASET} / {ch_label} (no_delta) ===')
        fu.run(sample_name=f'{DATASET}_{ch_label}_nodelta',
               show=False, save_path=umap_png,
               feature_mode='no_delta', histogram_path=hist_png)
        print(f'  [{ch_label}] elapsed: {time.time()-t0:.1f}s')
    print(f'\nTotal: {(time.time()-t_total)/60:.1f} min')


if __name__ == '__main__':
    main()
