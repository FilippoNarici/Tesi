# TODO - Tesi: Polarimetro a Immagine 2D Low-Cost

**Ultimo aggiornamento:** 2026-04-08

## Stato capitoli

| Capitolo | File | Responsabile | Stato |
|----------|------|-------------|-------|
| 1. Introduzione | `chapters/cap1_introduzione.tex` | Architetto | [ ] pending |
| 2. Fondamenti teorici | `chapters/cap2_teoria.tex` | Teorico | [ ] pending |
| 3. Apparato sperimentale | `chapters/cap3_apparato.tex` | Sperimentale | [ ] pending |
| 4. Campioni e dati | `chapters/cap4_campioni.tex` | Sperimentale | [ ] pending |
| 5. Analisi dati | `chapters/cap5_analisi.tex` | Analista | [ ] pending |
| 6. Risultati e discussione | `chapters/cap6_risultati.tex` | Analista | [ ] pending |
| 7. Conclusioni | `chapters/cap7_conclusioni.tex` | Architetto | [ ] pending |

## Note tecniche importanti

- 36 immagini RAW a passi di 10 gradi per S0/S1/S2 (pseudo-inversa)
- 2 immagini con lamina lambda/4 a +/-45 gradi per S3
- Convenzione angoli invertita per coerenza destrorsa
- Lamina lambda/4 zero-order a 633nm, correzione sin(delta) per altre lunghezze d'onda
- Downsampling 20x per sostenibilita' computazionale
- Smart mask morfologica per isolamento area illuminata
- Allineamento reference frame via compensazione LCD
- Clipping di sicurezza prima di arccos per evitare NaN

## Dipendenze

- Capitoli 2-6 possono essere scritti in parallelo
- Capitolo 1 (Introduzione) e 7 (Conclusioni) dipendono dal completamento dei capitoli 2-6
