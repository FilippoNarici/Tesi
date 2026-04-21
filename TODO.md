# TODO — Stato del progetto

Ultimo aggiornamento: 2026-04-20 (sessione di preparazione)

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

- [ ] Committare lavori in sospeso: saturation accumulator in `final_polarimeter.py` e `final_utils.py`
- [ ] Committare `python/final_umap.py` (attualmente untracked)
- [ ] Aggiungere `umap-learn` a `python/requirements.txt`
- [ ] Committare nuove figure in `Images/generated/barraon_v2/`
- [ ] Rigenerazione completa PDF per tutti i dataset (strati_v2, lambdaquarti_50deg, lambdamezzi_50deg, zucchero, barraon_v2, barraoff_v2, righello_v2), tutti e tre i canali
- [ ] Tabelle cap6: rimisurare valori di retardance con pipeline arctan2 [0°, 360°)

## Miglioramenti Python (se il tempo lo permette)

- [ ] Centralizzare numeri magici in `python/config.py` (o TOML)
- [ ] Docstring di modulo per ogni script
- [ ] Test minimale pytest per le operazioni Stokes (sanity check, ~5 casi)
- [ ] Separare logica di calcolo da plotting
- [ ] Cache del fit polinomiale 2D per evitare ricalcoli

## Domande aperte per l'utente (da risolvere nella prossima sessione)

- Quali figure dei 77 PDF in `Images/generated/` inserire effettivamente in cap6?
- Interpretazione fisica per ogni dataset / figura selezionata (serve l'input umano sulle mappe).
- Appendice A: quali script in full, quali come estratti?
- UMAP: approvare le due PNG esistenti o rigenerarle con parametri diversi?

## Infrastruttura Claude-friendly (ora in vigore)

- `CLAUDE.md` (radice) — persona, stile, navigazione, insidie, confine umano.
- `TODO.md` (questo file) — stato vivo.
- `python/CLAUDE.md`, `chapters/CLAUDE.md`, `Images/generated/CLAUDE.md` — guide nidificate.
- `prompts/next-session-deep-review.md` — prompt per sessione di revisione profonda.
