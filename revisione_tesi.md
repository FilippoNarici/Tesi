# Revisione completa — Polarimetro a Immagine 2D Low-Cost

Documento di revisione per la tesi di Filippo Narici.
Ogni sezione indica: problema, soluzione, e dove possibile il testo riscritto pronto da inserire.

---

## Principi generali della revisione

1. **Filo narrativo continuo**: ogni capitolo deve chiudersi con un ponte verso il successivo.
2. **Meno sottosezioni, più prosa**: le micro-sezioni da 3–5 righe vanno fuse in paragrafi.
3. **Motivare prima di definire**: ogni equazione o concetto va introdotto spiegando *perché* serve.
4. **Tono da tesi scientifica, non da documentazione software**: evitare titoli come "pipeline", "implementazione vettorializzata", "smart mask".
5. **Eliminare ridondanze**: se un concetto è spiegato nel cap. 2, non rispiegarlo nel cap. 4.

---

## Abstract

### Problema
L'abstract è tecnicamente corretto ma freddo. Manca una frase d'apertura che inquadri il *perché* e una chiusura che dia il significato del risultato.

### Testo riscritto

> La polarimetria — la misura quantitativa dello stato di polarizzazione della luce — è uno strumento trasversale a ottica, scienza dei materiali e ingegneria strutturale. Gli apparati convenzionali, tuttavia, forniscono misure puntuali e hanno costi dell'ordine delle decine di migliaia di euro, limitandone l'impiego ai laboratori specializzati.
>
> Questa tesi presenta la progettazione e la validazione di un polarimetro a immagine bidimensionale a basso costo, in cui il sensore CMOS di uno smartphone commerciale sostituisce il rivelatore tradizionale. Il sistema acquisisce 36 immagini a passi angolari regolari dell'analizzatore e due misure aggiuntive con una lamina quarto d'onda; il vettore di Stokes completo viene poi ricostruito pixel per pixel mediante regressione ai minimi quadrati. Si ottengono così mappe spazialmente risolte della polarizzazione lineare e circolare, della ritardanza e dell'orientazione dell'asse veloce sull'intero campo visivo.
>
> L'apparato è stato validato su campioni rappresentativi di birifrangenza (lamine d'onda commerciali, strati di nastro adesivo), attività ottica (soluzione di saccarosio) e fotoelasticità (righello in plastica, trave a sbalzo sotto carico). Le ritardanze misurate sulle lamine d'onda concordano con i valori nominali entro 2–5°; il nastro adesivo stratificato conferma la linearità della risposta; la soluzione di saccarosio riproduce la dispersione rotatoria attesa dal modello di Drude. I risultati dimostrano che un apparato il cui costo, escluso lo smartphone, è inferiore a 100 €, è in grado di produrre mappe polarimetriche bidimensionali quantitative, rendendolo un'alternativa concreta agli strumenti di laboratorio convenzionali per la didattica e la ricerca esplorativa.

---

## Capitolo 1 — Introduzione

### Problema
L'introduzione è divisa in quattro sottosezioni troppo brevi e meccaniche. La sezione 1.4 ("Struttura della tesi") è puro filler: il lettore ha l'indice. Il tono è più da relazione tecnica che da apertura di tesi.

### Soluzione
Eliminare la sezione 1.4. Fondere 1.1–1.3 in un testo continuo con al massimo due sottosezioni (non quattro). L'introduzione deve raccontare un arco: problema → opportunità → obiettivo.

### Testo riscritto

> # 1 | Introduzione
>
> La polarizzazione della luce descrive l'orientazione e il comportamento temporale del campo elettrico nel piano trasversale alla direzione di propagazione. Sebbene meno intuitiva dell'intensità o della frequenza, essa porta con sé informazioni decisive sulle proprietà del mezzo attraversato: struttura cristallina, stato di sollecitazione meccanica, chiralità molecolare. La polarimetria — la misura quantitativa dello stato di polarizzazione — è per questa ragione uno strumento trasversale a ottica, scienza dei materiali, chimica analitica e ingegneria strutturale, con applicazioni che spaziano dalla fotoelasticità alla diagnostica biomedica, dal controllo qualità industriale all'osservazione astronomica.
>
> ## 1.1 Dalla misura puntuale all'immagine
>
> L'approccio tradizionale alla polarimetria impiega un rivelatore puntuale — tipicamente un fotodiodo — posto dietro un sistema di analizzatore e lamine ritardatrici. Ruotando l'analizzatore si ricostruiscono i quattro parametri di Stokes del fascio incidente: è la configurazione descritta, ad esempio, nel manuale di laboratorio del corso di Fisica Sperimentale del Politecnico di Milano [5]. Il limite principale di questo schema è la sua natura zero-dimensionale: il rivelatore fornisce una singola misura scalare, integrata sull'intera sezione del fascio. Se il campione presenta variazioni spaziali delle proprietà ottiche — come accade nella maggior parte delle situazioni di interesse pratico, dai campi di tensione nei materiali fotoelastici alla birifrangenza non uniforme di un film polimerico — l'informazione spaziale viene irrimediabilmente perduta. Un secondo limite è economico: i polarimetri da laboratorio convenzionali, con sensori dedicati, componenti di precisione e attuatori motorizzati, hanno costi dell'ordine delle decine di migliaia di euro.
>
> L'idea di sostituire il rivelatore puntuale con un sensore a matrice trasforma il polarimetro da strumento scalare a strumento di imaging: ogni pixel diventa un polarimetro indipendente, e la misura restituisce una mappa bidimensionale dello stato di polarizzazione. I polarimetri a immagine di ricerca raggiungono prestazioni elevate con griglie micropolarizzatrici integrate o cristalli liquidi modulabili, ma a costi che ne limitano l'accesso a laboratori ben finanziati. La diffusione capillare degli smartphone con sensori CMOS ad alta risoluzione e acquisizione RAW suggerisce una possibilità concreta: impiegare un dispositivo già posseduto dalla quasi totalità degli studenti come rivelatore, riducendo il costo dell'apparato di due ordini di grandezza.
>
> ## 1.2 Obiettivo del lavoro
>
> Questa tesi si propone di progettare, realizzare e validare un polarimetro a immagine bidimensionale a basso costo, utilizzando come rivelatore il sensore CMOS di uno smartphone commerciale. Il sistema deve ricostruire il vettore di Stokes completo pixel per pixel e generare mappe spazialmente risolte del grado di polarizzazione, dell'angolo di polarizzazione lineare, della ritardanza e dell'orientazione dell'asse veloce. Per validarne le capacità, vengono analizzati campioni rappresentativi di birifrangenza, attività ottica e fotoelasticità.
>
> Il capitolo 2 richiama i fondamenti teorici necessari alla comprensione del metodo di misura. Il capitolo 3 descrive l'apparato sperimentale e il protocollo di acquisizione. Il capitolo 4 presenta i campioni selezionati. Il capitolo 5 documenta l'analisi dei dati. Il capitolo 6 discute i risultati e i limiti del metodo. Il capitolo 7 riassume le conclusioni e indica possibili sviluppi futuri.

**Nota**: la "struttura della tesi" qui è ridotta a un singolo paragrafo in coda alla sezione 1.2, non una sezione a sé. Se preferisci eliminarla del tutto, il capitolo regge comunque.

---

## Capitolo 2 — Fondamenti teorici

### Problema
Il capitolo è lungo e ha il sapore di un riassunto da libro di testo scollegato dal lavoro. Le sezioni 2.1 (natura ondulatoria), 2.2.2 (sfera di Poincaré), e i casi particolari dell'ellisse di polarizzazione sono materiale standard che non viene mai richiamato nei capitoli successivi. Inoltre le sottosezioni su birifrangenza, attività ottica e fotoelasticità ripetono concetti che poi vengono rispiegati nel capitolo 4 (campioni).

### Soluzione
- **Tagliare** la derivazione dell'ellisse di polarizzazione (eq. 2.2) e la lista dei casi particolari (lineare, circolare, ellittica): basta dire che la polarizzazione può essere lineare, circolare o ellittica a seconda della differenza di fase δ tra le componenti, con un rimando al testo di Hecht.
- **Accorciare** la sfera di Poincaré a un singolo paragrafo senza equazione (eq. 2.7 non è mai usata altrove).
- **Mantenere intatti**: definizione dei parametri di Stokes (eq. 2.3–2.6), legge di Malus generalizzata (eq. 2.9), matrici di Mueller del polarizzatore e del retarder (eq. 2.12–2.13), ritardanza (eq. 2.15), legge tensione-ottica (eq. 2.17).
- **Rendere ogni equazione motivata**: prima di presentarla, spiegare *a cosa servirà* nella tesi.
- **Fondere** le sezioni 2.5–2.7 (birifrangenza, attività ottica, fotoelasticità) in un'unica sezione "Fenomeni che influenzano la polarizzazione" strutturata come narrazione, non come tre mini-capitoli.

### Testo indicativo per le parti da riscrivere

#### Sezione 2.1 — accorciata

> ## 2.1 Polarizzazione della luce
>
> La luce è un'onda elettromagnetica trasversale. Per un'onda monocromatica che si propaga lungo l'asse $z$, il campo elettrico può essere decomposto in due componenti ortogonali $E_x$ e $E_y$, ciascuna con ampiezza e fase proprie [4]. La differenza di fase $\delta = \delta_y - \delta_x$ tra le due componenti determina lo stato di polarizzazione: quando $\delta = 0$ o $\pi$ la polarizzazione è lineare, quando $\delta = \pm\pi/2$ con ampiezze uguali è circolare, e nel caso generale è ellittica. Le sorgenti comuni emettono luce non polarizzata, in cui $\delta$ varia casualmente nel tempo; la sovrapposizione di una componente polarizzata e una non polarizzata produce luce parzialmente polarizzata, situazione tipica in ambito sperimentale.

#### Sezione 2.2.2 (Poincaré) — accorciata, senza equazione

> ### La sfera di Poincaré
>
> I parametri di Stokes normalizzati $s_1, s_2, s_3$ definiscono un punto nello spazio tridimensionale. Gli stati totalmente polarizzati giacciono sulla superficie di una sfera unitaria — la sfera di Poincaré — il cui equatore rappresenta la polarizzazione lineare e i cui poli rappresentano la polarizzazione circolare destra e sinistra. La distanza dal centro è pari al grado di polarizzazione. Questa rappresentazione geometrica sarà utile nell'interpretazione delle mappe di Stokes del capitolo 6.

#### Sezione 2.5–2.7 — fuse

> ## 2.5 Fenomeni che influenzano la polarizzazione
>
> I campioni analizzati in questa tesi interagiscono con la polarizzazione attraverso tre meccanismi distinti, ciascuno descritto da una specifica matrice di Mueller.
>
> **Birifrangenza.** Un materiale è birifrangente quando il suo indice di rifrazione dipende dalla direzione di polarizzazione. La differenza $\Delta n = n_e - n_o$ tra indice straordinario e ordinario genera, su uno spessore $d$, un ritardo di fase
> $$\delta = \frac{2\pi}{\lambda}\,\Delta n\, d \tag{2.15}$$
> Le lamine d'onda commerciali sfruttano questo effetto: una lamina $\lambda/4$ ($\delta = \pi/2$) converte polarizzazione lineare in circolare, una lamina $\lambda/2$ ($\delta = \pi$) ruota il piano di polarizzazione. Poiché $\delta$ dipende inversamente da $\lambda$, una lamina calibrata a una data lunghezza d'onda introduce ritardi diversi alle altre lunghezze d'onda — un aspetto che avrà conseguenze dirette sulla misura di $S_3$ con il sensore a tre canali colore (sezione 5.4).
>
> **Attività ottica.** Alcuni materiali chirali ruotano il piano di polarizzazione senza alterare l'ellitticità. Per soluzioni, l'angolo di rotazione segue la legge di Biot:
> $$\alpha_\text{rot} = [\alpha]^T_\lambda\, l\, c \tag{2.16}$$
> dove $[\alpha]^T_\lambda$ è la rotazione specifica, $l$ il cammino ottico e $c$ la concentrazione. Nel formalismo di Mueller, l'effetto corrisponde a un rotatore (eq. 2.14): $S_1$ e $S_2$ ruotano, $S_3$ resta invariato. Il campione di saccarosio del capitolo 4 è stato scelto per verificare questa proprietà.
>
> **Fotoelasticità.** Un materiale trasparente e normalmente isotropo diventa birifrangente sotto sollecitazione meccanica. La birifrangenza indotta è proporzionale alla differenza delle tensioni principali attraverso la legge tensione-ottica:
> $$\Delta n = C\,(\sigma_1 - \sigma_2) \tag{2.17}$$
> dove $C$ è la costante fotoelastica del materiale. Quando un campione fotoelastico è osservato tra polarizzatore e analizzatore incrociati, si osservano frange isocromatiche (loci a ritardanza costante) e isocline (loci in cui le direzioni principali sono allineate agli assi del polarimetro). Le mappe di ritardanza prodotte dal polarimetro a immagine rendono visibili entrambe le famiglie di frange, come si vedrà nel capitolo 6.

**Nota**: con queste modifiche il capitolo 2 passa da ~7 pagine a ~4.5, eliminando materiale che il lettore può trovare in qualsiasi testo di ottica e tenendo solo ciò che è direttamente usato nella tesi.

---

## Capitolo 3 — Apparato sperimentale

### Problema
Le sottosezioni 3.2.1–3.2.5 sono voci d'inventario da 3–4 righe ciascuna. La sezione 3.3 (sensore) ha due sotto-sottosezioni altrettanto brevi. Il capitolo legge come una distinta base, non come la descrizione di un apparato.

### Soluzione
- Fondere 3.2.1–3.2.3 in un unico paragrafo "Componenti ottici".
- Mantenere come sottosezione autonoma solo la lamina λ/4 (3.2.4), perché ha contenuto non banale (dispersione cromatica).
- Fondere 3.2.5 nella panoramica del setup (menzione breve dei supporti 3D).
- Fondere 3.3.1 e 3.3.2 in un'unica sezione "Sensore e acquisizione RAW".
- Fondere 3.4.3 e 3.4.4 nel protocollo di acquisizione.
- Eliminare la sezione 3.5 (calibrazione e riproducibilità): il contenuto è di 5 righe e può essere incorporato alla fine di 3.4.

### Testo riscritto per la sezione 3.2

> ## 3.2 Componenti ottici
>
> L'apparato è montato su una rotaia ottica Optosci con cavalieri scorrevoli, che garantisce l'allineamento dei componenti e la riproducibilità del posizionamento tra sessioni di misura. La sorgente luminosa è il display di un tablet Samsung Galaxy Tab S7 FE, impostato su schermata bianca alla massima luminosità. Il pannello LCD emette luce bianca a banda larga attraverso un polarizzatore integrato: la luce in uscita è già polarizzata linearmente con asse approssimativamente verticale (in configurazione landscape), il che rende il display una sorgente estesa a stato di polarizzazione ben definito. L'analizzatore è un polarizzatore lineare circolare Optosci, montato su supporto rotante calibrato con risoluzione angolare sufficiente per i passi di 10° previsti dal protocollo. Per integrare i dispositivi nella rotaia sono stati realizzati supporti personalizzati mediante stampa 3D in PLA.
>
> ### 3.2.1 Lamina λ/4 zero-order
>
> Per la determinazione del parametro $S_3$ si utilizza una lamina quarto d'onda Optosci di tipo zero-order, progettata per 633 nm. Rispetto a una lamina multi-ordine, la dipendenza dalla lunghezza d'onda è più debole — proprietà importante dato che il sensore opera simultaneamente sui tre canali colore. Il ritardo effettivo alla lunghezza d'onda $\lambda$ del canale in esame è:
> $$\delta(\lambda) = \frac{\pi}{2} \cdot \frac{633\;\text{nm}}{\lambda} \tag{3.2}$$
> La correzione per questo effetto cromatico è descritta in dettaglio nella sezione 5.4.

### Testo riscritto per la sezione 3.3

> ## 3.3 Sensore e acquisizione RAW
>
> Il rivelatore è la fotocamera principale di uno smartphone Samsung Galaxy S24 (sensore CMOS, ~10 megapixel effettivi, focale 7.0 mm equivalente 69 mm, apertura f/2.4, profondità fino a 12 bit per canale).
>
> Il sensore è ricoperto da una matrice di Bayer con disposizione RGGB. In condizioni normali di utilizzo, il processore di immagini dello smartphone applicherebbe demosaicizzazione, bilanciamento del bianco, correzione gamma e compressione — elaborazioni che distruggono la linearità del segnale. Per questo motivo, tutte le acquisizioni sono effettuate in formato RAW (DNG), che fornisce il segnale grezzo a 12 bit con risposta proporzionale all'intensità incidente, condizione necessaria per l'applicazione della legge di Malus. L'acquisizione viene controllata da remoto via USB tramite il software *scrcpy*, per evitare vibrazioni indotte dal contatto con il dispositivo.
>
> Ciascun canale colore (R, G, B) può essere estratto e analizzato indipendentemente, consentendo di fatto un'analisi polarimetrica a tre lunghezze d'onda con un singolo sensore.

### Testo per la fine del capitolo (ponte verso il cap. 4)

> Il protocollo descritto produce, per ogni sessione di misura, un dataset di 38 immagini RAW: 36 per la ricostruzione dei parametri di Stokes lineari e 2 per il parametro circolare. Il capitolo seguente presenta i campioni selezionati per la validazione dell'apparato, scelti per coprire i tre fenomeni polarimetrici descritti nel capitolo 2.

---

## Capitolo 4 — Raccolta dati e campioni

### Problema
Sei micro-sottosezioni (4.2.1–4.2.6) di 5–10 righe ciascuna, con struttura ripetitiva. Inoltre ripetono concetti già spiegati nel cap. 2 (cos'è una lamina λ/2, cos'è la fotoelasticità).

### Soluzione
- Eliminare la sezione 4.1 (criteri di selezione): sono 3 righe che possono aprire la sezione 4.2.
- Presentare i campioni in una **tabella** con nome, fenomeno fisico, parametro di validazione atteso, e poi discuterli in un unico flusso narrativo raggruppato per tipo di fenomeno.
- Non ripetere le definizioni del cap. 2. Dire "la lamina λ/2 (ritardanza nominale π, cfr. sezione 2.5)" e basta.
- Fondere la sezione 4.3 (preparazione e montaggio) nel testo principale: sono 4 righe.

### Testo riscritto

> # 4 | Campioni
>
> I campioni sono stati scelti per coprire i tre fenomeni polarimetrici di interesse — birifrangenza, attività ottica e fotoelasticità — privilegiando materiali trasparenti compatibili con la configurazione in trasmissione. Alcuni possiedono parametri nominali noti, utili per una validazione quantitativa; altri offrono strutture spaziali che mettono alla prova la capacità di imaging del sistema. La tabella 4.1 ne riassume le caratteristiche principali; tutti sono inseriti nel porta-campione sulla rotaia, tra sorgente e analizzatore, e le superfici vengono pulite prima dell'acquisizione.
>
> | Campione | Fenomeno | Validazione attesa |
> |---|---|---|
> | Lamina λ/2 zero-order | Birifrangenza | δ ≈ 180°, AoLP ruotato |
> | Lamina λ/4 zero-order | Birifrangenza | \|S₃/S₀\| ≈ 1 a 45° |
> | Nastro adesivo (1–5 strati) | Birifrangenza incrementale | δ ∝ N |
> | Soluzione di saccarosio | Attività ottica | α_rot ∝ 1/λ² |
> | Righello in plastica | Fotoelasticità (stress residuo) | Frange isocromatiche |
> | Trave a sbalzo | Fotoelasticità (stress applicato) | Frange sotto carico |
>
> **Campioni birifrangenti.** Le lamine d'onda commerciali (λ/2 e λ/4, entrambe zero-order a 633 nm, cfr. sezione 2.5) costituiscono il primo test di validazione: la ritardanza è nota con precisione e la risposta è spazialmente uniforme, il che consente un confronto diretto tra valore misurato e valore atteso. Il vetrino con strati di nastro adesivo trasparente (da 1 a 5 strati, in configurazione simmetrica 1-2-3-4-5-4-3-2-1) è un campione a birifrangenza incrementale controllata: il film polimerico orientato del nastro presenta una birifrangenza intrinseca, e la ritardanza totale cresce approssimativamente come $\delta_\text{tot} \approx N\,\delta_\text{singolo}$. La simmetria del campione fornisce un controllo interno di consistenza.
>
> **Attività ottica.** Una soluzione satura di saccarosio (8.4 g in 6.9 mL, cammino ottico 13 mm) consente di verificare due aspetti: la rotazione uniforme del piano di polarizzazione, osservabile come variazione omogenea dell'AoLP, e la legge di dispersione $\alpha_\text{rot} \propto 1/\lambda^2$, sfruttando i tre canali colore del sensore.
>
> **Campioni fotoelastici.** Un righello in plastica trasparente presenta tensioni residue da stampaggio a iniezione che generano birifrangenza non uniforme, visibile come frange isocromatiche. Una trave in materiale trasparente, vincolata a un'estremità, è stata analizzata scarica e sotto carico: il campo di sforzi noto dalla teoria di Eulero-Bernoulli genera un pattern di frange direttamente confrontabile con le previsioni teoriche.

---

## Capitolo 5 — Analisi dei dati

### Problema
Il capitolo è scritto come documentazione software. Titoli come "Pipeline morfologica", "Implementazione vettorializzata", "Raffinamento con S₃" appartengono a un README di GitHub. Il contenuto è ottimo ma va *raccontato* come un percorso logico.

### Soluzione
- Rinominare le sezioni con titoli scientifici.
- Ridurre le sotto-sottosezioni: molte sono di 3 righe.
- Raccontare il flusso come una sequenza logica ("dal dato grezzo al parametro fisico"), non come una lista di step.

### Nuovi titoli proposti

| Sezione attuale | Titolo attuale | Nuovo titolo proposto |
|---|---|---|
| 5.1 | Pre-elaborazione delle immagini RAW | Dalla immagine grezza alla matrice di intensità |
| 5.1.1 | Downsampling | Riduzione della risoluzione spaziale |
| 5.2 | Stima delle lunghezze d'onda centroide RGB | Lunghezze d'onda effettive dei canali colore |
| 5.3 | Ricostruzione dei parametri di Stokes lineari | Ricostruzione di S₀, S₁, S₂ |
| 5.3.1–5.3.4 | (4 sotto-sottosezioni) | Fondere in 5.3, eliminando 5.3.3 e 5.3.4 come sottosezioni |
| 5.4 | Misura del parametro di Stokes S₃ | Determinazione della componente circolare S₃ |
| 5.5 | Mascheramento dell'area illuminata | Selezione della regione utile |
| 5.5.1–5.5.2 | Pipeline morfologica / Raffinamento con S₃ | Fondere in 5.5 |
| 5.6 | Allineamento del reference frame | Allineamento del sistema di riferimento |
| 5.7 | Grado di polarizzazione lineare e angolo | Grandezze polarimetriche derivate |
| 5.8 | Calcolo della ritardanza e dell'asse veloce | Estrazione della ritardanza e dell'asse veloce |
| 5.8.1–5.8.4 | (4 sotto-sottosezioni) | Fondere in 2: "Modello" e "Trattamento delle ambiguità" |
| 5.9 | Strumento di validazione interattivo | Eliminare (menzione in una riga nel testo) |
| 5.10 | Visualizzazione dei risultati | Rappresentazione delle mappe |

### Testo riscritto per la sezione 5.3 (esempio di fusione)

> ## 5.3 Ricostruzione di S₀, S₁, S₂
>
> L'intensità trasmessa da un analizzatore lineare orientato ad angolo θ rispetto all'asse di riferimento segue la legge di Malus generalizzata (eq. 2.9):
> $$I(\theta) = \tfrac{1}{2}\bigl(S_0 + S_1\cos 2\theta + S_2\sin 2\theta\bigr)$$
> Per ogni pixel, le intensità misurate ai 36 angoli equispaziati $\theta_i = 0°, 10°, \ldots, 350°$ costituiscono un sistema di 36 equazioni in 3 incognite. In forma matriciale, $\mathbf{I} = A\,\mathbf{p}$, dove $\mathbf{p} = [S_0/2,\; S_1/2,\; S_2/2]^T$ e la matrice $A$ ha righe $[1,\; \cos 2\theta_i,\; \sin 2\theta_i]$. La sovradeterminazione consente di risolvere il sistema ai minimi quadrati tramite la pseudo-inversa di Moore-Penrose:
> $$\mathbf{p} = (A^T A)^{-1} A^T \mathbf{I}$$
>
> Poiché la matrice $A$ non dipende dal pixel, la pseudo-inversa viene calcolata una sola volta e applicata all'intero stack di immagini con un singolo prodotto matriciale, rendendo il calcolo computazionalmente efficiente anche su immagini di grandi dimensioni.
>
> Una nota sulle convenzioni: gli angoli nominali dell'analizzatore vengono invertiti ($\theta \to 360° - \theta_\text{nom}$) per garantire coerenza con la convenzione destrorsa del formalismo di Stokes, in cui l'osservatore guarda nella direzione di propagazione del fascio.

### Testo riscritto per la sezione 5.5 (esempio di de-jargonizzazione)

> ## 5.5 Selezione della regione utile
>
> Solo una porzione del campo visivo è effettivamente illuminata dal fascio che attraversa l'apparato: le regioni non illuminate contengono rumore di fondo che, se incluso nell'analisi, introdurrebbe artefatti nelle mappe normalizzate. È pertanto necessaria una maschera binaria che isoli l'area utile.
>
> La maschera viene generata a partire dalla mappa di intensità $S_0$. Si calcola un profilo di illuminazione locale tramite filtro gaussiano e si identificano come bordi i pixel con intensità inferiore al 95% del profilo locale. I bordi vengono dilatati morfologicamente per chiudere eventuali discontinuità, le cavità interne riempite, e si conserva la componente connessa di area maggiore con un margine di sicurezza.
>
> Quando è disponibile anche la mappa di $S_3$, la maschera viene ulteriormente ristretta all'area effettivamente coperta dall'apertura circolare della lamina λ/4, che è più piccola del campo illuminato. Il risultato è l'intersezione delle due regioni.

### Sezione 5.9 — eliminare come sezione autonoma

Inserire una frase alla fine di 5.8:

> A supporto dell'analisi è stato sviluppato uno strumento interattivo che consente di sovrapporre, per qualsiasi pixel selezionato, i 36 valori misurati alla curva di Malus teorica e di visualizzare l'ellisse di polarizzazione corrispondente.

### Ponte verso il cap. 6

> Le grandezze polarimetriche così calcolate — $S_0$, $S_1$, $S_2$, $S_3$, DoLP, AoLP, ritardanza $\delta$ e asse veloce $\alpha$ — vengono presentate per ciascun campione nel capitolo seguente sotto forma di mappe bidimensionali, organizzate in una griglia sinottica 3×3 con colormap scelte secondo le convenzioni della letteratura polarimetrica.

---

## Capitolo 6 — Risultati e discussione

### Problema
Ogni campione segue uno schema rigido identico (descrizione → tabella → commento breve). La ripetitività rende il capitolo monotono. Inoltre le sezioni 6.1 e 6.2 sono troppo brevi per stare da sole.

### Soluzione
- Fondere 6.1 e 6.2 in un'unica sezione introduttiva "Validazione preliminare e presentazione delle mappe".
- Raggruppare i campioni per tipo di validazione, non per ordine arbitrario:
  1. **Accuratezza della ricostruzione** (6.3.1 lamina λ/4 + 6.3.2 lamina λ/2): il sistema misura correttamente?
  2. **Linearità e risoluzione spaziale** (6.3.3 nastro adesivo): il sistema scala correttamente e distingue regioni diverse?
  3. **Versatilità** (6.3.4 saccarosio + 6.3.5 righello + 6.3.6 trave): il sistema rileva fenomeni di natura diversa?
- Aggiungere frasi di transizione tra i campioni.
- La sezione 6.4 (Discussione) è buona ma le sotto-sotto-sezioni 6.4.1–6.4.5 vanno fuse in prosa continua.

### Transizioni da aggiungere (esempi)

Tra lamine d'onda e nastro adesivo:
> Le lamine d'onda, con ritardanza uniforme e nota, hanno confermato l'accuratezza puntuale della ricostruzione. Il campione successivo è stato scelto per testare una proprietà diversa: la capacità del sistema di distinguere regioni con ritardanza crescente e di mantenere la linearità della risposta.

Tra nastro adesivo e saccarosio:
> Dopo aver verificato che il polarimetro produce mappe coerenti per un campione birifrangente, si passa a un fenomeno fisicamente distinto — l'attività ottica — che agisce su $S_1$ e $S_2$ senza coinvolgere $S_3$.

### Sezione 6.4 — riscritta come prosa continua

> ## 6.4 Discussione
>
> I risultati presentati nelle sezioni precedenti dimostrano che il sistema è in grado di ricostruire il vettore di Stokes completo con risoluzione spaziale bidimensionale, di misurare ritardanza e asse veloce su campioni macroscopici, e di distinguere fenomeni polarimetrici di natura diversa — birifrangenza, attività ottica, fotoelasticità — con un apparato il cui costo complessivo, escluso lo smartphone, è inferiore a 100 €.
>
> Il principale compromesso è introdotto dal downsampling, necessario per rendere il calcolo trattabile: con fattori tipici tra 10 e 20, la risoluzione scende da 12 megapixel a 10⁴–10⁵ pixel, rendendo irrisolvibili strutture più piccole di qualche centinaio di micrometri. Per i campioni macroscopici analizzati questa limitazione non è stata rilevante, ma applicazioni su scala microscopica richiederebbero un'elaborazione a blocchi o su GPU.
>
> Un secondo limite è l'approssimazione monocromatica: l'assegnazione di una singola lunghezza d'onda effettiva a ciascun canale colore ignora la larghezza di banda dei filtri Bayer, che si estende su diverse decine di nanometri. Per campioni con forte dispersione, la misura rappresenta una media pesata sulla banda — una caratterizzazione più fine richiederebbe filtri passa-banda stretti o una sorgente monocromatica.
>
> La sensibilità alla calibrazione della lamina λ/4 è un terzo fattore: la correzione cromatica $1/\sin\delta(\lambda)$ assume un modello di dispersione lineare che diventa meno accurato allontanandosi dalla lunghezza d'onda di progetto. Questo spiega la scelta del canale rosso come canale predefinito per l'analisi.
>
> Rispetto ai polarimetri di laboratorio convenzionali, il sistema scambia accuratezza assoluta e risoluzione spettrale con costo, portabilità e accessibilità (tabella 6.7). È particolarmente adatto a contesti didattici e a misure esplorative, dove la rapidità di setup e il basso costo compensano le limitazioni in precisione.

---

## Capitolo 7 — Conclusioni

### Problema
Le sezioni 7.1–7.3 ripetono quasi verbatim contenuti già presenti nel cap. 6. La sezione 7.4 è una lista di sviluppi futuri priva di prioritizzazione.

### Soluzione
- Fondere 7.1–7.3 in un unico testo di ~15 righe che *riassuma* senza ripetere.
- In 7.4, raggruppare gli sviluppi in "a breve termine" e "a lungo termine".

### Testo riscritto

> # 7 | Conclusioni e sviluppi futuri
>
> Questa tesi ha dimostrato che un polarimetro a immagine bidimensionale basato su smartphone è in grado di produrre mappe polarimetriche quantitative comparabili, per le applicazioni considerate, ai risultati ottenibili con strumentazione di laboratorio di costo due ordini di grandezza superiore. Il vettore di Stokes completo è stato ricostruito pixel per pixel su sei campioni rappresentativi di birifrangenza, attività ottica e fotoelasticità, con scarti rispetto ai valori nominali dell'ordine di 2–5° per le ritardanze e con dispersione rotatoria consistente con il modello di Drude per il saccarosio. Il limite principale dell'approccio è il compromesso tra risoluzione spaziale e sostenibilità computazionale imposto dal downsampling, seguito dall'approssimazione a banda larga intrinseca nei filtri Bayer.
>
> ## 7.1 Sviluppi a breve termine
>
> L'integrazione di un motore passo-passo per la rotazione dell'analizzatore eliminerebbe l'incertezza angolare manuale e ridurrebbe il tempo di acquisizione a pochi secondi. L'elaborazione su GPU o a blocchi consentirebbe di lavorare a risoluzione piena. La sostituzione del display LCD con LED monocromatici a banda stretta migliorerebbe l'accuratezza della correzione cromatica della lamina λ/4.
>
> ## 7.2 Prospettive a lungo termine
>
> L'acquisizione con sorgenti a diverse lunghezze d'onda aprirebbe la strada alla polarimetria spettro-spaziale. L'estensione alla configurazione in riflessione consentirebbe l'analisi di campioni opachi, con potenziali applicazioni in diagnostica biomedica e controllo qualità di superfici. L'impiego di tecniche di deep learning per la ricostruzione dei parametri di Stokes da un numero ridotto di immagini potrebbe avvicinare il sistema alla misura in tempo reale. Il basso costo e la riproducibilità dell'apparato ne fanno infine un candidato naturale per l'inserimento nei corsi di laboratorio di ottica.

---

## Riepilogo delle azioni

| # | Azione | Impatto stimato |
|---|---|---|
| 1 | Riscrivere abstract | Piccolo, ma dà il tono |
| 2 | Fondere intro in 2 sezioni, eliminare 1.4 | Medio |
| 3 | Tagliare teoria: accorciare 2.1, 2.2.2; fondere 2.5–2.7 | Grande (−2.5 pagine) |
| 4 | Fondere componenti ottici (3.2.x) e sensore (3.3.x) | Medio |
| 5 | Riscrivere cap. 4 con tabella e prosa continua | Medio |
| 6 | Rinominare sezioni cap. 5, fondere sotto-sottosezioni, eliminare 5.9 | Grande (qualità percepita) |
| 7 | Raggruppare risultati cap. 6 per tipo, aggiungere transizioni | Grande |
| 8 | Fondere discussione 6.4 in prosa | Medio |
| 9 | Riscrivere conclusioni senza ripetere | Medio |
| 10 | Aggiungere ponti di chiusura a ogni capitolo | Piccolo ma cumulativo |
