"""Rigenerazione batch dei PDF della tesi su tutti i dataset e tutti i canali.

Invoca ``final_thesis_figure.main()`` in sequenza per ciascuna combinazione
(dataset, canale), aggiornando on-the-fly le variabili globali di
``final_utils`` (TARGET_FOLDER, POL/WAV_SUBFOLDER, WAVEPLATE_AXES_SWAPPED,
TARGET_CHANNEL_IDX).

Uso:
    cd python && python final_thesis_figure_all.py

Produce PDF in ../Images/generated/<dataset>/ e versioni pickled in
../Images/generated/<dataset>/interactive/ (vedi view_fig.py).
"""

import os
import time
import traceback

import final_utils as utils
import final_thesis_figure as fig_mod


DATASETS = [
    'lambdaquarti_50deg',
    'lambdamezzi_50deg',
    'strati_v2',
    'zucchero',
    'barraon_v2',
    'barraoff_v2',
    'righello_v2',
]
CHANNELS = [(0, 'R'), (1, 'G'), (2, 'B')]


def _reconfigure(dataset_name, channel_idx):
    """Imposta le globals di final_utils per il dataset/canale correnti."""
    utils.TARGET_FOLDER = f'./raw/{dataset_name}'
    utils.POL_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'pol')
    utils.WAV_SUBFOLDER = os.path.join(utils.TARGET_FOLDER, 'wav')
    utils.WAVEPLATE_AXES_SWAPPED = 'lambdamezzi_50deg' in utils.TARGET_FOLDER.lower()
    utils.TARGET_CHANNEL_IDX = channel_idx


def main():
    # Genera tutti i parametri per ogni combinazione.
    utils.THESIS_FIGURE_PARAMS = 'all'

    total = len(DATASETS) * len(CHANNELS)
    done = 0
    failures = []
    t0 = time.time()

    for dataset in DATASETS:
        for channel_idx, channel_label in CHANNELS:
            done += 1
            banner = f"[{done}/{total}] {dataset} / canale {channel_label}"
            print('\n' + '=' * len(banner))
            print(banner)
            print('=' * len(banner))

            _reconfigure(dataset, channel_idx)
            try:
                fig_mod.main()
            except Exception as exc:
                print(f"FALLITO {dataset}/{channel_label}: {exc}")
                traceback.print_exc()
                failures.append((dataset, channel_label, str(exc)))

    elapsed = time.time() - t0
    print('\n' + '=' * 40)
    print(f"Tempo totale: {elapsed/60:.1f} min")
    print(f"Completati: {done - len(failures)}/{total}")
    if failures:
        print(f"Falliti ({len(failures)}):")
        for ds, ch, err in failures:
            print(f"  - {ds}/{ch}: {err}")


if __name__ == '__main__':
    main()
