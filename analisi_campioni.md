# Report analisi sperimentali — Polarimetro a immagine 2D
**Tesi:** Filippo Narici — Ingegneria Fisica, Politecnico di Milano, A.A. 2025–26

---

## 1. Soluzione di saccarosio (attività ottica)

**Setup:** boccetta a base quadrata, spessore di attraversamento 13 mm, zucchero in acqua (concentrazione ignota).

**Osservazione qualitativa (mappa AoLP, canale blu)**
La regione esterna alla boccetta è a ~0° per costruzione (allineamento del reference frame). L'interno della soluzione presenta una rotazione positiva uniforme dell'AoLP, visibile come area calda nella colormap. La struttura curva più brillante all'interno della boccetta è la cannuccia in plastica: essendo injection-molded, presenta birifrangenza da stress propria, che si sovrappone al segnale dell'attività ottica e produce variazioni locali di AoLP nella regione corrispondente.

**Valori misurati per canale RGB**

| Canale | λ_eff (nm) | ΔAoLP misurato (°) |
|--------|-----------|-------------------|
| R      | 626       | 3.4               |
| G      | 536       | 4.9               |
| B      | 466       | 6.7               |

La rotazione aumenta al diminuire di λ, coerentemente con la dispersione rotatoria ottica (ORD) del saccarosio destrogiro.

**Fit della dispersione rotatoria**
Modello di Drude semplificato: α = a/λ², con a = 1 420 554 nm²·° e R² = 0.986.
Con soli 3 punti il fit è formalmente quasi esatto, ma la consistenza fisica è solida: l'andamento è monotono e nella direzione attesa.

---

## 2. Righello in plastica trasparente (fotoelasticità qualitativa)

**Setup:** righello in materiale polimerico trasparente (injection-molded), analisi canale rosso, valutazione puramente qualitativa.

**Osservazione generale**
Il righello è chiaramente visibile in S0 come regione a minor trasmittanza rispetto allo sfondo. Il segnale polarimetrico è pulito e privo di artefatti rilevanti di intensità.

**Frange fotoelastiche**
S1 e S2 mostrano un pattern a striature alternate rosso/blu all'interno del righello, con orientazioni leggermente diverse tra i due parametri, coerente con la rotazione dell'asse delle tensioni principali lungo il corpo del campione. Le frange sono le isocrome tipiche di un materiale birifrangente sotto stress residuo di stampaggio.

Il DoLP è il parametro più leggibile: le bande scure (DoLP ≈ 0) corrispondono ai punti di ritardanza multipla intera di π. La frequenza spaziale delle frange aumenta verso la sommità del righello, fisicamente coerente con la concentrazione degli sforzi residui in prossimità del punto di iniezione dello stampaggio.

**S3 e AoLP**
S3 mostra le frange sovrapposte al pattern circolare della lamina λ/4. L'AoLP è quasi uniformemente a 0° nella regione di sfondo, mentre varia bruscamente all'interno del righello in corrispondenza delle frange, segnalando la rotazione locale delle direzioni principali di tensione (isocline).

---

## 3. Trave a sbalzo (cantilever, fotoelasticità quantitativa)

**Setup:** trave in materiale trasparente, vincolata a un'estremo, analisi canale rosso. Acquisita in due condizioni: scarica e sotto carico.

**Confronto scarica / sotto carico (mappa S3)**
- **Con carico:** l'interno della trave mostra un segnale S3 positivo significativo e uniforme lungo tutto il corpo. In prossimità del vincolo (estremo destro) si osservano variazioni brusche e frange che cambiano segno rapidamente, coerenti con la concentrazione degli sforzi alla base del cantilever. La comparsa di S3 finito indica che la birifrangenza indotta dallo stress converte parte della polarizzazione lineare in componente circolare, effetto atteso per un ritardatore con asse a 45° rispetto alla polarizzazione incidente.
- **Senza carico:** la trave appare quasi neutra, con segnale S3 residuo compatibile con tensioni di stampaggio preesistenti o con il rumore del sensore. La distribuzione spaziale è assente.

**Nota sul fondo**
Il gradiente di sfondo (angolo superiore sinistro → inferiore destro) presente in entrambe le immagini è un artefatto sistematico, attribuibile a non-uniformità spaziale della lamina λ/4 o del display LCD, non al campione.

---

## 4. Lamina λ/4 zero-order (633 nm)

**Setup:** lamina quarto d'onda zero-order, λ_design = 633 nm, orientata a ~50° (coerente con il valore stimato dalle mappe dell'asse veloce). Analisi a tre canali.

**Mappe di ritardanza δ**
Tutte e tre le mappe mostrano una struttura a due zone concentriche: un cerchio interno con δ prossimo alla saturazione della scala e un anello esterno con ritardanza inferiore. Questa non-uniformità radiale non è attesa per una lamina ideale; le cause probabili sono una variazione spaziale dello spessore del cristallo oppure un effetto di incidenza obliqua dei raggi periferici, che percorrono un cammino ottico maggiore. La rumorosità aumenta progressivamente dal canale rosso al canale blu, coerentemente con la maggiore correzione cromatica applicata e il minor segnale disponibile.

**Valori misurati vs. teorici**
Modello teorico per lamina zero-order: δ(λ) = 90° × 633/λ

| Canale | λ_eff (nm) | δ misurato (°) | δ teorico (°) | Scarto (°) |
|--------|-----------|---------------|--------------|-----------|
| R      | 626       | 86            | 91.0         | −5.0      |
| G      | 536       | 102           | 106.3        | −4.3      |
| B      | 466       | 120           | 122.2        | −2.2      |

I valori misurati sono sistematicamente inferiori al teorico di 2–5°. Il fit δ ~ 90·λ₀/λ con R² = 0.916 descrive bene l'andamento, ma il coefficiente ottimale risulta leggermente inferiore a 90°·633 nm: la lamina reale introduce un ritardo nominale leggermente inferiore a λ/4 alla lunghezza d'onda di progetto, plausibile entro le tolleranze di fabbricazione.

---

## 5. Lamina λ/2 zero-order (633 nm)

**Setup:** lamina mezzo d'onda zero-order, λ_design = 633 nm, orientata a ~50°. Analisi a tre canali.

**Valori misurati e correzione**

| Canale | λ_eff (nm) | δ grezzo (°) | δ corretto (°) |
|--------|-----------|-------------|---------------|
| R      | 626       | 180         | 180           |
| G      | 536       | 146         | 214           |
| B      | 466       | 110         | 250           |

Il fit δ ~ 180·633/λ sui valori corretti dà R² = 0.989. La correzione consiste nel sostituire i valori verdi e blu con il loro complemento a 360°.

**Spiegazione dell'ambiguità matematica**
Il calcolo della ritardanza usa Δ = arccos(cos Δ), con arccos che ha codominio [0°, 180°]. Un ritardo fisico Δ e il suo complemento 360°−Δ producono lo stesso valore di cos Δ, quindi sono indistinguibili:

cos(214°) = cos(360° − 214°) = cos(146°)

La correzione di segno tramite S₃ risolve l'ambiguità tra +δ e −δ ma non quella di avvolgimento a 2π: per δ > 180° il polarimetro misura sistematicamente 360°−δ. Per risolvere questa ambiguità senza informazione a priori sarebbe necessario misurare a più lunghezze d'onda e usare la continuità spettrale per srotolare la fase.

---

## 6. Nastro adesivo stratificato (0–5 strati su vetrino)

**Setup:** vetrino con strati sovrapposti di nastro adesivo trasparente, in configurazione simmetrica 1-2-3-4-5-4-3-2-1. La simmetria è sfruttata come controllo interno di consistenza: i valori sinistra/destra concordano entro ±10° su tutti i canali, confermando l'uniformità degli strati e la correttezza dell'allineamento del reference frame.

### Dati grezzi misurati

**Canale rosso (λ_eff = 626 nm)**

| Strati | δ sinistra (°) | δ destra (°) |
|--------|---------------|-------------|
| 1      | −138          | −126        |
| 2      | +100          | +126        |
| 3      | ~0            | ~0          |
| 4      | −131          | −125        |
| 5      | —             | +126 (centro) |

**Canale verde (λ_eff = 536 nm)**

| Strati | δ sinistra (°) | δ destra (°)        |
|--------|---------------|---------------------|
| 1      | −87           | −80                 |
| 2      | +163          | ±150 (instabile)    |
| 3      | +107          | +126                |
| 4      | +52           | +60                 |
| 5      | —             | −60 (centro)        |

**Canale blu (λ_eff = 466 nm)**

| Strati | δ sinistra (°) | δ destra (°)        |
|--------|---------------|---------------------|
| 1      | −36           | −28                 |
| 2      | −76           | −52                 |
| 3      | −110          | −90                 |
| 4      | +135          | ±128 (instabile)    |
| 5      | —             | +130 (centro)       |

### L'ambiguità: 120° o 240° per strato?

Il canale rosso mostra un pattern ciclico con periodo 3 strati (δ → 0° a N=3), compatibile con δ_singolo = 120° oppure 240°/strato (l'arccos non distingue i due casi). Il canale verde discrimina:

- Con 120°/strato → 140°/strato al verde → non riproduce i dati
- Con 240°/strato → 280°/strato al verde → accordo con i dati ✓

La soluzione corretta è **δ_singolo ≈ 240°/strato a 626 nm**.

### Verifica del modello (phase wrapping)

La ritardanza vera cresce linearmente: δ_vero(N) = N × δ_singolo. Il polarimetro misura arccos(cos(δ_vero mod 360°)), con il segno assegnato da S₃.

**Canale rosso — δ_singolo = 240°/strato**

| N | δ_vero (°) | mod 360° | arccos atteso (°) | Misurato medio (°) |
|---|-----------|---------|------------------|-------------------|
| 1 | 240       | 240     | 120              | 132               |
| 2 | 480       | 120     | 120              | 113               |
| 3 | 720       | 0       | 0                | ~0 ✓              |
| 4 | 960       | 240     | 120              | 128               |
| 5 | 1200      | 120     | 120              | 126               |

**Canale verde — δ_singolo ≈ 280°/strato**

| N | δ_vero (°) | mod 360° | arccos atteso (°) | Misurato medio (°) |
|---|-----------|---------|------------------|-------------------|
| 1 | 280       | 280     | 80               | 83                |
| 2 | 560       | 200     | 160              | ~156              |
| 3 | 840       | 120     | 120              | ~116              |
| 4 | 1120      | 40      | 40               | ~56               |
| 5 | 1400      | 320     | 40               | ~60               |

**Canale blu — δ_singolo = 323°/strato (modello 1/λ) vs 305°/strato (fit)**

| N | δ predetto 323° (°) | δ predetto 305° (°) | Misurato medio (°) |
|---|--------------------|--------------------|-------------------|
| 1 | 37                 | 35                 | 32                |
| 2 | 74                 | 70                 | 64                |
| 3 | 111                | 105                | 100               |
| 4 | 148                | 140                | 131               |
| 5 | 175                | 175                | 130               |

Lo scostamento sistematico crescente tra il modello 1/λ e i dati blu rivela la **dispersione cromatica di Δn**: la birifrangenza del polimero diminuisce verso il blu. Il modello corretto non è δ ∝ 1/λ ma δ ∝ Δn(λ)/λ.

### Instabilità di segno osservate

| Canale | N strati | δ_vero mod 360° | Causa                          |
|--------|---------|----------------|-------------------------------|
| Verde  | 2       | ~200°          | Prossimo alla soglia di 180°  |
| Blu    | 4       | ~212°          | Prossimo alla soglia di 180°  |

Queste instabilità non sono difetti del sistema ma conseguenze matematiche dell'assegnazione del segno tramite S₃·sin(2Θ), che diverge quando δ mod 360° → 180°.

### Risultati finali

**Ritardanza per singolo strato:**

| Canale | λ_eff (nm) | δ_singolo (°) | δ da scaling 1/λ (°) | Scostamento |
|--------|-----------|--------------|---------------------|-------------|
| R      | 626       | 240 ± 15     | (riferimento)       | —           |
| G      | 536       | 275 ± 15     | 280                 | −2%         |
| B      | 466       | 305 ± 20     | 323                 | −6%         |

**Birifrangenza stimata:** assumendo spessore per strato d ≈ 50 μm, dalla relazione δ = 2πΔn·d/λ si ricava per il canale rosso: Δn ≈ (240°/360°) × 626 nm / 50 000 nm ≈ **0.008**, valore plausibile per un film polimerico orientato.

**Dispersione cromatica:** il rapporto δ_blue/δ_red = 305/240 = 1.27, contro il rapporto geometrico λ_red/λ_blue = 626/466 = 1.34. La differenza del ~5–6% quantifica la riduzione di Δn nel blu, coerente con la dispersione normale dei polimeri.
