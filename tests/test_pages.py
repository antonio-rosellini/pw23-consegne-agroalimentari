"""Verifica i file destinati alla pubblicazione della pagina statica."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestPubblicazione(unittest.TestCase):
    def test_sito_identico_a_versione_locale(self):
        for file_name in ('index.html', 'style.css', 'app.js'):
            with self.subTest(file=file_name):
                self.assertEqual((ROOT/'web'/file_name).read_bytes(),
                                 (ROOT/'docs'/file_name).read_bytes())

    def test_file_github_pages(self):
        self.assertTrue((ROOT/'docs'/'.nojekyll').is_file())
        html = (ROOT/'docs'/'index.html').read_text(encoding='utf-8')
        self.assertIn('href="style.css"', html)
        self.assertIn('src="app.js"', html)
        for name in ('contesto', 'percorsi', 'economia', 'dati', 'metodo'):
            self.assertIn(f'id="{name}"', html)

    def test_nessun_asset_esterno_necessario(self):
        h = (ROOT/'docs'/'index.html').read_text(encoding='utf-8')
        self.assertNotRegex(h, r'<(?:script|link)\b[^>]*(?:https?://|//)')
        self.assertNotRegex(h, r'<iframe\b')

    def test_readme_istruzioni_esecuzione(self):
        readme = (ROOT/'README.md').read_text(encoding='utf-8')
        self.assertIn('python src/prepare_pages.py', readme)
        self.assertIn('python -m unittest discover -s tests -v', readme)


if __name__ == '__main__':
    unittest.main()
