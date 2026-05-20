# chapters/ — Guida ai capitoli

Questo file è letto da Claude quando lavora su file `.tex` dei capitoli. Per persona, stile e regole anti-IA vedere la `CLAUDE.md` alla radice; per bibliografia, `CLAUDE_bib_section.md`.

## File e stato di avanzamento

Vedi `TODO.md` per lo stato corrente (è il file vivo). Qui si annotano solo promemoria strutturali.

| File | Titolo | Note strutturali |
|------|--------|------------------|
| `cap1_introduzione.tex` | Introduzione | Contesto, limiti polarimetri tradizionali, obiettivo smartphone low-cost |
| `cap2_teoria.tex` | Fondamenti teorici | Stokes, Mueller, polarizzazione, birifrangenza, attività ottica, fotoelasticità |
| `cap3_apparato.tex` | Apparato sperimentale | Tablet LCD, Galaxy S24, analizzatore, λ/4, stampe 3D |
| `cap4_campioni.tex` | Raccolta dati e campioni | Tabella campioni (λ/2, λ/4, nastro adesivo, zucchero, righello, cantilever) |
| `cap5_analisi.tex` | Analisi dati | Demosaicizzazione, pseudo-inversa, correzione S3, mascheramento, allineamento LCD — tenere allineato alla pipeline corrente |
| `cap6_risultati.tex` | Risultati e discussione | Mappe spaziali, validazione, interpretazione fisica; figure e tabelle dipendono da output Python |
| `cap7_conclusioni.tex` | Conclusioni | Riepilogo, limiti, sviluppi futuri |

## Promemoria stilistici (rapido)

- Italiano formale, impersonale. ("Si è osservato che...", "In questo lavoro mostriamo...").
- **Evitare tassativamente**: cliché da IA (`È importante notare che`, `Come abbiamo visto`, `Un approccio innovativo`, `Tuffiamoci`), em-dash retorici, elenchi puntati per spiegare concetti.
- Prosa coesa, paragrafi ampi e argomentativi.
- Equazioni numerate solo se referenziate; spiegare sempre il significato fisico dei termini.
- Figure e tabelle con caption descrittiva dettagliata e `\label`. `\cite{}` con BibTeX verificato.

## Interpretazione delle mappe

Le mappe polarimetriche richiedono interpretazione visiva umana. Non scrivere commenti fisici sulle figure senza aver prima ricevuto dall'utente l'insight sperimentale. Vedi `CLAUDE.md` (radice), sezione "Confine di interpretazione umana".

## Flusso per aggiungere una figura

1. Verificare che il PDF esista in `Images/generated/<dataset>/`.
2. Chiedere all'utente se quella figura va nella tesi.
3. Inserire con `\includegraphics[width=...]{Images/generated/<dataset>/<file>.pdf}`.
4. Chiedere all'utente l'interpretazione fisica in 1–2 frasi.
5. Comporre caption e prosa discorsiva intorno all'insight dell'utente.
6. `\label{fig:<sample>_<param>_<ch>}` seguendo la convenzione esistente.

## Flusso per aggiungere una citazione

Vedi `CLAUDE_bib_section.md`. In breve: `tools/search_refs.py` → verifica DOI → copia BibTeX esatto → `\cite{}`. Mai inventare.
