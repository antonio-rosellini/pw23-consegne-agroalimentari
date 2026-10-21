"""Pianificazione delle consegne di Adriatica Fresco Distribuzione.

Avvio dalla cartella principale: python src/main.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.economics import compare_scenarios, sensitivity_analysis
from src.routing import solve_single_vehicle, solve_two_vehicles
from src.validation import InstanceError, validate_csv_consistency, validate_instance

ROOT = Path(__file__).resolve().parents[1]


def save_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def run_project(input_path: Path, output_folder: Path) -> dict:
    """Carica l'istanza, effettua la ricerca esaustiva e scrive i risultati."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    validate_instance(data)
    validate_csv_consistency(data, input_path.parent)

    single, evaluated_single = solve_single_vehicle(data)
    two, evaluated_two, partitions = solve_two_vehicles(data)
    economics = compare_scenarios(single["route"], two["routes"], data)
    sensitivity = sensitivity_analysis(single["route"], two["routes"], data)

    # Controllo difensivo dei risultati selezionati.
    ids = {loc["id"] for loc in data["locations"][1:]}
    assert set(single["route"]["customer_ids"]) == ids
    assert sum(route["load_kg"] for route in two["routes"]) == sum(
        loc["demand_kg"] for loc in data["locations"][1:])
    assert set(two["routes"][0]["customer_ids"]).isdisjoint(two["routes"][1]["customer_ids"])
    assert set(two["routes"][0]["customer_ids"] + two["routes"][1]["customer_ids"]) == ids
    assert all(route["load_kg"] <= data["fleet_scenarios"]["B"]["capacity_kg_per_vehicle"]
               for route in two["routes"])

    result = {
        "project": data["project_id"],
        "student": data["student"],
        "case_study": data["case_study"],
        "instance_reference_date": data["reference_date"],
        "input_distance_method": data["distance_matrix_method"],
        "input_distance_status": data["distance_data_status"],
        "nodes": data["locations"],
        "distance_km": data["distance_km"],
        "fleet_scenarios": data["fleet_scenarios"],
        "operation": data["operation"],
        "optimization_objective": "Distanza complessiva minima (non costo minimo)",
        "single_vehicle": single,
        "two_vehicles": two,
        "economic_comparison": economics,
        "sensitivity": sensitivity,
        "notes": [
            "Le distanze sono stime stradali normalizzate riferite ai centri comunali.",
            "Noleggi, costi chilometrici e velocità sono ipotesi didattiche.",
            "Gli itinerari non considerano traffico in tempo reale, vincoli orari o pedaggi separati.",
            "I percorsi sono ottimi rispetto alla matrice fornita; non rappresentano itinerari verificati in strada.",
        ],
    }

    output_folder.mkdir(parents=True, exist_ok=True)
    (output_folder / "risultati.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    save_csv(output_folder / "soluzioni_tsp.csv",
             ["ordine", "percorso", "distanza_km", "carico_kg"], [
                 [i, " -> ".join(x["cities"]), x["distance_km"], x["load_kg"]]
                 for i, x in enumerate(evaluated_single, 1)])
    save_csv(output_folder / "soluzioni_due_veicoli.csv",
             ["ordine", "percorso_veicolo_1", "percorso_veicolo_2", "carico_1_kg",
              "carico_2_kg", "distanza_1_km", "distanza_2_km", "distanza_totale_km"], [
                 [i, " -> ".join(x["vehicle_1"]["cities"]),
                  " -> ".join(x["vehicle_2"]["cities"]),
                  x["vehicle_1"]["load_kg"], x["vehicle_2"]["load_kg"],
                  x["vehicle_1"]["distance_km"], x["vehicle_2"]["distance_km"],
                  x["total_distance_km"]]
                 for i, x in enumerate(evaluated_two, 1)])
    save_csv(output_folder / "partizioni_ammissibili.csv",
             ["gruppo_1", "gruppo_2", "carico_1_kg", "carico_2_kg",
              "coppie_percorsi_esaminate", "distanza_minima_km", "miglior_giro_1", "miglior_giro_2"], [
                 [" ".join(x["group_1"]), " ".join(x["group_2"]),
                  x["load_1_kg"], x["load_2_kg"], x["evaluated_route_pairs"],
                  x["minimum_distance_km"], " ".join(x["best_vehicle_1_route"]),
                  " ".join(x["best_vehicle_2_route"])] for x in partitions])
    save_csv(output_folder / "analisi_sensibilita.csv",
             ["costo_chilometrico_A_eur_km", "costo_totale_A_eur", "costo_totale_B_eur",
              "differenza_B_meno_A_eur", "configurazione_conveniente", "prezzo_base", "pareggio"], [
                 [row["price_A_eur_km"], row["cost_A_eur"], row["cost_B_eur"],
                  row["difference_B_minus_A_eur"], row["cheaper"],
                  row["is_base_price"], row["is_break_even_price"]]
                 for row in sensitivity["records"]])

    summary = format_summary(result)
    (output_folder / "riepilogo.txt").write_text(summary + "\n", encoding="utf-8")
    return result


def format_summary(result: dict) -> str:
    a = result["single_vehicle"]
    b = result["two_vehicles"]
    econ = result["economic_comparison"]
    ea = econ["scenario_A"]
    eb = econ["scenario_B"]
    route_a = " -> ".join(a["route"]["cities"])
    routes_b = [" -> ".join(r["cities"]) for r in b["routes"]]
    return "\n".join([
        "PIANIFICAZIONE DELLE CONSEGNE - BARI",
        "Adriatica Fresco Distribuzione S.r.l. (caso simulato)",
        "",
        "Scenario A - un veicolo refrigerato (1.100 kg)",
        f"  Percorso: {route_a}",
        f"  Distanza: {a['minimum_distance_km']:.1f} km | carico: {a['route']['load_kg']:.0f} kg",
        f"  Percorsi valutati: {a['evaluated_routes']}; ottimi equivalenti: {a['optimal_route_count']}",
        f"  Ore operative: {ea['completion_hours']:.2f} | costo: {ea['total_eur']:.2f} EUR",
        "",
        "Scenario B - due veicoli identici (600 kg ciascuno)",
        f"  Veicolo 1: {routes_b[0]} | {b['routes'][0]['distance_km']:.1f} km | {b['routes'][0]['load_kg']:.0f} kg",
        f"  Veicolo 2: {routes_b[1]} | {b['routes'][1]['distance_km']:.1f} km | {b['routes'][1]['load_kg']:.0f} kg",
        f"  Distanza totale: {b['minimum_distance_km']:.1f} km",
        f"  Partizioni valide: {b['feasible_partitions']}; coppie di itinerari valutate: {b['evaluated_route_pairs']}",
        f"  Ore-autista: {eb['total_driver_hours']:.2f} | completamento: {eb['completion_hours']:.2f} ore",
        f"  Costo: {eb['total_eur']:.2f} EUR",
        "",
        f"Differenza B - A: {econ['difference_B_minus_A_eur']:.2f} EUR",
        f"Scenario meno costoso ai parametri di base: {econ['less_expensive_scenario']}",
        f"Punto di pareggio al variare del costo chilometrico del veicolo A: "
        f"{result['sensitivity']['break_even_price_eur_km']:.6f} EUR/km",
        "",
        "Distanze derivate da stime pubbliche dei centri comunali; costi e velocità sono ipotesi di studio.",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description="Enumerazione dei percorsi e confronto economico.")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "istanza.json",
                        help="Percorso al file JSON dei dati (default: data/istanza.json)")
    parser.add_argument("--output", type=Path, default=ROOT / "output",
                        help="Cartella destinata ai risultati (default: output/)")
    args = parser.parse_args()
    try:
        result = run_project(args.input, args.output)
    except (InstanceError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1
    print(format_summary(result))
    print(f"\nFile di risultato salvati in: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
