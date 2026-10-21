"""Aggiorna la cartella docs/ destinata alla pagina statica del progetto.

Dalla cartella principale:
    python src/main.py
    python src/export_html.py
    python src/prepare_pages.py
"""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STATIC_FILES = ("index.html", "style.css", "app.js")


def prepare_pages() -> None:
    source = ROOT / "web"
    destination = ROOT / "docs"
    destination.mkdir(exist_ok=True)
    for filename in STATIC_FILES:
        src = source / filename
        if not src.is_file():
            raise FileNotFoundError(f"File mancante: {src}")
        shutil.copy2(src, destination / filename)
    (destination / ".nojekyll").touch(exist_ok=True)


if __name__ == "__main__":
    prepare_pages()
    print("Cartella docs/ aggiornata: index.html, style.css, app.js")
