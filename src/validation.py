"""Controlli di coerenza dei dati dell'istanza di consegna."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


class InstanceError(ValueError):
    """Dati dell'istanza incompleti o non coerenti."""


def _number(value: Any, description: str, *, allow_zero: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InstanceError(f"{description}: è richiesto un valore numerico.")
    number = float(value)
    if not math.isfinite(number) or number < 0 or (not allow_zero and number == 0):
        raise InstanceError(f"{description}: valore non valido ({value!r}).")
    return number


def validate_instance(data: dict) -> None:
    """Valida l'istanza assegnata: un deposito, cinque clienti, due flotte."""
    if not isinstance(data, dict):
        raise InstanceError("Il file JSON deve contenere un oggetto.")
    try:
        locations = data["locations"]
        matrix = data["distance_km"]
        scenarios = data["fleet_scenarios"]
        operation = data["operation"]
    except KeyError as exc:
        raise InstanceError(f"Campo obbligatorio mancante: {exc.args[0]}") from exc

    if not isinstance(locations, list) or len(locations) != 6:
        raise InstanceError("La traccia richiede un deposito e cinque clienti.")
    if not isinstance(locations[0], dict) or locations[0].get("role") != "deposito":
        raise InstanceError("Il deposito deve occupare la prima posizione.")
    if any(not isinstance(x, dict) or x.get("role") != "cliente" for x in locations[1:]):
        raise InstanceError("Dopo il deposito devono essere presenti cinque clienti.")
    ids = [loc.get("id") for loc in locations]
    names = [loc.get("name") for loc in locations]
    if any(not isinstance(x, str) or not x.strip() for x in ids + names):
        raise InstanceError("Ogni nodo deve avere identificativo e nome.")
    if len(set(ids)) != 6 or len(set(names)) != 6:
        raise InstanceError("Gli identificativi e i nomi delle località devono essere univoci.")
    if not isinstance(matrix, list) or len(matrix) != 6 or any(
        not isinstance(row, list) or len(row) != 6 for row in matrix
    ):
        raise InstanceError("La matrice delle distanze deve avere dimensione 6×6.")

    for i in range(6):
        for j in range(6):
            value = _number(matrix[i][j], f"Distanza {names[i]} - {names[j]}")
            if i == j and abs(value) > 1e-9:
                raise InstanceError(f"La distanza di {names[i]} da sé stessa deve essere zero.")
            if i != j and value <= 0:
                raise InstanceError("La distanza tra località diverse deve essere positiva.")
            if abs(value - _number(matrix[j][i], "Distanza reciproca")) > 1e-9:
                raise InstanceError("La matrice dichiarata simmetrica non è simmetrica.")

    if _number(locations[0].get("demand_kg"), "Domanda del deposito") != 0:
        raise InstanceError("Il deposito non può avere una domanda di consegna.")
    demands = [_number(loc.get("demand_kg"), f"Domanda di {loc['name']}", allow_zero=False)
               for loc in locations[1:]]
    demand_total = sum(demands)
    if not isinstance(scenarios, dict) or not all(x in scenarios for x in ("A", "B")):
        raise InstanceError("Devono essere definiti gli scenari A e B.")
    for key, count in (("A", 1), ("B", 2)):
        s = scenarios[key]
        if not isinstance(s, dict) or s.get("vehicles") != count:
            raise InstanceError(f"Scenario {key}: numero di veicoli non valido.")
        for field in ("capacity_kg_per_vehicle", "fixed_cost_eur_per_vehicle_day", "variable_cost_eur_km"):
            _number(s.get(field), f"Scenario {key}: {field}", allow_zero=field != "capacity_kg_per_vehicle")
    big = scenarios["A"]["capacity_kg_per_vehicle"]
    small = scenarios["B"]["capacity_kg_per_vehicle"]
    if not (small < demand_total <= big and demand_total <= 2 * small):
        raise InstanceError("Le capacità non soddisfano i vincoli degli scenari della traccia.")
    if any(d > small for d in demands):
        raise InstanceError("Esiste una consegna troppo grande per un veicolo piccolo.")
    # Due mezzi sufficienti in totale non garantiscono sempre una partizione realizzabile.
    if not any(
        sum(demands[i] for i in range(5) if mask & (1 << i)) <= small
        and demand_total - sum(demands[i] for i in range(5) if mask & (1 << i)) <= small
        for mask in range(1, 2**5 - 1)
    ):
        raise InstanceError("Non esiste alcuna suddivisione ammissibile tra i due mezzi.")

    for field in ("speed_kmh_assumed", "service_minutes_per_customer", "driver_eur_hour"):
        _number(operation.get(field), field, allow_zero=field != "speed_kmh_assumed")
    for field in ("return_to_depot", "split_deliveries_allowed", "each_customer_visited_once"):
        if not isinstance(operation.get(field), bool):
            raise InstanceError(f"Campo {field}: è richiesto true/false.")
    if not operation["return_to_depot"] or operation["split_deliveries_allowed"] or not operation["each_customer_visited_once"]:
        raise InstanceError("L'applicativo richiede giri chiusi e consegne non frazionate.")


def validate_csv_consistency(data: dict, folder: Path) -> None:
    """Verifica che i due CSV principali coincidano con il JSON di riferimento."""
    matrix_path = folder / "matrice_distanze_km.csv"
    nodes_path = folder / "nodi_clienti.csv"
    if not matrix_path.is_file() or not nodes_path.is_file():
        raise InstanceError("Mancano i CSV dei nodi o delle distanze nella cartella dati.")
    with matrix_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    names = [loc["name"] for loc in data["locations"]]
    if len(rows) != len(names) + 1 or rows[0] != ["localita", *names]:
        raise InstanceError("Intestazioni o dimensioni del CSV delle distanze non corrispondenti.")
    for i, row in enumerate(rows[1:]):
        if len(row) != len(names) + 1 or row[0] != names[i]:
            raise InstanceError(f"CSV distanze: riga {i + 2} non coerente.")
        for j, text in enumerate(row[1:]):
            try:
                value = float(text)
            except ValueError as exc:
                raise InstanceError("Il CSV delle distanze contiene dati non numerici.") from exc
            if not math.isclose(value, float(data["distance_km"][i][j]), abs_tol=1e-9):
                raise InstanceError(f"Distanza diversa tra CSV e JSON: {names[i]} - {names[j]}.")
    with nodes_path.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_nodes = list(csv.DictReader(handle))
    if len(csv_nodes) != len(names):
        raise InstanceError("Numero di nodi diverso tra CSV e JSON.")
    for i, (row, loc) in enumerate(zip(csv_nodes, data["locations"])):
        if (row.get("id") != loc["id"] or row.get("localita") != loc["name"] or
                row.get("tipo") != loc["role"]):
            raise InstanceError(f"Nodo diverso tra CSV e JSON alla riga {i + 2}.")
        try:
            kg = float(row["quantita_kg"])
        except (ValueError, KeyError) as exc:
            raise InstanceError("Quantità non valida nel CSV dei nodi.") from exc
        if not math.isclose(kg, float(loc["demand_kg"]), abs_tol=1e-9):
            raise InstanceError(f"Quantità diversa tra CSV e JSON: {loc['name']}.")
