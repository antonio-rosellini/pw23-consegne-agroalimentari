# Pianificazione delle consegne agroalimentari

**Project Work n. 23 — Informatica per le Aziende Digitali (L-31)**  
**Studente:** Antonio Rosellini  
**Traccia:** Sviluppo di un codice Python per la pianificazione e il confronto economico dei percorsi di consegna di un’impresa agroalimentare.

Il caso di studio riguarda **Adriatica Fresco Distribuzione S.r.l.**, un'impresa *simulata* con deposito a Bari e cinque punti di consegna nei comuni di Modugno, Bitonto, Triggiano, Noicattaro e Mola di Bari. Un programma Python applica l'enumerazione completa per individuare i percorsi a distanza minima nelle configurazioni con uno e due veicoli refrigerati. Successivamente ne calcola tempi, costi e soglie di convenienza.

## Contenuto del progetto

| Cartella | Contenuto |
|---|---|
| `src/` | Programma Python, funzioni di ottimizzazione, analisi economica e generazione HTML. |
| `data/` | Dati dell'istanza, quantità richieste, matrice delle distanze e collegamenti alle fonti. |
| `output/` | Risultati JSON, riepiloghi, permutazioni e partizioni esaminate. |
| `web/` | Versione della pagina HTML da aprire localmente. |
| `docs/` | Copia statica del sito predisposta per GitHub Pages. |
| `analisi/` | Calcoli indipendenti, tabelle economiche e grafici. |
| `tests/` | Test automatici sulla correttezza del codice, delle elaborazioni e della pagina web. |
| `documentazione/` | Scheda delle distanze, prove di esecuzione e verifiche. |

## Avvio e risultati

Richiede **Python 3.10 o successivo**. Non sono necessarie librerie esterne per eseguire l'algoritmo o generare la pagina web.

Dalla cartella principale del progetto:

```bash
python src/main.py
python src/export_html.py
python src/prepare_pages.py
python -m unittest discover -s tests -v
```

Dopo l'esecuzione, aprire `web/index.html` con il browser. La pagina mostra i grafi dei due scenari, le quantità, la matrice delle distanze, il confronto economico e un controllo per variare il costo chilometrico del veicolo grande.

`docs/index.html` presenta gli stessi contenuti ed è destinato all'eventuale pubblicazione mediante GitHub Pages. Dopo ogni modifica ai dati e ogni nuova esecuzione di `export_html.py`, eseguire anche `prepare_pages.py` per allineare la versione pubblicabile.

## Risultati dell'istanza adottata

| Indicatore | Scenario A: un veicolo | Scenario B: due veicoli |
|---|---:|---:|
| Distanza minima totale | 85,6 km | 88,6 km |
| Costo giornaliero stimato | 239,95 € | 240,94 € |
| Durata massima del giro | 3 h 09 min | 1 h 54 min |

Nella configurazione di base, il veicolo unico comporta un costo minore di circa 0,99 € al giorno. Mantenendo invariati gli altri parametri, il costo chilometrico del veicolo grande che eguaglia i costi dei due scenari è circa **0,731558 €/km**.

## Ipotesi e limiti

Il deposito e i clienti sono riferiti ai centri comunali. La matrice simmetrica contiene **stime stradali normalizzate**, documentate in `data/fonti_distanze.csv`: non rappresenta distanze certificate tra indirizzi puntuali. I prezzi, la velocità media e i tempi di servizio sono ipotesi del modello. L'ottimalità dei percorsi si riferisce soltanto ai dati impiegati. I grafi sono rappresentazioni schematiche, non mappe della viabilità.

## Pubblicazione e consultazione

Le istruzioni per creare la repository, caricare i file e attivare GitHub Pages si trovano in [`PUBBLICAZIONE_GITHUB.md`](PUBBLICAZIONE_GITHUB.md). **La presenza di questa cartella non implica che il progetto sia già pubblicato.** La repository e la pagina web avranno un indirizzo effettivo soltanto dopo il caricamento su GitHub e l'attivazione del sito.
