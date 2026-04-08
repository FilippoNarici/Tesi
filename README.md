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
