# Verifica della pagina web – Project Work 23

**Studente:** Antonio Rosellini  
**Matricola:**   
**Tema:** La digitalizzazione dell'impresa

## Elementi disponibili

- Pagina `web/index.html` con cinque sezioni: contesto, percorsi, costi, dati, metodo.
- Grafi SVG dei giri ottimali ricavati dall'output del programma Python.
- Dati dei clienti, matrice delle distanze e vincoli di capacità.
- Costi fissi, chilometrici e del personale per i due scenari.
- Grafico della sensibilità del costo al prezzo chilometrico del veicolo grande.
- Controllo interattivo del prezzo da 0,50 a 1,00 €/km, con aggiornamento dei costi e del risultato del confronto.

## Controlli di corrispondenza

Sono stati eseguiti i test automatici presenti in `tests/` tramite:

```bash
python -m unittest discover -s tests -v
```

**Esito: 32 test superati su 32.** Otto verifiche riguardano direttamente la pagina web, la rigenerazione da `risultati.json` e la presenza degli elementi richiesti.

## Prove su browser

La pagina è stata renderizzata con Chromium, con viewport desktop di **1440 × 900 px** e viewport mobile di **390 × 844 px**. Nei due casi non sono stati registrati errori JavaScript durante la prova. Nessun elemento ha provocato uno scorrimento orizzontale dell'intera pagina. È stato inoltre verificato il controllo del prezzo:

- A **0,72 €/km**, costo A: **239,95 €**; costo B: **240,94 €**; soluzione più economica: **A**.
- A **0,90 €/km**, costo A: **255,36 €**; costo B: **240,94 €**; soluzione più economica: **B**.

La verifica grafica è stata effettuata su una copia della pagina caricata nel browser con gli stessi contenuti HTML, CSS e JavaScript. Non è stata effettuata in questa sessione una prova di apertura diretta tramite `file://`, bloccata dalle restrizioni dell'ambiente di test.

## Limitazioni del dataset

L'ottimo è calcolato rispetto alle distanze stradali stimate e normalizzate in `data/istanza.json`. I grafi sono schemi di collegamento geografico, non mappe con itinerari stradali. La documentazione delle fonti è contenuta in `data/fonti_distanze.csv`.

I file della relazione compilata secondo il template universitario non sono stati modificati.
