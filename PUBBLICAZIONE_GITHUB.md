# Pubblicazione della repository e della pagina HTML

Questa guida descrive la procedura per mettere online il progetto. I passaggi di pubblicazione devono essere completati da un account GitHub con i necessari permessi. I collegamenti per la relazione universitaria possono essere copiati solamente dopo l'attivazione effettiva.

## 1. Verifica preliminare

Prima di creare una repository pubblica, considerare che i file HTML e alcuni documenti riportano il nome dello studente e il numero di matricola. Una repository pubblica e una pagina GitHub Pages pubblica rendono tali dati consultabili da chiunque. Se non si desidera pubblicare la matricola, occorre oscurarla dai file destinati al web e dal README, mantenendo quella nel PDF da consegnare all'università.

Il progetto utilizza un caso aziendale simulato. Le distanze sono stime normalizzate, non distanze puntuali certificate.

## 2. Creazione della repository

1. Accedere a GitHub con l'account destinato a ospitare il progetto.
2. Aprire **New repository** (`+` → **New repository**).
3. Inserire come nome, per esempio, `pw23-consegne-agroalimentari`.
4. Impostare la visibilità **Private** o **Public** dopo aver valutato la presenza di dati personali. Per pubblicare gratuitamente la pagina con GitHub Pages, in genere è necessario che la repository sia pubblica: verificare le condizioni del proprio piano.
5. Per caricare i file preparati, è più semplice creare la repository senza aggiungere un README iniziale.
6. Selezionare **Create repository**.

**Caricamento tramite browser:** estrarre lo ZIP sul computer. Nella nuova repository scegliere **Add file** → **Upload files**, quindi caricare il contenuto della cartella `PW23_Rosellini_Fase5_Repository`, comprese le sottocartelle `src`, `data`, `web`, `docs`, `tests`, `analisi`, `documentazione` e `.github` (se supportato dal sistema di caricamento). Non caricare lo ZIP come unico file: GitHub non ne estrae automaticamente il contenuto. Confermare con **Commit changes** sul ramo `main`. Verificare che `README.md` e `docs/index.html` compaiano nei rispettivi percorsi.

**Alternativa tramite terminale (dalla cartella principale estratta):**

```bash
git init
git add .
git commit -m "Aggiungi progetto e documentazione"
git branch -M main
git remote add origin https://github.com/UTENTE/pw23-consegne-agroalimentari.git
git push -u origin main
```

Sostituire `UTENTE` con il vero nome dell'account GitHub; se il repository ha un altro nome, adattare anche il percorso. Il comando `git commit` richiede che identità Git e autenticazione siano configurate correttamente.

## 3. Pubblicazione della pagina con GitHub Pages

1. Aprire la repository su GitHub.
2. Andare in **Settings** → **Pages**.
3. In **Build and deployment** scegliere **Deploy from a branch**.
4. Selezionare il ramo `main` e la cartella **`/docs`**, poi **Save**.
5. Attendere il completamento della pubblicazione e aprire l'indirizzo mostrato da GitHub nella sezione Pages.
6. Verificare che grafi, tabelle e controllo del prezzo funzionino anche nell'indirizzo pubblico.

Il file `docs/.nojekyll` fa parte dei file da caricare. Lo URL effettivo della pagina deve essere preso da GitHub dopo il deploy, anziché dedotto in anticipo.

## 4. Collegamenti da inserire nel project work

Nella relazione universitaria occorre riportare:

- L'URL reale della **repository** contenente codice, dati e file HTML/CSS.
- L'URL reale della **pagina HTML** su GitHub Pages; in alternativa, le istruzioni per aprire `web/index.html` localmente, come ammesso dalla traccia.

Controllare entrambi i collegamenti da una finestra privata del browser e, se necessario, dopo aver effettuato l'accesso con le credenziali richieste. Per un docente che deve consultarli senza autorizzazioni specifiche, una repository privata potrebbe non essere accessibile.

## 5. Aggiornare il progetto dopo eventuali correzioni

In caso di variazioni a distanze, carichi o costi, eseguire:

```bash
python src/main.py
python src/export_html.py
python src/prepare_pages.py
python -m unittest discover -s tests -v
```

In seguito, caricare i file modificati nella repository. La copia `docs/` deve restare coerente con `web/`; entrambi i siti sono statici e non usano dati online in tempo reale.
