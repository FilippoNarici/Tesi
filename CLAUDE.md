# Progetto Tesi: Polarimetro a Immagine 2D Low-Cost

## Contesto
Tesi triennale in Ingegneria Fisica al Politecnico di Milano.
**Autore:** Filippo Narici | **Relatore:** Prof. Maurizio Zani
**Correlatori:** Sebastiano Luridiana, Giacomo Di Iorio

## Obiettivo del progetto
Espandere l'approccio puntuale 1D della polarimetria classica a un'analisi matriciale 2D usando il sensore CMOS di uno smartphone come imaging polarimeter low-cost.

## Struttura repository
```
├── CLAUDE.md                    # Questo file
├── Thesis.tex                   # File principale LaTeX (template PoliMi3i)
├── Configuration_Files/         # Template class e config LaTeX
├── Images/                      # Immagini per la tesi
├── chapters/                    # Capitoli LaTeX separati (da creare)
├── python/                      # Codice analisi
│   ├── final_utils.py           # Funzioni comuni (load RAW, Stokes, mask, retardance)
│   ├── final_polarimeter.py     # Pipeline principale: Stokes completo + plot 3x3
│   ├── final_fit.py             # Debugger interattivo pixel-per-pixel
│   ├── final_monochrome_approx.py  # Stima lunghezze d'onda centroide RGB
│   └── spettri/                 # CSV sensibilità spettrale
├── Thesis_bibliography.bib      # Bibliografia
└── TODO.md                      # Stato avanzamento (da creare)
```

## Convenzioni di scrittura
- Lingua della tesi: **Italiano** (abstract anche in inglese)
- Stile: accademico ma chiaro, adatto a tesi triennale
- Equazioni numerate solo se referenziate nel testo
- Figure e tabelle sempre con caption descrittiva e label
- Citazioni con `\cite{}` e BibTeX
- Ogni capitolo in un file separato in `chapters/`

## Struttura capitoli pianificata
1. **Introduzione** – Contestualizzazione, limiti polarimetri tradizionali, obiettivo
2. **Teoria** – Stokes, Mueller, polarizzazione, birifrangenza, attività ottica, fotoelasticità
3. **Apparato sperimentale** – Setup hardware, componenti 3D, protocollo acquisizione
4. **Raccolta dati e campioni** – Descrizione misurazioni e campioni
5. **Analisi dati** – Demosaicizzazione, pseudo-inversa, correzione S3, mascheramento, allineamento LCD
6. **Risultati e discussione** – Mappe spaziali, validazione, interpretazione fisica
7. **Conclusioni** – Riepilogo, limiti, sviluppi futuri

## Regole per i commit
- Messaggi in italiano
- Formato: `[capitolo/area]: descrizione breve`
- Esempio: `[cap2-teoria]: aggiunta sezione formalismo di Stokes`
- Commit frequenti, uno per sezione logica completata

## Note tecniche importanti (dal README e dal codice)
- 36 immagini RAW a passi di 10° per S0/S1/S2 (pseudo-inversa)
- 2 immagini con lamina λ/4 a ±45° per S3
- Convenzione angoli invertita per coerenza destrorsa
- Lamina λ/4 zero-order a 633nm → correzione sin(δ) per altre λ
- Downsampling 20x per sostenibilità computazionale
- Smart mask morfologica per isolamento area illuminata
- Allineamento reference frame via compensazione LCD
- Clipping di sicurezza prima di arccos per evitare NaN
