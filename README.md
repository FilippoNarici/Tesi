# Progetto di Tesi: Progettazione, sviluppo e validazione di un polarimetro a immagine 2D Low-Cost

**Autore:** Filippo Narici (Studente di Ingegneria Fisica, 3° anno, Politecnico di Milano)
**Relatore:** Prof. Maurizio Zani
**Correlatori / Tutor di Laboratorio:** Sebastiano Luridiana, Giacomo Di Iorio

Questo repository contiene il codice sorgente, i dati e la documentazione per la tesi di laurea triennale in Ingegneria Fisica relativa all'analisi della polarizzazione della luce.

---

## 🎯 Obiettivo e Novità del Progetto (Il "Memento")

L'esperimento classico di polarizzazione ottica (descritto nel manuale di laboratorio) prevede l'uso di un diodo laser, lamine ritardatrici e un singolo rivelatore puntuale per ricavare i parametri di Stokes di un singolo punto luminoso. 

**L'innovazione di questo progetto consiste nell'espandere l'approccio puntuale 1D a un'analisi matriciale 2D.** Invece di un sensore singolo, viene utilizzato il sensore CMOS di uno smartphone per creare un **polarimetro a immagine (Imaging Polarimeter) Low-Cost**. Questo permette di:
1. Analizzare intere superfici e mappare spazialmente lo stato di polarizzazione.
2. Sfruttare i 3 canali colore (RGB) del sensore per un'analisi multi-lunghezza d'onda simultanea (espandendo i calcoli tramite approssimazioni spettrali basate sui centroidi).
3. Superare le sfide computazionali e di allineamento ottico derivanti dall'uso di ottiche fotografiche commerciali e display LCD/OLED.

---

## 📑 Struttura della Tesi in LaTeX (Template PoliMi3i)

1. **Sommario / Abstract**
2. **Premessa / Introduzione:** Contestualizzazione e limiti dei polarimetri tradizionali.
3. **Teoria:** Formalismo di Stokes, matrici di Mueller, polarizzazione della luce, birifrangenza, attività ottica e fotoelasticità.
4. **Apparato sperimentale:** Setup hardware, componenti 3D, scelte progettuali.
5. **Raccolta dati e Campioni:** Le misurazioni effettuate.
6. **Analisi dati (Software e Matematica):** Demosaicizzazione RAW, calcolo pseudo-inversa per S0-S2, correzione S3, mascheramento, allineamento LCD e gestione numerica.
7. **Risultati e Discussione:** Valutazione fisica dei campioni (mappe spaziali).
8. **Conclusione**

---

## 🛠️ Materiali e Setup Sperimentale

L'apparato sperimentale è allestito su una rotaia ottica Optosci. I componenti, allineati sequenzialmente, sono:

* **Sorgente luminosa:** Tablet Samsung Tab S7 FE (genera luce polarizzata, asse "verticale", orientamento landscape).
* **Campione da analizzare**
* **Componenti Ottici mobili:** * Analizzatore (polarizzatore rotante).
  * Lamina $\lambda/4$ (inserita *solo* per le acquisizioni destinate al calcolo di $S_3$).
* **Rivelatore:** Smartphone Samsung Galaxy S24.
* **Meccanica:** Mount Optosci standard + **supporti custom stampati in 3D** per tablet e telefono per garantire l'allineamento sul banco ottico.

**Protocollo di Acquisizione:** * **Per S0, S1, S2:** Si acquisiscono 36 immagini (RAW/DNG) ruotando l'analizzatore a passi di 10°. *Nota:* La convenzione del segno dell'angolo in elaborazione viene invertita per mantenere coerenza destrorsa col raggio uscente dallo schermo.
* **Per S3:** Si acquisiscono due immagini specifiche inserendo la lamina $\lambda/4$ a +45° e -45°.

---

## 📷 Specifiche di Acquisizione (Costanti Radiometriche)

Per disabilitare la pipeline di auto-esposizione (ISP) del telefono e mantenere una risposta lineare:
* **Formato:** DNG (Linear RAW, estratti tramite `rawpy`), profondità 12-bit per canale.
* **Lente:** Focale 7.0 mm (69 mm eq. 35mm), Apertura f/2.4 fissa.
* **Esposizione bloccata:** Tempo 1/90 s, ISO 50, Bilanciamento Bianco D65 / Standard Light A.

---

## 🧪 Campioni Analizzati (I Dati Reali)

1. **Lamina $\lambda/2$:** Validazione del setup e rotazione del piano di polarizzazione.
2. **Lamina $\lambda/4$:** Validazione dell'ellitticità.
3. **Soluzione di Acqua e Zucchero (Attività Ottica):** Boccetta a base quadrata. Spessore attraversato: 13mm
4. **Righello di plastica trasparente:** Studio qualitativo delle tensioni di stampaggio (Fotoelasticità).
5. **Vetrino con nastro adesivo stratificato (0-5 strati):** Analisi della birifrangenza incrementale e della variazione di ritardo ($\delta$).
6. **Trave birifrangente a sbalzo (Cantilever):** Supportata da un lato, misurata scarica e poi sotto carico. Analisi quantitativa/qualitativa delle frange isocromatiche (sforzi interni).

---

## 💻 Algoritmi e Pipeline Software (Il "Core" dell'analisi)

Gli script Python (`final_*.py`) processano le immagini matricialmente, implementando calcoli ottici avanzati:

1. **Downsampling Spaziale (Binning):** I file RAW a 10 Megapixel vengono sottoposti a un downsampling (default fattore 20) calcolando la media dei blocchi di pixel. Questo passaggio abbatte il rumore del sensore e rende il calcolo matriciale computazionalmente sostenibile.
2. **Approssimazione Monocromatica (`final_monochrome_approx.py`):** Calcola la lunghezza d'onda di centroide effettiva per i canali R, G, B sovrapponendo lo spettro del tablet con la curva di sensibilità del sensore (proxy S22).
3. **Estrazione Stokes Lineari ($S_0, S_1, S_2$):** Eseguita risolvendo un sistema sovradeterminato tramite matrice pseudo-inversa (`numpy.linalg.pinv`) sull'equazione dell'intensità di Malus per i 36 frame.
4. **Calcolo S3 e Correzione Dispersione:** Calcolato come $(I_{45} - I_{-45}) / \sin(\delta)$. Poiché la lamina è "zero-order" a 633nm, il termine $\sin(\delta)$ corregge lo sfasamento se l'analisi avviene a lunghezze d'onda diverse (es. canale blu).
5. **Smart Background Mask:** Algoritmo morfologico (blur, threshold adattivo, fill holes, component isolation) che genera dinamicamente una maschera per escludere dal fit polvere, contorni e supporti meccanici, isolando la sola area illuminata.
6. **Allineamento Reference Frame (Compensazione LCD):** Il software estrae $S_1$ e $S_2$ medi dal "vuoto" (grazie alla maschera) e applica una rotazione matematica del sistema di riferimento. In questo modo la luce in ingresso risulta ad $AoLP = 0°$ (perfettamente orizzontale), compensando l'angolo nativo del display.
7. **Retardance ($\delta$) e Fast Axis ($\theta$) con Sicurezza Numerica:** Parametri ricavati dal vettore di Stokes completo. Il calcolo utilizza l'ampiezza reale di background (`s1_in`) per normalizzare la formula, applicando un clipping di sicurezza prima dell'arcocoseno per evitare errori di dominio (`NaN`) generati da fluttuazioni numeriche o rumore residuo.
8. **Interfaccia Debug (`final_fit.py`):** Strumento interattivo per selezionare un singolo pixel dell'immagine e visualizzare in tempo reale la sinusoide di fit di Malus e l'ellisse di polarizzazione associata.
