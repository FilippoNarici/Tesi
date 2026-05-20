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
| Load+Stokes | Pipeline 2-pass orchestrata da `polpipe`. Pass A: `run_pass_a_unified` (streaming RGB, 38 file letti 1 volta) o `run_pass_a_per_channel` (sequenziale single-channel). bg_mask unica da `mean(S0_RGB)` se `len(ACTIVE_CHANNELS) > 1`. Pass B parallelo (`ThreadPoolExecutor` su `polpipe.process_channel`): `align_reference_frame` + `align_poincare_ellipticity` + DoLP/AoLP + retardance/theta. Cache `outputs/stokes_<DATASET>_DS<n>.npz` (schema include `unified_mask`) | `stokes_data[ch]` |
| A | Maschera bg (display). Unica plot se `unified`, altrimenti una per canale. Overlay 3-color via `polplot.plot_mask_overlay_figure` (bg utile + XOR wav-holder + sample) | PDF in `Images/generated/<DATASET>/mask.pdf` (unified) o `<CH>_mask.pdf` (per-ch) |
| B | 8 mappe pubblicate (S0, S1, S2, S3, DoLP, AoLP, δ, θ). Configurazione cmap/range centralizzata in `polplot.STOKES_PARAM_CONFIG` + `STOKES_PARAM_ORDER`; S0 usa `polplot.make_s0_cmap(channel_idx)` (nero→R/G/B). | PDF in `Images/generated/<DATASET>/<CH>_<param>.pdf` + HTML interattivi |
| C-aolp | UMAP batch colorato per AoLP (mappa + scatter + hist) via `polumap.export_umap_panels` | PDF in `Images/generated/<DATASET>/aolp_umap/<CH>/` |
| C-delta | UMAP batch colorato per δ (cmap twilight ciclica) | PDF in `Images/generated/<DATASET>/delta_umap/<CH>/` |
| D-aolp | Clustering HDBSCAN sull'embedding UMAP (richiede `UMAP_CACHE_BY_CHANNEL` da C-aolp/C-delta) via `polumap.cluster_umap_hdbscan_by_aolp`. Plot 3-pannelli condiviso `polcluster.plot_cluster_winner_panels(mode='aolp', ...)`. Popola `D_AOLP_RESULTS[ch]` (`mean_deg`, `median_deg`, `R`, `ang_dist_deg`, `score`, `size`, `size_frac`). | PDF in `Images/generated/<DATASET>/<CH>_aolp_winner.pdf` |
| D-aolp-fit | Fit `ψ(λ) = k/λ²` (Drude per attività ottica naturale) via `poldisp.fit_inverse_lambda(..., power=2)` + `poldisp.plot_dispersion_fit`. Legge `D_AOLP_RESULTS` + `outputs/rgb_wavelengths.csv`. | PDF in `Images/generated/<DATASET>/aolp_lambda_fit.pdf` |
| D-delta | Mirror di D-aolp ma su δ ∈ [0°, 360°) ciclica. `polumap.cluster_umap_hdbscan_by_delta` + `polcluster.plot_cluster_winner_panels(mode='delta', ...)`. Popola `D_DELTA_RESULTS[ch]`. Escluso `strati_v2`. | PDF in `Images/generated/<DATASET>/<CH>_delta_winner.pdf` |
| D-delta-fit | Fit `δ(λ) = k/λ` (quarzo zero-order) via `poldisp.fit_inverse_lambda(..., power=1)`. Se `DATASET` in `polcfg.WAVEPLATE_DESIGN_ANCHOR` aggiunge punto di design (180°@633nm per λ/2, 90° per λ/4) come diamond nero. | PDF in `Images/generated/<DATASET>/delta_lambda_fit.pdf` |
| E | Istogramma δ pubblicato (`polplot.plot_delta_strati_histogram`) con plateau strati come vline + etichette 1L→5→1R (frazioni y da `polplot.STRATI_LABEL_Y_FRAC`). HTML interattivo via `save_delta_strati_histogram_html`. Hard-require `STRATI_SLICE_RESULTS` da F. | PDF + HTML in `Images/generated/<DATASET>/` |
| F | Slice δ multistrato (3 pannelli pub) tramite `polslice.build_slice_grid` + `sample_thick_delta` + `detect_plateaus` + `fit_layers`. Popola `STRATI_SLICE_RESULTS[ch]` per E + H. | PDF + HTML in `Images/generated/<DATASET>/` |
| H | Fit lineare `δ = m·n` through-origin per canale + fit dispersione `δ(λ) = k/λ` su slope via `poldisp.fit_inverse_lambda`. Hard-require `STRATI_SLICE_RESULTS` da F. | PDF + HTML in `Images/generated/strati_fit/` |
| I | Fotoelasticità barraon vs barraoff (solo `barraon_v2`). `polphoto.phase_correlation` (ROI supporto destro) → `shift_dict_inplace` su barraoff cache → `trace_centerline` + `polyfit_centerline` → `build_warp_field` + `warp_image(S3_on)`. Plot: overlay 4-panel, centerline+edges, centerline+fit+deflection, ΔS3 = warped(on) − off per canale. | PDF in `Images/generated/barraon_v2/` |

Strumenti opzionali (gated da flag, in fondo notebook):

| Code | Cella | Flag | Output |
|------|-------|------|--------|
| G0 | Stima centroidi spettrali RGB (one-shot, indipendente dal DATASET) | `RUN_SPECTRA` | `outputs/rgb_wavelengths.csv` + `outputs/Analisi_Spettrale_S24_RGB.pdf` |
| I | Debugger pixel-per-pixel (click su mappa S0, animazione I(θ), fit sinusoidale) | `RUN_DEBUGGER` | finestra mpl interattiva |

## Package `polarimetro/`

| Modulo | Contenuto |
|--------|-----------|
| `__init__.py` | Re-export public API e namespace di tutti i sotto-moduli (`config`, `pipeline`, `plotting`, `slice_fit`, `umap_runner`, `clustering_plot`, `dispersion`, `photoelasticity`) |
| `config.py` | Costanti immutabili (`SENSOR_WHITE_LEVEL=4095`, `SATURATION_FRACTION=0.98`, `WAV_HOLDER_THRESHOLD=0.50`, soglie Canny, dilation), `WAVEPLATE_SWAPPED_DATASETS`, `WAVEPLATE_DESIGN_ANCHOR` (punti design 633 nm per λ/2 e λ/4), `is_waveplate_swapped(target_folder)`, `get_channel_wavelength(csv_path, channel_index)` |
| `io_raw.py` | `load_raw_image`, `load_rotation_sequence`, `load_dark_frame`, `downsample_image`, `reset_saturation_accumulator`, `get_saturation_mask`. Globals modulo: `_SATURATION_ACCUMULATOR`, `_DARK_FRAME_CACHE` |
| `stokes.py` | `calculate_linear_stokes`, `calculate_s3` (con correzione λ via Ghosh), `calculate_linear_stokes_rgb_streaming` (38 file letti 1 volta), `calculate_s3_rgb`, `quartz_birefringence`, `waveplate_retardance`, `get_wav_intensity_cache()`. Global `_WAV_INTENSITY_CACHE` (esposto via getter per evitare import circolari con `align`) |
| `mask.py` | `generate_background_mask` (Canny + dark prior + flood-fill multi-component + compactness + erosione scalata DS) |
| `align.py` | `align_reference_frame` (asse S3), `align_poincare_ellipticity` (asse S2, usa `stokes.get_wav_intensity_cache()`), `get_poincare_bg_mask()`. Global `_POINCARE_BG_MASK_CACHE` |
| `retardance.py` | `calculate_dolp_aolp`, `calculate_retardance_and_fast_axis` (arctan2 [0°, 360°), valuta `WAVEPLATE_SWAPPED` a runtime via arg `target_folder`) |
| `umap_runner.py` | Helper UMAP: `build_validity_mask`, `random_sample_mask`, `plot_sample_diagnostic`, `build_feature_matrix`, `color_spec`, `aolp_clip_range`, `normalize_stokes`, `fit_umap`, `cluster_umap_hdbscan_by_aolp` / `_by_delta` (HDBSCAN sull'embedding UMAP + statistica circolare + score `size_frac × R × ang_dist²`), `compute_or_load_umap_cache` (one-channel runner: build_validity_mask + random_sample_mask + fit_umap + cache npz schema v3), `export_umap_panels` (3 PDF pubblicabili: mappa, scatter UMAP, hist filtrato sample) |
| `clustering_plot.py` | `plot_cluster_winner_panels(mode='aolp'\|'delta', ...)` — figura 3-pannelli (UMAP scatter, mappa spaziale, istogramma) con cluster vincente rosso. Dedup celle D-aolp + D-delta del notebook |
| `dispersion.py` | Fit spettrale `f(λ) = k/λ^p` parametrico. `fit_inverse_lambda(lambdas, values, power=1\|2)` ritorna dict `{k, k_err, r2, ...}`; `plot_dispersion_fit(fit, ..., design_point=None)` genera figura 1-pannello stile tesi. Usato da D-aolp-fit (`p=2`, Drude), D-delta-fit (`p=1` + design anchor), H (`p=1` su slope) |
| `plotting.py` | `apply_thesis_style` (rcParams serif dpi 300), `save_and_show`, `mask_overlay_rgb`, `plot_mask_overlay_figure`, `make_param_figure`, `save_param_html`, `resolve_sym_limits`, `mpl_cmap_to_plotly_scale`, `fmt_sci`. **Costanti**: `STOKES_PARAM_CONFIG` + `STOKES_PARAM_ORDER` (8 mappe pubblicate per cella B), `STRATI_LABEL_Y_FRAC` (frazioni y per etichette plateau 1L→1R). **Cella E**: `plot_delta_strati_histogram`, `save_delta_strati_histogram_html` (istogramma δ + vline plateau). **S0 cmap**: `make_s0_cmap(channel_idx)` (nero→R/G/B) |
| `slice_fit.py` | Algoritmo F (strati_v2): `build_slice_grid` (slice spessa diagonale), `sample_thick_delta` (media circolare lungo larghezza), `find_auto_crop` (esclude bordi + δ vicini 0/360), `detect_plateaus` (gradient threshold + min_run filter), `fit_layers` (fit δ = m·n through origin con unwrap L/R separato) |
| `pipeline.py` | Orchestratore Pass A + Pass B per cella Load+Stokes. API: `run_pass_a_unified` (streaming RGB 1×38 file), `run_pass_a_per_channel` (sequenziale single-channel), `compute_unified_bg_mask` (mean S0_RGB → Canny mask), `process_channel` (Pass B puro: align + retardance per canale, thread-safe), `apply_saturation_global` (NaN OR fra canali), `load_cache_npz` + `save_cache_npz` (schema: downsample_factor, dataset, unified_mask, per-ch keys) |
| `photoelasticity.py` | Cella I (barraon vs barraoff): `phase_correlation` (FFT + Hanning + interp parabolica subpixel), `shift_dict_inplace` (applica shift a tutti i campi 2D + maschere di un dict canale), `trace_centerline` (peak detection bordi sup/inf colonna-per-colonna), `polyfit_centerline` + `rms_residual`, `build_warp_field` (Δy(x) da fit on/off), `warp_image` (deforma colonna-per-colonna preservando NaN), `composite_rgb`, `normalize_for_display` |

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
