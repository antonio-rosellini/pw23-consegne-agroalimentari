# Contenuti della repository pubblica

La repository contiene il codice Python, i dati logistici, i risultati, i test e la pagina HTML del caso di studio. La matricola non viene riportata nella versione pubblica; resta nel documento universitario destinato alla consegna.

## Esecuzione

Dalla cartella principale:

```bash
python src/main.py
python src/export_html.py
python src/prepare_pages.py
python -m unittest discover -s tests -v
```

La pagina per GitHub Pages si trova nella cartella `docs/`.
