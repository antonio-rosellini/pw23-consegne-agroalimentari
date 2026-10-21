# Scheda tecnica — Fase 1, validazione dati

**Progetto:** PW23, Antonio Rosellini,   
**Data di consultazione delle fonti:** 16/10/2026

## Controlli eseguiti

- 1 deposito e 5 clienti in comuni reali dell’area barese: **OK**.
- Cinque quantità positive, totale 1.000 kg: **OK**.
- Veicolo A (1.100 kg) in grado di soddisfare l’intera domanda: **OK**.
- Veicoli B (2 × 600 kg), necessari entrambi: **OK**.
- Assegnazioni ammissibili delle cinque consegne ai due mezzi, a meno dello scambio dei veicoli: **5 ripartizioni**.
- Matrice 6×6 completa, diagonale nulla, simmetria, positività delle 15 distanze fra coppie diverse: **OK**.
- Copertura documentale: **15 coppie**, con un collegamento a una fonte esterna per ognuna; per alcune tratte la disponibilità è limitata a uno dei due versi.

## Osservazioni per la continuazione

1. Le distanze complessive indicate nella versione preliminare della relazione sono **da verificare** rispetto ai risultati ottenuti dalla matrice dei dati, senza considerarle confermate.
2. Il modello usa centri abitati di riferimento, non indirizzi di clienti identificati. Lo si dovrà spiegare esplicitamente.
3. La simmetrizzazione è un'operazione matematica documentata, non una misura di un singolo itinerario.
4. Tratte con autostrade a pedaggio: occorre discutere l'esclusione dei pedaggi dal modello iniziale.
5. Per lo scopo della traccia il codice deve cercare sistematicamente gli ordinamenti e le partizioni, non affidarsi alla lettura intuitiva della mappa.
