"""Test dell'istanza, dell'enumerazione e della produzione dei risultati."""

from __future__ import annotations

import copy
import csv
import itertools
import json
import math
import tempfile
import unittest
from pathlib import Path

from src.economics import compare_scenarios, operating_hours, scenario_economics, sensitivity_analysis
from src.main import run_project
from src.routing import feasible_partitions, route_distance, solve_single_vehicle, solve_two_vehicles
from src.validation import InstanceError, validate_csv_consistency, validate_instance

ROOT = Path(__file__).resolve().parents[1]


class TestProjectWork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input = ROOT / "data" / "istanza.json"
        cls.data = json.loads(cls.input.read_text(encoding="utf-8"))
        cls.single, cls.single_candidates = solve_single_vehicle(cls.data)
        cls.double, cls.double_candidates, cls.partitions = solve_two_vehicles(cls.data)

    def test_01_instance_valid(self):
        validate_instance(self.data)
        validate_csv_consistency(self.data, ROOT / "data")

    def test_02_customer_count_and_demand(self):
        self.assertEqual(len(self.data["locations"]), 6)
        self.assertEqual(sum(x["demand_kg"] for x in self.data["locations"]), 1000)
        self.assertLessEqual(1000, self.data["fleet_scenarios"]["A"]["capacity_kg_per_vehicle"])
        self.assertGreater(1000, self.data["fleet_scenarios"]["B"]["capacity_kg_per_vehicle"])

    def test_03_120_single_vehicle_orders(self):
        self.assertEqual(self.single["evaluated_routes"], math.factorial(5))
        self.assertEqual(len(self.single_candidates), 120)
        self.assertEqual(len(set(tuple(x["customer_ids"]) for x in self.single_candidates)), 120)

    def test_04_single_route_global_minimum(self):
        self.assertAlmostEqual(self.single["minimum_distance_km"], 85.6)
        self.assertEqual(self.single["route"]["nodes"],
                         ["D", "C2", "C1", "C3", "C4", "C5", "D"])
        self.assertEqual(self.single["optimal_route_count"], 2)
        self.assertTrue(all(r["distance_km"] >= 85.6 for r in self.single_candidates))

    def test_05_reverse_route_same_length(self):
        route = (2, 1, 3, 4, 5)
        self.assertAlmostEqual(route_distance(self.data["distance_km"], route),
                               route_distance(self.data["distance_km"], route[::-1]))

    def test_06_two_vehicles_5_partitions_60_pairs(self):
        self.assertEqual(len(list(feasible_partitions(self.data))), 5)
        self.assertEqual(self.double["feasible_partitions"], 5)
        self.assertEqual(self.double["evaluated_route_pairs"], 60)
        self.assertEqual(sum(x["evaluated_route_pairs"] for x in self.partitions), 60)
        self.assertEqual(len(self.double_candidates), 60)

    def test_07_two_vehicles_optimum(self):
        self.assertAlmostEqual(self.double["minimum_distance_km"], 88.6)
        self.assertEqual(self.double["optimal_pair_count"], 4)
        routes = self.double["routes"]
        self.assertEqual([r["distance_km"] for r in routes], [37.0, 51.6])
        self.assertEqual([r["load_kg"] for r in routes], [400, 600])

    def test_08_all_candidates_respect_constraints(self):
        customers = set(range(1, 6))
        names_to_index = {loc["id"]: i for i, loc in enumerate(self.data["locations"])}
        for candidate in self.double_candidates:
            a = {names_to_index[c] for c in candidate["vehicle_1"]["customer_ids"]}
            b = {names_to_index[c] for c in candidate["vehicle_2"]["customer_ids"]}
            self.assertFalse(a & b)
            self.assertEqual(a | b, customers)
            self.assertLessEqual(candidate["vehicle_1"]["load_kg"], 600)
            self.assertLessEqual(candidate["vehicle_2"]["load_kg"], 600)
            self.assertEqual(candidate["vehicle_1"]["nodes"][0], "D")
            self.assertEqual(candidate["vehicle_2"]["nodes"][-1], "D")

    def test_09_independent_exhaustive_check(self):
        """Secondo enumeratore, indipendente dalle funzioni del programma."""
        mat = self.data["distance_km"]
        quantity = [loc["demand_kg"] for loc in self.data["locations"]]
        brute_single = min(sum(mat[u][v] for u, v in zip((0, *p), (*p, 0)))
                           for p in itertools.permutations((1, 2, 3, 4, 5)))
        brute_two = float("inf")
        valid_labeled = 0
        for assignment in itertools.product((0, 1), repeat=5):
            left = [i + 1 for i, owner in enumerate(assignment) if owner == 0]
            right = [i + 1 for i, owner in enumerate(assignment) if owner == 1]
            if not left or not right:
                continue
            if sum(quantity[i] for i in left) > 600 or sum(quantity[i] for i in right) > 600:
                continue
            valid_labeled += 1
            for order_l in itertools.permutations(left):
                for order_r in itertools.permutations(right):
                    score = sum(mat[u][v] for u, v in zip((0, *order_l), (*order_l, 0)))
                    score += sum(mat[u][v] for u, v in zip((0, *order_r), (*order_r, 0)))
                    brute_two = min(brute_two, score)
        self.assertEqual(valid_labeled, 10)
        self.assertAlmostEqual(brute_single, self.single["minimum_distance_km"])
        self.assertAlmostEqual(brute_two, self.double["minimum_distance_km"])

    def test_10_hours_sum_vs_parallel_completion(self):
        op = self.data["operation"]
        a_time = operating_hours(self.single["route"], op)
        routes = self.double["routes"]
        two_times = [operating_hours(x, op) for x in routes]
        self.assertAlmostEqual(a_time, 85.6 / 45 + 5 * 0.25)
        self.assertAlmostEqual(sum(two_times), 88.6 / 45 + 5 * 0.25)
        self.assertAlmostEqual(max(two_times), 51.6 / 45 + 3 * 0.25)
        self.assertLess(max(two_times), a_time)

    def test_11_costs_and_winner(self):
        c = compare_scenarios(self.single["route"], self.double["routes"], self.data)
        self.assertAlmostEqual(c["scenario_A"]["total_eur"], 239.95)
        self.assertAlmostEqual(c["scenario_B"]["total_eur"], 240.94)
        self.assertAlmostEqual(c["difference_B_minus_A_eur"], 0.99)
        self.assertEqual(c["less_expensive_scenario"], "A")

    def test_12_break_even_and_sensitivity(self):
        sensitivity = sensitivity_analysis(self.single["route"], self.double["routes"], self.data)
        threshold = sensitivity["break_even_price_eur_km"]
        self.assertAlmostEqual(threshold, 0.731558, places=6)
        cfg = self.data["fleet_scenarios"]
        op = self.data["operation"]
        total_b = scenario_economics(self.double["routes"], cfg["B"], op)["total_eur"]
        cheaper_a = scenario_economics([self.single["route"]], cfg["A"], op,
                                       km_price=threshold - 0.1)["total_eur"]
        cheaper_b = scenario_economics([self.single["route"]], cfg["A"], op,
                                       km_price=threshold + 0.1)["total_eur"]
        self.assertLess(cheaper_a, total_b)
        self.assertGreater(cheaper_b, total_b)
        self.assertTrue(any(row["is_base_price"] for row in sensitivity["records"]))
        self.assertTrue(any(row["is_break_even_price"] for row in sensitivity["records"]))

    def test_13_modified_data_detected(self):
        modified = copy.deepcopy(self.data)
        modified["distance_km"][1][2] += 1
        with self.assertRaises(InstanceError):
            validate_instance(modified)
        modified = copy.deepcopy(self.data)
        modified["distance_km"][1][2] += 1
        modified["distance_km"][2][1] += 1
        validate_instance(modified)
        with self.assertRaises(InstanceError):
            validate_csv_consistency(modified, ROOT / "data")

    def test_14_invalid_capacity_detected(self):
        modified = copy.deepcopy(self.data)
        modified["fleet_scenarios"]["B"]["capacity_kg_per_vehicle"] = 450
        with self.assertRaises(InstanceError):
            validate_instance(modified)

    def test_15_zero_edge_detected(self):
        modified = copy.deepcopy(self.data)
        modified["distance_km"][1][2] = 0
        modified["distance_km"][2][1] = 0
        with self.assertRaises(InstanceError):
            validate_instance(modified)

    def test_16_export_and_content(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            result = run_project(self.input, folder)
            self.assertEqual(len(list(folder.glob("*.csv"))), 4)
            for name in ("risultati.json", "riepilogo.txt", "soluzioni_tsp.csv",
                         "soluzioni_due_veicoli.csv", "partizioni_ammissibili.csv",
                         "analisi_sensibilita.csv"):
                self.assertTrue((folder / name).is_file(), name)
            self.assertEqual(json.loads((folder / "risultati.json").read_text(encoding="utf-8")), result)
            with (folder / "soluzioni_tsp.csv").open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(sum(1 for _ in csv.DictReader(f)), 120)
            with (folder / "soluzioni_due_veicoli.csv").open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(sum(1 for _ in csv.DictReader(f)), 60)

    def test_17_reproducibility(self):
        with tempfile.TemporaryDirectory() as temp:
            folder1 = Path(temp) / "one"
            folder2 = Path(temp) / "two"
            run_project(self.input, folder1)
            run_project(self.input, folder2)
            self.assertEqual((folder1 / "risultati.json").read_bytes(),
                             (folder2 / "risultati.json").read_bytes())
            self.assertEqual((folder1 / "analisi_sensibilita.csv").read_bytes(),
                             (folder2 / "analisi_sensibilita.csv").read_bytes())

    def test_18_road_triangle_inequality_not_assumed(self):
        matrix = self.data["distance_km"]
        # La matrice normalizzata può violare la disuguaglianza triangolare.
        self.assertGreater(matrix[2][3], matrix[2][1] + matrix[1][3])
        self.assertEqual(self.single["evaluated_routes"], 120)


if __name__ == "__main__":
    unittest.main()
