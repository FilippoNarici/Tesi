# TODO — Stato del progetto

Ultimo aggiornamento: 2026-05-12 (refactor team `ipynb-refactor`: `python/analisi.ipynb` singolo + package `python/polarimetro/` + archivio `python/legacy/`)

Questo file è la singola fonte di verità sullo stato di avanzamento. Aggiornare ad ogni task completato. Per istruzioni operative vedere `CLAUDE.md`.

## Capitoli della tesi

| Cap | Titolo | Stato | Note |
|-----|--------|-------|------|
| 1 | Introduzione | ~80% | Pulizia stilistica (em-dash, cliché IA) |
| 2 | Fondamenti teorici | ~90% | Denso, ben citato |
| 3 | Apparato sperimentale | ~95% | Figure setup presenti |
| 4 | Raccolta dati e campioni | ~85% | Formattazione tabella campioni |
| 5 | Analisi dati | ~95% | Pipeline allineata 2026-05-11 (dark frame, saturazione, mascheramento Canny + flood-fill multi-comp, allineamento via fit superfici 2D, ribasamento Poincaré attorno S2, retardance `arctan2` [0°,360°), `WAVEPLATE_AXES_SWAPPED`). Aperti: voce BibTeX Canny 1986; descrizione sorgente spettrale (AvaSpec 2048). |
| 6 | Risultati e discussione | ~75% | Tutte le figure sono placeholder (77 PDF già esistono in `Images/generated/`); tabelle retardance da rimisurare con pipeline arctan2; istogrammi δ pronti come supporto alle misure per-strato |
| 7 | Conclusioni | ~70% | Reggere meglio il passaggio agli sviluppi futuri; menzionare UMAP come esplorazione raffinabile (v. sotto) |

## Consegnabili mancanti (livello tesi)

- [ ] Appendice A: listati dei principali script Python (attualmente placeholder)
- [ ] Ringraziamenti (placeholder — li scrive l'utente)
- [ ] Espansione bibliografia: target 10–15 voci nuove (attualmente 6, quasi tutti libri di testo)
- [ ] Menzione UMAP in cap7 come esplorazione raffinabile (decisione 2026-04-22: i risultati attuali non giustificano una sottosezione in cap6)

## Revisione cap6 per-sample (in corso)

Flusso iterativo, un campione alla volta. Per ogni sample:

1. AI produce sintesi: cosa è scritto attualmente nel `.tex`, quali figure sono già incluse, quali PDF candidati esistono in `Images/generated/<dataset>/`.
2. Utente risponde con: intenzione del sample, misure prese, plot già pronti vs. plot da scrivere/codificare ex novo, focus della discussione fisica.
3. AI rifattorizza la sezione cap6 di quel sample: prosa, figure, caption, eventuali nuovi script Python.
4. Commit per-sample.

| Sample | Stato revisione | Note |
|--------|-----------------|------|
| lambdaquarti_50deg | [ ] | — |
| lambdamezzi_50deg | [ ] | — |
| strati_v2 | [ ] | dipende da B2 (retardance rimisurate) e B4 (istogrammi δ) |
| zucchero | [ ] | UMAP AoLP appena rigenerato (R/G/B) |
| barraon_v2 | [ ] | — |
| barraoff_v2 | [ ] | — |
| righello_v2 | [ ] | — |

## Refactor notebook + package (team `ipynb-refactor`, 2026-05-11/12)

Eseguito da un team di 4 agenti Claude (architect, core_cells, analysis_cells, optional_cells) coordinato da team-lead. 16 commit incrementali con messaggio `[ipynb-refactor]: ...`.

- [x] `python/polarimetro/` package estratto da `final_utils.py` (config, io_raw, stokes, mask, align, retardance, umap_runner, plotting, `__init__`).
- [x] `python/analisi.ipynb` (26 celle): config + dispatcher analisi-per-dataset + Load+Stokes (cache npz) + 9 mappe (AB) + UMAP AoLP/δ + slice δ + fit retardance-vs-strati + istogrammi δ con marker strati + strumenti opzionali off-by-default (G0, debugger, FULL BATCH).
- [x] 11 script originali (`final_*.py`, incluso `final_utils.py`) spostati in `python/legacy/`.
- [x] Smoke test end-to-end su `strati_v2` canale G a DS=4: pipeline completa, cache salvato in `outputs/stokes_strati_v2_DS4.npz` (gitignored).
- [x] `.gitignore` aggiornato con pattern `python/outputs/stokes_*.npz`.
- [x] `CLAUDE.md` (radice + `python/`) e `TODO.md` aggiornati.

Punto d'ingresso unico ora: aprire `python/analisi.ipynb`, impostare `DATASET`/`CHANNEL`/`DOWNSAMPLE_FACTOR`, eseguire. Le analisi si attivano in base al dispatcher.

## TODO notebook `analisi.ipynb` (annotati dall'utente 2026-05-12, sessione post-refactor)

Letti i TODO inline (cell markdown / commenti codice) prima del revert. Otto voci concrete, ordinate per priorità implicita.

- [ ] **N-A** — commentare il codice (rimandato a quando il notebook è completo nel suo design finale, non ora).
- [~] **N-B** — rinominare schema codici analisi: una lettera per operazione (2026-05-14). FATTO `AB` → split in `A` (maschera) + `B` (8 mappe). Ancora da fare: `E-ext` → ? (suggerimento `E`). `C-delta`/`C-aolp` lasciati.
- [x] **N-C** — *(cella Load+Stokes + FULL BATCH)* maschera unica per tutti i canali (2026-05-14). Quando `len(ACTIVE_CHANNELS) > 1`, la pipeline esegue Pass A (load + Stokes + S3 per canale) → calcola `mean(S0_R, S0_G, S0_B)` → `generate_background_mask` UNA volta → Pass B (align + retardance per canale usando la stessa `bg_mask_shared`). Cache npz invalida automaticamente se cambia il flag `unified_mask`. Stessa logica replicata nel loop `FULL BATCH` (`BATCH_UNIFIED_MASK = True`). Quando si seleziona un singolo canale, mantiene comportamento per-canale (no extra load).
- [ ] **N-D** *(cella C-aolp)* — collegato a `N-G`: stessa idea di clustering automatico anche su lambdamezzi.
- [ ] **N-E** *(celle C-aolp e C-delta)* — la griglia UMAP appare sparsa. Verificare se lo stride viene applicato all'immagine downscalata (probabile baco); switch a campionamento random (~10000 punti) con debug plot che mostra dove i punti sono caduti.
- [ ] **N-F** *(cella C-delta)* — bug cache: durante una run lambdamezzi è stata caricata la cache di strati (run precedente). Workaround: restart kernel risolve. Permanente: double-check cache (chiave includere `DATASET` e validare a lettura).
- [ ] **N-G** *(cella C-delta)* — il selettore poligono interattivo non funziona in Jupyter. Trovare soluzione compatibile (plotly select? ipywidgets?). L'interattività serve solo per lambdamezzi/lambdaquarti; per `strati_v2` basta un clustering automatico che identifichi un cluster ben definito. Valutare split delle celle vs duplicazione codice.
- [ ] **N-H** *(cella H fit-strati)* — eliminare i valori placeholder. Usare i dati dai fit precedenti del cella F (slice) come input per il fit retardance-vs-strati.

## Pipeline Python

- [x] Committare lavori in sospeso: saturation accumulator in `final_polarimeter.py` e `final_utils.py` (2026-04-21)
- [x] Committare `python/final_umap.py` (2026-04-21)
- [x] Aggiungere `umap-learn` a `python/requirements.txt` (creato file, 2026-04-21)
- [x] Committare nuove figure in `Images/generated/barraon_v2/` (come stato pre-saturazione, 2026-04-21)
- [x] Integrazione accumulatore saturazione in `final_thesis_figure.py` (A1, 2026-04-21) — tutti i 77 PDF erano prodotti senza maschera
- [x] `final_plot_strati.py`: lunghezze d'onda lette da CSV, valori retardance marcati come placeholder da rimisurare (A4, 2026-04-21)
- [x] B1: rigenerazione completa PDF per tutti i dataset (strati_v2, lambdaquarti_50deg, lambdamezzi_50deg, zucchero, barraon_v2, barraoff_v2, righello_v2), tutti e tre i canali — con pipeline completa (saturazione + dark + arctan2 + allineamento 2D). Batch runner `final_thesis_figure_all.py`; 189 PDF + 189 HTML plotly interattivi in 22.7 min, zero fallimenti (2026-04-21)
- [ ] B2: rerun `final_fit_plot_strati.py` con valori di retardance rimisurati dall'utente
- [x] U1: reimplementare `final_umap.py` con campionamento sparso a risoluzione nativa (2026-04-21). Feature set (S1/S0, S2/S0, S3/S0, DoLP, delta), stride=20 su S0/S1/S2/S3 calcolati a piena risoluzione. Pearson |r(UMAP1, delta)| salita da 0.10 a 0.67 su lambdaquarti/R. bg_mask generata al DOWNSAMPLE_FACTOR standard e upsamplata (il Sobel a piena risoluzione satura di rumore). ~165 s / combo.
- [ ] Tabelle cap6: rimisurare valori di retardance con pipeline arctan2 [0°, 360°) — l'utente si occupa della misura. Istogrammi δ interattivi in `Images/generated/<dataset>/interactive/*_hist_delta.html` aiutano a individuare i picchi (hover = data cursor).
- [ ] UMAP (raffinazione, rimandata a cap7): le tre opzioni aperte 2026-04-22 sono state in parte sciolte. (a) `(sin δ, cos δ)` ciclico — testato 2026-05-11 (U2b), peggio di `no_delta` sia da solo che con Stokes raw. (b) HDBSCAN sopra l'embedding — **rigettato esplicitamente** 2026-05-11 dall'utente: selezione cluster solo manuale via poligono. (c) multi-canale stacked R/G/B → unica embedding — ancora aperto, non tentato. Resta una nota: l'analisi cap7 menziona UMAP come esplorazione raffinabile, non come contributo principale.
- [x] Istogrammi δ per strati_v2: PDF pubblicabile + HTML plotly interattivo con barre colorate twilight in `Images/generated/strati_v2/` (2026-04-22). Script: `python/final_delta_histogram.py`.
- [x] S3 ellipticity correction via Poincaré rotation (2026-04-23). Nuova funzione `align_poincare_ellipticity` in `final_utils.py`: rotazione pixel-wise attorno asse S2 con β(x,y) da fit polinomiale grado 2 di s1_bg e s3_bg su maschera wav-bright (esclude holder lamina). Chiamata nei pipeline dopo `align_reference_frame`. Integrata in `final_polarimeter.py`, `final_thesis_figure.py`, `final_umap.py`. Verifica: |S|² preservato a precisione macchina; residuo s3_bg std 0.083→0.023 su strati_v2/R; δ median 21°→111° (recupera segnale prima biased). Overlay diagnostico nel debug mask plot mostra rosso=holder escluso, ciano=cleaned bg usato per fit β.
- [x] B3: rigenerazione figure su 7 dataset × 3 canali × 9 parametri con correzione Poincaré + nuova `generate_background_mask` Canny (2026-04-25). 189 PDF + 189 HTML in 52.7 min, zero fallback/empty/warn su tutte le 21 combo.
- [ ] B4: rerun `final_delta_histogram.py` su strati_v2 (3 canali) — gli istogrammi δ sono ora calcolati su δ corretto.
- [x] Commit modifiche: `align_poincare_ellipticity` + integrazione + debug plot RGB overlay (2026-04-25).
- [x] M1: rewrite `generate_background_mask` (2026-04-25). Vecchia logica `mean(Sobel) + 1.5% dilation` falliva su 3 combo a DOWNSAMPLE_FACTOR=1 (lambdaquarti R/B, barraoff_v2 R) producendo bg_mask vuota → align_reference_frame e align_poincare_ellipticity skippate → δ/θ sistematicamente errate. Nuova pipeline: Canny (sigma=1.5, low=0.05, high=0.15, scelti via parameter sweep su strati_v2/B) + dark prior (S0_norm < 0.3) + circle expansion (dilation disco) + flood-fill bg da componente connessa al bordo foto + fill_holes sample + opening contorno + erosione di sicurezza. Auto error detection via compactness 4πA/P². Tutte 21 combo OK, zero fallback. Soglie tunate manualmente, robuste su 7 dataset diversi.
- [x] M2: overlay 2-color maschere bg + Poincaré in plot finali (2026-04-25). `final_polarimeter.py` debug plot 3x3 e `final_thesis_figure.py` parametro `mask`: pixel coperti da entrambe = grayscale modulato S0; XOR (una sola, tipicamente holder lamina) = rosso × 0.5 × S0; nessuna (sample / fuori scena) = rosso × S0. Legenda patch in basso a destra.
- [x] D1: `final_slice_debug.py` (2026-04-23, esteso 2026-04-24) — slice diagonale (141°, anchor (767, 422) px nativi) attraverso gli strati. Auto-crop su soglia δ ∈ [margin, 360-margin] + ignore band; rilevamento plateau con gradiente; etichette 1L–5–1R; fit through-origin con unwrap per-side cumulativo. Single PNG output. Eseguito su strati_v2 R/G/B.
- [ ] D2: anomalia 3R-B (47° asimm vs 14-21° su G/R) **ancora non spiegata**. L'asimmetria è specifica del singolo strato (3) nel singolo canale (B), non presente negli altri strati né negli altri canali — incompatibile con asimmetria fisica generica del campione (che si manifesterebbe in tutti gli strati e canali in modo proporzionale alla slope). Tentativi 2026-04-24 (tutti scartati come cause): (a) `WAV_HOLDER_THRESHOLD` 0.7→0.5 inerte (escluse solo 200 px in più, β extrapolazione invariata, codice rimosso); (b) frame alignment FFT phase-corr pol+wav — verificato corretto (pol26 a 260° shift reale 13.16 px peak/med=36, altri 35 frame <0.03 px) ma riduce 3L-3R solo da 47.8° a 43.9°, codice rimosso; (c) DoP slice — DoP_min ≈ DoP_med ovunque, DoP 3L=0.45 ≈ 3R=0.43 simmetrico → no depolarizzatore locale; (d) verifica numerica: vettori Stokes 3L e 3R su posizioni diverse della sfera con stesso |raggio|. Cause residue da indagare: chromatic registration B vs R/G (anchor slice mappato su posizioni fisiche leggermente diverse); thin-film interference selettiva in B; aliasing Bayer su griglia B (mezza densità di campionamento); risonanza ottica wavelength-specific. Codice diagnostico β/Stokes/DoP rimosso da `final_slice_debug.py` per pulizia.
- [x] D3: `WAV_HOLDER_THRESHOLD` config in `final_utils.py` (2026-04-24). Parametrizza la soglia hardcoded di `align_poincare_ellipticity` (default invariato 0.7).
- [x] M3: rewrite maschera s3 in `align_poincare_ellipticity` (2026-04-26). Vecchia logica `wav > 0.7 × median(wav[bg]) + erosione 1%` sostituita con: `wav_mean = (I+45+I-45)/2`, threshold dark = `WAV_HOLDER_THRESHOLD × max(wav_mean[bg])` (default 0.50, semantica MAX non median), unione con banda di bordo immagine a `dilate_r/2` (75 px nativi), poi dilation disco `150 // DOWNSAMPLE_FACTOR` (150 px nativi). `bg_mask_s3 = bg_mask & ~holder`. Erosione safety di `generate_background_mask` (S1/S2) scalata `100 // DOWNSAMPLE_FACTOR` (100 px nativi). Test su strati_v2/B (DS=10): residuo fit s3_bg 0.0623 → 0.0120 (ratio 0.40 → 0.08), s3_bg post std 0.0593 → 0.0118. Debug plot maschera: XOR ora gradient nero→blu (canale B = wav_mean_n) per verifica visiva soglia/dilation.
- [x] M4: rerun B3 batch DS=4 (21 combo) con nuova maschera s3 + erosione scalata + multi-component flood-fill (2026-04-26). 25.0 min, 21/21, zero warning, zero fallimenti. Soglia 20% del max per filtrare leak interni (es. righello_v2/B compactness 0.048 → 0.478).
- [x] M5: fix flood-fill multi-componente in `generate_background_mask` (2026-04-26). Vecchia logica teneva solo la componente più grande border-touching → su zucchero il bg veniva spezzato in due dalla bottiglia verticale e metà finiva in sample. Fix: union di tutte le componenti border-touching con size >= 20% del max, per (a) coprire bg legittimi splittati da sample verticali e (b) escludere leak interni dell'edge sample (es. righello che esce dal frame e ha edges Canny incompleti in B con DS=4).
- [x] U2a: parametrizzazione `final_umap.py` per coloraggio AoLP **o** δ (2026-05-11). Nuovo config top-of-script `INTERACTIVE_COLOR_BY = 'aolp'|'delta'`, helper `_color_spec` che incapsula cmap/range/etichette/file di export, refactor `_interactive_panel` + `_export_panels` + `run_interactive` + `run_interactive_dataset` + `run_dataset_rgb` per accettare `color_by`. CLI flag `--color-by aolp|delta`. Cache npz v2 include `delta_deg` (cache v1 ricomputata). Export delta in `Images/generated/<dataset>/delta_umap/<CH>/{delta_map,umap_scatter,delta_hist}.pdf`; modalità delta usa cmap `twilight` ciclica range 0-360 con bande di esclusione ±20° sull'istogramma.
- [x] U2b: feature set di UMAP per coloraggio AoLP e δ (2026-05-11). Tentativi: `cyclic_delta` `(s1, s2, s3, DoLP, sin δ, cos δ)`, `retardance_focus` `(sin δ, cos δ, sin 2θ, cos 2θ, DoLP)`, `stokes_axis` `(s1, s2, s3, sin 2θ, cos 2θ)` — tutti peggio della baseline `no_delta` `(s1, s2, s3, DoLP)` su strati_v2/R. **Decisione finale**: entrambe le modalità usano `no_delta`. Modi alternativi rimossi dal codice; rimane il dispatcher `_default_feature_mode(color_by)` con due rami separati per modifica futura indipendente quando si volesse sperimentare feature set dedicati per δ. Cache npz separato per feature_mode (`umap_<dataset>_<CH>_no_delta_cache.npz`); vecchi nomi senza suffisso non più caricati. CLI flag `--feature-mode no_delta` solo (lista riespanderà se si aggiungono modi).
- [x] U2c: filtro confidenza δ via `sin²(2θ)` in `_build_validity_mask` (2026-05-11). Config top-of-script `UMAP_AXIS_CONFIDENCE_MIN = 0.05`. Esclude pixel con asse veloce vicino a 0°/90°, dove le formule `cos δ` / `sin δ` sono degeneri e il peso continuo della pipeline retardance spinge δ artificialmente a 0. Pulisce il blob fittizio δ≈0 che dominava lo scatter UMAP su strati_v2/B. Cache schema bumped a v3 (aggiunge `axis_conf_min`): cache v2 vengono invalidate al primo accesso quando la soglia cambia, garantendo embedding consistente con la valid_mask corrente.
- [x] U2d: poligono interattivo guidato da tastiera (2026-05-11). Aggiunta vertici via tasto `a` alla posizione corrente del mouse, click sinistro liberato per toolbar matplotlib (zoom rect / pan / home). Chiusura poligono via click destro (≥3 vertici). `enter` resta dedicato all'export PDF, `esc` annulla la sequenza in corso, `r` reset overlay. Rimosso lo stato `active` e l'hotkey toggle `d` introdotti in via intermedia: il selettore è sempre live ma gestito da tastiera, niente conflitti con zoom/pan.
- [x] U2e: fit UMAP condiviso fra coloraggio AoLP e δ (2026-05-11). Cache filename rinominato `umap_<dataset>_<CH>_cache.npz` (senza feature_mode), poiché entrambe le modalità di coloraggio puntano allo stesso fit `no_delta`: cambia solo cmap, range, etichette e sottocartella di export (`aolp_umap/` vs `delta_umap/`). Batch `run_dataset_rgb` accetta `color_by='both'` (CLI `--color-by both`) per esportare entrambe le viste in un solo passaggio, senza recomputare l'embedding. Interactive accetta solo `'aolp'` o `'delta'` (pannello mostra una vista alla volta). Vecchi cache `umap_<dataset>_<CH>_no_delta_cache.npz` non più caricati; eliminare manualmente per pulizia disco.

## Miglioramenti Python (se il tempo lo permette)

- [ ] Centralizzare numeri magici in `python/config.py` (o TOML)
- [ ] Docstring di modulo per ogni script
- [ ] Test minimale pytest per le operazioni Stokes (sanity check, ~5 casi)
- [ ] Separare logica di calcolo da plotting
- [ ] Cache del fit polinomiale 2D per evitare ricalcoli

## Domande aperte per l'utente (2026-04-21)

Risolte nella sessione Phase 2:
- [x] Figure cap6: selezione per-campione basata sul fenomeno fisico da mostrare (R, G, B, interpolazione, o S0 greyscale come vista naked-eye), non regola uniforme. Gate per-sample in C2.
- [x] Tabelle retardance: l'utente rimisura personalmente. AI prepara solo scheletri LaTeX vuoti con struttura corretta.
- [x] UMAP: risultati attuali insufficienti per il downsampling. Implementare campionamento sparso a risoluzione nativa (U1), poi decidere fra cap6, cap7, o mention breve.

Ancora aperte:
- [ ] Appendice A: quali script in full, quali come estratti? (gate in C7)

Risolte 2026-04-22:
- [x] ~~UMAP feature set: confermato `(S1/S0, S2/S0, S3/S0, DoLP, delta)`. Variante `no_delta` testata → UMAP perde struttura senza hint di δ.~~ **Decisione rovesciata 2026-05-11 (U2b)**: feature set definitivo `no_delta = (s1, s2, s3, DoLP)`. Tentativi con δ esplicito (full / cyclic_delta) o con θ ciclico (retardance_focus / stokes_axis) tutti peggio su strati_v2 dopo pipeline arctan2 + Poincaré.
- [x] UMAP collocazione: **cap7**, non cap6. I risultati mostrano recupero mono-dimensionale della retardance (|r|~0.9) ma zero clustering per strato; non rappresentativo come strumento di analisi al livello attuale. Resta la possibilità di raffinazione (HDBSCAN rigettata dall'utente; cos/sin δ testato e scartato; multi-canale stacked ancora non tentato).

## Infrastruttura Claude-friendly (ora in vigore)

- `CLAUDE.md` (radice) — persona, stile, navigazione, insidie, confine umano.
- `TODO.md` (questo file) — stato vivo.
- `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` — guide nidificate.
