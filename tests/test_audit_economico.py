"""Controlli aggiuntivi, indipendenti dalle funzioni del progetto."""
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analisi.verifica_economica import audit

class TestVerificaEconomica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=audit()
    def test_01_distance_A(self):
        self.assertEqual(Decimal(self.result['routes']['A_km']),Decimal('85.6'))
    def test_02_distance_B(self):
        self.assertEqual(Decimal(self.result['routes']['B_total_km']),Decimal('88.6'))
    def test_03_enumeration(self):
        self.assertEqual(self.result['counts']['labelled_route_pairs'],120)
        self.assertEqual(self.result['counts']['unlabelled_route_pairs'],60)
    def test_04_economic_delta(self):
        self.assertEqual(Decimal(self.result['costs_rounded_eur']['B_minus_A']),Decimal('0.99'))
    def test_05_break_even_prices(self):
        self.assertAlmostEqual(float(self.result['break_even']['A_km_price_eur_km']),0.7315576324,places=9)
        self.assertAlmostEqual(float(self.result['break_even']['A_rent_price_eur_day']),120.9893333,places=6)
    def test_06_parallel_completion(self):
        self.assertLess(Decimal(self.result['completion_hours']['B']),Decimal(self.result['completion_hours']['A']))

if __name__=='__main__': unittest.main()
