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
2. Sfruttare i 3 canali colore (RGB) del sensore per un'analisi multi-lunghezza d'onda simultanea (espandendo i calcoli tramite approssimazioni spettrali).
3. Superare le sfide computazionali e di allineamento ottico derivanti dall'uso di ottiche fotografiche e display commerciali.

---

## 📑 Struttura della Tesi

La struttura finale del documento LaTeX (configurato tramite il template `PoliMi3i_thesis.cls`) seguirà questo schema:

1. **Sommario / Abstract**
2. **Premessa / Introduzione:** Contestualizzazione e limiti dei polarimetri tradizionali.
3. **Teoria:** Formalismo di Stokes, matrici di Mueller, polarizzazione della luce, birifrangenza e fotoelasticità.
4. **Apparato sperimentale:** Descrizione del setup Low-Cost (Display + Smartphone).
5. **Raccolta dati e Campioni:** Descrizione delle misurazioni effettuate.
6. **Analisi dati (Sviluppo Software):** Metodologia di estrazione dei dati RAW e calcolo matriciale.
7. **Risultati e Discussione:** Analisi dei campioni.
8. **Conclusione**

---

## 🛠️ Materiali e Setup Sperimentale

L'apparato sperimentale è stato allestito su una rotaia ottica Optosci. Le viste assionometriche del setup (presenti nella cartella `Images/` come `Vista 1.png` e `Vista 2.png`) mostrano l'allineamento dei seguenti componenti:

* **Dispositivo di acquisizione (Sensore):** Smartphone Samsung Galaxy S24 (montato alla fine della rotaia).
* **Sorgente luminosa:** Tablet Samsung Tab S7 FE (genera luce polarizzata con asse verticale, orientamento landscape, montato all'inizio della rotaia).
* **Componenti Ottici:** Analizzatore (polarizzatore rotante) e una Lamina $\lambda/4$ (utilizzata specificamente per il calcolo del parametro di Stokes $S_3$).
* **Supporti:** Mount Optosci standard integrati con supporti per tablet e telefono **stampati in 3D** appositamente progettati per garantire l'allineamento ottico.

**Procedura di misurazione:** Il campione viene posto tra la sorgente e l'analizzatore. Vengono catturate 36 immagini ruotando l'analizzatore di 10 gradi per volta. *Nota: Nel software la convenzione del segno dell'angolo viene invertita per usare un sistema di riferimento coerente con il raggio uscente dallo schermo.*

---

## 🧪 Campioni Analizzati

Per validare il polarimetro a immagine, sono stati misurati e analizzati i seguenti campioni, scelti per evidenziare diversi fenomeni ottici:

1. **Lamina $\lambda/2$ (Mezz'onda):** Per la validazione del setup e la rotazione del piano di polarizzazione.
2. **Lamina $\lambda/4$ (Quarto d'onda):** Per la validazione dell'ellitticità.
3. **Soluzione di Acqua e Zucchero:** Contenuta in una boccetta a base quadrata (Spessore: 1.35 cm, Volume: 6.9 ml, Zucchero disciolto: 8.4 g). Utilizzata per misurare l'**attività ottica (potere rotatorio)** e la chiralità delle molecole di saccarosio.
4. **Righello di plastica trasparente:** Per lo studio qualitativo della **fotoelasticità** (tensioni residue di stampaggio).
5. **Vetrino con scotch stratificato (da 0 a 5 strati):** Per analizzare la birifrangenza incrementale e la variazione di ritardo (Retardance) in funzione dello spessore del nastro.
6. **Trave in materiale birifrangente (a sbalzo):** Supportata da un solo lato, misurata prima a riposo e poi sottoposta a un carico meccanico, per l'analisi quantitativa degli sforzi interni tramite le frange di fotoelasticità.

---

## 💻 Pipeline Software (Python)

Il processing delle immagini è gestito da script custom in Python che lavorano direttamente sui file RAW (DNG) per mantenere la linearità del segnale radiometrico:

* `final_monochrome_approx.py`: Stima la lunghezza d'onda preponderante (centroide) per i canali RGB sfruttando i dati di sensibilità spettrale del Samsung S22 (usato come proxy per l'S24) combinati con lo spettro di emissione del tablet.
* `final_utils.py`: Cuore matematico. Gestisce il caricamento dei RAW, il downsampling, il mascheramento del background (smart select) e calcola i parametri di Stokes ($S_0, S_1, S_2, S_3$), il DoLP (Degree of Linear Polarization), l'AoLP (Angle of Linear Polarization), la Retardance ($\delta$) e il Fast Axis ($\theta$).
* `final_polarimeter.py`: Script principale di esecuzione che genera una griglia 3x3 di grafici (heatmap) che mappano spazialmente tutti i parametri polarimetrici calcolati per l'intero campione.
* `final_fit.py`: Un debugger interattivo. Cliccando su un singolo pixel dell'immagine, mostra in tempo reale la curva di fit dell'intensità rispetto all'angolo dell'analizzatore e l'ellisse di polarizzazione di Stokes associata a quel pixel.

---

## 📷 Specifiche di Acquisizione (Costanti)

Per garantire la coerenza analitica e radiometrica, i parametri della fotocamera sono stati bloccati per evitare compensazioni software:
* **Formato:** DNG (Linear RAW) a 12-bit per canale.
* **Lunghezza Focale:** 7.0 mm (69 mm eq. 35mm).
* **Apertura:** f/2.4 (fissa).
* **Shutter Speed:** 1/90 s.
* **ISO:** 50.
* **Bilanciamento del Bianco:** D65 / Standard Light A.
