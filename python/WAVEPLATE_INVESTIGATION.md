# Journal — indagine parametri lamine d'onda

## IPOTESI PRINCIPALE (utente, 2026-06-11): lamine = fogli di polimero TAGLIATI

Entrambe le lamine sarebbero dischi ritagliati da un foglio di polimero stirato.
Spiega in un colpo: spessore ~mm, basso costo, diametro ~cm, superficie liscia,
ASSENZA di colla/sandwich, nessuna "stranezza" di indice nel tilt (foglio omogeneo,
non assemblato), industrializzabilità, e l'errore di design-λ.

**Verifica sui dati (2026-06-11):** con dispersione piatta + design libera, ENTRAMBE
fittano come polimero ~mm multi-ordine:
| lamina | ordine | spessore (Δn≈0.0035) | design λ | RMS |
|---|---|---|---|---|
| λ/4 | 6.25 | 1.13 mm | 625 nm | 6.0° |
| λ/2 | 5.5  | 0.99 mm | 626 nm | 4.1° |

Stesso spessore (~mm), stesso ordine (~5–6), STESSO design ~625–626 nm → coerente con
ritaglio dallo stesso tipo di foglio. **Il "deficit del rosso" si spiega così**: il
design vero è ~625 (non 633 dell'etichetta, scarto ~8 nm CONDIVISO); il canale rosso
(626) è ~al design → legge ~nominale. Niente artefatto di misura. Spiega anche la
**depol crescente al blu** (banda spettrale di un multi-ordine, intrinseca, per
entrambe — non più attribuita all'illuminazione).

**Caveat:** (1) la λ/4 fitta lo zero-order LEGGERMENTE meglio (RMS 4.2 vs 6.0), e un
zero-order su substrato di vetro apparirebbe comunque come disco liscio ~mm → i dati
non FORZANO il multi-ordine per la λ/4, ma parsimonia + assenza-colla lo favoriscono.
(2) **Tesi**: cap3 ("Optosci zero-order") e cap6 (λ/4 "zero-order, δ∝1/λ") andrebbero
rivisti se si adotta il multi-ordine polimerico. **La calibrazione S3 e i risultati
NON cambiano** (δ_a misurato direttamente, indipendente dall'ordine).

Stato: ipotesi fisica leading, coerente coi dati e con le osservazioni dirette delle
lamine. Ordine non univoco (degenere a 3 punti) ma il quadro è unitario.

---


Diario di lavoro (non parte della tesi). Traccia l'indagine su materiale, ordine,
tilt e l'anomalia aperta del **canale rosso sotto-design**. Voci datate, in coda.
Contesto stabile in `S3_CALIBRATION.md`; correzione S3 risolta e validata.

---

## Culprit aperto: δ del rosso SOTTO il valore di design

**Osservazione (canale R, il più affidabile, vicino a design 633 nm):**

| lamina | design @633 | misurato R (626 nm) | scarto vs design | scarto vs modello |
|:-:|:-:|:-:|:-:|:-:|
| λ/4 | 90°  | 88.4° (self-ref) / 87.1° (pipeline) | −1.6° | −2.7° (vs quarzo 91.1) |
| λ/2 | 180° | 176.9° | −3.1° | −5.1° (vs singolo-ordine 182) |

Entrambe leggono **sotto** il design al rosso. Per dispersione normale ci si
aspetterebbe δ(626) > δ(633) (λ più corta → più ritardo), quindi **sopra** il
design: l'opposto di quanto misurato.

**Firma quantitativa decisiva:** lo scarto è **∝ al valore di design** (λ/2 ≈ 2× λ/4,
= 180/90), NON ∝ all'ordine. Deficit frazionario ~**1.75%** uguale per le due lamine.

### Candidati e valutazione

| causa | scala con | atteso λ/2 vs λ/4 | osservato 2× | verdetto |
|---|---|---|---|---|
| **Tilt** (allineamento manuale) | ordine × θ² | ~22× (ord 5.5 vs 0.25) | no | **escluso come causa principale** (un tilt che dà −1.6° sul λ/4 zero-order darebbe ~36° sul λ/2 ord 5.5). Contributo minore possibile, e diverso fra le due lamine. |
| **λ effettiva del canale R errata** | δ (frazionario) | 2× (= design) | **sì** | **CANDIDATO PRINCIPALE**. δ∝1/λ → +1.75% di deficit = λ_R vera ~+11 nm (≈637 invece di 626). Il rosso ha struttura a righe strette KSF (609/631/647 nm, cap5): la λ *efficace per la ritardanza* può differire dal centroide d'intensità. Stessa per entrambe le lamine (stesso canale). |
| **Bias moltiplicativo dell'estrazione δ** | δ (frazionario) | 2× | sì | possibile (depol/Poincaré/self-ref); ma il self-ref è depol-unbiased per costruzione → andrebbe verificato un residuo ~1.75%. |
| **Design reale < nominale** (lamine sottili) | design | 2× | sì | possibile ma richiede coincidenza (stessa frazione su due lamine diverse). Meno elegante della λ. |

### Test fatto (2026-06-11): quale λ_R rende il rosso design-consistente?
Invertendo δ(λ_R)=design per ciascuna lamina:
- λ/4 → **644.5 nm** (geom) / 643.6 (quarzo)
- λ/2 → **644.1 nm** (geom) / 643.3 (quarzo)

**Le due lamine, DIVERSE, danno lo stesso λ_R a 0.4 nm.** Coincidenza esclusa →
la causa è il **canale rosso condiviso** (stesso sensore/sorgente/pipeline), NON
le lamine. Il centroide d'intensità è 626 nm; servirebbe λ_eff ≈ 644 (+18 nm).

**Ma attenzione al meccanismo (puzzle di segno):** la media di banda semplice
NON spiega +18 nm. A primo ordine δ_misurato ≈ δ(centroide aritmetico)=δ(626);
le correzioni di banda sono second'ordine (≪18 nm su banda di decine di nm con
dispersione mite). Inoltre la media armonica pesata in intensità darebbe
λ_eff < centroide (segno SBAGLIATO). Quindi NON è banale averaging spettrale.

### SVOLTA 2026-06-11 (sera): tutti gli effetti ∝ordine ESCLUSI; λ_R=644 era un artefatto

Errore corretto: il calcolo "λ_R=644 riconcilia entrambe" usava la formula
ZERO-ORDER (δ=design·633/λ), invalida per la λ/2 MULTI-ORDINE. Fatto bene, lo
spostamento della δ AVVOLTA scala col ritardo TOTALE = ordine·360°:

| effetto | λ/4 (ord 0.25) | λ/2 (ord 5.5) | rapporto |
|---|---|---|---|
| errore λ +18 nm | ~2.6° | ~55° | 22× |
| tilt 5° | 0.14° | 3.1° | 22× |
| spread multi-riga KSF | ~5° | ~120° | 22× |

**Osservato: deficit λ/2 / λ/4 = 2×** (−1.6° / −3.1°), NON 22×. Quindi TUTTI gli
effetti ∝ordine sono **esclusi**: tilt, errore di λ, E overlap multi-riga (era
"ultima risorsa" → fuori anch'esso). Il "644" era un artefatto della formula
zero-order: una vera λ_R≠626 manderebbe la λ/2 avvolta fuori di ~55°, NON osservato.

**Il deficit scala col valore NOMINALE di design (90/180), non con l'ordine fisico
(0.25/5.5).** A δ≈90 la ricostruzione è S3/sin-dominata, a δ≈180 è S1S2/cos-dominata:
entrambi i **punti di degenerazione** dove un canale si annulla e δ è massimamente
sensibile a un piccolo offset residuo nel canale che svanisce. È l'unica classe che
scala col nominale.

**Conclusione (culprit ~chiuso):** deficit PICCOLO (1.6°/3.1°, entro lo scatter di
pochi gradi), tutti i sistematici ∝ordine eliminati, residuo compatibile con
**sensibilità di ricostruzione alle degenerazioni δ=90°/180°** o semplice scatter +
ambiguità di design-λ (il design vero della λ/4 potrebbe essere ~615 nm). Il
rapporto 2× di due numeri piccoli può essere coincidenza. NON un sistematico singolo
identificabile. **Irrilevante per la correzione S3** (rosso 1/sin≈1.000).

### Candidati (storico, ora superati dalla svolta sopra)
1. **Centroide rosso errato → PROBABILMENTE NO** (decisione utente). L'algoritmo del
   centroide è semplice e affidabile; il picco principale del rosso è a **631 nm**,
   comunque lontano dai 644 richiesti. Sotto l'approssimazione monocromatica non
   esiste una singola λ rossa plausibile vicino a 644. Scartato (salvo sorprese).
2. **Bias moltiplicativo ~1.75% nell'estrazione δ → CANDIDATO PRINCIPALE.** Un
   fattore ~0.982 su tutte le δ mima esattamente lo shift apparente di +18 nm al
   rosso e spiega l'accordo fra le due lamine (stessa pipeline). Sarebbe su TUTTI i
   canali (sposta i fit di dispersione, non solo il rosso). Sorgenti possibili:
   cos+sin / pesi `sin²2θ` / Poincaré / normalizzazione self-ref.
3. **Overlap multi-λ del solo canale rosso → ULTIMO TENTATIVO** (se 2 è vicolo cieco).
   Il rosso NON è monocromatico (righe KSF 609/631/647): la δ misurata è la
   superposizione `<I·sinδ>`,`<I·cosδ>` sulle righe. Per un multi-ordine δ(609),
   δ(631), δ(647) sono molto diverse → la δ ricostruita ≠ δ(λ singola), e prevede
   anche un po' di depol al rosso. Richiede di abbandonare l'approssimazione
   monocromatica SOLO per il rosso (modello a più righe pesate). Tenuto come ultima
   risorsa per la complessità.

### STATO: APERTO (issue minore, irrilevante per S3)

Sintesi finale del deficit del rosso, dopo aver escluso tutto il resto:

- **Tutti i sistematici ∝ordine esclusi** (tilt, errore-λ del canale, overlap
  multi-riga KSF): scalano col ritardo totale (ordine·360°) → darebbero λ/2 ≈ 22× λ/4,
  ma si osserva 2×.
- **NON è un bias moltiplicativo della pipeline.** Il rapporto misurato/modello
  NON è costante sui canali (λ/4: R 0.97 / G 1.03 / B 1.04): il rosso legge basso,
  G/B leggono ALTI. Nessun fattore unico ~0.982. Quindi non è una "δ sotto-letta":
  è solo la **dispersione reale** di una lamina con design un po' sotto i 633 nm
  d'etichetta (il rosso ≈ al design → ~nominale; G/B salgono più ripide).
- **Depol risolta a parte** (vedi esperimento 5-righe sotto): la DoP è
  **indipendente dall'ordine** (λ/4 ≈ λ/2 a ogni canale) → haze/scattering del
  materiale, NON effetto di banda/multi-ordine. Coerente con foglio di polimero.

**Cosa resta aperto:** il deficit è piccolo (1.6°/3.1°, dentro lo scatter di pochi
gradi). Con **N=2 lamine** non si distingue una **tolleranza/etichettatura
sistematica del costruttore** (design reale del lotto ~615–633, "633" nominale) da
una **coincidenza** di due piccole deviazioni dello stesso segno (~25% di probabilità
a 2 campioni). Non risolvibile coi dati attuali: 2 lamine × 3 canali larghi è
degenere. **Servirebbe**: più lamine (statistica di lotto) o una misura di ritardanza
diretta e indipendente, per separare sistematico-vs-coincidenza.

**Irrilevante per la correzione S3** (al rosso δ_a≈90° → 1/sin≈1.000). Tocca solo i
valori assoluti di δ e i fit di dispersione, mai il fattore di correzione né i
risultati della tesi.

---

## Sintesi indagine materiale / ordine (chiusa, material-agnostic)

- **λ/4**: zero-order, material-INSENSITIVE su RGB (quarzo/MgF₂/zaffiro/calcite/geom
  tutti entro 3–6° a ordine 0.25). Design vero ~640–650 nm. Correzione robusta.
- **λ/2**: NON fittata da alcun cristallo a 633 fisso (best calcite ord 4.5, RMS 12°).
  Con **design libera (~626 nm)** una dispersione **piatta** (qualunque materiale,
  geom 1/λ) a **ordine ~5.5** fitta a **RMS 4.4°** (180/153/140 vs 177/157/134):
  discesa = **aliasing** di multi-ordine. Spessore ~mm + Δn basso → **mica** coerente
  (ord ~5.5 = 0.83 mm di mica raw; quarzo raw mm darebbe ord ~14, fuori ladder →
  escluso; quarzo/cellophane solo se film sottile sandwich nel vetro).
- **Conclusione difendibile**: λ/2 = lamina economica multi-ordine (mica-compatibile),
  ordine ~5–6, design ~626 nm; materiale/ordine non determinabili univocamente da 3
  punti RGB (degenere, ipersensibile a λ_design, steepness, tilt).

## Tilt (quantificato)
Variazione frazionaria δ ≈ ±0.16%/(5°)², ∝ θ². Spostamento δ avvolta = frazione ×
(ordine×360°): λ/4 ≤0.15° a 5° (**trascurabile** → calibrazione tilt-robusta);
λ/2 ord 5.5 ~3° a 5°, ~13° a 10° (∝ ordine → nuisance reale sul multi-ordine).

---

### Esperimento "per gioco": rosso = 5 righe KSF (609/613/631/635/647)

Pesi d'intensita' da `r.csv`: 631→0.37, 635→0.29, 613→0.18, 609→0.08, 647→0.08
(centroide 5 righe = 628 nm, coerente col 626). δ ricostruita = media circolare
pesata di δ_s sulle righe; |risultante| = ritenzione DoP.
- **Zero-order**: shift ~0.3°, DoP 1.00 → le 5 righe ≡ 1 centroide. Niente cambia.
- **Multi-ordine (5–6)**: modello prevede shift ~−9° + DoP ~0.80.
- **MA i dati NON mostrano la depol prevista**: DoP rossa misurata λ/4=0.906,
  λ/2=0.923 (entrambe ~0.92, λ/2 multi-ordine perfino PIÙ ALTA della λ/4). Se la
  depol fosse l'effetto banda multi-ordine, la λ/2 dovrebbe avere la DoP più bassa.
  → la depol rossa (~0.9) è **indipendente dall'ordine** (illuminazione/misura),
  NON effetto multi-riga. Le due righe dominanti 631/635 distano solo 4 nm → spread
  in δ minimo anche a ordine 5–6; il modello a 5-δ sovrastima usando le code deboli.
- **Esito: nessun risultato interessante** (come previsto). Effetto multi-riga
  trascurabile; un altro vicolo cieco chiuso pulito. Non per la tesi.

### Voci datate

**2026-06-11** — Aperto il journal. Indagine materiale/ordine/tilt chiusa come sopra.
Culprit aperto: δ rosso sotto-design (∝ design, ~1.75%) → tilt escluso come causa
principale. **Avanzamento**: invertendo δ=design, entrambe le lamine richiedono
λ_R ≈ 644 nm, identico a 0.4 nm → causa nel **canale rosso condiviso**, non nelle
lamine. Ma +18 nm non è media di banda (sarebbe second'ordine + segno opposto):
restano centroide-rosso-errato (vs 626) o bias moltiplicativo ~1.75% dell'estrazione
δ. Prossimo: ricomputare il centroide rosso dallo spettro. NB: irrilevante per la
correzione S3 (al rosso 1/sin≈1.000).

**2026-06-11 (sera) — SVOLTA + correzione.** Il "λ_R=644" era un artefatto: usava la
formula zero-order su una λ/2 multi-ordine. Rifatto bene, tilt/λ-error/multi-riga
scalano TUTTI col ritardo totale (ordine·360°) → λ/2 dovrebbe deviare 22× la λ/4;
osservato solo 2× (∝ valore nominale 90/180). Tutti i sistematici ∝ordine ESCLUSI
(incluso il multi-riga "ultima risorsa"). Centroide rosso anche scartato (utente:
algoritmo semplice, picco 631 ≪ 644). Residuo piccolo (1.6°/3.1°), compatibile con
sensibilità di ricostruzione ai punti degeneri δ=90°/180° o scatter + ambiguità di
design-λ. Culprit ~chiuso: non un sistematico singolo; irrilevante per S3.

**2026-06-11 (chiusura indagine).** Due verifiche finali: (1) il rapporto
misurato/modello NON è costante sui canali (λ/4 R/G/B = 0.97/1.03/1.04) → NON c'è
bias moltiplicativo; il "deficit del rosso" è la dispersione reale di una lamina con
design un po' sotto 633. (2) la DoP è indipendente dall'ordine (λ/4≈λ/2 a ogni
canale) → la depol è haze/scattering del materiale, non effetto banda/multi-ordine.
**Issue lasciato APERTO** (deciso utente): se il piccolo below-design sia tolleranza
sistematica di lotto o coincidenza a N=2 non è separabile coi dati attuali (2 lamine
× 3 canali larghi). Ipotesi fisica leading = fogli di polimero tagliati (spiega
spessore, multi-ordine λ/2, depol-haze, design off-label condiviso). Tesi invariata,
correzione S3 robusta. Indagine sospesa qui.
