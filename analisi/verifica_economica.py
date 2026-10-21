"""Verifica indipendente dei percorsi e dei costi di distribuzione.

Eseguire dalla cartella principale: python analisi/verifica_economica.py
Non usa i moduli dell'algoritmo principale.
"""
from __future__ import annotations
import csv
import json
import itertools
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "istanza.json"
OUT = BASE / "analisi" / "output"


def dec(value):
    return Decimal(str(value))


def euros(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def validate(cond, message):
    if not cond:
        raise AssertionError(message)


def audit():
    config = json.loads(DATA.read_text(encoding="utf-8"))
    recorded = json.loads((BASE / "output" / "risultati.json").read_text(encoding="utf-8"))
    mat = [[dec(x) for x in line] for line in config["distance_km"]]
    loc = config["locations"]
    qty = [dec(x["demand_kg"]) for x in loc]
    customers = tuple(range(1, 6))
    cap = dec(config["fleet_scenarios"]["B"]["capacity_kg_per_vehicle"])

    def length(order):
        nodes = (0, *order, 0)
        return sum((mat[nodes[i]][nodes[i+1]] for i in range(len(nodes)-1)), Decimal(0))

    # Ricerca indipendente: tutte le permutazioni per un mezzo.
    sequences = [(length(order), order) for order in itertools.permutations(customers)]
    best_a = min(x[0] for x in sequences)
    count_best_a = sum(distance == best_a for distance, _ in sequences)

    # Ricerca indipendente per due mezzi: assegnazioni binarie etichettate.
    valid_assignments = 0
    pairs = []
    for assign in itertools.product((0, 1), repeat=5):
        g1 = tuple(i for i, who in zip(customers, assign) if who == 0)
        g2 = tuple(i for i, who in zip(customers, assign) if who == 1)
        if not g1 or not g2 or sum(qty[i] for i in g1) > cap or sum(qty[i] for i in g2) > cap:
            continue
        valid_assignments += 1
        for p1 in itertools.permutations(g1):
            for p2 in itertools.permutations(g2):
                pairs.append((length(p1) + length(p2), p1, p2))
    best_b = min(x[0] for x in pairs)
    count_best_b_labelled = sum(dist == best_b for dist, _, _ in pairs)
    validate(best_a == dec(recorded["single_vehicle"]["minimum_distance_km"]), "Minimo del veicolo A non coincidente")
    validate(best_b == dec(recorded["two_vehicles"]["minimum_distance_km"]), "Minimo della flotta B non coincidente")
    validate(len(sequences) == 120 and valid_assignments == 10 and len(pairs) == 120,
             "Conteggi non corretti nell'enumerazione indipendente")
    validate(count_best_a == recorded["single_vehicle"]["optimal_route_count"] == 2,
             "Molteplicità dell'ottimo A inattesa")
    validate(count_best_b_labelled == 2 * recorded["two_vehicles"]["optimal_pair_count"] == 8,
             "Molteplicità dell'ottimo B inattesa")

    op = config["operation"]
    speed = dec(op["speed_kmh_assumed"])
    per_client = dec(op["service_minutes_per_customer"]) / dec(60)
    salary = dec(op["driver_eur_hour"])
    a_cfg, b_cfg = config["fleet_scenarios"]["A"], config["fleet_scenarios"]["B"]
    routes_b = recorded["two_vehicles"]["routes"]
    validate(sum(dec(r["load_kg"]) for r in routes_b) == 1000,
             "Somma dei carichi diversa da 1000 kg")
    validate(all(dec(r["load_kg"]) <= cap for r in routes_b), "Capacità dei due mezzi non rispettata")
    route_b_distance = [dec(r["distance_km"]) for r in routes_b]
    route_b_customers = [int(r["customers_served"]) for r in routes_b]
    validate(sum(route_b_distance) == best_b and sum(route_b_customers) == 5,
             "Somma dei giri B o clienti diversa dall'atteso")
    total_hours_a = best_a/speed + dec(5)*per_client
    each_hours_b = [dist/speed + dec(count)*per_client
                    for dist, count in zip(route_b_distance, route_b_customers)]
    total_hours_b = sum(each_hours_b)
    completion_b = max(each_hours_b)
    completion_a = total_hours_a

    fixed_a = dec(a_cfg["fixed_cost_eur_per_vehicle_day"])
    fixed_b = dec(b_cfg["fixed_cost_eur_per_vehicle_day"]) * dec(2)
    km_a = dec(a_cfg["variable_cost_eur_km"])
    km_b = dec(b_cfg["variable_cost_eur_km"])
    variable_a = best_a*km_a
    variable_b = best_b*km_b
    labour_a = total_hours_a*salary
    labour_b = total_hours_b*salary
    base_a = fixed_a + variable_a + labour_a
    base_b = fixed_b + variable_b + labour_b
    delta = base_b - base_a
    price_threshold = (base_b - fixed_a - labour_a) / best_a
    fixed_threshold = base_b - variable_a - labour_a

    for k, expected in [
        ("scenario_A", euros(base_a)),
        ("scenario_B", euros(base_b)),
    ]:
        validate(euros(dec(recorded["economic_comparison"][k]["total_eur"])) == expected,
                 "Costo pubblicato non coincidente per " + k)
    validate(euros(delta) == dec(recorded["economic_comparison"]["difference_B_minus_A_eur"]),
             "Differenza monetaria pubblicata non coincidente")
    validate(abs(price_threshold-dec(recorded["sensitivity"]["break_even_price_eur_km"])) < dec("0.000001"),
             "Punto di pareggio pubblicato non coincidente")
    validate(completion_b < completion_a, "I giri paralleli non riducono i tempi")

    rows_prices = []
    prices = [dec(x) for x in ("0.50", "0.60", "0.65", "0.70", "0.72", "0.73", "0.74", "0.75", "0.80", "0.90", "1.00")]
    prices.append(price_threshold)
    for price in sorted(prices):
        ca = fixed_a + price*best_a + labour_a
        diff = base_b - ca
        classification = "A" if diff > 0 else "B" if diff < 0 else "parita"
        if abs(price-price_threshold) < dec("0.000000000001"):
            classification = "pareggio teorico"
        rows_prices.append({
            "prezzo_A_eur_km": str(price.quantize(dec("0.000001"))),
            "costo_A_eur": str(euros(ca)),
            "costo_B_eur": str(euros(base_b)),
            "differenza_B_meno_A_eur": str(euros(diff)),
            "scelta_conveniente": classification,
        })
    rows_rent = []
    rents = [dec(x) for x in ("95", "105", "115", "120", "121", "125", "130", "140")]
    rents.append(fixed_threshold)
    for rent in sorted(rents):
        ca = rent + variable_a + labour_a
        diff = base_b-ca
        classification = "A" if diff>0 else "B" if diff<0 else "parita"
        if abs(rent-fixed_threshold) < dec("0.000000000001"):
            classification = "pareggio teorico"
        rows_rent.append({
            "noleggio_A_eur_giorno": str(rent.quantize(dec("0.000001"))),
            "costo_A_eur": str(euros(ca)),
            "costo_B_eur": str(euros(base_b)),
            "differenza_B_meno_A_eur": str(euros(diff)),
            "scelta_conveniente": classification,
        })

    # Verifica esaustiva delle cinque partizioni secondo codifica canonica C1 nel primo gruppo.
    canon = {}
    for dist, p1, p2 in pairs:
        # Etichette invertibili: porta C1 nel gruppo 1.
        if 1 not in p1: p1, p2 = p2, p1
        groups = (tuple(sorted(p1)), tuple(sorted(p2)))
        canon[groups] = min(canon.get(groups, dist), dist)
    partition_rows = []
    for (g1,g2), distance in sorted(canon.items(), key=lambda x: (x[1], x[0])):
        partition_rows.append({
            "gruppo_1": "-".join(loc[i]["name"] for i in g1),
            "gruppo_2": "-".join(loc[i]["name"] for i in g2),
            "carico_1_kg": str(sum(qty[i] for i in g1)),
            "carico_2_kg": str(sum(qty[i] for i in g2)),
            "distanza_minima_km": str(distance),
        })
    validate(len(partition_rows) == 5, "Il numero delle partizioni canoniche non è cinque")

    report = {
        "student": config["student"],
        "case_study": config["case_study"]["company"],
        "distances_are_estimates": True,
        "source_dataset": "data/istanza.json",
        "verified_against": "output/risultati.json",
        "counts": {"tsp_orders":len(sequences), "labelled_feasible_assignments":valid_assignments,
                   "labelled_route_pairs":len(pairs), "unlabelled_feasible_assignments":len(partition_rows),
                   "unlabelled_route_pairs": len(pairs)//2,
                   "tied_optimal_tsp_routes":count_best_a,
                   "tied_optimal_labelled_route_pairs":count_best_b_labelled},
        "costs_exact_eur": {"A":str(base_a),"B":str(base_b),"B_minus_A":str(delta),
                            "A_fixed":str(fixed_a),"A_km":str(variable_a),"A_driver":str(labour_a),
                            "B_fixed":str(fixed_b),"B_km":str(variable_b),"B_driver":str(labour_b)},
        "costs_rounded_eur": {"A":str(euros(base_a)),"B":str(euros(base_b)),"B_minus_A":str(euros(delta))},
        "routes": {"A_km":str(best_a),"B_total_km":str(best_b),
                   "B_vehicle_km":[str(v) for v in route_b_distance]},
        "driver_hours": {"A":str(total_hours_a),"B_total":str(total_hours_b),
                         "B_each": [str(h) for h in each_hours_b]},
        "completion_hours": {"A":str(completion_a),"B":str(completion_b),
                             "reduction_pct":str((completion_a-completion_b)/completion_a*100)},
        "break_even": {"A_km_price_eur_km":str(price_threshold),
                       "A_rent_price_eur_day":str(fixed_threshold)},
        "limitations": ["Distanze stradali stimate e simmetrizzate, non tratte geocodificate certificate",
                        "Ipotesi di velocita media costante, servizi fissi e costi unitari ipotetici",
                        "I due veicoli partono nello stesso istante per il confronto dei tempi"],
    }
    OUT.mkdir(exist_ok=True, parents=True)
    (OUT/"verifica_indipendente.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for filename, rows in (("sensibilita_prezzo_A.csv",rows_prices),
                           ("sensibilita_noleggio_A.csv",rows_rent),
                           ("minimi_per_partizione.csv",partition_rows)):
        with (OUT/filename).open("w",encoding="utf-8-sig",newline="") as fd:
            writer=csv.DictWriter(fd,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    costs_rows = [
        {"voce":"Noleggio giornaliero","scenario_A_eur":str(euros(fixed_a)),"scenario_B_eur":str(euros(fixed_b))},
        {"voce":"Costo dei chilometri","scenario_A_eur":str(euros(variable_a)),"scenario_B_eur":str(euros(variable_b))},
        {"voce":"Personale","scenario_A_eur":str(euros(labour_a)),"scenario_B_eur":str(euros(labour_b))},
        {"voce":"TOTALE","scenario_A_eur":str(euros(base_a)),"scenario_B_eur":str(euros(base_b))},
    ]
    with (OUT/"componenti_di_costo.csv").open("w",encoding="utf-8-sig",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=list(costs_rows[0]));writer.writeheader();writer.writerows(costs_rows)
    print("Verifica indipendente completata:")
    print("- TSP: 120 ordini, minimo",best_a,"km")
    print("- Due veicoli: 10 assegnazioni etichettate, 120 coppie; minimo",best_b,"km")
    print("- Costi:",euros(base_a),"EUR (A);",euros(base_b),"EUR (B)")
    print("- Prezzo di pareggio A:",price_threshold,"EUR/km")
    print("- Noleggio di pareggio A:",fixed_threshold,"EUR/giorno")
    return report

if __name__ == "__main__":
    audit()
