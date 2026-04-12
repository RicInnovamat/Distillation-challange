# Distillation Challenge – Meeting 3
**Data:** 12 aprile 2026

## Obiettivo del meeting
Allineamento sullo stato del progetto Distillation Challenge, con focus su:
- analisi del paper;
- test su modelli frontier e small models;
- revisione del cheat sheet;
- definizione delle priorità operative per i prossimi giorni.

---

## 1. Stato generale del progetto

### Analisi del paper
- L’analisi del paper è stata completata.
- È stato chiarito meglio il senso della competizione: gli autori sono riusciti a completare lo **schema delle implicazioni**, ma lo hanno fatto con una procedura che **non è realmente scalabile**.
- Il punto critico emerso è che:
  - **falsificare un’implicazione** può essere affrontato con strategie relativamente più scalabili;
  - **dimostrare la verità di un’implicazione** è molto più difficile e richiede strategie meno generalizzabili, spesso vicine al brute force.

### Gap strutturale tra strumenti
È stato esplicitato con maggiore chiarezza il problema centrale del campo:

- **Automatic Theorem Provers (ATP)**  
  - deterministici;
  - logicamente rigorosi;
  - richiedono parametrizzazione molto fine;
  - poco creativi.

- **LLM**
  - molto creativi;
  - capaci di esplorare strategie;
  - non distinguono in modo affidabile vero/falso;
  - mancano di rigore logico stabile.

### Insight chiave
> “Stabilire i parametri giusti per un ATP è un’arte.”

Questa osservazione è stata considerata centrale: la scelta dei parametri per sistemi come Lean, Vampire, Mace4 ecc. non è un dettaglio tecnico, ma parte integrante del **ragionamento dimostrativo**.

### Obiettivo di lungo periodo
Costruire, o avvicinarsi a, uno strumento che sia insieme:
- **logico**
- **creativo**

Questo è il vero punto di convergenza tra formal verification e modelli generativi.

---

## 2. Automatic Theorem Provers e implicazioni metodologiche

Sono stati citati diversi ATP / strumenti affini:
- Lean
- Vampire
- Mace4
- altri prover/improver automatici

### Osservazione metodologica
Gli ATP non funzionano come “black box” in cui si inserisce uno statement e si ottiene automaticamente una dimostrazione utile.  
Per ottenere output significativi:
- bisogna definire i parametri corretti;
- questi parametri influenzano drasticamente:
  - la qualità dell’output,
  - la probabilità di successo,
  - il tempo computazionale.

Questo rafforza l’idea che il ragionamento formale non sia automatizzabile in modo banale.

---

## 3. Test su Opus 4.6

Andrea ha condotto una serie di test con **Opus 4.6**, usato in modalità:
- frontier model;
- massimo reasoning;
- timeout fissato a **1800 secondi**;
- nessun aiuto specifico (“off the shelf”).

### Obiettivo del test
Usare un modello molto forte per:
- osservare come risolve i problemi di **Hard One**;
- capire quali strategie emergono spontaneamente;
- estrarre lezioni utili per migliorare il cheat sheet e i prompt dei modelli più piccoli.

### Risultati principali
- **40 prove totali**
- **30 risolte**
- le rimanenti terminate in:
  - timeout;
  - parsing error / run troppo lunghe

### Pattern osservato
#### Affermazioni vere
- Quando Opus conclude, la risposta è **sempre corretta**.
- Le implicazioni vere vengono tipicamente dimostrate in **meno di 700 secondi**.
- Nessun caso vero ha richiesto più di circa **729 secondi**.

#### Affermazioni false
- I tempi sono distribuiti in modo molto più ampio:
  - circa **50–1500 secondi**
- Il modello tende a perdersi nella ricerca di controesempi.
- Lo **stage 2** della prova, cioè la **costruzione del controesempio**, appare molto più difficile della semplice classificazione vero/falso.

### Conclusione operativa
Opus si comporta come un **cecchino** quando riesce a chiudere il problema, ma il costo computazionale è troppo elevato per usarlo su larga scala.

---

## 4. Costo computazionale

L’uso di Opus ha evidenziato un forte vincolo economico/computazionale.

### Dati condivisi
- circa **20% del budget settimanale** consumato in 2 giorni;
- circa **2 milioni di token** utilizzati;
- costo equivalente via API: circa **300 dollari**.

### Confronto con i modelli piccoli
I modelli piccoli testati finora:
- hanno consumato complessivamente circa **100 milioni di token**;
- con costo totale nell’ordine di **30–35 euro**.

### Implicazione
- **Hard One** è forse affrontabile con Opus;
- **Hard Two** e **Hard Three** non sono sostenibili con questo setup.

Opus resta quindi utile come:
- strumento di esplorazione;
- generatore di insight;
- sorgente di esempi e strategie da distillare.

Non come motore principale per l’intero benchmark.

---

## 5. Sviluppo Cheat Sheet V4.4

Riccardo ha lavorato a una nuova versione del cheat sheet, la **V4.4**.

### Novità principale
Introduzione di un **Domain Specific Language (DSL)** per strutturare meglio:
- parametri;
- procedure;
- output del modello.

### Evidenze emerse dai test
- **Gemma**
  - ignora strutture “stile codice” troppo esplicite;
  - recepisce meglio un **DSL** più vicino a un linguaggio formalizzato ma non troppo “Python-like”.

- **GPT-OS**
  - risponde bene anche a linguaggi simili a codice;
  - è più reattivo su formati ibridi tra naturale e Python-like.

- **Llama**
  - salta completamente questa struttura;
  - tende a dare output poveri o sempre uguali;
  - in diversi test produce semplicemente “false”.

### Conclusione
La V4.4 consiste sostanzialmente in:
- base della **V4.1**
- più inserimento mirato di **DSL** in alcune procedure.

L’ipotesi è che questa struttura possa migliorare la robustezza del ragionamento, almeno su alcuni modelli.

---

## 6. Vincoli tecnici emergenti

### 6.1 Upper bound dei token
Per alcuni modelli, in particolare Gemma:
- senza reasoning attivo, il modello non supera in pratica **3–4k token** di output;
- questo limita fortemente la profondità del ragionamento.

### 6.2 Reasoning mode
È emerso che alcuni provider suggeriscono di abbassare o disattivare il reasoning level per evitare sforamenti, ma questo rischia di compromettere proprio la qualità del comportamento desiderato.

### 6.3 Llama
Llama è stato giudicato, allo stato attuale:
- poco utile;
- troppo biased verso “false”;
- non competitivo rispetto agli altri modelli.

Inoltre è stato osservato che:
- il modello risulta di fatto disallineato rispetto alle necessità del task;
- non sembra valere la pena continuare a investirci tempo.

### Decisione emersa
**Rimuovere o sospendere Llama** e concentrare il lavoro su:
- **Gemma**
- **GPT-OS**

---

## 7. Strategie matematiche per implicazioni vere

Tommaso ha portato alcuni chiarimenti teorici importanti su cosa significhi dimostrare che un’implicazione è vera.

### 7.1 Completezza di Birkhoff
Se un’implicazione del tipo:

`E => E'`

è vera, allora `E'` può essere ottenuta tramite **sostituzioni iterative finite** a partire da `E`.

### Traduzione operativa
Per verificare che un’implicazione sia vera:
- si tratta `E` come una **legge di riscrittura**;
- si prendono i membri di `E'`;
- si riscrivono iterativamente usando `E`.

Questa è, di fatto, la logica di base dietro molte strategie dei theorem prover.

### Implicazione per il cheat sheet
Parte di questa idea è **già presente** nel cheat sheet:
- replacement
- left/right projection
- collapse step

Ma potrebbe essere:
- resa più esplicita;
- generalizzata meglio;
- formulata in modo che il modello capisca che il principio generale è la **riscrittura iterativa**.

---

## 8. Forma canonica

Un punto ritenuto cruciale da Tommaso è la **forma canonica**.

### Perché è importante
La forma canonica è fondamentale sia per:
- implicazioni vere;
- implicazioni false.

Serve perché:
- molti invarianti hanno senso solo se applicati a una rappresentazione coerente;
- il confronto tra implicazioni dipende da una normalizzazione affidabile;
- senza una canonizzazione corretta, si rischia di costruire euristiche fragili.

### Stato attuale
- Il dataset **Hard One / Hard Two / Hard Three** **non è in forma canonica**.
- La numerazione del progetto principale (quella sulle ~4000 equazioni) invece sì: lì la forma canonica entra nella costruzione stessa dell’indicizzazione.

### Follow-up teorico
Nel paper, in appendice, è descritta la procedura per ottenere la forma canonica.  
Questa sezione va ripresa e controllata per capire:
- se il cheat sheet la implementa già in modo sufficiente;
- dove va rafforzata.

---

## 9. Classi di equivalenza e transitività

Tommaso ha segnalato anche un ulteriore livello non ancora ben implementato nel cheat sheet:

### Idea
Una volta ottenute forme canoniche affidabili, si può:
- trattare le implicazioni equivalenti come classi di equivalenza;
- ragionare tramite proprietà come la **transitività**.

### Problema
Questa parte richiede:
- un certo grado di auto-riferimento;
- capacità di riuso coerente dei risultati intermedi;
- una struttura di ragionamento che gli LLM spesso gestiscono male.

### Stato
Questo punto è stato identificato come:
- teoricamente promettente;
- ma ancora difficile da implementare bene nel cheat sheet attuale.

---

## 10. Proposte di miglioramento del cheat sheet

### 10.1 Meta-prompt optimization
Tommaso ha ripreso una tecnica dal paper:
- chiedere al modello di costruire da solo il proprio cheat sheet;
- identificare gli esempi più difficili;
- migliorare iterativamente le istruzioni a partire dagli errori.

### Struttura dell’idea
1. si forniscono esempi;
2. il modello produce un cheat sheet utile a risolverli;
3. si individuano i casi più difficili;
4. si rafforza il cheat sheet per quei casi specifici.

### Potenziale vantaggio
- trasformare gli errori in materiale strutturato;
- avvicinare il processo a una forma di auto-miglioramento controllato.

---

### 10.2 Default to true
È emersa anche un’euristica da testare:

> se non ci sono evidenze solide di falsità, default to true.

### Razionale
Se il sistema di rilevazione del falso è abbastanza affidabile, questa regola potrebbe:
- ridurre il **false bias**;
- migliorare la distribuzione delle risposte.

### Nota
Dal punto di vista matematico l’euristica è discutibile, ma dal punto di vista ingegneristico/statistico potrebbe essere utile in alcuni modelli.

---

### 10.3 Integrazione di reasoning esplicito
Un’altra proposta è inserire nel cheat sheet:
- esempi espliciti di ragionamento;
- razionali sintetici;
- esempi di come il modello dovrebbe procedere sia su casi veri sia su casi falsi.

L’idea è fornire non solo regole, ma anche **tracce di processo**.

---

## 11. Discussione strategica

Riccardo ha evidenziato una difficoltà concreta:
- stanno entrando molte idee nuove nel prompt;
- mancano però criteri chiari per capire:
  - cosa tenere;
  - cosa togliere;
  - come integrare i nuovi elementi senza rompere ciò che già funziona;
  - come controllare che gli insight siano davvero generalizzabili e non validi solo su sottoinsiemi del dataset.

In particolare è stato notato che alcuni insight prodotti nei report precedenti sembrano valere solo per gruppi limitati di equazioni (per esempio Hard One) e non per tutto il benchmark.

Questo rende urgente una gestione più disciplinata del prompt e delle versioni del cheat sheet.

---

## 12. Decisioni operative emerse

### Andrea
Andrea si occuperà di:
- far proseguire **Opus** su **Hard One** fino al completamento;
- estrarre da Opus:
  - note di lavoro,
  - osservazioni utili,
  - possibili improvement del cheat sheet;
- mettere a confronto i cheat sheet esistenti con il comportamento del modello grande.

### Riccardo + Tommaso
Riccardo e Tommaso lavoreranno a una nuova versione:
- **Cheat Sheet V5 / V6**

con possibile integrazione di:
- miglioramento sulla **forma canonica**;
- esplicitazione delle logiche di **riscrittura / sostituzione**;
- uso del **DSL**;
- eventuali elementi di **meta-prompt**;
- esempi più strutturati per reasoning vero/falso.

### Modelli
Focus operativo su:
- **Gemma**
- **GPT-OS**

Sospensione o rimozione di:
- **Llama**

---

## 13. Prossimi appuntamenti
- **Martedì ore 18:00** – prossimo incontro di allineamento
- poi direttamente **sabato mattina**

---

## 14. Sintesi finale

### Punti chiave del meeting
- Il problema centrale non è solo classificare implicazioni, ma farlo in modo **scalabile**.
- Gli ATP sono rigorosi ma poco creativi; gli LLM creativi ma poco affidabili sul vero/falso.
- Opus 4.6 ha mostrato risultati forti su Hard One, ma a costi troppo alti per essere il motore principale del progetto.
- Il cheat sheet V4.4 introduce una prima integrazione utile via **DSL**.
- La **forma canonica** e le **strategie di riscrittura** diventano priorità teoriche e operative.
- Serve una nuova iterazione del cheat sheet più controllata, più esplicita e meno dispersiva.
- La direzione condivisa è:
  - usare i modelli grandi per estrarre insight;
  - distillare questi insight in prompt/cheat sheet per modelli più economici.

---

## Action Items

### Andrea
- [ ] Completare la run di Opus su Hard One
- [ ] Estrarre insight e note di lavoro da Opus
- [ ] Condividere osservazioni utili per improvement del cheat sheet

### Riccardo
- [ ] Creare la v5
- [ ] Preparare base di lavoro per V5/V6

### Tommaso
- [ ] Esplicitare meglio nel cheat sheet:
  - [ ] completezza di Birkhoff / sostituzione iterativa
  - [ ] ruolo della forma canonica
  - [ ] possibile uso della transitività tra classi di equivalenza
- [ ] Supportare la scrittura della nuova versione del cheat sheet

### Team
- [ ] Valutare rimozione definitiva di Llama
- [ ] Testare DSL + reasoning examples
- [ ] Verificare se il meta-prompt può aiutare nella generazione/miglioramento del cheat sheet
