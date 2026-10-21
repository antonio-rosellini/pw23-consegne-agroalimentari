# Verifica tecnico-economica dei percorsi

**Project Work 23** — Antonio Rosellini, matricola ****  
Corso di laurea: Informatica per le Aziende Digitali (L-31)

## Dati e metodo

L'analisi riprende il dataset della fase 1 e il programma della fase 2. I cinque clienti sono Modugno (180 kg), Bitonto (220 kg), Triggiano (160 kg), Noicattaro (210 kg), Mola di Bari (230 kg). La domanda totale è 1.000 kg; il deposito è a Bari. Le distanze sono stime stradali pubbliche normalizzate in forma simmetrica, non misurazioni certificate fra indirizzi puntuali.

L'obiettivo è minimizzare la **distanza totale**, come richiesto. I costi vengono calcolati dopo aver individuato gli itinerari migliori. Lo scenario A utilizza un mezzo refrigerato da 1.100 kg; lo scenario B due mezzi da 600 kg ciascuno.

## Verifica dell'enumerazione

- Scenario A: 120 permutazioni; distanza minima **85,6 km**.
- Scenario B: cinque ripartizioni ammissibili senza duplicare lo scambio dei mezzi; 60 coppie di giri; distanza minima **88,6 km**.
- Verifica indipendente: 10 assegnazioni ammissibili con due mezzi distintamente etichettati e 120 coppie di itinerari, equivalenti alle 60 soluzioni non etichettate.

Percorso A: **Bari → Bitonto → Modugno → Triggiano → Noicattaro → Mola di Bari → Bari**.  
Percorso B1: **Bari → Modugno → Bitonto → Bari**, 400 kg, 37,0 km.  
Percorso B2: **Bari → Triggiano → Noicattaro → Mola di Bari → Bari**, 600 kg, 51,6 km.

## Calcolo dei tempi

Con velocità convenzionale di 45 km/h e servizio di 15 minuti per consegna:

- A: 85,6 / 45 + 5 × 0,25 = **3,152222 ore**.
- B1: 37 / 45 + 2 × 0,25 = **1,322222 ore**.
- B2: 51,6 / 45 + 3 × 0,25 = **1,896667 ore**.
- Ore-autista B sommate: **3,218889 ore**.
- Tempo di completamento B, con partenze simultanee: **1,896667 ore**, riduzione **39,83%** rispetto ad A.

## Calcolo economico

Formula: `C = noleggio + distanza × costo_km + ore_autista × costo_orario`.

| Componente | A | B |
|---|---:|---:|
| Noleggio | 120,00 € | 130,00 € |
| Costo chilometrico | 61,63 € | 51,39 € |
| Costo autisti | 58,32 € | 59,55 € |
| **Totale** | **239,95 €** | **240,94 €** |

Differenza con base di calcolo non arrotondata: **0,989333 €**, pari a **0,99 €** esposti ai centesimi. Con i parametri assunti il veicolo unico è leggermente più economico.

### Sensibilità al costo per km del veicolo A

Il punto di pareggio teorico, tenendo gli altri parametri costanti, è **0,7315576324 €/km**. A 0,72 €/km conviene A; a 0,75 €/km conviene B. La tabella completa è `analisi/output/sensibilita_prezzo_A.csv`, il grafico corrispondente è `analisi/grafici/sensibilita_costo_km.svg`.

### Sensibilità al costo fisso giornaliero del veicolo A

Con gli altri valori invariati, il canone di pareggio è **120,989333 €/giorno**. A 120 € conviene A; a 125 € conviene B. La tabella completa è `analisi/output/sensibilita_noleggio_A.csv`.

## Ripetizione della verifica

Dalla cartella principale:

```bash
python src/main.py
python analisi/verifica_economica.py
python -m unittest discover -s tests -v
```

Il secondo programma ricalcola i risultati direttamente dalla matrice, senza importare le funzioni di ottimizzazione. Controlla anche la coerenza con il file `output/risultati.json`.

## Limiti

Tutte le conclusioni valgono **per l'istanza fornita**. La matrice simmetrica deriva da fonti stradali eterogenee e può violare la disuguaglianza triangolare; non deve essere presentata come un'unica rilevazione diretta di Google Maps. Prezzi e velocità sono assunzioni didattiche. Non sono modellati traffico dinamico, finestre di consegna, incompatibilità merceologiche, retribuzioni minime a turno o pedaggi separati.

La relazione principale già compilata nel template resta invariata in questa fase; il riallineamento dei risultati economici è previsto al completamento degli artefatti web.
