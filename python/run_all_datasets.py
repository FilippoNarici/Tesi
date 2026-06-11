"""Batch re-run di TUTTI i dataset col nuovo delta_a calibrato (S3 data-driven).

Cancella le cache stokes_*/umap_* (NON invalidano sul cambio di correzione S3 ->
altrimenti il notebook ricaricherebbe la S3 vecchia), poi esegue il notebook
headless per ogni dataset (patch della cella config DATASET), salvando PDF/HTML.

UTILITY DI RE-RUN (mantenuta). Rigenera cache + UMAP + tutti i PDF dei 7 dataset
con la pipeline corrente. Eseguire dopo una modifica che cambia i risultati ma
NON la chiave di cache (es. correzione S3, allineamenti): le cache stokes_*/umap_*
non invalidano da sole su questi cambi, quindi vanno svuotate (lo fa questo
script). Uso: `python run_all_datasets.py` dalla cartella `python/`. ~1 h.
"""
import glob
import os
import re
import time

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

HERE = os.path.dirname(os.path.abspath(__file__))   # python/
NB = os.path.join(HERE, "analisi.ipynb")
OUTPUTS = os.path.join(HERE, "outputs")

# barraoff PRIMA di barraon (la cella I di barraon carica la cache di barraoff)
DATASETS = [
    "righello_v2", "barraoff_v2", "barraon_v2",
    "lambdaquarti_50deg", "lambdamezzi_50deg", "strati_v2", "zucchero",
]


def clear_caches():
    n = 0
    for pat in ("stokes_*.npz", "umap_*.npz"):
        for f in glob.glob(os.path.join(OUTPUTS, pat)):
            os.remove(f)
            n += 1
    print(f"[cache] rimossi {n} file stokes_*/umap_* (forza ricalcolo S3 nuovo)",
          flush=True)


def patch_dataset(nb, ds):
    for cell in nb.cells:
        if cell.cell_type == "code" and re.search(r"DATASET = '[^']*'", cell.source):
            cell.source = re.sub(r"DATASET = '[^']*'", f"DATASET = '{ds}'",
                                 cell.source, count=1)
            return True
    return False


def main():
    t_all = time.time()
    clear_caches()
    results = {}
    for ds in DATASETS:
        nb = nbformat.read(NB, as_version=4)
        if not patch_dataset(nb, ds):
            print(f"[{ds}] SKIP: cella config non trovata", flush=True)
            results[ds] = "no-config"
            continue
        print(f"\n[{ds}] start ...", flush=True)
        t0 = time.time()
        client = NotebookClient(
            nb, timeout=2400, kernel_name="python3",
            resources={"metadata": {"path": HERE}})
        try:
            client.execute()
            dt = time.time() - t0
            print(f"[{ds}] OK  {dt:.0f}s", flush=True)
            results[ds] = f"OK {dt:.0f}s"
        except CellExecutionError as e:
            dt = time.time() - t0
            msg = str(e).splitlines()[-1][:160]
            print(f"[{ds}] FAIL {dt:.0f}s: {msg}", flush=True)
            results[ds] = f"FAIL: {msg}"
        except Exception as e:
            print(f"[{ds}] ERROR: {type(e).__name__}: {e}", flush=True)
            results[ds] = f"ERROR: {e}"

    print("\n" + "=" * 60, flush=True)
    print(f"BATCH DONE in {(time.time()-t_all)/60:.1f} min", flush=True)
    for ds in DATASETS:
        print(f"  {ds:22} {results.get(ds,'?')}", flush=True)


if __name__ == "__main__":
    main()
