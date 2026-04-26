# python/ — Guida al codice di analisi

Questo file è letto da Claude quando lavora nella directory `python/`. Per regole di stile e persona vedere la `CLAUDE.md` alla radice del repo.

## Inventario script (in ordine di rilevanza)

| Script | Tipo | Scopo |
|--------|------|-------|
| `final_utils.py` | libreria | Funzioni comuni: RAW loading, Stokes (pseudo-inversa), S3 via lamina λ/4, maschere, allineamento 2D (S3 axis) + ellitticità Poincaré (S2 axis), retardance arctan2, saturation/dark handling |
| `final_polarimeter.py` | entry point principale | Pipeline completa su un dataset: Stokes + derivate + plot 3×3 (con overlay RGB per bg mask Poincaré) |
| `final_thesis_figure.py` | generatore figure | Produce PDF per tesi (S0/S1/S2/S3/DoLP/AoLP/δ/θ/mask) con stile pubblicazione |
| `final_umap.py` | analisi | UMAP 2D di vettori di Stokes, colorato per retardance |
| `final_delta_histogram.py` | figura tesi | Istogrammi pubblicabili di δ (PDF + HTML plotly) con barre colorate twilight |
| `final_plot_strati.py` | analisi specifica | Fit retardance-vs-strati (nastro adesivo multistrato); fit 1/λ² per dispersione |
| `final_slice_debug.py` | diagnostica | Slice diagonale spessa di δ: auto-crop su soglia angolare + ignore band, rilevamento plateau, etichette 1L–5–1R, fit through-origin con unwrap per-side cumulativo. Single PNG `slice_delta_<dataset>_<channel>.png`. Utile per quantificare asimmetrie left/right per strato. |
| `final_slice_figure.py` | figura tesi | Versione publication-style del precedente: 3 pannelli (mappa δ con banda evidenziata, profilo 1D con plateau etichettati, fit through-origin) in stile coerente con `final_thesis_figure`. PDF + HTML plotly (profilo interattivo). Default su `strati_v2`. |
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

- **Configurazione in testa al file**: `TARGET_FOLDER`, `TARGET_CHANNEL_IDX`, `DOWNSAMPLE_FACTOR`, `ENABLE_BACKGROUND_ALIGNMENT`, `USE_RAW_BAYER`, `DARK_FRAME_PATH`, `SATURATION_FRACTION`, `WAV_HOLDER_THRESHOLD` (frazione del median wav-bg per maschera holder lamina nel rebase Poincaré, default 0.7).
- `load_raw_image`, `load_rotation_sequence` — caricamento DNG + dark subtract + downsampling.
- `calculate_linear_stokes` — S0/S1/S2 via pseudo-inversa sui 36 angoli.
- `calculate_s3` — S3 da lamina λ/4 con correzione `sin(δ(λ))` (modello Ghosh del quarzo). Cache `_WAV_INTENSITY_CACHE` = I(+45)+I(-45), usata a valle per mask holder.
- `quartz_birefringence`, `waveplate_retardance` — modelli dispersivi.
- `generate_background_mask` — segmentazione Canny + dark prior + flood-fill (2026-04-25). Pipeline: normalizza S0 in [0,1] → Canny (sigma=1.5, low=0.05, high=0.15) → dilation con disco (circle expansion) → unione con `S0_norm < 0.3` (dark prior, holder neri) → closing → label complemento → bg = componente che tocca il bordo foto + max area → fill_holes su sample → opening contorno → erosione di sicurezza. Fallback brightness se la mask risulta degenere; auto-warning compactness `4πA/P²` < 0.05. Richiede `scikit-image`.
- `align_reference_frame` — rotazione S1/S2 attorno asse S3 (equatore Poincaré) con fit superfici polinomiali 2D sullo sfondo. Zera s2_bg.
- `align_poincare_ellipticity` (2026-04-23) — rotazione S1/S3 attorno asse S2 pixel-wise, β(x,y) da fit grado 2 di s1_bg e s3_bg su cleaned wav-bright mask (holder lamina escluso via `_WAV_INTENSITY_CACHE > 0.7 × median`). Complementare a `align_reference_frame`: la composizione porta bg Stokes → (1,0,0), assunto dalle formule retardance. Cache cleaned mask in `_POINCARE_BG_MASK_CACHE` per debug plot.
- `calculate_dolp_aolp`, `calculate_retardance_and_fast_axis` — derivate fisiche. **Retardance in [0°, 360°) via arctan2 dal 2026-04**. Assume base Poincaré già ribalzata via `align_poincare_ellipticity`.
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
- Pipeline ordine obbligato: `calculate_s3` → `align_reference_frame` → **`align_poincare_ellipticity`** → `calculate_retardance_and_fast_axis`. Il rebasing Poincaré richiede `_WAV_INTENSITY_CACHE` popolato da `calculate_s3`.
- `align_poincare_ellipticity` modifica S1 e S3 in-place logicamente (ritorna nuovi array). Riassegnare al nome originale nei chiamanti: `S1, S3 = utils.align_poincare_ellipticity(S0, S1, S3, bg_mask)`.

## Test

Nessuna suite di test al momento. Validazione via `final_fit.py` e confronto con i campioni di calibrazione (λ/2, λ/4, nastro multistrato).
