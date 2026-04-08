# Progetto di Tesi: Analisi della Polarizzazione della Luce

Questo documento illustra la struttura della tesi, i materiali impiegati e la configurazione dell'apparato sperimentale.

## 📑 Struttura della Tesi

La struttura finale del documento (espandibile se necessario con indici, appendici, ecc.) è la seguente:

1. **Sommario / Abstract**
2. **Premessa**
3. **Teoria**
4. **Apparato sperimentale**
5. **Raccolta dati**
6. **Analisi dati**
7. **Conclusione**

---

## 🛠️ Materiali Utilizzati

Per la realizzazione dell'esperimento è stata utilizzata la seguente strumentazione:

* **Dispositivo di acquisizione:** Samsung Galaxy S24 (Fotocamera)
* **Sorgente luminosa:** Samsung Tab S7 FE (Sorgente di luce polarizzata con asse verticale, orientamento landscape)
* **Banco ottico:** Rotaia Optosci con relativi mount
* **Componenti Custom:** Supporti per tablet e telefono stampati in 3D, progettati per la compatibilità con i mount Optosci
* **Componenti Ottici:** Lamina $\lambda/4$ (quarto d'onda) per il calcolo del parametro di Stokes $S_3$, Polarizzatore in uscita (analizzatore)

---

## 🔬 Descrizione dell'Esperimento

L'apparato sperimentale è stato allestito sfruttando la rotaia Optosci, sulla quale sono stati posizionati i vari supporti ottici e i componenti custom stampati in 3D. 

Innanzitutto, a un'estremità della rotaia è stato montato il tablet (Samsung Tab S7 FE), che funge da sorgente di luce controllata. Sulla stessa linea ottica vengono poi allineati in ordine il campione da analizzare, l'analizzatore, la lamina $\lambda/4$ (Aggiunta soltanto la misura di S3) e lo smartphone (Samsung Galaxy S24) per l'acquisizione delle immagini e la successiva analisi dello stato di polarizzazione.

Vengono catturate svariate immagini ruotando di 10 gradi per volta l'analizzatore, così da catturare 36 immagini con il polarizzatore in uscita ad angoli crescenti (si noti che in elaborazione la convenzione del segno dell'angolo viene invertita per usare un sistema di riferimento coerente con il raggio uscente dallo schermo.

Queste immagini vengono poi processate dagli script python.

---

## Specifiche di Acquisizione (Fotocamera e Impostazioni)

Le immagini utilizzate in questo progetto sono state acquisite cercando di mantenere i parametri costanti per garantire la coerenza analitica. Di seguito sono riportati i dati tecnici e le specifiche dell'obiettivo estratti direttamente dai metadati EXIF dei file RAW:

### 📱 Dispositivo e Sensore
* **Dispositivo:** Samsung Galaxy S24
* **Formato File:** DNG (Linear RAW)
* **Profondità Colore:** 12-bit per canale (36-bit totali)
* **Risoluzione Immagine:** 3648 x 2736 (10 Megapixel)

### 🔭 Ottica e Geometria
* **Lunghezza Focale:** 7.0 mm (equivalente a 69 mm nel formato 35mm)
* **Apertura Diaframma:** f/2.4 (fissa)
* **Campo Visivo (FOV):** 29.2°
* **Distanza Iperfocale:** 6.70 m

### ⚙️ Impostazioni di Scatto (Mantenute Fisse)
Per evitare alterazioni introdotte dal software di auto-esposizione della fotocamera, i parametri principali del triangolo dell'esposizione sono stati bloccati sui seguenti valori:
* **Tempo di Esposizione (Shutter Speed):** 1/90 s
* **Sensibilità ISO:** 50
* **Bilanciamento del Bianco (Illuminant):** D65 / Standard Light A
