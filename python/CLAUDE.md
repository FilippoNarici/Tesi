# python/ — Guida al codice di analisi

Questo file è letto da Claude quando lavora nella directory `python/`. Per regole di stile e persona vedere la `CLAUDE.md` alla radice del repo.

## Inventario script (in ordine di rilevanza)

| Script | Tipo | Scopo |
|--------|------|-------|
| `final_utils.py` | libreria | Funzioni comuni: RAW loading, Stokes (pseudo-inversa), S3 via lamina λ/4, maschere, allineamento 2D, retardance arctan2, saturation/dark handling |
| `final_polarimeter.py` | entry point principale | Pipeline completa su un dataset: Stokes + derivate + plot 3×3 |
| `final_thesis_figure.py` | generatore figure | Produce PDF per tesi (S0/S1/S2/S3/DoLP/AoLP/δ/θ/mask) con stile pubblicazione |
| `final_umap.py` | analisi | UMAP 2D di vettori di Stokes, colorato per retardance |
| `final_plot_strati.py` | analisi specifica | Fit retardance-vs-strati (nastro adesivo multistrato); fit 1/λ² per dispersione |
| `final_monochrome_approx.py` | utility spettrale | Stima lunghezza d'onda centroide per canale RGB del sensore + sorgente |
| `final_fit.py` | debugger interattivo | Ispettore pixel-per-pixel con animazione intensità |

## Ordine operativo tipico

1. `final_monochrome_approx.py` una tantum per `outputs/rgb_wavelengths.csv`.
2. Impostare `TARGET_FOLDER` in `final_utils.py` sul dataset di interesse.
3. `final_polarimeter.py` per Stokes completo + plot 3×3 di controllo.
4. `final_thesis_figure.py` per PDF pubblicabili in `Images/generated/<dataset>/`.
5. Analisi specifiche: `final_plot_strati.py`, `final_umap.py`.
6. `final_fit.py` per debug pixel-per-pixel quando qualcosa non torna.

## Punti chiave di `final_utils.py`

- **Configurazione in testa al file**: `TARGET_FOLDER`, `TARGET_CHANNEL_IDX`, `DOWNSAMPLE_FACTOR`, `ENABLE_BACKGROUND_ALIGNMENT`, `USE_RAW_BAYER`, `DARK_FRAME_PATH`, `SATURATION_FRACTION`.
- `load_raw_image`, `load_rotation_sequence` — caricamento DNG + dark subtract + downsampling.
- `calculate_linear_stokes` — S0/S1/S2 via pseudo-inversa sui 36 angoli.
- `calculate_s3` — S3 da lamina λ/4 con correzione `sin(δ(λ))` (modello Ghosh del quarzo).
- `quartz_birefringence`, `waveplate_retardance` — modelli dispersivi.
- `generate_background_mask` — edge + brightness, tiene regioni >20% dell'isola più grande, non taglia più la vignette.
- `align_reference_frame` — rotazione S1/S2 con fit di superfici polinomiali 2D sullo sfondo.
- `calculate_dolp_aolp`, `calculate_retardance_and_fast_axis` — derivate fisiche. **Retardance in [0°, 360°) via arctan2 dal 2026-04**.
- `reset_saturation_accumulator`, `get_saturation_mask` — accumulatore OR globale dei pixel saturati su tutti i frame.

## Dati

- Input RAW: `./raw/<dataset>/pol/pol*.dng` (36 angoli, passi di 10°) + `./raw/<dataset>/wav/wav±45.dng` + `./raw/<dataset>/dark.dng`.
- Spettri: `./spettri/Samsung-Galaxy-S22-Rear-Telephoto-Camera.csv` (risposta sensore), `./spettri/rgb.csv` (sorgente).
- Output analisi: `./outputs/*.csv`, `./outputs/*.pdf`, `./outputs/umap_*.png`.
- Output figure tesi: `../Images/generated/<dataset>/{R,G,B}_<parametro>.pdf`.

## Insidie note

Vedi `CLAUDE.md` (radice), sezione "Insidie tecniche note". In breve:
- Retardance arctan2 [0°, 360°); non usare più `arccos`.
- Dataset `lambdamezzi_50deg` richiede `WAVEPLATE_AXES_SWAPPED`.
- Lamina λ/4 ottimizzata a 633 nm — correzione dispersiva necessaria.
- Saturation accumulator va resettato a inizio run (`reset_saturation_accumulator()`).
- `umap-learn` va installato a parte se non in `requirements.txt`.

## Test

Nessuna suite di test al momento. Validazione via `final_fit.py` e confronto con i campioni di calibrazione (λ/2, λ/4, nastro multistrato).
