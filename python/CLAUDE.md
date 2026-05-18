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
* Flag off-by-default: `RUN_SPECTRA`, `RUN_DEBUGGER`. Cambiano e re-runni; pattern Jupyter classico.
* `CHANNEL` ('R' | 'G' | 'B' | 'all') è **solo di display**: pipeline computa sempre i 3 canali RGB (cache RGB unificata, parallel Pass B 3-thread). `DISPLAY_CHANNELS` deriva da `CHANNEL` e gate solo `show=` dei plot per-canale. Plot cross-channel (fit dispersione H, D-aolp-fit, D-delta-fit, C-debug 3-panel) sempre visualizzati. PDF sono salvati sempre per tutti i canali.

Cella **dispatcher**: `ANALYSES_PER_DATASET` mappa ogni dataset alle analisi attive.

| Dataset | Analisi |
|---------|---------|
| `lambdaquarti_50deg` | A, B, C-delta, D-delta, D-delta-fit |
| `lambdamezzi_50deg` | A, B, C-delta, D-delta, D-delta-fit |
| `strati_v2` | A, B, C-delta, F, E, H |
| `zucchero` | A, B, C-aolp, D-aolp, D-aolp-fit |
| `barraon_v2`, `barraoff_v2`, `righello_v2` | A, B |

Celle analisi (gated dal dispatcher):

| Code | Cella | Output |
|------|-------|--------|
| Load+Stokes | Pipeline 2-pass. Pass A: `calculate_linear_stokes_rgb_streaming` (legge 38 file UNA volta, accumulator `params[ch]` streaming) + `calculate_s3_rgb` (2 wav letti 1 volta) quando `UNIFIED_BG_MASK = len(ACTIVE_CHANNELS)>1`; per-canale altrimenti. bg_mask unica da `mean(S0_R,S0_G,S0_B)` se unified. Pass B in PARALLELO (ThreadPoolExecutor) per canale: `align_reference_frame` + `align_poincare_ellipticity(..., wav_intensity=, return_mask=True)` + DoLP/AoLP + retardance/theta. Cache `outputs/stokes_<DATASET>_DS<n>.npz` (schema include `unified_mask`) | `stokes_data[ch]` |
| A | Maschera bg (display). Unica plot se `UNIFIED_BG_MASK`, altrimenti una per canale. Overlay 2-color (bg + Poincaré) | PDF in `Images/generated/<DATASET>/mask.pdf` (unified) o `<CH>_mask.pdf` (per-ch) |
| B | 8 mappe pubblicabili (S0, S1, S2, S3, DoLP, AoLP, δ, θ) display + autosave | PDF in `Images/generated/<DATASET>/<CH>_<param>.pdf` + HTML interattivi |
| C-aolp | UMAP batch colorato per AoLP (mappa + scatter + hist) | PDF in `Images/generated/<DATASET>/aolp_umap/<CH>/` |
| C-delta | UMAP batch colorato per δ (cmap twilight ciclica) | PDF in `Images/generated/<DATASET>/delta_umap/<CH>/` |
| D-aolp | Clustering automatico AoLP via HDBSCAN sull'embedding UMAP (richiede C-aolp / C-delta eseguita prima — usa `UMAP_CACHE_BY_CHANNEL`). Score generico `size_frac × R × ang_dist_deg²` (no AoLP-hint). 3-panel: UMAP scatter colorato AoLP + winner rosso, AoLP map + scatter rosso pixel winner, AoLP hist colorato twilight + bin rossi scalati `N_total/N_emb` + vline mediana. Popola `D_AOLP_RESULTS[ch] = winner_info` (include `mean_deg`, `median_deg`, `R`, `ang_dist_deg`, `score`, `size`, `size_frac`). | PDF in `Images/generated/<DATASET>/<CH>_aolp_winner.pdf` |
| D-aolp-fit | Fit dispersione AoLP mediano vs λ centroide RGB come `ψ(λ) = k/λ²`. Legge `D_AOLP_RESULTS` (D-aolp prima) + `outputs/rgb_wavelengths.csv` (G0). Stampa k ± errore, R². Scatter 3 punti R/G/B colorati + curva fit nera tratteggiata. | PDF in `Images/generated/<DATASET>/aolp_lambda_fit.pdf` |
| D-delta | Clustering automatico δ via HDBSCAN sull'embedding UMAP (richiede C-delta prima — usa `UMAP_CACHE_BY_CHANNEL`). Stats su δ ∈ [0°, 360°) ciclica senza fattore 2θ; median in frame locale per wrap. 3-panel cmap `twilight`: UMAP scatter + winner rosso, δ map + scatter rosso, δ hist colorato + vline median. Popola `D_DELTA_RESULTS[ch]`. Escluso `strati_v2` (δ varia continuamente). | PDF in `Images/generated/<DATASET>/<CH>_delta_winner.pdf` |
| D-delta-fit | Fit dispersione δ mediano vs λ centroide RGB come `δ(λ) = k/λ` (quarzo zero-order). Legge `D_DELTA_RESULTS` (D-delta prima) + `outputs/rgb_wavelengths.csv` (G0). Se `DATASET` in `polcfg.WAVEPLATE_DESIGN_ANCHOR` aggiunge 4° punto di design (180°@633nm per λ/2, 90°@633nm per λ/4) come diamond nero. Stampa `k ± err`, R². | PDF in `Images/generated/<DATASET>/delta_lambda_fit.pdf` |
| E | Istogramma δ pubblicabile con marker plateau strati (etichette 1L–5–1R da `STRATI_SLICE_RESULTS` di F) | PDF + HTML in `Images/generated/<DATASET>/` |
| F | Slice δ multistrato (3 pannelli pub) | PDF + HTML in `Images/generated/<DATASET>/` |
| H | Fit retardance-vs-strati (lineare attraverso l'origine) + fit dispersione `δ(λ) = k/λ` su slope per-canale (quarzo zero-order: Δn ≈ costante). Hard-require `STRATI_SLICE_RESULTS` da cella F (raise se assente). Stampa `k ± err`. | PDF + HTML in `Images/generated/<DATASET>/strati_fit/` |
| I | Debug overlay fotoelasticità: solo `barraon_v2`. Carica cache `barraoff_v2` via `polpipe.load_cache_npz`, costruisce composite RGB (R=on, B=off) per visualizzare disallineamento residuo. 3-panel: S0 on, S0 off, overlay. Espandibile a diff S2/S3/AoLP/δ + slice 1D | PDF in `Images/generated/barraon_v2/<CH>_overlay_debug.pdf` |

Strumenti opzionali (gated da flag, in fondo notebook):

| Code | Cella | Flag | Output |
|------|-------|------|--------|
| G0 | Stima centroidi spettrali RGB (one-shot, indipendente dal DATASET) | `RUN_SPECTRA` | `outputs/rgb_wavelengths.csv` + `outputs/Analisi_Spettrale_S24_RGB.pdf` |
| I | Debugger pixel-per-pixel (click su mappa S0, animazione I(θ), fit sinusoidale) | `RUN_DEBUGGER` | finestra mpl interattiva |

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
| `umap_runner.py` | Helper UMAP: `build_validity_mask` (bg_mask opzionale, filtri DoLP/`sin²(2θ)` disattivati di default — `DOLP_MIN=0.0`, `UMAP_AXIS_CONFIDENCE_MIN=0.0`), `random_sample_mask`, `plot_sample_diagnostic`, `default_feature_mode`, `build_feature_matrix`, `color_spec`, `aolp_clip_range`, `normalize_stokes`, `fit_umap`, `cluster_aolp_kmeans` (KMeans su `(sin2θ,cos2θ)`, legacy), `cluster_umap_hdbscan_by_aolp` (HDBSCAN sull'embedding UMAP, ritorna anche `median_deg` per cluster), `cluster_umap_hdbscan_by_delta` (analogo per δ ∈ [0°, 360°), no fattore 2θ, median in frame locale per wrap), `compute_or_load_umap_cache` (one-channel runner: build_validity_mask + random_sample_mask + fit_umap + cache npz schema v3), `export_umap_panels` (3 PDF pubblicabili: mappa, scatter UMAP, hist). Reimport drop-in dello script legacy `final_umap.py` |
| `plotting.py` | `apply_thesis_style` (rcParams serif dpi 300), `save_and_show`, `mask_overlay_rgb` (3-color overlay bg + Poincaré), `plot_mask_overlay_figure` (figura + legenda + save), `make_param_figure` (mappa parametro imshow + colorbar), `save_param_html` (heatmap plotly CDN), `resolve_sym_limits` (`'sym99'` → ±99-percentile), `mpl_cmap_to_plotly_scale`, `fmt_sci` (notazione LaTeX `c·10^e`) |
| `slice_fit.py` | Algoritmo F (strati_v2): `build_slice_grid` (slice spessa diagonale), `sample_thick_delta` (media circolare lungo larghezza), `find_auto_crop` (esclude bordi + δ vicini 0/360), `detect_plateaus` (gradient threshold + min_run filter), `fit_layers` (fit δ = m·n through origin con unwrap L/R separato) |
| `pipeline.py` | Orchestratore Pass A + Pass B per cella Load+Stokes. API: `run_pass_a_unified` (streaming RGB 1×38 file), `run_pass_a_per_channel` (sequenziale single-channel), `compute_unified_bg_mask` (mean S0_RGB → Canny mask), `process_channel` (Pass B puro: align + retardance per canale, thread-safe), `apply_saturation_global` (NaN OR fra canali), `load_cache_npz` + `save_cache_npz` (schema: downsample_factor, dataset, unified_mask, per-ch keys) |

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

`numpy, scipy, matplotlib, pandas, rawpy, tqdm, umap-learn, plotly, scikit-image, scikit-learn` (HDBSCAN in D-aolp).

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
