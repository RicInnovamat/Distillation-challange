# Distillation Challenge – Meeting 5
**Data:** 19 aprile 2026

## Obiettivo del meeting
Sessione di sviluppo tecnico sulla versione 7.1 e preparazione della 7.2, con focus su:
- analisi comparativa dei risultati V5.5 e V7.1;
- revisione e pulizia dei motif C1–C10;
- normalizzazione delle variabili e chiarimento della nomenclatura;
- gestione delle allucinazioni del modello;
- organizzazione del lavoro e accesso agli strumenti.

---

## 1. Stato generale e risultati delle versioni recenti

### Confronto V5.5 / V7.1
I risultati della V5.5 non mostrano peggioramenti rispetto alla baseline, con variazioni rientranti nell'intervallo di variabilità atteso. La **V7.1** è confermata come punto di riferimento operativo, nonostante il problema dei byte in eccesso (circa 200 byte di troppo).

### Risultati della V7.1
- Guadagno di **tre punti percentuali** su Hard 1 Gemma, superando l'**80%**.
- Hard 2 e Hard 3 allineati alle aspettative.
- Hard 3 mostra una leggera perdita marginale.
- Gemma ottiene risultati ottimi con l'approccio preciso adottato.
- Con V5.5 su Gemma, il punteggio ha raggiunto **78**, con riduzione delle confabulations.

### Decisione operativa
La V7.1 viene mantenuta come base. L'obiettivo immediato è testare la **V7.2**, che incorpora le modifiche discusse in questa sessione. Una volta completata, Tommaso eseguirà una run completa, poi il team si incontrerà nel pomeriggio per revisione e troubleshooting.

---

## 2. Linea strategica e posizionamento

### Approccio matematico vs. overfitting
Il team ha identificato di essere l'unico partecipante alla competizione che persegue un approccio matematico rigoroso. Chi ottiene punteggi elevati appare stia facendo overfitting, con una metodologia "tutto tranne che matematica". La linea strategica esplicita del team è evitare l'overfitting sui dataset disponibili, mantenendo un approccio fondato sul **ragionamento matematico**.

Il sistema di misurazione della competizione incoraggia strutturalmente l'overfitting, focalizzandosi esclusivamente sull'accuratezza sui dataset disponibili. Nessun partecipante sul blog ha condiviso idee teoriche, solo strategie per il miglioramento dell'accuratezza.

### Fonte matematica
È stato concordato che la descrizione della submission dovrà menzionare esplicitamente che la matematica utilizzata è tratta dall'**Equational Theories Project**, dove sono state validate 22 milioni di equazioni.

### Priorità tecnica: sezione 2.8 (Contradiction Motive)
Il prossimo grande elemento da affrontare è la sezione 2.8, relativa alle *contradiction motive*, che rappresentano il "cannone" sulle *bare equation*. Il 75% delle *missed implication* sono bare equation, quindi questo punto offre il margine di miglioramento più significativo.

---

## 3. Motif C1–C10: revisione e pulizia

### Metodologia di Tommaso
Non potendo ancora produrre dimostrazioni generali, Tommaso ha utilizzato esempi e controesempi per verificare ciascun motivo. I motif C1–C10 riguardano equazioni che costringono il magma a essere un *singleton*, rendendo tutte le equazioni vere.

### Esito della revisione motif per motif

**C1:** Inizialmente ritenuto valido, è stato successivamente identificato come falso. Richiede ulteriori modifiche.

**C3:** Già incluso in C1. Rimosso come ridondante.

**C5:** Trovato un controesempio (un prodotto che risulta sempre B anche se X può essere A o B). Rimosso perché falso.

**C6:** Rimosso perché non veniva mai attivato.

**C9:** Da verificare se, insieme a C1, forza il magma a essere un singleton.

**C10:** Trovato un controesempio. Rimosso dalla V7.2. Si è discusso se C10 fosse logicamente vera ma insufficiente come *contradiction motive*.

### Struttura della sezione motif nella V7.2
È stato deciso di riscrivere la sezione dei motif includendo:
- un esempio esplicito del **formato vettoriale** delle sette caratteristiche calcolate;
- un'istruzione chiara per confrontare il vettore con ciascun motivo;
- linguaggio positivo, rimuovendo istruzioni negative come "do not skip".

### Logica di attivazione
È stato chiarito un punto importante: se un motivo corrisponde (*"if one motive matches"*), la verifica restituisce *true* solo se la condizione logica è soddisfatta. Il mancato match non falsifica l'implicazione — quindi *else false* non si applica al mancato match.

---

## 4. Normalizzazione delle variabili e formato vettoriale

### Importanza della normalizzazione
La normalizzazione delle variabili è considerata fondamentale per il calcolo corretto delle *sorted occurrence counts*. Nella sezione 2.8 dovrà essere specificato cosa significa *bare* e come normalizzare le equazioni, con l'istruzione di rinominare l'equazione in formato bare prima di procedere.

### Convenzione finale per il vettore di occorrenze
Il vettore di occorrenze è definito come una **lista ordinata di molteplicità non associata ai nomi delle variabili**. L'ordinamento si riferisce solo al valore numerico (maggiore o minore), senza tenere traccia di quale variabile (X, Y, Z) corrisponda a quale conteggio.

Il campo "Right and Side Totals" è stato abbreviato in: *"Sorted list of occurrence counts of all distinct variables of P"*.

### Caratteristica Top Product Split
Per chiarire la caratteristica X_stop, è stata aggiunta la specifica *"at the top split of P"* per descrivere l'occorrenza della variabile X nel prodotto U o V.

### Errore di interpretazione identificato
È emersa e corretta una confusione nell'ordine dei vettori di occorrenze: l'interpretazione del *sorted* era stata invertita rispetto alle aspettative nella logica originale del codice.

---

## 5. Revisione della nomenclatura e pulizia del prompt

### Modifiche alla sezione 2.3–2.5
- Sostituzione di "where" con un formato più chiaro nella sezione 2.3.
- Rimozione di definizioni ripetute nelle sezioni 2.4 e 2.5.
- Uso di "match normalization against" in sostituzione della descrizione estesa del processo di ridenominazione.

### Terminologia delle proiezioni
I termini "left most variable" e "right most variable" sono stati sostituiti con **"left projection"** e **"right projection"** per coerenza con il resto del documento.

### Verdetto booleano standardizzato
L'uso di *"verdict true, else false"* è stato reso coerente in tutte le sezioni applicabili.

### Sezione Extract Features (3.6)
Rimossa la ripetizione delle definizioni di "word parity" e "parity", lasciando la definizione solo nel punto in cui viene utilizzata. Discussa l'eliminazione di alcune variabili non utilizzate.

### Regola 2.12
La formulazione è risultata parzialmente sovrapposta ad altri check. La semplificazione è stata identificata come possibile ma rinviata.

---

## 6. Gestione delle allucinazioni

### Pattern identificato
Analizzando i risultati, il modello ha catturato nove bug comportamentali con un'accuratezza del 75%. In due casi su dodici, il modello identificava correttamente la regola ma emetteva un **verdetto opposto**: questo è stato classificato come allucinazione estrema.

### Interventi proposti
- Riscrittura della regola per la proiezione, aggiungendo la clausola *"recursively"* nella condizione *"If equation 2's applying left projection"*.
- Sostituzione di *"same result →"* con *"verdict true else false"* per rendere il verdetto esplicito e non ambiguo.
- Riscrittura della sezione *"small finiteness root"* nella versione finale.

### Step 5
Lo step 5 non è mai stato attivato nelle run (zero volte su 100). Questo offre spazio per inserire **controesempi** in quello slot. Lo step 5 era originariamente concepito come salvagente (*"if did not decide"*), ma nella pratica è risultato inutilizzato. La decisione è di sfruttarlo per i controesempi piuttosto che rimuoverlo.

---

## 7. Ottimizzazione dei byte

La V7.2 è risultata più compatta del previsto: circa 230 byte di spazio avanzato, in larga parte grazie alla rimozione dei motif. È stato corretto un errore di sintassi (parentesi in eccesso nel codice).

Sono state discusse strategie per risparmiare ulteriori byte, tra cui l'abbreviazione di nomi di variabili (es. "Right and Side Totals" → "Right and Side V"). Riccardo si è impegnato a interrogare Claude/GPT per identificare i punti ottimali per ulteriori restrizioni.

---

## 8. Prossimi sviluppi tecnici

### Verso la V7.3
Una volta completata la run della V7.2 e la riscrittura dello step 4, Tommaso ha proposto due attività aggiuntive:
- **Aggiunta di controesempi modulari** (opzionale).
- **Elaborazione del Metaprompt**.

Riccardo ha sollevato la preoccupazione che il Metaprompt possa richiedere troppo tempo. La decisione è stata di procedere con la run della V7.2 e valutare le priorità successivamente.

### Submission
Riccardo si occuperà di scrivere la sezione descrittiva della submission, illustrando la metodologia e il riferimento all'Equational Theories Project.

---

## 9. Accesso a Claude Code e fondi universitari

Tommaso ha richiesto l'accesso a Claude Code per poter eseguire autonomamente le verifiche sui motif. Riccardo ha espresso riserve sulla condivisione delle credenziali e sulle complicazioni dell'installazione.

**Soluzione identificata:** Tommaso invierà una mail al capo dipartimento per richiedere fondi universitari per l'abbonamento, mettendo Riccardo in CC. Nel frattempo, il team valuterà con Andrea come strutturare l'accesso necessario per lo Stage 2.

---

## 10. Nota metodologica: gestione degli appunti e organizzazione

Nel corso della sessione è emersa una riflessione pratica sulla gestione delle informazioni.

### Problema identificato
Un collega esterno perdeva informazioni sistematicamente utilizzando circa otto fonti diverse per gli appunti (post-it, fogli, taccuini, note vocali, file). L'errore si compone a ogni passaggio tra fonti, aumentando la probabilità di perdita.

### Raccomandazione condivisa
Limitare le fonti a due: una per quando si è in movimento, una per quando si è al computer. Eliminare la carta per gli appunti di lavoro.

Tommaso ha riconosciuto di tenere le cose "in testa", con conseguente sovraccarico e difficoltà di prioritizzazione. La scrittura è fondamentale per prioritizzare, organizzare, calendarizzare e condividere.

### Sistema di Riccardo
- Unica eccezione cartacea: una to-do list fisica.
- Per il resto: Google Calendar con codifica a colori per tipo di attività.
- Blocchi da 15 minuti per promemoria rapidi, *focus time* dedicato, blocchi personali (es. palestra).
- Colore verde per attività non ancora confermate.
- Check mensile ogni venerdì per pianificare la settimana successiva.

---

## Action Items

### Riccardo Gay
- [ ] Scrivere la sezione descrittiva della submission (metodologia e ispirazione matematica)
- [ ] Interrogare Claude/GPT sui punti ottimali per la restrizione dei byte e applicare le modifiche
- [ ] Inviare la definizione dei motif modificati a Claude e richiedere feedback
- [ ] Parlare con Andrea per definire l'accesso a Claude Code per Tommaso (essenziale per lo Stage 2)
- [ ] Ripristinare il blocco di pianificazione weekend sul calendario
- [ ] Inviare la cheat sheet aggiornata all'IT Guy
- [ ] Delegare ad Andrea la run con le modifiche alle *small finitness root* (verso la V7.3)

### Tommaso Rossi
- [ ] Rimuovere C10 dalla V7.2 e aggiungere un esempio per la definizione delle 7 caratteristiche in formato vettoriale
- [ ] Continuare la ricerca di controesempi per i motif rimanenti, con focus sui magma finiti
- [ ] Salvare in modo sicuro tutte le dimostrazioni matematiche e i controesempi sviluppati
- [ ] Inviare a Riccardo i commenti sulle modifiche implementate
- [ ] Inviare mail al capo dipartimento per i fondi Claude Code (Riccardo in CC)
- [ ] Preparare gli strumenti di produzione per una futura sessione di consulenza sui processi di lavoro

### Andrea
- [ ] Eseguire la run con le modifiche apportate alla root 3.1

### Team
- [ ] Verificare se C1 e C9 forzano il magma a essere un singleton; produrre controesempio in caso contrario
- [ ] Valutare l'inserimento di controesempi modulari nello Step 5 (attività opzionale)
- [ ] Valutare l'elaborazione del Metaprompt dopo la run della V7.2
