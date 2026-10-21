"""Controlli di corrispondenza tra pagina web e risultati del programma."""
from __future__ import annotations
import json
import re
import tempfile
import unittest
from pathlib import Path

from src.export_html import create_html, euro, km, integer_it

BASE=Path(__file__).resolve().parents[1]


class TestPaginaWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=json.loads((BASE/'output'/'risultati.json').read_text(encoding='utf-8'))
        cls.html=(BASE/'web'/'index.html').read_text(encoding='utf-8')

    def test_rigenerazione_identica(self):
        self.assertEqual(self.html, create_html(self.results))

    def test_risultati_economici_presenti(self):
        e=self.results['economic_comparison']
        for label in ('scenario_A','scenario_B'):
            self.assertIn(euro(e[label]['total_eur']),self.html)
        self.assertIn(euro(e['difference_B_minus_A_eur']),self.html)

    def test_percorsi_ottimi_corrispondono_al_json(self):
        for route in [self.results['single_vehicle']['route'],*self.results['two_vehicles']['routes']]:
            for node in route['cities']:
                self.assertIn(node,self.html)
            self.assertIn(km(route['distance_km']),self.html)

    def test_tutti_i_nodi_comparsi(self):
        for node in self.results['nodes']:
            self.assertIn(node['name'],self.html)
        self.assertEqual(len(self.results['nodes']),6)

    def test_matrice_e_quantita_corrispondenti(self):
        self.assertIn('Matrice delle distanze',self.html)
        self.assertIn(integer_it(sum(x['demand_kg'] for x in self.results['nodes']))+' kg',self.html)
        for row in self.results['distance_km']:
            for v in row:
                self.assertIn(km(v),self.html)

    def test_configurazione_interattiva_da_output(self):
        config=re.search(r'<script type="application/json" id="dashboard-config">(.*?)</script>',self.html,re.DOTALL)
        self.assertIsNotNone(config)
        values=json.loads(config.group(1))
        r=self.results
        self.assertEqual(values['distanceA'],r['economic_comparison']['scenario_A']['total_distance_km'])
        self.assertEqual(values['breakEven'],r['sensitivity']['break_even_price_eur_km'])
        self.assertAlmostEqual(values['costB'],240.9374444444,places=3)

    def test_nessuna_dipendenza_di_rete(self):
        self.assertNotIn('https://fonts.',self.html)
        self.assertIn('href="style.css"',self.html)
        self.assertIn('src="app.js"',self.html)
        self.assertNotIn('fetch(', (BASE/'web'/'app.js').read_text(encoding='utf-8'))

    def test_grafi_e_tabella_sensibilita(self):
        self.assertEqual(self.html.count('class="route-svg"'),2)
        self.assertIn('id="price-chart"',self.html)
        self.assertIn('id="km-price"',self.html)
        self.assertEqual(self.html.count('is_base_price'),0)
        self.assertGreaterEqual(self.html.count('€/km'),8)


if __name__=='__main__':
    unittest.main()
