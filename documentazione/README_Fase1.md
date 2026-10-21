# PW23 — Fase 1: base dati geografica e logistica

**Studente:** Antonio Rosellini — **Matricola:**   
**Corso:** Informatica per le Aziende Digitali (L-31)  
**Traccia:** 23 — Sviluppo di un codice Python per la pianificazione e il confronto economico dei percorsi di consegna di un’impresa agroalimentare  
**Rilevazione documentale:** 16 ottobre 2026

## Impresa e territorio

Il caso di studio considera la seguente configurazione: la **Adriatica Fresco Distribuzione S.r.l.** è **un'impresa simulata**, con deposito modellato a Bari e cinque clienti modellati nei comuni di Modugno, Bitonto, Triggiano, Noicattaro e Mola di Bari. I nomi dei comuni sono reali, ma **non sono stati individuati indirizzi di magazzino o di singoli negozi**. Le coordinate geografiche sono indicative del centro dei comuni e servono solo a rappresentarli graficamente.

## Consegne giornaliere

| Codice | Comune | Quantità |
|---|---|---:|
| D | Bari (deposito) | 0 kg |
| C1 | Modugno | 180 kg |
| C2 | Bitonto | 220 kg |
| C3 | Triggiano | 160 kg |
| C4 | Noicattaro | 210 kg |
| C5 | Mola di Bari | 230 kg |
| | **Totale da consegnare** | **1.000 kg** |

**Scenario A:** un veicolo refrigerato con capacità 1.100 kg.  
**Scenario B:** due veicoli refrigerati identici con capacità 600 kg ciascuno.  
Le quantità e le capacità sono **ipotesi progettuali** definite per il caso di studio e non dati aziendali verificati. La domanda totale di 1.000 kg supera la capacità di un solo mezzo piccolo, mentre è inferiore alla capacità complessiva dei due mezzi piccoli (1.200 kg). Sono possibili ripartizioni senza spezzare una singola consegna.

## Come sono state ottenute le distanze

Il file `fonti_distanze.csv` riporta per **tutte le 15 coppie non ordinate di località** le misure pubblicate, le pagine da cui sono ricavate e il criterio usato. La fonte prevalente è PercorsoMigliore.com; sono presenti anche Percorsostrada.it e Rome2Rio per alcune tratte. I collegamenti sono riportati in forma esplicita per permettere il controllo delle tratte.

**Attenzione al significato dei numeri:** le fonti pubblicano stime stradali riferite ai centri dei comuni, normalmente arrotondate al chilometro, con percorsi che possono non coincidere nei due sensi. Per rimanere fedeli al modello simmetrico descritto nell'elaborato, se sono disponibili entrambi i versi è usata la loro media aritmetica arrotondata al decimo di km; se ne è documentato uno solo si usa quest'ultimo come proxy simmetrico. I decimali così ottenuti **non indicano una precisione cartografica di 100 metri**: sono l'effetto della normalizzazione del modello. Queste distanze NON sono misurazioni di un magazzino reale verso punti vendita specifici.

Alcuni servizi mostrano itinerari che usano autostrade anche a pedaggio. I pedaggi non sono conteggiati come voce separata nei costi iniziali: ciò è un limite del modello economico da esplicitare nella relazione, o da correggere in fase successiva se si sceglierà di considerarli. La velocità media di 45 km/h è una **ipotesi operativa** e non la velocità ricavata dai singoli siti di viaggio.

La matrice è **simmetrica** e con diagonale nulla, ma non è necessariamente una metrica stradale esatta: l'uso di fonti e percorsi diversi può violare in alcuni casi la disuguaglianza triangolare. Per un uso industriale occorre interrogare un unico servizio di routing sugli indirizzi esatti e includere l'opzione relativa ai pedaggi.

## Parametri economici (ipotesi tratte dalla relazione)

| Parametro | Scenario A (1 veicolo) | Scenario B (2 veicoli) |
|---|---:|---:|
| Capacità per veicolo | 1.100 kg | 600 kg |
| Noleggio / disponibilità per veicolo al giorno | 120,00 € | 65,00 € |
| Costo variabile per km | 0,72 €/km | 0,58 €/km |
| Numero veicoli | 1 | 2 |

Per entrambi: costo autista **18,50 €/ora per autista**, velocità media **45 km/h**, sosta di servizio **15 minuti per cliente**. Sono ipotesi accademiche dichiarate, non preventivi commerciali raccolti sul mercato.

## Contenuto della cartella

- `dati/istanza.json`: sorgente dati unica, con informazioni dello studente, società simulata, comuni, domande, matrice di distanze e parametri economici.
- `dati/nodi_clienti.csv`: nodi, domande e coordinate geografiche indicative.
- `dati/matrice_distanze_km.csv`: matrice stradale simmetrica, numeri in km.
- `dati/fonti_distanze.csv`: le 15 coppie, le osservazioni da fonti esterne, i collegamenti e il procedimento per la simmetrizzazione.
- `documentazione/Scheda_dati_Fase1.md`: riepilogo delle scelte, delle verifiche e dei limiti.
- `Scheda_Dati_PW23_Rosellini.xlsx`: foglio di consultazione per controllare agevolmente nodi, matrice e fonti.

## Stato della documentazione

**Base dati:** matrice, fonti, parametri logistici e verifiche documentali.  
**Integrazione applicativa:** i dati sono predisposti per l’implementazione dell’enumerazione completa dei percorsi (TSP e CVRP a due veicoli), del confronto economico e delle rappresentazioni HTML.

**Coerenza dei risultati:** le distanze complessive di 84,2 km e 89,4 km riportate nella versione preliminare della relazione dovranno essere confrontate con gli output del programma, ottenuti dalla matrice allegata. In caso di differenze, i risultati numerici della relazione saranno aggiornati.
