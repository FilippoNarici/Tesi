# TODO — Stato del progetto

Ultimo aggiornamento: 2026-05-21 (pass humanize em-dash + tell AI su cap1–cap7 con skill `humanizer`; cap3 "polarizzatore lineare di forma circolare"; cap4 tabella campioni sistemata. Prima, 2026-05-20: revisione cap6 7 sample bozza, lambdamezzi chiuso multi-ordine via b<1, anomalia 3R-B chiusa inspiegata, superate voci legacy B2/B4/tabelle-cap6. TUTTE le sezioni cap5/cap6 DA RIVEDERE MANUALMENTE. Vedi memory `project_waveplate_multiorder.md`, `project_strati_3R_B_anomaly.md`, `feedback_chapters_manual_review.md`)

Questo file è la singola fonte di verità sullo stato di avanzamento. Aggiornare ad ogni task completato. Per istruzioni operative vedere `CLAUDE.md`.

## Capitoli della tesi

| Cap | Titolo | Stato | Note |
|-----|--------|-------|------|
| 1 | Introduzione | DONE (bozza, DA RIVEDERE) | Em-dash + tell AI rimossi (humanizer) 2026-05-21. Claim costo riscritto 2026-05-21 (deep research mercato): puntuale ~qualche k€, full-Stokes/Mueller imaging decine–centinaia k€; "2 ordini" scoped a Classi 3–4; DoFP lineare non misura S3. Solo ordini di grandezza, no cifra puntuale. Paragrafo prior-art (7 \cite verificati). Nessun TODO inline aperto. |
| 2 | Fondamenti teorici | ~90% | Denso, ben citato |
| 3 | Apparato sperimentale | ~95% | Figure setup presenti |
| 4 | Raccolta dati e campioni | ~90% | Tabella campioni sistemata (colonne X, full textwidth); em-dash + copula avoidance rimossi |
| 5 | Analisi dati | ~99% | Rewrite end-to-end 2026-05-19 allineato a pipeline `polarimetro` + notebook `analisi.ipynb`: aggiunte sez. organizzazione pipeline 2-pass + cache npz, dispersione quarzo Ghosh, sez. nuove UMAP/HDBSCAN diagnostica, slice + fit dispersione `k/λ^p`, fotoelasticità warp ΔS3, riscrittura sez. visualizzazione (8 PDF per canale, no più 3×3). AvaSpec 2048 descritto. BibTeX Ghosh1999/Canny1986/McInnes2018/Campello2013 verificati crossref + cablati `\cite` (2026-05-21). |
| 6 | Risultati e discussione | ~90% | Tutti i 7 sample revisionati 2026-05-20 (BOZZA, DA RIVEDERE): righello (apertura/panoramica), lamine λ/4+λ/2, nastro strati, zucchero, trave. Figure reali subfloat, dati da pipeline corrente. Rimossa vecchia sec:validazione (misura a vuoto falsa). Ordine: righello → lamine → nastro → versatilità (zucchero, trave). λ/2 = multi-ordine concluso (b<1, ordine indeterminato); anomalia 3R-B CHIUSA (inspiegata, nessun impatto su fit); barra solo qualitativa. Em-dash + tell AI rimossi. **Discussione incertezza aggiunta 2026-05-21** (sec:discussione): no errore calibrato (serve calibrazione su standard a ritardanza+incertezza nota, assente per prototipo); accordo con teoria nell'ordine di pochi gradi (λ/4 vs Ghosh ≤4° come ordine di grandezza, non barra calibrata); gerarchia precisione AoLP/DoLP > δ (δ ha catena più lunga: S3+λ/4+Ghosh+Poincaré+wrap). SCARTATO l'uso di σ cluster (√(−2 ln R)) come errore: sample+clustering dependent. **tab:confronto riscritta 2026-05-21**: 4 colonne (Questo lavoro/Puntuale/DoFP/Full-Stokes-Mueller imaging), full textwidth, cifre da deep research (puntuale ~3-6k€, DoFP ~2-2,5k€ ma no-S3, full-Stokes/Mueller 3·10⁴–>10⁵€); frase introduttiva adattata (DoFP rinuncia a S3, sistemi full-Stokes/Mueller 2-3 ordini più cari). Aggiunta riga "Accuratezza (ordine di grandezza)": prototipo ~1-5° (vs teoria, NON calibrato), PAX ±0,25°, DoFP <0,5° (σ AoLP post-cal), Mueller/ellissometro ≲0,1° — verificati da spec; caveat in caption (apples-to-oranges esplicitato). Resta: revisione manuale + `% TODO` interno lettura ΔS3 barra. |
| 7 | Conclusioni | ~70% | Reggere meglio il passaggio agli sviluppi futuri; menzionare UMAP come esplorazione raffinabile (v. sotto) |

## Consegnabili mancanti (livello tesi)

- [ ] Appendice A: listati dei principali script Python (attualmente placeholder)
- [ ] Ringraziamenti (placeholder — li scrive l'utente)
- [x] Espansione bibliografia (2026-05-21): `.bib` ora a 17 voci (era 6), tutte DOI-verificate crossref e tutte citate. 4 method (Ghosh/Canny/McInnes/Campello → cap5) + 7 stato-dell'arte low-cost/imaging (Burggraaff2020ispex, Gonzalez2020colposcope, Louie2021skin, Gallitto2024malus, Bernard2020polarimeter, Baek2022lensless, Gu2022fullstokes → paragrafo prior-art cap1, no niche-positioning, spiega costo prodotto equivalente). Gemini aveva allucinato 2 DOI su 7 (iSPEX2 talk→paper, Baek rivista/vol/DOI sbagliati) + 1 autore (Bernard primo, non Mendez).
- [ ] Menzione UMAP in cap7 come esplorazione raffinabile (decisione 2026-04-22: i risultati attuali non giustificano una sottosezione in cap6)

## TODO inline nei file `.tex` (ri-scansionati 2026-05-21)

Commenti `% TODO` presenti nei sorgenti LaTeX, da risolvere. Scan completo 2026-05-21: i capitoli sono puliti (solo titoli + separatori `% ----`); tutti i `% TODO` residui vivono in `cap6_risultati.tex` e `Thesis.tex`.

- [x] Em-dash su TUTTA la tesi (skill `humanizer` installata in `~/.claude/skills/humanizer`) — fatto 2026-05-20: cap1–cap6, em-dash (`---` e unicode `—`) sostituiti con virgole/parentesi/due punti; cap1 anche false-range "spaziano da…a…"; subcaption "θ — canale R" → "θ, canale R". Restano solo i `% ----` separatori di commento (invisibili). Applicata SOLO la rimozione dei pattern AI del plugin, NON la parte "soul/prima persona" (conflitta con lo stile formale tesi). Pass humanize completo cap1–cap7 fatto 2026-05-20: oltre agli em-dash, rimossi copula avoidance (costituisce/funge da → è/fornisce) in cap4/cap5/cap6, parole gonfiate ("fondamentale" cap2, "chiave"→"determinante" e "robusto"→"solido" cap6), cliché "aprirebbe la strada"→"estenderebbe" (cap7), false-range cap1. La tesi è in italiano formale già asciutto: pochi tell trovati, niente riscritture forzate su prosa pulita. NON applicata la parte "soul/prima persona" del plugin (incompatibile con stile tesi). Possibile-refuso segnalato all'utente: cap3 "polarizzatore lineare circolare" (contraddittorio).
- [x] `chapters/cap1_introduzione.tex:8,11` (2026-05-21) — costo riscritto con deep research di mercato (Gemini, verificato contro listini reali: Thorlabs PAX1000 puntuale ~3,7k$ distributore / ~6,1k€ listino UE; FLIR/Lucid DoFP lineare ~2,1–2,4k$ ma SOLO S0/S1/S2, no S3; Bossa Nova SALSA full-Stokes imaging >30k€; J.A. Woollam RC2 Mueller 50–150k$). Riscritto in ordini di grandezza: puntuale ~qualche k€; full-Stokes/Mueller imaging decine–centinaia k€. "Due ordini di grandezza" scoped esplicitamente ai sistemi imaging full-Stokes/Mueller (Classi 3–4). NIENTE \cite ancora (vedi sotto: voci BibTeX smartphone-polarimetry da verificare).
- [x] `chapters/cap4_campioni.tex:9` (2026-05-20) — tabella campioni: full `\textwidth`, colonne Fenomeno+Validazione entrambe `X` (spazio condiviso), `\raggedright` + `\small`. Risolto il wrapping brutto della terza colonna.
- [x] `chapters/cap5_analisi.tex` (2026-05-21) — 4 voci method BibTeX scritte, DOI verificati via crossref, `\cite` cablati (commenti `% TODO` rimossi): `Ghosh1999dispersion`, `Canny1986edge` (vol PAMI-8(6)), `McInnes2018umap` (arXiv DOI 10.48550/arXiv.1802.03426), `Campello2013hdbscan` (LNCS 7819, pp 160-172).
> NB 2026-05-21: molti commenti utente erano stati scritti su Overleaf e sincronizzati su GitHub solo durante un rebase successivo; il catalogo sotto è il set completo dopo la sync. 13 commenti totali.

**Azione AI possibile (contenuto / struttura):**
- [ ] `chapters/cap3_apparato.tex:58` — metodo per ricavare $S_3$ preso dal manuale di laboratorio Polimi: aggiungere `\cite{manuale_polarizzazione}` (voce già in bib).
- [ ] `chapters/cap4_campioni.tex:31` — spiegare in brevissimo perché birifrangenza (polimero stirato).
- [ ] `chapters/cap4_campioni.tex:52` — le frange NON sono visibili: si osserva variazione di $S_3$ ma poco altro. Non parlare di "frange" ma di variazione delle proprietà di birifrangenza; analisi prettamente qualitativa, no quantitativo. Da aggiornare.
- [ ] `chapters/cap5_analisi.tex:8` — `sec:organizzazione_pipeline` chiaro ma disordinato, non segue bene l'ordine logico della catena: riorganizzare.
- [ ] `chapters/cap5_analisi.tex:33` — downsample: il testo dice "$f = 4$–$20$" ma in realtà è stato usato $f = 4$ (arbitrario) su tutti i dataset. Correggere il testo.
- [ ] `chapters/cap5_analisi.tex:44` — prima della risposta in assorbimento, nota sullo spettro misurato: G e B omogenei e larghi, R con picchi definiti (uso di KSF, firma spettrale che coincide).
- [x] `chapters/cap6_risultati.tex:98` (2026-05-21) — float "scavalcati"/spostati di pagina: RISOLTO convertendo TUTTI i float (figure + tabelle, cap3/cap4/cap6) da `[htbp]` a `[H]` del package `float` (già caricato Thesis.tex:47). Ora le figure/tabelle sono ancorate al punto esatto del sorgente, come testo, e il testo non le scavalca. Tradeoff noto di `[H]`: se un float non entra in fondo pagina, viene spinto alla pagina successiva lasciando uno spazio bianco (no text-flow oltre il float). Anche le tabelle convertite per coerenza (utente può chiedere revert se voleva solo figure).

**Serve asset / generazione:**
- [ ] `chapters/cap3_apparato.tex:44` — inserire foto del pattern Bayer RGGB (immagine Wikipedia Commons `File:Bayer_pattern_on_sensor.svg`, verificare licenza prima dell'uso).
- [ ] `chapters/cap5_analisi.tex:52` — inserire plot G0 (analisi spettrale RGB; output di `RUN_SPECTRA` in `python/outputs/Analisi_Spettrale_S24_RGB.pdf`).

**Utente / confine umano:**
- [ ] `chapters/cap6_risultati.tex:376` — **lettura qualitativa ΔS3 barra** (dove compare il segnale sotto carico, segno, localizzazione al vincolo): confine di interpretazione umana, spetta all'utente.
- [ ] `Thesis.tex:203` — **verificare la rilevanza delle fonti** una a una fornendo il fulltext a un modello (commento utente). NB: i DOI sono già verificati per esistenza + metadata via crossref (2026-05-21); questo è un check di *pertinenza del contenuto*, non di esistenza.
- [ ] `Thesis.tex:217` — Appendice A "Codice sorgente": inserire listati. ATTENZIONE: il commento cita script legacy (`final_utils.py`, `final_polarimeter.py`) ora archiviati in `python/legacy/`; l'appendice deve listare il package corrente `polarimetro/` + `analisi.ipynb`, non i legacy.
- [ ] `Thesis.tex:245` — sostituire placeholder con ringraziamenti reali (utente).

## Revisione cap6 per-sample (in corso)

> **DA RIVEDERE MANUALMENTE**: tutte le sezioni `.tex` redatte dall'AI vanno verificate manualmente dall'utente prima della consegna (prosa, numeri, figure, interpretazione fisica). Lo stato "[x]" nella tabella indica "bozza scritta dall'AC", non "approvato".

Flusso iterativo, un campione alla volta. Per ogni sample:

1. AI produce sintesi: cosa è scritto attualmente nel `.tex`, quali figure sono già incluse, quali PDF candidati esistono in `Images/generated/<dataset>/`.
2. Utente risponde con: intenzione del sample, misure prese, plot già pronti vs. plot da scrivere/codificare ex novo, focus della discussione fisica.
3. AI rifattorizza la sezione cap6 di quel sample: prosa, figure, caption, eventuali nuovi script Python.
4. Commit per-sample.

| Sample | Stato revisione | Note |
|--------|-----------------|------|
| lambdaquarti_50deg | [x] bozza, DA RIVEDERE (2026-05-20) | Validazione zero-order riuscita. S0 3-panel + θ/δ 3×2 + tab winner HDBSCAN + fit k/λ. δ_win R 87,1 / G 108,9 / B 129,8° vs Ghosh 90,9/107,5/126,9° (scarto ≤4°). Lamina = analizzatore S3 → auto-validazione pipeline. |
| lambdamezzi_50deg | [x] bozza, DA RIVEDERE (2026-05-20) | δ_win R 183,1 / G 202,8 / B 224,1° (con swap). Fit zero-order k/λ (design escluso). Scarto crescente al blu (+1,3/−12,1/−29,6° vs Ghosh). CONCLUSIONE: fit `δ=a/λ^b` dà b≈0,69<1 → impossibile a singolo passaggio (material-indep) → lamina MULTI-ORDINE (δ avvolti). Ordine indeterminato (materiale ignoto; ad alto ordine la predizione avvolta dipende da Δn). Argomento b<1 in prosa cap6 (no cella dedicata, fit a 3 punti banale). Swap confermata. Vedi memory `project_waveplate_multiorder.md`. |
| strati_v2 | [x] bozza, DA RIVEDERE (2026-05-20) | Riscritta da zero. S0 3-panel + slice 3-panel + istogramma δ per ogni canale (textbook interleaved) + tab plateau (9×3) + tab slope + 2 plot wavelength (fit_strati_linear, fit_lambda_inverse). Slope R/G/B = 240,2 / 280,8 / 316,8°/strato (R²>0,998). Dispersione k=1,49·10⁵, m_B/m_R=1,319 vs geom 1,343. Anomalia 3R-B documentata come APERTA (vedi memory `project_strati_3R_B_anomaly.md`). Niente più tabelle arccos. |
| zucchero | [x] bozza, DA RIVEDERE (2026-05-20) | Riscritta da zero. S0 3-panel + aolp_winner 3-panel per canale + fit Drude ψ=k/λ² + tab concentrazione. ΔAoLP_win R/G/B = 3,85 / 4,92 / 6,14°. k=1,39·10⁶, R²=0,94. Stima c_ott≈0,47 g/mL (legge Biot, [α]_589=66,5, L=13mm, scaling Drude), consistente sui 3 canali. NIENTE confronto gravimetrico (mix non controllato, c_grav vecchio 1,22 era inventato). |
| barraon_v2 + barraoff_v2 | [x] bozza, DA RIVEDERE (2026-05-20) | Riscritta da zero (`subsec:risultati_cantilever`). Trave a sbalzo sez. quadrata 8mm, L≈73mm, carico ~900g (~9N) — dati di contesto, niente quantitativo (modulo+coeff fotoelastico ignoti, orientazione sfavorevole). Framing: asse barra ∥ polarizzazione → α≈0 → S3 soppresso + δ degenere → analisi solo qualitativa su S3. Figure: S0 3-panel (barraon) + ΔS3 3-panel (warped(on)−off). Catena I (phase-corr + warp, cap5). Lasciato `% TODO` utente per lettura spaziale specifica ΔS3 (confine interpretazione). |
| righello_v2 | [x] bozza, DA RIVEDERE (2026-05-20) | Spostato come PRIMA analisi del cap6 (`sec:panoramica_righello`): validazione qualitativa + panoramica dato polarimetrico. Sostituisce la vecchia `sec:validazione` (narrativa "misura a vuoto" FALSA, rimossa; fatti sfondo DoLP≈1/AoLP≈0/S3≈0 tenuti come riferimento dal fit sulla parte visibile). Figure: overview 6-param (S0,S1,S2,S3,DoLP,AoLP) canale R + DoLP 3-panel R/G/B (frange più fitte al blu). Frange fotoelastiche da stampaggio, frequenza ∝ 1/λ. |

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

Letti i TODO inline (cell markdown / commenti codice) prima del revert. Ordinate per priorità implicita. Voci originali ridotte da 8 a 2 dopo cleanup 2026-05-16: archiviati N-C (mask unificata RGB), N-D (D-aolp HDBSCAN + median + D-aolp-fit `k/λ²`), N-E (random sampling con `random_sample_mask`), N-F (cache bug risolto), N-H (cella H ora richiede `STRATI_SLICE_RESULTS`, fit `k/λ²`); droppato N-G (selettore poligono Jupyter, infattibile).

- [ ] **N-A** — commentare il codice (rimandato a quando il notebook è completo nel suo design finale, non ora).
- [x] **N-B** — rinominare schema codici analisi (2026-05-14, completato 2026-05-16): `AB` → split in `A` (maschera) + `B` (8 mappe); `E-ext` → `E`; `C-delta`/`C-aolp` mantengono il suffisso (semantica distinta della mappa colorata, due output cartelle separate). Aggiunti `D-aolp-fit`/`D-delta-fit` come codici espliciti nel dispatcher (no più gate implicito sulla presenza di `D-aolp` o `D-delta`).

## Pipeline Python

- [x] Committare lavori in sospeso: saturation accumulator in `final_polarimeter.py` e `final_utils.py` (2026-04-21)
- [x] Committare `python/final_umap.py` (2026-04-21)
- [x] Aggiungere `umap-learn` a `python/requirements.txt` (creato file, 2026-04-21)
- [x] Committare nuove figure in `Images/generated/barraon_v2/` (come stato pre-saturazione, 2026-04-21)
- [x] Integrazione accumulatore saturazione in `final_thesis_figure.py` (A1, 2026-04-21) — tutti i 77 PDF erano prodotti senza maschera
- [x] `final_plot_strati.py`: lunghezze d'onda lette da CSV, valori retardance marcati come placeholder da rimisurare (A4, 2026-04-21)
- [x] B1: rigenerazione completa PDF per tutti i dataset (strati_v2, lambdaquarti_50deg, lambdamezzi_50deg, zucchero, barraon_v2, barraoff_v2, righello_v2), tutti e tre i canali — con pipeline completa (saturazione + dark + arctan2 + allineamento 2D). Batch runner `final_thesis_figure_all.py`; 189 PDF + 189 HTML plotly interattivi in 22.7 min, zero fallimenti (2026-04-21)
- [x] B2 SUPERATO (2026-05-20): il fit retardance-vs-strati è ora prodotto dal notebook (cella F slice + cella H) con i dati arctan2 correnti e l'unwrap L/R; il rewrite di cap6 (strati_v2) usa già questi valori. Lo script legacy `final_fit_plot_strati.py` non serve più.
- [x] U1: reimplementare `final_umap.py` con campionamento sparso a risoluzione nativa (2026-04-21). Feature set (S1/S0, S2/S0, S3/S0, DoLP, delta), stride=20 su S0/S1/S2/S3 calcolati a piena risoluzione. Pearson |r(UMAP1, delta)| salita da 0.10 a 0.67 su lambdaquarti/R. bg_mask generata al DOWNSAMPLE_FACTOR standard e upsamplata (il Sobel a piena risoluzione satura di rumore). ~165 s / combo.
- [x] Tabelle cap6 SUPERATO (2026-05-20): le ritardanze sono ora estratte automaticamente dal cluster vincente HDBSCAN (D-delta/D-aolp) e dalla slice (F), con pipeline arctan2 [0°,360°). Tutte le tabelle di cap6 (lamine, strati, zucchero) sono state riscritte con questi valori nel rewrite per-sample. Niente più misura manuale.
- [ ] UMAP (raffinazione, rimandata a cap7): le tre opzioni aperte 2026-04-22 sono state in parte sciolte. (a) `(sin δ, cos δ)` ciclico — testato 2026-05-11 (U2b), peggio di `no_delta` sia da solo che con Stokes raw. (b) HDBSCAN sopra l'embedding — **rigettato esplicitamente** 2026-05-11 dall'utente: selezione cluster solo manuale via poligono. (c) multi-canale stacked R/G/B → unica embedding — ancora aperto, non tentato. Resta una nota: l'analisi cap7 menziona UMAP come esplorazione raffinabile, non come contributo principale.
- [x] Istogrammi δ per strati_v2: PDF pubblicabile + HTML plotly interattivo con barre colorate twilight in `Images/generated/strati_v2/` (2026-04-22). Script: `python/final_delta_histogram.py`.
- [x] S3 ellipticity correction via Poincaré rotation (2026-04-23). Nuova funzione `align_poincare_ellipticity` in `final_utils.py`: rotazione pixel-wise attorno asse S2 con β(x,y) da fit polinomiale grado 2 di s1_bg e s3_bg su maschera wav-bright (esclude holder lamina). Chiamata nei pipeline dopo `align_reference_frame`. Integrata in `final_polarimeter.py`, `final_thesis_figure.py`, `final_umap.py`. Verifica: |S|² preservato a precisione macchina; residuo s3_bg std 0.083→0.023 su strati_v2/R; δ median 21°→111° (recupera segnale prima biased). Overlay diagnostico nel debug mask plot mostra rosso=holder escluso, ciano=cleaned bg usato per fit β.
- [x] B3: rigenerazione figure su 7 dataset × 3 canali × 9 parametri con correzione Poincaré + nuova `generate_background_mask` Canny (2026-04-25). 189 PDF + 189 HTML in 52.7 min, zero fallback/empty/warn su tutte le 21 combo.
- [x] B4 SUPERATO (2026-05-20): gli istogrammi δ di strati_v2 sono ora prodotti dalla cella E del notebook (`plot_delta_strati_histogram`) con δ corretto + vline plateau dalla slice, e inclusi nel rewrite di cap6. Lo script legacy `final_delta_histogram.py` non serve più.
- [x] Commit modifiche: `align_poincare_ellipticity` + integrazione + debug plot RGB overlay (2026-04-25).
- [x] M1: rewrite `generate_background_mask` (2026-04-25). Vecchia logica `mean(Sobel) + 1.5% dilation` falliva su 3 combo a DOWNSAMPLE_FACTOR=1 (lambdaquarti R/B, barraoff_v2 R) producendo bg_mask vuota → align_reference_frame e align_poincare_ellipticity skippate → δ/θ sistematicamente errate. Nuova pipeline: Canny (sigma=1.5, low=0.05, high=0.15, scelti via parameter sweep su strati_v2/B) + dark prior (S0_norm < 0.3) + circle expansion (dilation disco) + flood-fill bg da componente connessa al bordo foto + fill_holes sample + opening contorno + erosione di sicurezza. Auto error detection via compactness 4πA/P². Tutte 21 combo OK, zero fallback. Soglie tunate manualmente, robuste su 7 dataset diversi.
- [x] M2: overlay 2-color maschere bg + Poincaré in plot finali (2026-04-25). `final_polarimeter.py` debug plot 3x3 e `final_thesis_figure.py` parametro `mask`: pixel coperti da entrambe = grayscale modulato S0; XOR (una sola, tipicamente holder lamina) = rosso × 0.5 × S0; nessuna (sample / fuori scena) = rosso × S0. Legenda patch in basso a destra.
- [x] D1: `final_slice_debug.py` (2026-04-23, esteso 2026-04-24) — slice diagonale (141°, anchor (767, 422) px nativi) attraverso gli strati. Auto-crop su soglia δ ∈ [margin, 360-margin] + ignore band; rilevamento plateau con gradiente; etichette 1L–5–1R; fit through-origin con unwrap per-side cumulativo. Single PNG output. Eseguito su strati_v2 R/G/B.
- [x] D2 (CHIUSA 2026-05-20): anomalia 3R-B (47° asimm vs 14-21° su G/R) **inspiegata, chiusa**. Documentata in cap6 (sez. nastro) come asimmetria residua localizzata (3° strato × canale B), cause standard escluse, non incide su pendenza media né linearità (R²>0,998). Non si indaga oltre. Storia tentativi sotto. L'asimmetria è specifica del singolo strato (3) nel singolo canale (B), non presente negli altri strati né negli altri canali — incompatibile con asimmetria fisica generica del campione (che si manifesterebbe in tutti gli strati e canali in modo proporzionale alla slope). Tentativi 2026-04-24 (tutti scartati come cause): (a) `WAV_HOLDER_THRESHOLD` 0.7→0.5 inerte (escluse solo 200 px in più, β extrapolazione invariata, codice rimosso); (b) frame alignment FFT phase-corr pol+wav — verificato corretto (pol26 a 260° shift reale 13.16 px peak/med=36, altri 35 frame <0.03 px) ma riduce 3L-3R solo da 47.8° a 43.9°, codice rimosso; (c) DoP slice — DoP_min ≈ DoP_med ovunque, DoP 3L=0.45 ≈ 3R=0.43 simmetrico → no depolarizzatore locale; (d) verifica numerica: vettori Stokes 3L e 3R su posizioni diverse della sfera con stesso |raggio|. Cause residue da indagare: chromatic registration B vs R/G (anchor slice mappato su posizioni fisiche leggermente diverse); thin-film interference selettiva in B; aliasing Bayer su griglia B (mezza densità di campionamento); risonanza ottica wavelength-specific. Codice diagnostico β/Stokes/DoP rimosso da `final_slice_debug.py` per pulizia.
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
