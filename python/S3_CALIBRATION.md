# Calibrazione data-driven della correzione di S₃

Documento di processo. Spiega come la correzione cromatica di $S_3$ è stata resa
**data-driven** (giugno 2026), perché, e come riprodurla o rivederla. Letto da
chiunque (umano o AI) tocchi `stokes.py`, la correzione di $S_3$, o il capitolo 6.

## 1. Il problema (risolto)

$S_3$ si ricostruisce inserendo una lamina $\lambda/4$ come analizzatore:

```
S3 = (I_-45 - I_+45) / sin(delta_a(lambda))
```

dove `delta_a(lambda)` è il ritardo della lamina analizzatore al variare della
lunghezza d'onda. Tutte le mappe di ritardanza e asse veloce del lavoro dipendono
da `delta_a`. Prima, `delta_a` veniva **assunto** dal modello di dispersione del
quarzo cristallino (Sellmeier di Ghosh, `waveplate_retardance`). Due incognite
non verificate: il **materiale** della lamina e il suo **ordine**. Era il punto
più debole della tesi: la critica "perché quarzo?" affondava tutta la $S_3$.

## 2. L'insight

Esistono due lamine $\lambda/4$ dello stesso tipo: una usata come **campione**
(dataset `lambdaquarti_50deg`), l'altra come **analizzatore** sempre inserito per
misurare $S_3$. Hanno lo stesso `delta_a`. Quindi **misurare la ritardanza del
campione = misurare `delta_a`**, la quantità che entra nella correzione. E si può
fare senza assumere materiale, ordine, né la correzione stessa.

## 3. Il metodo (non circolare, depol-unbiased, material-free)

Tre ostacoli, tre soluzioni:

1. **Circolarità.** Misurare `delta` via $S_3$ richiederebbe già la correzione.
   Si evita: i parametri lineari $S_0, S_1, S_2$ (36 frame con solo analizzatore
   lineare, **senza** la $\lambda/4$ nel cammino) fissano il modulo del ritardo
   tramite il canale coseno, **a prescindere da $S_3$**.

2. **Auto-riferimento.** Sample == analizzatore ⟹ `delta = delta_a`, quindi il
   segnale circolare **grezzo** (non corretto) raccoglie due fattori `sin(delta_a)`
   (conversione lamina-campione + rivelazione analizzatore):
   ```
   I_-45 - I_+45  ∝  p · sin(2*theta) · sin²(delta_a)
   ```
   `delta_a` compare al quadrato e si auto-riferisce → il sistema si chiude
   **senza** la correzione che si vuole calibrare.

3. **Depolarizzazione.** La lamina depolarizza davvero (DoP totale 0.91/0.82/0.77
   R/G/B vs sfondo ~0.99). Normalizzare sullo sfondo (canale coseno puro) spinge
   `delta` verso 90°. Si evita lavorando con i **rapporti** delle componenti di
   Stokes / la **direzione** del vettore: la depol scalare `p` si elide.

La stima finale adottata è il **punto fisso** auto-consistente con la pipeline
ESATTA (rotazione di Poincaré reale per l'ellitticità LCD, non sottrazione),
letto con stima depol-unbiased dalla direzione del vettore. Vedi
`calibrate_s3_retardance.py`.

## 4. Il risultato

| canale | λ (nm) | δ_a misurato | 1/sin δ_a | δ_a quarzo (riscontro) |
|:------:|:------:|:------------:|:---------:|:----------------------:|
| R | 626 | **88.4°**  | 1.000 | 91.1° |
| G | 536 | **111.0°** | 1.071 | 107.9° |
| B | 466 | **130.8°** | 1.321 | 126.2° |

Verifiche interne (non imposte, emergono dalla soluzione):
- il fattore di depolarizzazione `p` ricostruito riproduce la DoP misurata;
- `theta` esce uniforme (~32°) sui tre canali, come deve per una lamina omogenea.

Riscontro material-free: il modello di quarzo (mai usato nell'inversione) cade
entro pochi gradi → quarzo **validato a posteriori**, non assunto. A R,
`delta_a ≈ 90°` → correzione `≈ 1.000`, **insensibile** a qualunque modello: il
canale rosso è robusto comunque. Conta solo G/B.

## 5. Implementazione (codice)

- `config.MEASURED_S3_RETARDANCE_DEG = {0: 88.4, 1: 111.0, 2: 130.8}` (per indice
  canale 0=R/1=G/2=B) + flag `config.USE_MEASURED_S3_RETARDANCE = True`.
- `stokes.analyzer_retardance(channel_index, wavelength_nm)`: ritorna il `delta_a`
  misurato se il canale è calibrato e il flag è attivo, altrimenti **fallback** al
  modello di quarzo `waveplate_retardance`.
- Usato da `calculate_s3` e `calculate_s3_rgb`. Nessun altro punto calcola la
  correzione.

Per tornare al quarzo: `USE_MEASURED_S3_RETARDANCE = False`.

## 6. Impatto = minimo (ed è il punto)

Adottare la correzione misurata invece del quarzo sposta la `delta` ricostruita
dei campioni di **≤ 1.4°** (solo lambdamezzi al blu); le pendenze del nastro
restano invariate. Questa **insensibilità** dimostra che i risultati non
dipendono dal modello di dispersione di $S_3$: l'obiezione "perché quarzo?" perde
mordente sul piano quantitativo.

**Insidia residua nota:** la lettura della `delta` nella pipeline combina canale
coseno (depol-biased verso 90°) e canale seno ($S_3$). La correzione di $S_3$ è
ora corretta, ma la `delta`-readout resta leggermente depol-biased → la `delta`
del campione `lambdaquarti` letta dalla pipeline (~128°) non coincide esattamente
con `delta_a` (130.8°). È un limite separato della readout, non della correzione.

## 7. Dove vive nella tesi

- **cap6** `\section{Calibrazione della correzione cromatica di S3}`
  (`sec:calibrazione_s3`): apre i risultati quantitativi. Eq. auto-riferimento
  (`eq:s3_selfref`), tabella (`tab:s3_calibrazione`), figura (`fig:s3_calibration`).
- **cap5** `sec:determinazione-s3`: `delta_a` misurato (forward-ref), quarzo =
  riscontro.
- **cap6** `subsec:risultati_qw`: la $\lambda/4$ come campione (de-circolarizzata).
- **notebook** cella `S3CAL` (gated `lambdaquarti`) → `poldisp.plot_s3_calibration`
  → `Images/generated/lambdaquarti_50deg/s3_calibration.pdf`.

## 8. Come riprodurre

**Ricalibrare `delta_a`** (solo se cambia l'hardware o le λ effettive dei canali):
```
cd python
../.venv/Scripts/python.exe calibrate_s3_retardance.py
# copia i delta_a stampati in config.MEASURED_S3_RETARDANCE_DEG
```
Richiede la cache UMAP di `lambdaquarti_50deg` (ROI cluster vincente).

**Rigenerare tutti i risultati** dopo un cambio di correzione (o di pipeline che
non cambia la chiave di cache):
```
cd python
../.venv/Scripts/python.exe run_all_datasets.py   # ~1 h, 7 dataset
```
**CRITICO:** le cache `stokes_*`/`umap_*` NON invalidano sul cambio di correzione
$S_3$ (la correzione non è nella chiave di cache). `run_all_datasets.py` le svuota
prima del re-run. Se rigeneri a mano dal notebook, **cancella prima** quelle cache,
altrimenti caricherà la $S_3$ vecchia.

---
Contesto storico completo: memory AI `project_s3_datadriven_calibration.md`.
Convenzione segni di $S_3$ e multi-ordine λ/2: `project_waveplate_multiorder.md`.
