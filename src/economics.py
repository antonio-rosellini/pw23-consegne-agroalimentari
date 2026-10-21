"""Tempi di percorrenza, confronto economico e analisi di sensibilità."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def _rounded_euro(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def operating_hours(route: dict, operation: dict) -> float:
    """Ore di guida più tempo fisso di servizio per cliente."""
    return (route["distance_km"] / operation["speed_kmh_assumed"]
            + route["customers_served"] * operation["service_minutes_per_customer"] / 60.0)


def scenario_economics(routes: list[dict], scenario: dict, operation: dict,
                       *, km_price: float | None = None) -> dict:
    """Costo della flotta; le ore-autista si sommano, la durata è il massimo."""
    if len(routes) != scenario["vehicles"]:
        raise ValueError("Numero di percorsi non conforme alla flotta indicata.")
    if km_price is None:
        km_price = scenario["variable_cost_eur_km"]
    if km_price < 0:
        raise ValueError("Il costo chilometrico non può essere negativo.")
    km = sum(route["distance_km"] for route in routes)
    hours = [operating_hours(route, operation) for route in routes]
    fixed = scenario["vehicles"] * scenario["fixed_cost_eur_per_vehicle_day"]
    variable = km * km_price
    personnel = sum(hours) * operation["driver_eur_hour"]
    return {
        "vehicles": scenario["vehicles"],
        "total_distance_km": round(km, 6),
        "vehicle_hours": [round(x, 6) for x in hours],
        "total_driver_hours": round(sum(hours), 6),
        "completion_hours": round(max(hours), 6),
        "km_price_eur_km": round(km_price, 8),
        "fixed_eur": _rounded_euro(fixed),
        "distance_cost_eur": _rounded_euro(variable),
        "driver_cost_eur": _rounded_euro(personnel),
        # Il totale è calcolato sui valori non arrotondati.
        "total_eur": _rounded_euro(fixed + variable + personnel),
    }


def compare_scenarios(route_a: dict, routes_b: list[dict], data: dict) -> dict:
    cfg = data["fleet_scenarios"]
    op = data["operation"]
    a = scenario_economics([route_a], cfg["A"], op)
    b = scenario_economics(routes_b, cfg["B"], op)
    saving = round(b["total_eur"] - a["total_eur"], 2)
    winner = "A" if saving > 0 else ("B" if saving < 0 else "parità")
    return {
        "scenario_A": a,
        "scenario_B": b,
        "difference_B_minus_A_eur": saving,
        "less_expensive_scenario": winner,
        "distance_difference_B_minus_A_km": round(b["total_distance_km"] - a["total_distance_km"], 6),
        "completion_reduction_with_B_percent": round(
            (a["completion_hours"] - b["completion_hours"]) / a["completion_hours"] * 100, 4),
    }


def sensitivity_analysis(route_a: dict, routes_b: list[dict], data: dict) -> dict:
    """Varia il solo costo €/km del mezzo A, mantenendo invariato tutto il resto."""
    cfg = data["fleet_scenarios"]
    op = data["operation"]
    b = scenario_economics(routes_b, cfg["B"], op)
    distance_a = route_a["distance_km"]
    hours_a = operating_hours(route_a, op)
    fixed_a = cfg["A"]["fixed_cost_eur_per_vehicle_day"]
    # Costo di B non arrotondato: consente un pareggio matematico preciso.
    distance_b = sum(route["distance_km"] for route in routes_b)
    hours_b = sum(operating_hours(route, op) for route in routes_b)
    cost_b_exact = (cfg["B"]["vehicles"] * cfg["B"]["fixed_cost_eur_per_vehicle_day"]
                    + distance_b * cfg["B"]["variable_cost_eur_km"]
                    + hours_b * op["driver_eur_hour"])
    threshold = (cost_b_exact - fixed_a - hours_a * op["driver_eur_hour"]) / distance_a

    # 0,50..1,00 €/km a intervalli regolari, valore di base e pareggio.
    candidates = {round(k / 100, 8) for k in range(50, 101, 5)}
    candidates.add(round(cfg["A"]["variable_cost_eur_km"], 8))
    if threshold >= 0:
        candidates.add(round(threshold, 8))
    rows = []
    for p in sorted(candidates):
        cost_a = scenario_economics([route_a], cfg["A"], op, km_price=p)
        diff = round(b["total_eur"] - cost_a["total_eur"], 2)
        rows.append({
            "price_A_eur_km": p,
            "cost_A_eur": cost_a["total_eur"],
            "cost_B_eur": b["total_eur"],
            "difference_B_minus_A_eur": diff,
            "cheaper": "A" if diff > 0 else ("B" if diff < 0 else "parità"),
            "is_base_price": abs(p - cfg["A"]["variable_cost_eur_km"]) < 1e-8,
            "is_break_even_price": threshold >= 0 and abs(p - threshold) < 1e-6,
        })
    return {
        "parameter_varied": "Costo variabile chilometrico del veicolo A",
        "unit": "EUR/km",
        "base_price_eur_km": cfg["A"]["variable_cost_eur_km"],
        "break_even_price_eur_km": round(threshold, 6),
        "break_even_note": "Soglia teorica con costi non arrotondati; i costi a video sono espressi in centesimi.",
        "records": rows,
    }
