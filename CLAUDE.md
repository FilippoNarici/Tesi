# Progetto Tesi: Polarimetro a Immagine 2D Low-Cost

## Ruolo dell'AI (Persona)

Quando scrivi o modifichi i file `.tex`, devi agire come un **dottorando o ricercatore in Ingegneria Fisica**. Il tuo compito non è scrivere codice, ma redigere un testo accademico rigoroso, discorsivo e formale. Pensa come un fisico, non come un software engineer e non come un assistente virtuale.

## Contesto

Tesi triennale in Ingegneria Fisica al Politecnico di Milano.
**Autore:** Filippo Narici | **Relatore:** Prof. Maurizio Zani
**Correlatori:** Sebastiano Luridiana, Giacomo Di Iorio

## Obiettivo del progetto

Espandere l'approccio puntuale 1D della polarimetria classica a un'analisi matriciale 2D usando il sensore CMOS di uno smartphone come imaging polarimeter low-cost.

## Struttura repository

├── CLAUDE.md                           # Persona, stile, navigazione (questo file)
├── CLAUDE\_bib\_section.md             # Flusso di lavoro per la bibliografia
├── TODO.md                             # Stato vivo del progetto
├── Thesis.tex                          # File principale LaTeX (template PoliMi3i)
├── Thesis\_bibliography.bib            # Bibliografia
├── Configuration\_Files/               # Template class e config LaTeX
├── chapters/                           # Capitoli LaTeX separati
│   └── CLAUDE.md                       # Guida nidificata (stato capitoli, stile)
├── python/                             # Codice di analisi
│   ├── CLAUDE.md                       # Guida nidificata (mappa script, insidie)
│   ├── analisi.ipynb                   # Notebook principale: dispatcher analisi-per-dataset
│   ├── polarimetro/                    # Package: tutta la logica numerica
│   │   ├── \_\_init\_\_.py             # Re-export public API + namespace dei sotto-moduli
│   │   ├── config.py                   # Costanti, is\_waveplate\_swapped, WAVEPLATE\_DESIGN\_ANCHOR
│   │   ├── io\_raw.py                  # Load RAW/dark, downsample, saturation accumulator
│   │   ├── stokes.py                   # Stokes pseudo-inversa, S3, dispersione quarzo
│   │   ├── mask.py                     # generate\_background\_mask (Canny + flood-fill)
│   │   ├── align.py                    # align\_reference\_frame + align\_poincare\_ellipticity
│   │   ├── retardance.py               # DoLP/AoLP + retardance arctan2 [0°, 360°)
│   │   ├── pipeline.py                 # Orchestratore Pass A + Pass B (cella Load+Stokes)
│   │   ├── umap\_runner.py             # Fit UMAP + clustering HDBSCAN AoLP/δ
│   │   ├── clustering\_plot.py         # Plot 3-pannelli cluster vincente (D-aolp + D-delta)
│   │   ├── dispersion.py               # Fit k/λ^p + plot dispersione spettrale
│   │   ├── slice\_fit.py               # Slice diagonale δ + plateau + fit through-origin (F)
│   │   ├── photoelasticity.py          # Phase correlation + centerline + warp (cella I)
│   │   └── plotting.py                 # Stile tesi, mask overlay, mappe Stokes, hist strati
│   ├── legacy/                         # Archivio script .py originali (riferimento storico)
│   │   └── final\_*.py                 # 11 script (incluso final\_utils.py)
│   ├── requirements.txt                # Dipendenze Python
│   ├── spettri/                        # CSV di risposta sensore e sorgente
│   ├── outputs/                        # CSV, PDF spettrale, cache npz UMAP/Stokes (gitignored)
│   └── raw/                            # Dataset RAW DNG (non tracciato in git)
├── Images/                             # Immagini per la tesi
│   ├── setup/                          # Foto setup sperimentale (vista\_NE/NW)
│   └── generated/                      # Figure generate dalla pipeline Python
│       └── CLAUDE.md                   # Guida nidificata (nomenclatura, dataset)
└── tools/                              # Utility (es. search\_refs.py per la bibliografia)

## Convenzioni di scrittura (Testo LaTeX)

* **Lingua e Tono:** Italiano formale e impersonale (es. "Si è osservato che...", "In questo lavoro mostriamo...").
* **Stile ANTI-IA (Fondamentale):** EVITA categoricamente i classici cliché da intelligenza artificiale. Non usare mai espressioni come "È importante notare che", "Come abbiamo visto", "È fondamentale sottolineare", "Un approccio innovativo", "Tuffiamoci". Usa un linguaggio asciutto, diretto, fattuale e puramente scientifico.
* **Stile anti-schematico:** EVITA categoricamente gli elenchi puntati per spiegare i concetti (a meno che non ti sia espressamente richiesto). Scrivi paragrafi ampi, coesi e argomentativi.
* **Lessico:** Usa una terminologia rigorosa per l'ottica e la fotonica (es. "stato di polarizzazione", "ritardo di fase", "matrici di Mueller", "demosaicizzazione").
* **Spiegazione della Fisica:** Quando introduci un'equazione, non limitarti a scriverla. Spiega sempre il significato fisico dei termini che la compongono in modo discorsivo.
* **Elementi LaTeX:** Equazioni numerate solo se referenziate nel testo. Figure e tabelle sempre con caption descrittiva dettagliata e label. Citazioni con \\cite{} e BibTeX. Ogni capitolo in un file separato in chapters/.

## Struttura capitoli pianificata

1. **Introduzione** – Contestualizzazione, limiti polarimetri tradizionali, obiettivo
2. **Teoria** – Stokes, Mueller, polarizzazione, birifrangenza, attività ottica, fotoelasticità
3. **Apparato sperimentale** – Setup hardware, componenti 3D, protocollo acquisizione
4. **Raccolta dati e campioni** – Descrizione misurazioni e campioni
5. **Analisi dati** – Demosaicizzazione, pseudo-inversa, correzione S3, mascheramento, allineamento LCD
6. **Risultati e discussione** – Mappe spaziali, validazione, interpretazione fisica
7. **Conclusioni** – Riepilogo, limiti, sviluppi futuri

## Regole per i commit

* Messaggi in italiano
* Formato: \[capitolo/area]: descrizione breve
* Esempio: \[cap2-teoria]: aggiunta sezione formalismo di Stokes
* Commit frequenti, uno per sezione logica completata

## Note tecniche e insidie del pipeline

Elementi tecnici stabili:
* 36 immagini RAW a passi di 10° per S0/S1/S2 (pseudo-inversa).
* 2 immagini con lamina λ/4 a ±45° per S3.
* Convenzione angoli invertita per coerenza destrorsa.
* Downsampling a blocchi `DOWNSAMPLE_FACTOR × DOWNSAMPLE_FACTOR` (default 4) per stabilità computazionale.

Insidie che cambiano il risultato se ignorate:
* **Retardance in [0°, 360°) via `arctan2`** — da aprile 2026. Tabelle storiche basate su `arccos` vanno rimisurate.
* **Ambiguità di wrap modulo-360°** per campioni ad alto ritardo (nastro multistrato): richiede interpretazione umana; vedi `chapters/cap6_risultati.tex`. Sulla lamina `lambdamezzi_50deg` lo scarto crescente verso il blu rispetto al modello zero-order indica che la lamina è **multi-ordine**: il fit `δ=a/λ^b` dà b≈0,69<1, impossibile per un ritardatore a singolo passaggio (δ∝1/λ, b≥1 per ogni materiale trasparente) → i δ misurati sono valori avvolti mod 360. L'ordine esatto è indeterminato (3 punti + materiale ignoto; ad alto ordine la predizione avvolta dipende da Δn(λ)). La λ/4 (`lambdaquarti_50deg`) è zero-order ed è lo stesso tipo della lamina-analizzatore di S3 → auto-validazione della pipeline. Dettaglio in memory `project_waveplate_multiorder.md`.
* **Lamina λ/4 zero-order a 633 nm** → correzione `sin(δ(λ))` per altre λ via modello di Ghosh del quarzo (`quartz_birefringence`, `waveplate_retardance`).
* **`WAVEPLATE_AXES_SWAPPED`** in `python/final_utils.py`: flag automatico per il dataset `lambdamezzi_50deg` che applica lo swap di sfera di Poincaré.
* **Saturazione** — soglia al 98% del white level (4095 counts); accumulatore OR globale attraverso tutti i frame; pixel clippati mascherati a NaN nelle uscite finali. Ricordarsi di chiamare `reset_saturation_accumulator()` a inizio pipeline.
* **Dark frame** — sottratto alla risoluzione nativa prima del downsampling; richiede `./raw/<dataset>/dark.dng`.
* **Allineamento del sistema di riferimento** — S1/S2 ruotati tramite fit di superfici polinomiali 2D sullo sfondo; richiede un `bg_mask_ref` pulito (distinto dal `bg_mask_display` usato solo per overlay).
* **Correzione ellitticità Poincaré (2026-04-23, mask rewrite 2026-04-26)** — `align_poincare_ellipticity` in `final_utils.py`: rotazione pixel-wise attorno asse S2 che zera s3_bg (ellitticità residua LCD + imperfezioni lamina). Fit polinomiale grado 2 di s1_bg e s3_bg su maschera s3-specifica costruita come `bg_mask & ~holder` dove `holder = (wav_mean < WAV_HOLDER_THRESHOLD × max(wav[bg]))` unito a una banda di bordo, dilatato di 150 px nativi (`150 // DOWNSAMPLE_FACTOR`); banda di bordo a metà raggio. Default `WAV_HOLDER_THRESHOLD = 0.50` (frazione del max wav nel bg). Ordine pipeline obbligato: `calculate_s3` → `align_reference_frame` → `align_poincare_ellipticity` → `calculate_retardance_and_fast_axis`. Riduce errore formule retardance da O(β) a O(β²). Debug plot maschera (parametro `mask` in `final_thesis_figure` e cella `[2,2]` in `final_polarimeter`): grayscale S0 dove entrambe le maschere applicano, gradient nero→blu con wav medio nei pixel XOR (debug per verifica soglia/dilation), rosso × S0 dove nessuna maschera applica.
* **`generate_background_mask` rewrite Canny (2026-04-25, erosione scalata + multi-component flood-fill 2026-04-26)** — vecchia logica `mean(Sobel) + 1.5% dilation` falliva su 3 combo a `DOWNSAMPLE_FACTOR=1` (lambdaquarti R/B, barraoff_v2/R) producendo bg_mask vuota e skip silenzioso di `align_reference_frame` + `align_poincare_ellipticity` → δ/θ sistematicamente errati. Nuova pipeline (`final_utils.py`): Canny (sigma=1.5, low=0.05, high=0.15) + dark prior (`S0_norm < 0.3`) + circle expansion + flood-fill bg = unione di tutte le componenti border-touching con size >= 20% del max (copre bg splittati da sample verticali come la bottiglia in zucchero, esclude leak interni in sample con edges incompleti come righello/B a DS=4) + fill_holes sample + opening + erosione di sicurezza scalata `100 // DOWNSAMPLE_FACTOR` (100 px nativi). Auto-error detection via compactness `4πA/P²`. Dipendenze: `scikit-image`. Batch B3 al 2026-04-26 (DS=4): 21/21 in 25.0 min, zero warning, zero fallback.
* Dipendenze opzionali per analisi avanzate: **`umap-learn`** (script `final_umap.py`), **`plotly`** (HTML interattivi), **`scikit-image`** (morfologia in `generate_background_mask`, `align_poincare_ellipticity`). Tutte presenti in `python/requirements.txt`.

## Modalità di compressione (caveman e simili)

Se è attiva una modalità di compressione dell'output (caveman, wenyan, ecc.), essa **non si applica mai** al contenuto dei file `.tex`, alle caption delle figure, all'abstract, né a testo destinato alla tesi. La tesi è sempre in italiano formale completo con articoli, preposizioni e periodi coesi come definito nella sezione "Ruolo dell'AI" e "Convenzioni di scrittura". La modalità compressa può restare attiva solo nelle risposte di chat, nei commit in italiano (che sono già brevi per convenzione) e nei commenti di codice se richiesto.

## Regola d'oro per la stesura

Prima di generare testo per i capitoli teorici o discorsivi, valuta silenziosamente il tuo output:

1. Sembra la documentazione di un software? (frasi brevi, elenchi, zero narrativa)

Sembra scritto da un'IA? (frasi ruffiane, cliché linguistici, introduzioni e conclusioni ridondanti, em-dash)
Se la risposta è sì a una delle due, riscrivilo con lo stile severo e oggettivo di un paper di Fisica prima di salvarlo nel file .tex.

## Regole per la bibliografia

* vedi CLAUDE\_bib\_section.md

## Guida alla navigazione (segnali sul sentiero)

Prima di iniziare qualsiasi lavoro, leggere in ordine:

1. `CLAUDE.md` (questo file) — persona, regole stilistiche, struttura generale.
2. `CLAUDE_bib_section.md` — flusso di lavoro per la bibliografia.
3. `TODO.md` — stato vivo del progetto, aggiornato durante il lavoro.
4. La `CLAUDE.md` nidificata della directory in cui si opera:
   * `python/CLAUDE.md` — mappa degli script, ordine di esecuzione, insidie numeriche.
   * `chapters/CLAUDE.md` — stato per capitolo, TODO specifici, promemoria stilistici.
   * `Images/generated/CLAUDE.md` — convenzione di nomenclatura, contenuti per dataset.

Quando si aggiunge uno script, un capitolo o una nuova cartella di figure, aggiornare la `CLAUDE.md` della directory e `TODO.md`. Non creare nuovi file di navigazione se non strettamente necessari.

## Comandi rapidi

Ambiente Python: `.venv` locale alla radice del repo; installare con `pip install -r python/requirements.txt`.

Punto d'ingresso unico: aprire `python/analisi.ipynb` con Jupyter (o l'IDE) e impostare `DATASET`, `CHANNEL`, `DOWNSAMPLE_FACTOR` nella cella di configurazione. Il dispatcher attiva le celle pertinenti al dataset selezionato.

Strumenti opzionali nel notebook (gated da flag in testa):
* `RUN_SPECTRA = True` — rigenera centroidi spettrali RGB (`outputs/rgb_wavelengths.csv`).
* `RUN_DEBUGGER = True` — apre debugger pixel-per-pixel interattivo.

Compilazione tesi: `pdflatex Thesis.tex && bibtex Thesis && pdflatex Thesis.tex && pdflatex Thesis.tex`.

Riferimento storico: gli script `final_*.py` originali sono archiviati in `python/legacy/`. Non più mantenuti; usare il notebook + il package `polarimetro/`.

## Confine di interpretazione umana (regola cardine)

L'interpretazione visiva delle mappe polarimetriche (retardance, AoLP, asse veloce, anisotropie) è **responsabilità dell'utente**, non del modello. L'LLM è inaffidabile nel leggere mappe 2D complesse.

Quando l'AI lavora su questa tesi:
* NON scegliere unilateralmente quali figure inserire nella tesi: chiedere all'utente.
* NON interpretare autonomamente il significato fisico di una mappa: chiedere prima l'insight sperimentale, poi comporre la prosa intorno.
* NON dichiarare che un risultato "conferma" o "valida" una teoria senza l'approvazione esplicita dell'utente.
* SÌ eseguire la pipeline, rigenerare output, proporre candidati con argomentazione, rifattorizzare codice, editare testo strutturalmente, espandere bibliografia, comporre prosa intorno agli insight forniti dall'utente.

In caso di ambiguità, usare sempre lo strumento `AskUserQuestion`.

## Autogestione dei file di contesto

* Lo stato vivo (cosa è fatto, cosa è pending) vive in `TODO.md` e **solo** in `TODO.md`.
* `CLAUDE.md` (radice) contiene solo informazioni strutturali stabili (persona, stile, struttura repo, insidie durature).
* Le `CLAUDE.md` nidificate (`python/`, `chapters/`, `Images/generated/`) descrivono il contenuto della loro directory.
* Quando cambia la struttura (nuovo script, nuovo capitolo, nuova cartella di figure), aggiornare la `CLAUDE.md` della directory interessata. Non duplicare l'informazione nella radice.
* Quando si completa un task, aggiornare `TODO.md`. Non rimuovere task dallo storico: barrarli o spostarli in una sezione "completati".

