# TODO — Stato del progetto

Ultimo aggiornamento: 2026-04-25 (rewrite `generate_background_mask` Canny + B3 batch)

Questo file è la singola fonte di verità sullo stato di avanzamento. Aggiornare ad ogni task completato. Per istruzioni operative vedere `CLAUDE.md`.

## Capitoli della tesi

| Cap | Titolo | Stato | Note |
|-----|--------|-------|------|
| 1 | Introduzione | ~80% | Pulizia stilistica (em-dash, cliché IA) |
| 2 | Fondamenti teorici | ~90% | Denso, ben citato |
| 3 | Apparato sperimentale | ~95% | Figure setup presenti |
| 4 | Raccolta dati e campioni | ~85% | Formattazione tabella campioni |
| 5 | Analisi dati | ~85% | Allineare descrizione pipeline allo stato attuale (arctan2, saturazione, dark frame, superfici 2D, WAVEPLATE_AXES_SWAPPED); chiarire sorgente spettrale |
| 6 | Risultati e discussione | ~75% | Tutte le figure sono placeholder (77 PDF già esistono in `Images/generated/`); tabelle retardance da rimisurare con pipeline arctan2; istogrammi δ pronti come supporto alle misure per-strato |
| 7 | Conclusioni | ~70% | Reggere meglio il passaggio agli sviluppi futuri; menzionare UMAP come esplorazione raffinabile (v. sotto) |

## Consegnabili mancanti (livello tesi)

- [ ] Appendice A: listati dei principali script Python (attualmente placeholder)
- [ ] Ringraziamenti (placeholder — li scrive l'utente)
- [ ] Espansione bibliografia: target 10–15 voci nuove (attualmente 6, quasi tutti libri di testo)
- [ ] Menzione UMAP in cap7 come esplorazione raffinabile (decisione 2026-04-22: i risultati attuali non giustificano una sottosezione in cap6)

## Pipeline Python

- [x] Committare lavori in sospeso: saturation accumulator in `final_polarimeter.py` e `final_utils.py` (2026-04-21)
- [x] Committare `python/final_umap.py` (2026-04-21)
- [x] Aggiungere `umap-learn` a `python/requirements.txt` (creato file, 2026-04-21)
- [x] Committare nuove figure in `Images/generated/barraon_v2/` (come stato pre-saturazione, 2026-04-21)
- [x] Integrazione accumulatore saturazione in `final_thesis_figure.py` (A1, 2026-04-21) — tutti i 77 PDF erano prodotti senza maschera
- [x] `final_plot_strati.py`: lunghezze d'onda lette da CSV, valori retardance marcati come placeholder da rimisurare (A4, 2026-04-21)
- [x] B1: rigenerazione completa PDF per tutti i dataset (strati_v2, lambdaquarti_50deg, lambdamezzi_50deg, zucchero, barraon_v2, barraoff_v2, righello_v2), tutti e tre i canali — con pipeline completa (saturazione + dark + arctan2 + allineamento 2D). Batch runner `final_thesis_figure_all.py`; 189 PDF + 189 HTML plotly interattivi in 22.7 min, zero fallimenti (2026-04-21)
- [ ] B2: rerun `final_plot_strati.py` con valori di retardance rimisurati dall'utente
- [x] U1: reimplementare `final_umap.py` con campionamento sparso a risoluzione nativa (2026-04-21). Feature set (S1/S0, S2/S0, S3/S0, DoLP, delta), stride=20 su S0/S1/S2/S3 calcolati a piena risoluzione. Pearson |r(UMAP1, delta)| salita da 0.10 a 0.67 su lambdaquarti/R. bg_mask generata al DOWNSAMPLE_FACTOR standard e upsamplata (il Sobel a piena risoluzione satura di rumore). ~165 s / combo.
- [ ] Tabelle cap6: rimisurare valori di retardance con pipeline arctan2 [0°, 360°) — l'utente si occupa della misura. Istogrammi δ interattivi in `Images/generated/<dataset>/interactive/*_hist_delta.html` aiutano a individuare i picchi (hover = data cursor).
- [ ] UMAP (raffinazione, rimandata a cap7): provare (sin δ, cos δ) per ciclicità, HDBSCAN sopra l'embedding, o multi-canale stacked. Attualmente in cap7 come cenno breve, non come contributo principale.
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
- [x] UMAP feature set: confermato `(S1/S0, S2/S0, S3/S0, DoLP, delta)`. Variante `no_delta` testata → UMAP perde struttura senza hint di δ.
- [x] UMAP collocazione: **cap7**, non cap6. I risultati mostrano recupero mono-dimensionale della retardance (|r|~0.9) ma zero clustering per strato; non rappresentativo come strumento di analisi al livello attuale. Resta la possibilità di raffinazione (HDBSCAN, cos/sin δ, multi-canale).

## Infrastruttura Claude-friendly (ora in vigore)

- `CLAUDE.md` (radice) — persona, stile, navigazione, insidie, confine umano.
- `TODO.md` (questo file) — stato vivo.
- `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` — guide nidificate.
- `prompts/next-session-deep-review.md` — prompt per sessione di revisione profonda.
