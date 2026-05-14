# python/ — Guida al codice di analisi

Questo file è letto da Claude quando lavora nella directory `python/`. Per regole di stile e persona vedere la `CLAUDE.md` alla radice del repo.

## Architettura attuale (2026-05-11, post-refactor team `ipynb-refactor`)

Tre artefatti:

1. **`analisi.ipynb`** — singolo notebook con dispatcher per dataset. Punto di ingresso unico per l'analisi quotidiana.
2. **`polarimetro/`** — package Python che contiene tutta la logica numerica (split di `final_utils.py`). Tutte le funzioni public API esposte tramite `__init__.py`.
3. **`legacy/`** — archivio dei 11 script `final_*.py` originali (compreso `final_utils.py`). Riferimento storico, non più mantenuto.

Convenzione: edit del notebook + edit del package. Non riprendere mai logica nei `final_*.py` in `legacy/`.

## Notebook `analisi.ipynb`

Cella **config** (in testa):
* `DATASET` — stringa hardcoded fra le 7 cartelle in `raw/`.
* `CHANNEL` — `'R'`, `'G'`, `'B'` o `'all'`.
* `DOWNSAMPLE_FACTOR` — default 4.
* `SAVE_PLOTS` — `True` per autosave PDF accanto a `plt.show()`.
* `OUTPUT_DIR` — default `../Images/generated`.
* Flag off-by-default: `RUN_SPECTRA`, `RUN_DEBUGGER`, `RUN_FULL_BATCH`. Cambiano e re-runni; pattern Jupyter classico.

Cella **dispatcher**: `ANALYSES_PER_DATASET` mappa ogni dataset alle analisi attive.

| Dataset | Analisi |
|---------|---------|
| `lambdaquarti_50deg` | A, B, C-delta |
| `lambdamezzi_50deg` | A, B, C-delta |
| `strati_v2` | A, B, C-delta, F, H, E-ext |
| `zucchero` | A, B, C-aolp |
| `barraon_v2`, `barraoff_v2`, `righello_v2` | A, B |

Celle analisi (gated dal dispatcher):

| Code | Cella | Output |
|------|-------|--------|
| Load+Stokes | Pipeline 2-pass (Pass A: load + S0/S1/S2 + S3 per canale; bg_mask unificata da mean(S0_R,S0_G,S0_B) se `UNIFIED_BG_MASK = len(ACTIVE_CHANNELS)>1`, altrimenti per-canale; Pass B: align_reference_frame + align_poincare_ellipticity + DoLP/AoLP + retardance/theta). Cache `outputs/stokes_<DATASET>_DS<n>.npz` (schema include `unified_mask`, invalida auto se cambia) | Variabili in `stokes_data[ch]` |
| A | Maschera bg (display). Unica plot se `UNIFIED_BG_MASK`, altrimenti una per canale. Overlay 2-color (bg + Poincaré) | PDF in `Images/generated/<DATASET>/mask.pdf` (unified) o `<CH>_mask.pdf` (per-ch) |
| B | 8 mappe pubblicabili (S0, S1, S2, S3, DoLP, AoLP, δ, θ) display + autosave | PDF in `Images/generated/<DATASET>/<CH>_<param>.pdf` + HTML interattivi |
| C-aolp | UMAP batch colorato per AoLP (mappa + scatter + hist) | PDF in `Images/generated/<DATASET>/aolp_umap/<CH>/` |
| C-delta | UMAP batch colorato per δ (cmap twilight ciclica) | PDF in `Images/generated/<DATASET>/delta_umap/<CH>/` |
| E-ext | Istogramma δ pubblicabile con marker plateau strati | PDF + HTML in `Images/generated/<DATASET>/` |
| F | Slice δ multistrato (3 pannelli pub) | PDF + HTML in `Images/generated/<DATASET>/` |
| H | Fit retardance-vs-strati + dispersione 1/λ² | PDF + HTML in `Images/generated/<DATASET>/` |

Strumenti opzionali (gated da flag, in fondo notebook):

| Code | Cella | Flag | Output |
|------|-------|------|--------|
| G0 | Stima centroidi spettrali RGB (one-shot, indipendente dal DATASET) | `RUN_SPECTRA` | `outputs/rgb_wavelengths.csv` + `outputs/Analisi_Spettrale_S24_RGB.pdf` |
| I | Debugger pixel-per-pixel (click su mappa S0, animazione I(θ), fit sinusoidale) | `RUN_DEBUGGER` | finestra mpl interattiva |
| FULL BATCH | Loop 7 dataset × 3 canali × analisi rilevanti (no preview, solo savefig) | `RUN_FULL_BATCH` | tutti i PDF in `Images/generated/` |

## Package `polarimetro/`

| Modulo | Contenuto |
|--------|-----------|
| `__init__.py` | Re-export public API e namespace `config` |
| `config.py` | Costanti immutabili (`SENSOR_WHITE_LEVEL=4095`, `SATURATION_FRACTION=0.98`, `WAV_HOLDER_THRESHOLD=0.50`, soglie Canny, dilation), `WAVEPLATE_SWAPPED_DATASETS`, `is_waveplate_swapped(target_folder)`, `get_channel_wavelength(csv_path, channel_index)` |
| `io_raw.py` | `load_raw_image`, `load_rotation_sequence`, `load_dark_frame`, `downsample_image`, `reset_saturation_accumulator`, `get_saturation_mask`. Globals modulo: `_SATURATION_ACCUMULATOR`, `_DARK_FRAME_CACHE` |
| `stokes.py` | `calculate_linear_stokes`, `calculate_s3` (con correzione λ via Ghosh), `quartz_birefringence`, `waveplate_retardance`, `get_wav_intensity_cache()`. Global `_WAV_INTENSITY_CACHE` (esposto via getter per evitare import circolari con `align`) |
| `mask.py` | `generate_background_mask` (Canny + dark prior + flood-fill multi-component + compactness + erosione scalata DS) |
| `align.py` | `align_reference_frame` (asse S3), `align_poincare_ellipticity` (asse S2, usa `stokes.get_wav_intensity_cache()`), `get_poincare_bg_mask()`. Global `_POINCARE_BG_MASK_CACHE` |
| `retardance.py` | `calculate_dolp_aolp`, `calculate_retardance_and_fast_axis` (arctan2 [0°, 360°), valuta `WAVEPLATE_SWAPPED` a runtime via arg `target_folder`) |
| `umap_runner.py` | Helper UMAP: `build_validity_mask` (filtro `sin²(2θ) > 0.05`), `default_feature_mode`, `build_feature_matrix`, `color_spec`, `aolp_clip_range`, `normalize_stokes`, `fit_umap`. Reimport drop-in dello script legacy `final_umap.py` |
| `plotting.py` | `apply_thesis_style` (rcParams serif dpi 300), `save_and_show`, `mask_overlay_rgb` (2-color overlay bg + Poincaré) |

API pubblica (re-export in `__init__.py`):
`load_rotation_sequence, load_raw_image, load_dark_frame, calculate_linear_stokes, calculate_s3, quartz_birefringence, waveplate_retardance, generate_background_mask, align_reference_frame, align_poincare_ellipticity, calculate_dolp_aolp, calculate_retardance_and_fast_axis, reset_saturation_accumulator, get_saturation_mask, get_wav_intensity_cache, get_poincare_bg_mask`.

## Ordine pipeline obbligato

```
reset_saturation_accumulator()
↓
load_rotation_sequence(pol, ch, DS, dark_path)
↓
calculate_linear_stokes(angles, stack) → S0, S1, S2
↓
calculate_s3(wav, ch, DS, wavelength, dark_path) → S3   # popola _WAV_INTENSITY_CACHE
↓
generate_background_mask(S0, DS) → bg_mask
↓
S1, S2 = align_reference_frame(S1, S2, bg_mask)         # rot attorno S3
↓
S1, S3 = align_poincare_ellipticity(S0, S1, S3, bg_mask, DS)   # rot attorno S2; usa wav cache
↓
DoLP, AoLP = calculate_dolp_aolp(S0, S1, S2)
↓
delta_deg, theta_deg = calculate_retardance_and_fast_axis(S0, S1, S2, S3, bg_mask, target_folder)
```

Tutto invariato rispetto al pre-refactor; questa è la stessa pipeline di `legacy/final_polarimeter.py` ma riorganizzata in moduli.

## Dipendenze (`requirements.txt`)

`numpy, scipy, matplotlib, pandas, rawpy, tqdm, umap-learn, plotly, scikit-image`.

Ambiente: `.venv` alla radice del repo (`../.venv/Scripts/python.exe` da `python/`).

## Cache files

| File | Contenuto | Gitignore |
|------|-----------|-----------|
| `outputs/stokes_<DATASET>_DS<n>.npz` | Cache della cella Load+Stokes (Stokes + maschere + retardance per canale) | Sì |
| `outputs/umap_<DATASET>_<CH>_cache.npz` | Cache fit UMAP (schema v3, condiviso AoLP/δ, include `axis_conf_min`) | Sì |
| `outputs/rgb_wavelengths.csv` | λ centroidi R/G/B per il sensore S24 (output di G0) | No (file leggero, dato calibrato) |
| `outputs/Analisi_Spettrale_S24_RGB.pdf` | Plot spettri (output di G0) | No |

Le cache npz sono rigenerabili eseguendo la cella Load+Stokes o `RUN_SPECTRA`/UMAP cells.

## Dati

* Input RAW: `./raw/<dataset>/pol/pol*.dng` (36 angoli, passi di 10°) + `./raw/<dataset>/wav/wav±45.dng`. Dark frame globale `./raw/dark.dng`.
* Spettri sensore + sorgente in `./spettri/`.
* Output figure tesi in `../Images/generated/<dataset>/`.

## Insidie note

Vedi `CLAUDE.md` (radice), sezione "Insidie tecniche note". Le più critiche per chi tocca il notebook o il package:

* `align_poincare_ellipticity` ritorna nuovi array (riassegnare `S1, S3` nei chiamanti). La cella Load+Stokes lo fa correttamente.
* `WAVEPLATE_AXES_SWAPPED` per `lambdamezzi_50deg` ora gestito a runtime via `config.is_waveplate_swapped(target_folder)` chiamato dentro `calculate_retardance_and_fast_axis`. Cambiare DATASET nel notebook è sicuro.
* Retardance arctan2 [0°, 360°); le tabelle storiche basate su `arccos` vanno rimisurate (TODO B2).
* Saturation accumulator va resettato all'inizio di ogni run; la cella Load+Stokes lo fa.
* La cache npz `stokes_*` invalida automaticamente se cambia `DOWNSAMPLE_FACTOR` o `DATASET` salvato.
* Per cambiare canale senza ricomputare l'intera pipeline, lasciare `CHANNEL='all'` per salvare R/G/B insieme; le celle gated dal dispatcher leggono `stokes_data[ch]`.

## Test

Smoke test eseguito 2026-05-11 su `strati_v2` canale G (DS=4): pipeline completa, cache npz salvato. Nessuna suite di test automatica.

Per testare un dataset diverso: cambiare `DATASET` nella cella config, eseguire dall'alto (`Run All` salta le celle non in `ANALYSES_PER_DATASET[DATASET]`).
