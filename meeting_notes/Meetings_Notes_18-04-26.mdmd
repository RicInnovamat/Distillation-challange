# Distillation Challenge – Meeting 4
**Data:** 18 aprile 2026

## Obiettivo del meeting
Sessione di allineamento e sviluppo tecnico, con focus su:
- analisi del fallimento della V6 e transizione alla V7;
- gestione della stocasticità dei modelli;
- definizione e implementazione di nuove regole logiche;
- revisione delle proiezioni e dello step 4;
- preparazione della submission finale.

---

## 1. Analisi della variabilità e stocasticità dei modelli

### Risultati delle run V5.5
Le esecuzioni della V5.5 sono state ripulite da parametri spuri (rimozione del *fall back on*, correzione del bug sulla temperatura a zero). Nonostante ciò, i modelli continuano a comportarsi in modo incoerente:

- **AM**: produce "false" in modo deterministico, ma sistematicamente errato.
- **Gemma**: variabilità del 6–7%.
- **GPT-OS**: variabilità del 20–25%, equivalente a un "tiro di dadi".

### Accuratezza complessiva della V5.5
Il modello si attesta intorno al **70% di accuratezza** con una variabilità di circa ±2%, perché gli errori tendono a compensarsi. Tuttavia, il 25% delle soluzioni viene raggiunto con un processo interno scorretto — analogamente a uno studente che ottiene il risultato giusto con un procedimento sbagliato.

### Problema con l'approccio dell'organizzazione
Gli organizzatori della competizione (YZ / "master della chat") hanno risposto ai problemi di variabilità suggerendo di fare girare il modello "due o tre volte". Il team ha criticato questo approccio come non scientifico: senza analisi Montecarlo per determinare media e varianza, poche run non sono statisticamente significative, specialmente con una variabilità del 25%.

### Osservazione critica
Il team è stato l'unico a rilevare che le regole e i modelli erano instabili, pur avendo speso solo circa $40 in test. Questo ha richiesto di riscrivere internamente parti delle regole della competizione.

---

## 2. Fallimento della V6 e transizione alla V7

### Cause del fallimento della V6
La V6 è fallita per due ragioni principali:

**Default true inefficace.** Il meccanismo di *default true* non si adattava bene al task specifico del team.

**Guard rails distruttivi.** Sono stati introdotti dei *guard rails* per GPT-OS per prevenire le confabulations su passaggi prolissi. Questi hanno involontariamente compromesso la leggibilità del prompt per il modello, causando in alcune versioni iniziali anche *parser error*.

La causa strutturale è stata identificata nell'accettazione di troppe modifiche proposte da "Cloudgest", che hanno introdotto cambiamenti architetturali destabilizzanti.

### Decisione operativa
Data la natura disastrosa della V6, si è deciso di saltarla e passare direttamente alla **V7**, ripartendo dalla base solida della V5.5.

---

## 3. Piano di azione per la V7

### Struttura a fasi
Riccardo ha proposto il seguente piano d'azione:

1. Implementare le correzioni di **Priorità 1** sul prompt.
2. Lanciare una run e, durante l'esecuzione, leggere il cheat sheet del dataset Hard 3 overfitted per prendere ispirazione.
3. Analizzare l'output JSON della run V7.
4. Valutare se implementare le correzioni di **Priorità 2**.

### Correzioni di Priorità 1
- Stabilizzare il **problema 2.4** (regola Constant).
- Non concludere mai "verdict true" se una variabile appare solo su un lato dell'equazione.
- Includere il *reasoning* nella *global discipline* del prompt, non solo la *proof*.

### Correzioni di Priorità 2
Riguardano concetti più generali come la distinzione tra controesempi dichiarativi e procedurali. La loro inclusione è condizionale ai risultati della run di Priorità 1.

---

## 4. Problema 2.4 e regola Constant

### Descrizione del problema
Il problema riguarda come concludere che un'operazione è costante: se le variabili nei prodotti su entrambi i lati dell'equazione sono disgiunte, l'operazione potrebbe essere costante. Il modello tende a concludere erroneamente "true" in questi casi.

### Approccio proposto (Andrea Gay)
Se l'equazione è costante (ovvero $x * y = K$), si può effettuare una sostituzione simbolica per ridurre l'ordine dell'equazione — ad esempio da 5 a 4 o meno — rendendola più gestibile per il modello e riducendo le confabulations.

### Nuova regola: Missing Variable Absorption
È stata definita una nuova regola da inserire come **step 2.2**:

**Condizioni:** L'equazione 1 è della forma $x * y = t$, con $t$ prodotto che non contiene variabili singole, e le variabili di $t$ disgiunte da $x$ e $y$.

**Azione:** Se la condizione è soddisfatta — e vale per ogni variabile del magma — l'equazione 1 viene ridotta a una proiezione. Il risultato viene poi applicato all'equazione 2 per il verdetto finale.

**Mandatory check:** Verificare che la variabile $y$ non appaia nell'espressione $t$.

### Simmetria
È stata inclusa anche la possibilità di effettuare *side swap* se necessario prima di applicare la rinominazione.

---

## 5. Controesempi e Magma Theory

### Discussione sul concetto di operazione costante
Il team ha lavorato alla costruzione di un controesempio per mostrare che variabili non banali e disgiunte non garantiscono che l'operazione sia costante. È stato esaminato un magma con elementi $\{0, A, B, C\}$ e regole operative specifiche.

### Risultato
Il magma modificato costituisce un controesempio valido: l'operazione costante non è un'ipotesi valida in quel contesto.

### Ampliamento dei controesempi
È stata espressa l'intenzione di ampliare la sezione dei controesempi includendo:
- **Magmi Passini**
- **Magmi modulari** ($\mathbb{Z}_n$ con operazioni affini o lineari)

La formulazione dei controesempi dovrà essere resa più esplicita, analogamente allo stile dell'esempio esterno già presente (step 6).

---

## 6. Regole logiche: revisioni e nuove definizioni

### Singleton Collapse
La notazione per questa regola è stata aggiornata: "can be renamed" è stato preferito a "has the form", in quanto semanticamente più preciso. La regola include ora la possibilità di rinominare le variabili.

### Regola 2.11 / Substitution Rule
La regola 2.11 è stata rafforzata in modo controllato: l'equazione 2 viene trattata come un *substitution instance* dell'equazione 1. La nuova denominazione proposta è "exact instance" o "substitution rule", e consente l'uso dell'equazione 1 come regola di riscrittura per l'equazione 2 anche dopo una possibile rinominazione.

### Condizione di Verdict
La condizione per la verità è stata riformulata in modo coerente su tutte le sezioni:

> "If both sides of equation 2 reduce to the same variable, verdict true; otherwise verdict false."

---

## 7. Spine Isolation e Mandatory Check

### Problema identificato
Il modello cita la regola di Spine Isolation dalla cheat sheet, ma ne sbaglia le precondizioni. Questo genera falsi positivi.

### Soluzione
Inserimento di una **checklist obbligatoria** prima di applicare la Spine Isolation:

- **Condizione:** se l'equazione 1 è una *pure left spine*, allora l'equazione 2 deve essere *left spine*.
- Il linguaggio deve essere diretto: usare "verdict otherwise verdict" per gestire in modo esplicito i casi in cui le condizioni non sono soddisfatte.
- Aggiungere una formula esplicita per il calcolo dell'esclusione *left most / right most* nella cheat sheet.

### Trace e Path
È stato definito il concetto di "Trace" come il percorso dalla radice a $X$: si registra $L$ (left) o $R$ (right) a ogni nodo stella. Questo consente di verificare in modo procedurale la struttura dell'equazione.

---

## 8. Analisi dei motif e Global Discipline

### Motif C1–C10
Tre problemi principali sono stati identificati da risolvere nel ciclo successivo:
- I motif C1–C10 non scattano correttamente.
- La gestione del *non-bear*.
- La Spine Isolation (vedi sezione 7).

Tommaso si occuperà di analizzare i motif in modo approfondito per identificare le aree con maggiore margine di miglioramento, con particolare attenzione agli **Hols motif**.

### Global Discipline
È stato deciso di includere il *reasoning* (non solo la *proof*) nella *global discipline* del prompt. La distinzione tra approccio dichiarativo e procedurale per i controesempi è identificata come priorità per il prossimo ciclo.

### Principio "deterministic classifier not freeform proving"
Questo principio, emerso dall'analisi dei suggerimenti di Fun Xiang, è stato recepito per la *global discipline*: il modello deve comportarsi come un classificatore deterministico, non come un dimostratore libero.

---

## 9. Matching Invariants e False Route

### Utilità degli invarianti
I *matching invariants* (invarianti di matching) sono stati identificati come strumento utile per rilevare le *false route*.

### Proposte operative
- Valutare l'inserimento di una **legenda** che specifichi tutti gli invarianti numerici delle equazioni.
- Valutare l'aggiunta di **false route** basate su tali invarianti numerici.

### Reputation Block (Step 4)
È stato analizzato lo "Step 4: Reputation Block" come esempio di magma per le false route. Nonostante il focus attuale sia sulle true route, è stato ritenuto sufficientemente generalizzabile da includere senza rischio di overfitting.

---

## 10. Revisione dello Step 4 e Xor Parity

### Stato attuale
Lo step 4 e le definizioni di "Xor Parity" sono stati giudicati scritti male.

### Decisione
Riscrittura completa dello step 4, incluse le formule di Xor Parity e i concetti correlati. Questo è stato assegnato a Tommaso come task esplicito.

---

## 11. Risultati della run V7 (preliminari)

### Hard 2
Leggero aumento dell'1% nell'accuratezza rispetto alla V5.5 (da 71.5% a 72.5%). Il team ha ritenuto che questo rientrasse nell'intervallo di variabilità del modello.

Un risultato significativo è la conferma che lo **step 6 può essere rimosso** in quanto ridondante rispetto alle proiezioni già presenti.

### Hard 3
Accuratezza del **60%**, stabile rispetto al 61% precedente. Il problema principale rimane la grande quantità di *missed implication* (implicazioni mancate).

### Tassi di confabulazione
- Hard 2: circa **7%**
- Hard 3: tra **8% e 9%**

### Interpretazione strategica
Il focus sulle *true route* affidabili implica accettare un numero maggiore di *missed implications*. Questo è coerente con gli obiettivi della seconda fase del progetto, che richiede controesempi per prevenire la confabulazione.

---

## 12. Proiezioni: revisione concettuale

### Proiezioni come "black box"
Le proiezioni sono state concettualizzate come *black box* che il modello può usare per regole di sostituzione complesse. La struttura attuale è stata giudicata più rigorosa, sebbene meno dettagliata.

### Ridefinizione di Reshaping
È stato chiarito il significato del termine "reshaping" all'interno delle proiezioni:
- Include la sostituzione di variabili.
- Include l'uso effettivo dell'equazione 1 come regola di riscrittura.
- Il concetto chiave è la **substitution after renaming** (sostituzione dopo la rinominazione).

Il termine dovrà essere marcato nello step 2.9 per successiva chiarificazione.

---

## 13. Submission finale

### Requisiti
La mail di sottomissione richiede una breve descrizione (anche se opzionale) che spieghi:
- l'organizzazione del team;
- l'architettura dell'approccio;
- i prompt utilizzati;
- le idee matematiche alla base.

### Comunicazione con Chuck Ng
È stato deciso di inviare un messaggio di ringraziamento a Chuck Ng per la sfida e la challenge.

---

## 14. Riflessione teorica: Magma Theory e didattica dell'algebra

Nel corso della sessione è emersa una riflessione più ampia sul valore educativo della Magma Theory.

### Punto chiave
Riccardo ha sostenuto che un corso incentrato sulla **manipolazione delle equazioni** — piuttosto che sulla trasmissione assiomatica — fornirebbe una struttura più efficace per comprendere l'algebra dei gruppi e gli argomenti successivi. L'approccio costruttivo rende esplicito il ragionamento e il *problem solving*, a differenza dell'approccio trasmissivo in cui si copia una dimostrazione.

### Dicotomia strutturale / costruttiva
I due approcci didattici sono stati etichettati come "più strutturale" (approccio assiomatico tradizionale) e "più costruttivo" (approccio equazionale esplicito). Riccardo ha sostenuto che il secondo è più efficace nell'insegnare il ragionamento.

### Riferimento all'ETP
Tommaso ha segnalato che la **sezione 10 del paper ETP** (Equational Theories Project) descrive come strutture matematiche complesse — inclusi i gruppi — possano essere completamente caratterizzate usando solo le equazioni dei magmi. Questa sezione è stata identificata come lettura rilevante per il prosieguo del progetto.

---

## Action Items

### Riccardo Gay
- [ ] Implementare le modifiche di Priorità 1 e lanciare la V7
- [ ] Analizzare i risultati JSON della run V7 su Hard 3
- [ ] Valutare e integrare le modifiche di Priorità 2 se ancora rilevanti
- [ ] Inviare messaggio di ringraziamento a Chuck Ng
- [ ] Copiare il piano di lavoro e inviarlo a Tommaso su WhatsApp
- [ ] Segnare il termine "reshaping" nello step 2.9 per successiva chiarificazione
- [ ] Ampliare la sezione dei controesempi (magmi Passini e modulari)
- [ ] Rivedere la formulazione delle sezioni 4.3/4.4 sui controesempi
- [ ] Rimuovere il riferimento a "every magma" dalla documentazione
- [ ] Eseguire ricerca approfondita (depth research) con file specifici per contesto
- [ ] Rinominare il file deep research
- [ ] Inviare il deep research paper a Tommaso su Mat Distillation

### Tommaso Rossi
- [ ] Inserire commento sul set di spunti riguardante la specificità delle proiezioni
- [ ] Analizzare i motif (Hols motif, C1–C10) e identificare le aree con maggiore margine di miglioramento
- [ ] Riscrivere completamente lo step 4 (Xor Parity e formule correlate)

### Team
- [ ] Implementare "can be renamed" nelle regole di Singleton Collapse, incluso side swap
- [ ] Valutare l'inserimento di una legenda degli invarianti numerici
- [ ] Valutare l'aggiunta di false route basate sugli invarianti numerici
- [ ] Aggiornare la run grossa su Gemma V7.1
- [ ] Revisionare il documento di note e idee di Tommaso Rossi
