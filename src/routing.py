"""Ricerca esaustiva dei percorsi per TSP e CVRP con cinque clienti."""

from __future__ import annotations

from itertools import combinations, permutations


def route_distance(matrix: list[list[float]], order: tuple[int, ...]) -> float:
    """Somma in km le tratte deposito -> clienti -> deposito."""
    sequence = (0, *order, 0)
    return round(sum(matrix[a][b] for a, b in zip(sequence, sequence[1:])), 8)


def route_details(order: tuple[int, ...], data: dict) -> dict:
    locations = data["locations"]
    sequence = (0, *order, 0)
    return {
        "nodes": [locations[i]["id"] for i in sequence],
        "cities": [locations[i]["name"] for i in sequence],
        "customer_ids": [locations[i]["id"] for i in order],
        "distance_km": route_distance(data["distance_km"], order),
        "load_kg": sum(locations[i]["demand_kg"] for i in order),
        "customers_served": len(order),
    }


def solve_single_vehicle(data: dict) -> tuple[dict, list[dict]]:
    """Valuta tutte le 5! = 120 permutazioni dei clienti."""
    customer_ids = tuple(range(1, len(data["locations"])))
    evaluated = []
    for order in permutations(customer_ids):
        detail = route_details(order, data)
        evaluated.append(detail)
    best_distance = min(r["distance_km"] for r in evaluated)
    ties = [r for r in evaluated if abs(r["distance_km"] - best_distance) < 1e-8]
    # L'ordine canonico restituisce un risultato identico tra esecuzioni.
    best = min(ties, key=lambda r: tuple(r["customer_ids"]))
    return {
        "route": best,
        "minimum_distance_km": best_distance,
        "evaluated_routes": len(evaluated),
        "optimal_route_count": len(ties),
        "all_best_routes": [r["nodes"] for r in ties],
    }, evaluated


def feasible_partitions(data: dict):
    """Genera una sola volta ciascuna partizione A/B di mezzi indistinguibili."""
    customers = tuple(range(1, len(data["locations"])))
    capacity = data["fleet_scenarios"]["B"]["capacity_kg_per_vehicle"]
    demand = lambda indexes: sum(data["locations"][i]["demand_kg"] for i in indexes)
    for count in range(1, len(customers)):
        for first in combinations(customers, count):
            # Il primo cliente appartiene convenzionalmente al veicolo 1.
            if customers[0] not in first:
                continue
            second = tuple(i for i in customers if i not in first)
            if demand(first) <= capacity and demand(second) <= capacity:
                yield first, second


def solve_two_vehicles(data: dict) -> tuple[dict, list[dict], list[dict]]:
    """Enumera le partizioni ammissibili e tutti gli ordinamenti di ciascun giro."""
    all_candidates = []
    partitions_summary = []
    for first, second in feasible_partitions(data):
        best_in_partition = None
        count_in_partition = 0
        for order1 in permutations(first):
            detail1 = route_details(order1, data)
            for order2 in permutations(second):
                detail2 = route_details(order2, data)
                total = round(detail1["distance_km"] + detail2["distance_km"], 8)
                candidate = {
                    "vehicle_1": detail1,
                    "vehicle_2": detail2,
                    "total_distance_km": total,
                }
                all_candidates.append(candidate)
                count_in_partition += 1
                if (best_in_partition is None or total < best_in_partition["total_distance_km"] - 1e-8):
                    best_in_partition = candidate
        if best_in_partition is None:
            raise RuntimeError("Partizione vuota inattesa.")
        partitions_summary.append({
            "group_1": [data["locations"][i]["id"] for i in first],
            "group_2": [data["locations"][i]["id"] for i in second],
            "load_1_kg": best_in_partition["vehicle_1"]["load_kg"],
            "load_2_kg": best_in_partition["vehicle_2"]["load_kg"],
            "evaluated_route_pairs": count_in_partition,
            "minimum_distance_km": best_in_partition["total_distance_km"],
            "best_vehicle_1_route": best_in_partition["vehicle_1"]["nodes"],
            "best_vehicle_2_route": best_in_partition["vehicle_2"]["nodes"],
        })
    if not all_candidates:
        raise ValueError("Nessuna configurazione a due veicoli rispetta i vincoli.")
    best_distance = min(c["total_distance_km"] for c in all_candidates)
    ties = [c for c in all_candidates if abs(c["total_distance_km"] - best_distance) < 1e-8]
    best = min(ties, key=lambda c: (tuple(c["vehicle_1"]["customer_ids"]),
                                   tuple(c["vehicle_2"]["customer_ids"])))
    return {
        "routes": [best["vehicle_1"], best["vehicle_2"]],
        "minimum_distance_km": best_distance,
        "feasible_partitions": len(partitions_summary),
        "evaluated_route_pairs": len(all_candidates),
        "optimal_pair_count": len(ties),
        "all_best_route_pairs": [[c["vehicle_1"]["nodes"],
                                  c["vehicle_2"]["nodes"]] for c in ties],
    }, all_candidates, partitions_summary
