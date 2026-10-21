# Verifica del programma Python — Project Work 23

**Studente:** Antonio Rosellini · **Matricola:**   
**Oggetto:** pianificazione e confronto economico dei percorsi di distribuzione con partenza da Bari.

## 1. Materiale esaminato

L'istanza utilizza un deposito e cinque clienti. Le consegne giornaliere sono: Modugno 180 kg, Bitonto 220 kg, Triggiano 160 kg, Noicattaro 210 kg e Mola di Bari 230 kg. La domanda complessiva è 1.000 kg. Lo scenario A prevede un veicolo da 1.100 kg; lo scenario B due mezzi da 600 kg. I file `data/istanza.json`, `data/nodi_clienti.csv` e `data/matrice_distanze_km.csv` sono confrontati dal programma prima dei calcoli.

## 2. Enumerazione dei percorsi

La ricerca nello scenario A esamina 120 ordinamenti. La sequenza selezionata è:

**Bari → Bitonto → Modugno → Triggiano → Noicattaro → Mola di Bari → Bari (85,6 km).**

In presenza di matrice simmetrica esiste anche il percorso inverso, con la stessa distanza. Entrambi i giri sono registrati nei risultati.

Lo scenario B ha cinque ripartizioni ammissibili a meno dello scambio dei mezzi. Per ciascuna sono state esaminate tutte le coppie di permutazioni. Il risultato è:

- **Veicolo 1:** Bari → Modugno → Bitonto → Bari; 37,0 km; carico 400 kg.
- **Veicolo 2:** Bari → Triggiano → Noicattaro → Mola di Bari → Bari; 51,6 km; carico 600 kg.

La distanza totale è **88,6 km**. Esistono quattro coppie di percorsi equivalenti per inversione dell'ordine di visita dei clienti nei due gruppi.

### Ripartizioni ammissibili

| Gruppo 1 | Gruppo 2 | Carico 1 | Carico 2 | Distanza minima |
|---|---|---:|---:|---:|
| Modugno, Bitonto | Triggiano, Noicattaro, Mola di Bari | 400 kg | 600 kg | 88,6 km |
| Modugno, Bitonto, Triggiano | Noicattaro, Mola di Bari | 560 kg | 440 kg | 106,1 km |
| Modugno, Triggiano, Noicattaro | Bitonto, Mola di Bari | 550 kg | 450 kg | 133,5 km |
| Modugno, Mola di Bari | Bitonto, Triggiano, Noicattaro | 410 kg | 590 kg | 134,5 km |
| Modugno, Triggiano, Mola di Bari | Bitonto, Noicattaro | 570 kg | 430 kg | 139,5 km |

Ogni partizione produce dodici coppie di ordinamenti: 2! × 3! = 12. Totale **5 × 12 = 60**.

## 3. Modello dei tempi e dei costi

Tempo di ogni giro: `distanza_km / 45 + 0,25 × clienti_serviti` (ore). I tempi sono stimati e non derivano da traffico reale.

Costo giornaliero: `mezzi × costo_fisso + km_totali × costo_variabile_km + ore_autista_totali × 18,50`.

| Grandezza | Scenario A | Scenario B |
|---|---:|---:|
| Chilometri | 85,6 | 88,6 |
| Ore autista totali | 3,1522 | 3,2189 |
| Tempo massimo dei giri | 3,1522 | 1,8967 |
| Costo fisso | 120,00 € | 130,00 € |
| Costo dei chilometri | 61,63 € | 51,39 € |
| Costo del lavoro | 58,32 € | 59,55 € |
| **Costo complessivo** | **239,95 €** | **240,94 €** |

La differenza è 0,99 € a favore dello scenario A. Con due veicoli in parallelo il tempo di completamento diminuisce di circa il **39,83%**.

L'analisi di sensibilità modifica esclusivamente il costo chilometrico del mezzo grande. Eguagliando i costi *prima dell'arrotondamento ai centesimi*, si ottiene un punto di pareggio di **0,731558 €/km**. Nelle tabelle economiche i valori monetari sono riportati con due decimali.

## 4. Prove automatiche

Comando utilizzato:

```bash
python -m unittest discover -s tests -v
```

**Risultato: 18 test superati (18/18)**. I controlli comprendono:

1. Validità complessiva dell'istanza e corrispondenza tra JSON e CSV.
2. Numero di clienti, totale dei carichi e capacità dei mezzi.
3. Enumerazione di tutte le 120 sequenze TSP, assenza di duplicati.
4. Valore minimo TSP e inversione dei percorsi simmetrici.
5. Cinque partizioni ammissibili e 60 coppie di itinerari CVRP.
6. Controllo delle consegne, di tutti i vincoli di capacità e dei giri chiusi.
7. Ricerca esaustiva **indipendente**, basata su assegnazioni binarie e permutazioni, per confermare i due valori minimi.
8. Distinzione tra somma delle ore-autista e tempo massimo per due mezzi paralleli.
9. Costi di entrambi gli scenari e soglia di pareggio.
10. Rilevazione di dati non coerenti o distanze non valide.
11. Creazione dei file di output e loro stabilità tra due esecuzioni.
12. Gestione della matrice senza imporre una proprietà triangolare non dimostrata.

Il programma si arresta con un messaggio esplicito se i dati essenziali non sono validi o se JSON e CSV riportano distanze diverse.

## 5. Risultati e documenti prodotti

- `output/risultati.json`: dati completi, percorsi, alternative ottime e costo dei due scenari.
- `output/soluzioni_tsp.csv`: 120 sequenze di visita valutate.
- `output/soluzioni_due_veicoli.csv`: 60 coppie di itinerari con carichi e distanze.
- `output/partizioni_ammissibili.csv`: cinque ripartizioni con i rispettivi minimi.
- `output/analisi_sensibilita.csv`: prezzi testati e convenienza relativa.
- `output/riepilogo.txt`: riepilogo consultabile dei risultati.

## 6. Avvertenze per la relazione finale

Le distanze del documento preliminare, **84,2 km** e **89,4 km**, non coincidono con quelle calcolate dalla matrice della fase 1. La versione finale della relazione dovrà utilizzare **85,6 km** e **88,6 km**, aggiornando anche tempi, costi, soglia di pareggio e relative figure. Questa fase fornisce gli output informatici verificati, senza modificare il template PDF già compilato.

La verifica dimostra l'ottimalità dei percorsi **rispetto al dataset modellato**. Non certifica che le distanze siano quelle effettive tra indirizzi aziendali reali. Questa distinzione è essenziale per interpretare correttamente il risultato.
