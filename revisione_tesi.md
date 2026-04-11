# Revisione Tesi — Appunti per Claude Code

Questo file contiene le istruzioni di revisione per la tesi "Polarimetro a Immagine 2D Low-Cost per Polarimetria Spazialmente Risolta". Le modifiche sono organizzate per capitolo. Dove possibile, sono fornite riscritture esplicite da usare come sostituzione diretta.

**Regola generale da applicare ovunque:** eliminare i rimandi anticipatori tipo "come descritto nel capitolo X", "come vedremo nella sezione Y", "come discusso in seguito". Tenerne al massimo 3-4 in tutta la tesi, solo dove il rimando è strettamente necessario per la comprensione. Il lettore ha l'indice.

**Seconda regola generale:** eliminare le frasi che ribadiscono cose ovvie dal titolo ("approccio low-cost", "smartphone come rivelatore", "36 immagini a passi di 10°"). Ogni concetto chiave va introdotto UNA volta nel capitolo appropriato, poi basta riferirsi ad esso senza rispiegarlo.

---

## Capitolo 1 — Introduzione

### 1.0 Preambolo (prima di 1.1)

I due paragrafi prima della sezione 1.1 sono ridondanti con le sezioni 1.1 e 1.2. Riscrivere l'intera apertura del capitolo così:

> La polarizzazione della luce descrive l'orientazione e il comportamento temporale del campo elettrico nel piano trasversale alla direzione di propagazione. Sebbene meno intuitiva dell'intensità o della frequenza, porta con sé informazioni decisive sulle proprietà del mezzo attraversato: struttura cristallina, stato di sollecitazione meccanica, chiralità molecolare. La polarimetria — la misura quantitativa dello stato di polarizzazione — è per questa ragione uno strumento trasversale a ottica, scienza dei materiali, chimica analitica e ingegneria strutturale, con applicazioni che spaziano dalla fotoelasticità alla diagnostica biomedica, dal controllo qualità industriale all'osservazione astronomica.

Questo sostituisce TUTTO il testo che precede la sezione 1.1. Niente duplicazioni con quanto segue.

### 1.1 Polarimetria classica e suoi limiti

Il contenuto è buono, ma la prima frase ripete il preambolo. Riscrivere l'attacco:

> L'approccio tradizionale alla polarimetria impiega un rivelatore puntuale — tipicamente un fotodiodo — posto dietro un sistema di analizzatore e lamine ritardatrici. Ruotando l'analizzatore si ricostruiscono i quattro parametri di Stokes del fascio incidente: è la configurazione descritta, ad esempio, nel manuale di laboratorio del corso di Fisica Sperimentale del Politecnico di Milano [5].

(Elimina la frase "Questa configurazione è consolidata, accurata e didatticamente efficace:" — è un giudizio vuoto.)

Il secondo paragrafo ("Il limite principale...") è buono, tenerlo. Ma tagliare la frase finale "Per ottenere una mappa bidimensionale sarebbe necessaria una scansione meccanica punto per punto, operazione lenta, complessa e raramente praticata in contesti didattici o di ricerca preliminare." e sostituirla con:

> Ottenere una mappa bidimensionale richiederebbe una scansione punto per punto, operazione lenta e raramente praticata al di fuori di contesti industriali specializzati.

Il terzo paragrafo (limite economico) va bene così.

### 1.2 Polarimetria a immagine

Il primo paragrafo è buono. Il secondo ("I polarimetri a immagine commerciali...") ripete "il costo rimane elevato" — già detto in 1.1. Riscrivere il passaggio da "I polarimetri a immagine commerciali" fino alla fine della sezione come segue:

> I polarimetri a immagine di ricerca utilizzano sensori CCD o CMOS dedicati con griglie micropolarizzatrici integrate o cristalli liquidi modulabili, raggiungendo prestazioni elevate ma a costi che ne limitano l'accesso a laboratori ben finanziati. L'ampia diffusione degli smartphone con sensori CMOS ad alta risoluzione e acquisizione RAW suggerisce una possibilità concreta: impiegare un dispositivo già posseduto da quasi tutti gli studenti come rivelatore, riducendo il costo dell'apparato di due ordini di grandezza.

### 1.3 Obiettivo della tesi

Questa sezione è troppo lunga e anticipa i contenuti dei capitoli 3, 4 e 5. Riscriverla interamente:

> Questa tesi si propone di progettare, realizzare e validare un polarimetro a immagine bidimensionale a basso costo, utilizzando come rivelatore il sensore CMOS di uno smartphone commerciale. Il sistema deve essere in grado di ricostruire il vettore di Stokes completo pixel per pixel e di generare mappe spazialmente risolte del grado di polarizzazione, dell'angolo di polarizzazione lineare, della ritardanza e dell'orientazione dell'asse veloce. Per validare l'approccio, sono stati analizzati campioni rappresentativi di birifrangenza, attività ottica e fotoelasticità.

Tutto il resto (modello del tablet, passo angolare, pseudo-inversa, elenco dei campioni, pipeline Python) va tolto — è materia dei capitoli successivi.

### 1.4 Struttura della tesi

Riscrivere in forma compatta:

> Il capitolo 2 richiama i fondamenti teorici della polarimetria: formalismo di Stokes, matrici di Mueller, e i fenomeni fisici investigati. Il capitolo 3 descrive l'apparato sperimentale e il protocollo di acquisizione. Il capitolo 4 presenta i campioni selezionati per la validazione. Il capitolo 5 documenta la pipeline di analisi dati. Il capitolo 6 discute i risultati ottenuti e i limiti del metodo. Il capitolo 7 riassume le conclusioni e indica possibili sviluppi futuri.

---

## Capitolo 2 — Fondamenti teorici

### 2.1

Il paragrafo finale introduce il DOP (eq. 2.3) usando i parametri di Stokes, che vengono definiti solo nella sezione 2.2. Spostare la definizione del DOP alla fine della sezione 2.2.1, subito dopo l'eq. 2.6 (la disuguaglianza fondamentale). In 2.1, al posto del paragrafo sul DOP, chiudere con:

> Nella realtà, le sorgenti comuni emettono luce non polarizzata, in cui la fase δ varia casualmente nel tempo. La sovrapposizione di una componente polarizzata e una non polarizzata produce luce parzialmente polarizzata, il cui grado di polarizzazione è definito formalmente nella sezione 2.2.

### 2.2.3 Misura sperimentale dei parametri di Stokes

Questa sottosezione è troppo breve e consiste quasi interamente di rimandi. Eliminarla come sottosezione autonoma. Spostare il suo contenuto (3 righe) alla fine della 2.2.1, dopo la definizione operativa dei parametri di Stokes (eq. 2.5):

> Dal punto di vista sperimentale, S₀, S₁ e S₂ si ottengono da misure di intensità attraverso un analizzatore lineare a diversi angoli, come mostrato dalla legge di Malus generalizzata (sezione 2.3). Il parametro S₃ richiede l'inserimento di una lamina λ/4 prima dell'analizzatore.

### 2.5–2.7 Chiusure anticipatorie

Eliminare le frasi finali di 2.5.3, 2.6 e 2.7 che rimandano ai capitoli successivi. Esempi:
- In 2.5.3, eliminare da "Questa dipendenza cromatica ha una conseguenza importante per il polarimetro sviluppato in questa tesi:" fino a fine paragrafo.
- In 2.6, eliminare l'ultimo paragrafo ("L'attività ottica è rilevante per il polarimetro di questa tesi nella misura di soluzioni zuccherine...").
- In 2.7, eliminare l'ultimo paragrafo ("L'analisi fotoelastica è una delle applicazioni dirette...").

---

## Capitolo 3 — Apparato sperimentale

### 3.1 Panoramica del setup

Riscrivere l'intera sezione. Attualmente ripete per la terza volta il concetto fondamentale della tesi. Nuova versione:

> L'apparato opera in configurazione di trasmissione su rotaia ottica. Lo schema generale è:
>
> Sorgente → Campione → [λ/4] → Analizzatore → Sensore    (3.1)
>
> dove la lamina λ/4 viene inserita solo per la determinazione di S₃. La fig. 3.1 mostra due viste dell'apparato assemblato. Le sezioni seguenti descrivono ciascun componente.

Eliminare i paragrafi "La filosofia progettuale..." (è nel titolo) e "Rispetto al polarimetro puntuale descritto nel manuale..." (già detto nel cap. 1).

### 3.2.1 Rotaia ottica

Troppo generica. Riscrivere:

> L'apparato è montato su una rotaia ottica Optosci con cavalieri scorrevoli, che garantisce l'allineamento dei componenti lungo un asse ottico comune e la riproducibilità del posizionamento tra sessioni di misura.

(Un solo paragrafo. Eliminare il secondo paragrafo sull'importanza della riproducibilità — è ovvio.)

### 3.2.2 Sorgente luminosa

Buona nel contenuto, ma appesantita. Riscrivere:

> La sorgente è un tablet Samsung Galaxy Tab S7 FE con display impostato su schermata bianca alla massima luminosità. Il pannello LCD emette luce bianca a banda larga attraverso un polarizzatore integrato: la luce in uscita è quindi già polarizzata linearmente, con asse orientato approssimativamente in verticale in configurazione landscape. Questa caratteristica rende il display una sorgente estesa a stato di polarizzazione ben definito e relativamente uniforme, ideale per illuminare l'intero campo visivo del sensore.

(Elimina il paragrafo successivo della sezione originale 3.2.2, che parla della compensazione software — è materia del cap. 5.)

### 3.3.1 Smartphone Samsung Galaxy S24

Eliminare la frase "La scelta di utilizzare uno smartphone come rivelatore è il punto cardine dell'approccio low-cost: il sensore CMOS di un moderno smartphone offre..." e riscrivere:

> Il rivelatore è la fotocamera principale di uno smartphone Samsung Galaxy S24, con sensore CMOS da circa 10 megapixel effettivi, obiettivo a focale 7.0 mm (equivalente 69 mm), apertura f/2.4, e profondità di acquisizione fino a 12 bit per canale in modalità RAW.

### 3.5 Calibrazione e riproducibilità

Questa sezione ha sovrapposizioni significative con il capitolo 5. Riscrivere in forma sintetica:

> I parametri di Stokes normalizzati (sᵢ = Sᵢ/S₀) sono per definizione indipendenti dall'intensità assoluta della sorgente, eliminando la necessità di una calibrazione assoluta. L'accuratezza è garantita da tre accorgimenti: acquisizione in formato RAW con parametri manuali (per preservare la linearità della risposta), downsampling spaziale (per ridurre il rumore, sezione 5.1), e allineamento software del sistema di riferimento (per compensare l'offset angolare della sorgente, sezione 5.6). La variabilità residua è dominata dal rumore del sensore, ridotto dal binning e dalla sovradeterminazione del sistema lineare.

---

## Capitolo 4 — Raccolta dati e campioni

### 4.1 Criteri di selezione

I quattro bullet point sono ovvii. Riscrivere come prosa:

> I campioni sono stati scelti per coprire fenomeni ottici distinti (birifrangenza, attività ottica, fotoelasticità), privilegiando materiali trasparenti compatibili con la configurazione in trasmissione. Alcuni campioni — le lamine d'onda commerciali — possiedono parametri nominali noti, utili per una validazione quantitativa; altri — nastro adesivo, righello, trave a sbalzo — offrono strutture spaziali interessanti per verificare la capacità di imaging del sistema.

### 4.2.3 Soluzione di saccarosio

La legge di Biot e il modello di Drude sono già nel cap. 2. Eliminare la riderivazione delle eq. 4.1 e la rispiegazione di [α]. Riscrivere il passaggio:

> Il potere rotatorio specifico del saccarosio segue in prima approssimazione il modello di Drude (eq. 2.16), con [α]_D = 66.47 °/(dm·g/mL) alla riga D del sodio. La soluzione è stata preparata sciogliendo 8.4 g di zucchero in una boccetta a base quadrata da 6.9 mL, con cammino ottico l = 13 mm (0.13 dm), per una concentrazione gravimetrica c_grav ≈ 1.22 g/mL.
>
> Il campione consente di verificare due aspetti: la rotazione uniforme del piano di polarizzazione, osservabile come variazione omogenea dell'AoLP; e la legge di dispersione α_rot ∝ 1/λ², sfruttando i tre canali colore del sensore.

### 4.3 Preparazione e montaggio

Troppi bullet point ovvii. Condensare:

> Tutti i campioni sono inseriti nel porta-campione sulla rotaia, tra sorgente e analizzatore. Le superfici ottiche vengono pulite prima dell'acquisizione; il campione è centrato nel campo visivo e mantenuto stabile per l'intera sequenza di 38 immagini. Le acquisizioni avvengono in oscurità ambientale, con la sola illuminazione del display. Le immagini sono salvate con nomenclatura standardizzata (pol000.dng...pol350.dng per la sequenza lineare; wav45.dng e wav-45.dng per la lamina λ/4).

---

## Capitolo 5 — Analisi dei dati

### 5.1 Apertura

Eliminare la prima frase ("Le immagini acquisite dallo smartphone vengono salvate in formato DNG...") — è già nel cap. 3. Iniziare con:

> Il primo passo della pipeline consiste nel caricamento di ciascun file DNG e nella conversione in matrice numerica. La demosaicizzazione viene eseguita tramite rawpy con bilanciamento del bianco della fotocamera e curva di trasferimento lineare, producendo un array H×W×3 in RGB a 16 bit. Si estrae poi il singolo canale colore di interesse come matrice H×W in virgola mobile a 32 bit.

### 5.3.3 Implementazione vettorializzata

Troppo dettagliata per il corpo della tesi (menziona np.linalg.pinv, prodotto matriciale NumPy). Riscrivere:

> Per evitare cicli espliciti sui pixel, lo stack di N immagini viene riorganizzato in una matrice N × (H·W). La pseudo-inversa, calcolata una sola volta, viene moltiplicata per l'intera matrice dei dati con un singolo prodotto matriciale, restituendo le tre mappe S₀, S₁, S₂.

### 5.5.1 Pipeline morfologica

I 7 passi numerati sono troppo procedurali (stile documentazione software). Riscrivere come prosa:

> La maschera opera sulla mappa S₀. Si calcola un profilo di illuminazione locale tramite filtro gaussiano e si identificano come bordi i pixel con intensità inferiore al 95% del profilo locale. I bordi vengono dilatati per chiudere eventuali discontinuità, le cavità interne riempite, e si conserva unicamente la componente connessa di area maggiore. Un margine di sicurezza dilata leggermente la regione individuata. Il complemento di questa regione costituisce la maschera di sfondo.

### 5.9 Strumento di validazione interattivo

Spostare in appendice. Nella sezione, lasciare solo:

> A supporto della pipeline è stato sviluppato un debugger interattivo per la verifica pixel-per-pixel della qualità del fit. Lo strumento, descritto in appendice A, consente di sovrapporre i 36 valori misurati alla curva teorica e di visualizzare l'ellisse di polarizzazione per qualsiasi pixel selezionato.

---

## Capitolo 6 — Risultati e discussione

### 6.2.1–6.2.3 Mappe generiche dei parametri di Stokes

Queste tre sottosezioni descrivono cosa sono S₀, S₁, S₂, S₃ in termini generali — informazione già nel cap. 2. Eliminarle tutte e tre. Al loro posto mettere un unico paragrafo di raccordo:

> Per ciascun campione la pipeline produce le mappe bidimensionali di S₀, S₁, S₂, S₃ e delle grandezze derivate (DoLP, AoLP, δ, α), visualizzate nella griglia 3×3 descritta nella sezione 5.10. I risultati sono discussi campione per campione nelle sezioni seguenti.

### 6.3.4 Stima ottica della concentrazione — discussione della discrepanza

La discussione della discrepanza (fattore 2.6) è troppo frettolosa. Espandere:

> La discrepanza di un fattore ~2.6 tra concentrazione ottica (0.47 g/mL) e gravimetrica (1.22 g/mL) merita un'analisi. La causa più probabile è la non applicabilità del modello di Drude semplificato a concentrazioni così elevate: la soluzione preparata è prossima alla saturazione (~67% in peso), regime in cui la relazione lineare tra rotazione e concentrazione (eq. 2.16) perde validità e il potere rotatorio specifico [α] diminuisce apprezzabilmente rispetto al valore tabulato per soluzioni diluite. Un contributo secondario potrebbe derivare dal cammino ottico attraverso le pareti in vetro della boccetta (~2 mm di vetro borosilicato), che non è otticamente attivo ma introduce una ritardanza da stress residuo che potrebbe interferire con la misura dell'AoLP. Nonostante la discrepanza quantitativa, la misura conferma la capacità del sistema di rilevare l'attività ottica e di riprodurre la legge di dispersione rotatoria.

### 6.4.1 Capacità del metodo

Eliminare i bullet point e riscrivere come prosa:

> I risultati dimostrano che il sistema ricostruisce il vettore di Stokes completo con risoluzione spaziale bidimensionale, misura ritardanza e asse veloce su campioni macroscopici, e distingue fenomeni polarimetrici di natura diversa. L'apparato produce mappe fisicamente interpretabili con un costo complessivo inferiore a quello di un singolo componente ottico di precisione di un polarimetro convenzionale.

---

## Capitolo 7 — Conclusioni

### 7.1 Riepilogo

Troppo lungo, ripete l'intero setup. Riscrivere:

> In questo lavoro è stato realizzato un polarimetro a immagine bidimensionale che utilizza il sensore CMOS di uno smartphone come rivelatore. Il vettore di Stokes completo viene ricostruito pixel per pixel da 36 immagini RAW per i parametri lineari e 2 immagini aggiuntive con lamina λ/4 per il parametro circolare. L'intera pipeline di analisi è stata implementata in Python e validata su campioni con proprietà polarimetriche note.

### 7.2 Risultati principali

I bullet point vanno riformulati come prosa:

> Le lamine d'onda commerciali hanno restituito valori di ritardanza coerenti con i nominali (scarti di 2–5°), confermando l'accuratezza della ricostruzione. Il campione a strati di nastro adesivo ha verificato la linearità della risposta, con ritardanza proporzionale al numero di strati. La soluzione di saccarosio ha mostrato la rotazione del piano di polarizzazione attesa per l'attività ottica, con dispersione rotatoria consistente con il modello di Drude. I provini fotoelastici hanno prodotto frange isocromatiche chiaramente risolte, dimostrando la capacità del sistema di mappare la distribuzione spaziale degli sforzi interni.

### 7.4 Sviluppi futuri

Le prime tre voci (automazione, GPU, sorgente monocromatica) sono ovvie. Aggiungere un suggerimento più originale alla fine della sezione:

> Un'ulteriore direzione di sviluppo riguarda l'estensione alla polarimetria in riflessione, che consentirebbe l'analisi di campioni opachi (metalli, tessuti biologici) e aprirebbe applicazioni in diagnostica dermatologica e controllo qualità di superfici. In prospettiva, l'impiego di tecniche di deep learning per la ricostruzione dei parametri di Stokes da un numero ridotto di immagini potrebbe abbreviare significativamente i tempi di acquisizione, avvicinando il sistema alla misura in tempo reale.

---

## Checklist finale

- [ ] Eliminare tutti i "come descritto nel capitolo X" eccetto 3-4 rimandi strettamente necessari
- [ ] Verificare che nessun concetto venga introdotto più di una volta
- [ ] Convertire tutti i bullet point nel corpo della tesi in prosa (i bullet point vanno bene solo in tabelle e appendici)
- [ ] Aggiungere stime di incertezza dove possibile (deviazione standard, intervalli di confidenza) — questo è un punto debole significativo per una tesi di ingegneria fisica
- [ ] Verificare le didascalie delle figure (alcune sembrano placeholder)
