# TODO — Stato del progetto

Ultimo aggiornamento: 2026-04-21 (sessione Phase 3 Layer A + B1)

Questo file è la singola fonte di verità sullo stato di avanzamento. Aggiornare ad ogni task completato. Per istruzioni operative vedere `CLAUDE.md`.

## Capitoli della tesi

| Cap | Titolo | Stato | Note |
|-----|--------|-------|------|
| 1 | Introduzione | ~80% | Pulizia stilistica (em-dash, cliché IA) |
| 2 | Fondamenti teorici | ~90% | Denso, ben citato |
| 3 | Apparato sperimentale | ~95% | Figure setup presenti |
| 4 | Raccolta dati e campioni | ~85% | Formattazione tabella campioni |
| 5 | Analisi dati | ~85% | Allineare descrizione pipeline allo stato attuale (arctan2, saturazione, dark frame, superfici 2D, WAVEPLATE_AXES_SWAPPED); chiarire sorgente spettrale |
| 6 | Risultati e discussione | ~75% | Tutte le figure sono placeholder (77 PDF già esistono in `Images/generated/`); tabelle retardance da rimisurare con pipeline arctan2; sottosezione UMAP da scrivere |
| 7 | Conclusioni | ~70% | Reggere meglio il passaggio agli sviluppi futuri |

## Consegnabili mancanti (livello tesi)

- [ ] Appendice A: listati dei principali script Python (attualmente placeholder)
- [ ] Ringraziamenti (placeholder — li scrive l'utente)
- [ ] Espansione bibliografia: target 10–15 voci nuove (attualmente 6, quasi tutti libri di testo)
- [ ] Sottosezione UMAP in cap6

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
- [ ] Tabelle cap6: rimisurare valori di retardance con pipeline arctan2 [0°, 360°) — l'utente si occupa della misura

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
- [ ] UMAP feature set: confermare `(S1/S0, S2/S0, S3/S0, DoLP, delta)` come vettore di feature in U1.

## Infrastruttura Claude-friendly (ora in vigore)

- `CLAUDE.md` (radice) — persona, stile, navigazione, insidie, confine umano.
- `TODO.md` (questo file) — stato vivo.
- `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` — guide nidificate.
- `prompts/next-session-deep-review.md` — prompt per sessione di revisione profonda.
