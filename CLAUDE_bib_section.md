## Gestione della bibliografia (REGOLA ASSOLUTA)

**Non inserire mai una voce BibTeX o un \cite{} senza aver prima eseguito una ricerca reale.**
Le allucinazioni bibliografiche invalidano la tesi. Ogni citazione deve essere verificata.

### Workflow obbligatorio per ogni nuova citazione

1. **Identifica il concetto** da citare (es. "formalismo di Stokes", "demosaicizzazione Bayer").
2. **Cerca fonti reali** con lo script dedicato:
   ```bash
   python tools/search_refs.py "stokes vector imaging polarimetry" --limit 6
   python tools/search_refs.py --arxiv "mueller matrix CMOS sensor"
   python tools/search_refs.py --verify 10.1364/OE.26.029669   # verifica DOI
   ```
3. **Valuta i risultati**: scegli il paper più pertinente e autorevole (citationCount alto = buon segnale).
4. **Copia la voce BibTeX** in `Thesis_bibliography.bib`. Non modificare mai i metadati (titolo, autori, anno) — usali esattamente come restituiti dall'API.
5. **Inserisci `\cite{key}`** nel testo LaTeX solo dopo che la voce è nel `.bib`.

### Quando cercare

| Situazione | Azione |
|---|---|
| Introduci un'equazione fondamentale (Stokes, Mueller, Jones) | Cerca il paper o libro originale |
| Descrivi una tecnica (pseudo-inversa, demosaicizzazione) | Cerca un paper che la descriva in contesto polarimetrico |
| Citi dati tecnici (sensibilità CMOS, λ/4 zero-order) | Verifica datasheet o paper specifico |
| Fai un'affermazione quantitativa | Serve una fonte, cerca prima di scrivere |
| Usi un termine tecnico di settore | Non necessariamente una citazione, ma valuta |

### Query efficaci per questo progetto

```bash
# Polarimetria di base
python tools/search_refs.py "Stokes parameters Mueller matrix polarimetry review"
python tools/search_refs.py "imaging polarimeter CMOS camera"
python tools/search_refs.py "division of focal plane polarimeter"

# Metodi numerici
python tools/search_refs.py "polarimeter calibration pseudoinverse least squares"
python tools/search_refs.py "Bayer pattern demosaicing polarization"

# Applicazioni fisiche
python tools/search_refs.py "photoelasticity stress birefringence imaging"
python tools/search_refs.py "optical activity chiral medium Stokes"
python tools/search_refs.py "liquid crystal retardance Mueller"

# Libri fondamentali (cerca per titolo noto)
python tools/search_refs.py "Born Wolf Principles of Optics"
python tools/search_refs.py "Goldstein Polarized Light handbook"
```

### Regole ferree

- **Mai inventare** un titolo, un autore, un anno, una rivista o un DOI.
- **Mai usare** fonti Wikipedia, blog o siti commerciali come riferimenti LaTeX.
- **Se l'API non trova nulla** di pertinente, dì esplicitamente "non ho trovato una fonte verificata per questa affermazione" e lascia un `% TODO: citazione mancante` nel .tex.
- **Dopo ogni aggiunta al .bib**, esegui `pdflatex` + `bibtex` per verificare che non ci siano errori.
- Le chiavi BibTeX generate dallo script seguono il formato `PrimoAutoreAnnoParola` — non rinominarle.
