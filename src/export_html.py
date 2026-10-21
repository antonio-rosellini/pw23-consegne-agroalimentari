"""Creazione della pagina web a partire dai risultati del programma di routing.

Avvio dalla cartella del progetto: python src/export_html.py
Funziona con la sola libreria standard di Python.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"D": "Bari", "C1": "Modugno", "C2": "Bitonto", "C3": "Triggiano", "C4": "Noicattaro", "C5": "Mola di Bari"}


def txt(s: object) -> str:
    return html.escape(str(s), quote=True)


def km(value: float) -> str:
    return f"{value:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def euro(value: float) -> str:
    return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') + ' €'


def integer_it(value: float) -> str:
    return f'{value:,.0f}'.replace(',', '.')


def hour_minutes(hours: float) -> str:
    minutes = round(hours * 60)
    return f"{minutes // 60} h {minutes % 60:02d} min"


def number_it(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".replace('.', ',')


def svg_map(nodes: list[dict], routes: list[dict], palette: list[str], suffix: str) -> str:
    # Proiezione affine delle coordinate dei centri comunali; gli archi sono segmenti illustrativi.
    min_lon, max_lon = min(n['lon'] for n in nodes), max(n['lon'] for n in nodes)
    min_lat, max_lat = min(n['lat'] for n in nodes), max(n['lat'] for n in nodes)
    pt = {n['id']: (
        95 + (n['lon'] - min_lon) / (max_lon - min_lon) * 700,
        74 + (max_lat - n['lat']) / (max_lat - min_lat) * 268
    ) for n in nodes}
    svg = ['<svg class="route-svg" viewBox="0 0 900 423" role="img" aria-label="' +
           txt('Schema dei percorsi dello scenario '+('A' if len(routes)==1 else 'B')) + '" xmlns="http://www.w3.org/2000/svg">',
           '<defs>']
    for i, color in enumerate(palette):
        svg.append(f'<marker id="arrow-{suffix}-{i}" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="{color}"/></marker>')
    svg.append('</defs><rect x="0" y="0" width="900" height="423" rx="16" fill="#f9fbfd"/>')
    for x in range(95, 860, 95):
        svg.append(f'<line x1="{x}" y1="40" x2="{x}" y2="377" stroke="#e7edf4" stroke-width="1"/>')
    for y in range(67, 380, 62):
        svg.append(f'<line x1="53" y1="{y}" x2="849" y2="{y}" stroke="#e7edf4" stroke-width="1"/>')
    # Sotto i nodi: archi nel loro ordine di percorrenza.
    for i, (route, color) in enumerate(zip(routes, palette)):
        points=route['nodes']
        for u,v in zip(points, points[1:]):
            x1,y1=pt[u];x2,y2=pt[v]
            dx=x2-x1;dy=y2-y1; d=math.hypot(dx,dy)
            if not d: continue
            # Offset per i due mezzi, per distinguere archi condivisi e partenza dal deposito.
            orth_x,orth_y=-dy/d* (3 if i==0 else -3), dx/d*(3 if i==0 else -3)
            a,b=x1+orth_x+dx/d*17,y1+orth_y+dy/d*17
            c,e=x2+orth_x-dx/d*19,y2+orth_y-dy/d*19
            svg.append(f'<path d="M{a:.1f},{b:.1f} L{c:.1f},{e:.1f}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round" marker-end="url(#arrow-{suffix}-{i})"/>')
    offsets = {'D':(-8,-23),'C1':(13,26),'C2':(-8,-24),'C3':(-16,-23),'C4':(-20,29),'C5':(-10,-23)}
    for n in nodes:
        x,y=pt[n['id']]
        depot=n['id']=='D'
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{14 if depot else 10}" fill="{("#173c65" if depot else "#fff")}" stroke="{("#173c65" if depot else "#64748b")}" stroke-width="{3 if depot else 2}"/>')
        if depot:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff"/>')
        ox,oy=offsets[n['id']]
        anchor='end' if ox<0 else 'start'
        svg.append(f'<text x="{x+ox:.1f}" y="{y+oy:.1f}" text-anchor="{anchor}" font-size="15" font-family="Arial, sans-serif" font-weight="{700 if depot else 600}" fill="#20334c">{txt(n["name"])}</text>')
    svg.append('<text x="24" y="407" font-size="12" fill="#718096" font-family="Arial, sans-serif">Coordinate comunali indicative · archi rettilinei illustrativi, non itinerari stradali</text></svg>')
    return ''.join(svg)


def svg_sensitivity(result:dict) -> str:
    econ=result['economic_comparison']; cfg=result['fleet_scenarios']; operation=result['operation']
    dist=econ['scenario_A']['total_distance_km']
    a_fixed=cfg['A']['fixed_cost_eur_per_vehicle_day']
    h=dist/operation['speed_kmh_assumed'] + 5*operation['service_minutes_per_customer']/60
    intercept=a_fixed+h*operation['driver_eur_hour']
    b_cost=(cfg['B']['vehicles']*cfg['B']['fixed_cost_eur_per_vehicle_day'] + econ['scenario_B']['total_distance_km']*cfg['B']['variable_cost_eur_km'] + econ['scenario_B']['total_driver_hours']*operation['driver_eur_hour'])
    xlo,xhi=.5,1.0
    ylo,yhi=216,268
    def x(v): return 68+(v-xlo)/(xhi-xlo)*788
    def y(v): return 292-(v-ylo)/(yhi-ylo)*251
    out=['<svg id="price-chart" class="chart-svg" viewBox="0 0 930 360" role="img" aria-label="Grafico dei costi per lo scenario A e lo scenario B al variare del costo al chilometro" xmlns="http://www.w3.org/2000/svg">']
    for cost in [220,230,240,250,260]:
        out.append(f'<line x1="68" y1="{y(cost):.1f}" x2="856" y2="{y(cost):.1f}" stroke="#e8edf3" stroke-width="1"/><text x="56" y="{y(cost)+5:.1f}" text-anchor="end" font-size="13" fill="#64748b">{cost} €</text>')
    for price in [.5,.6,.7,.8,.9,1.0]:
        out.append(f'<text x="{x(price):.1f}" y="323" text-anchor="middle" font-size="13" fill="#64748b">{number_it(price,2)}</text>')
    out.append('<text x="462" y="350" text-anchor="middle" font-size="13" fill="#64748b">Costo chilometrico del veicolo grande (€/km)</text>')
    out.append(f'<line x1="{x(.5)}" y1="{y(b_cost):.2f}" x2="{x(1.0)}" y2="{y(b_cost):.2f}" stroke="#d89538" stroke-width="3" stroke-dasharray="8 6"/>')
    out.append(f'<line x1="{x(.5)}" y1="{y(intercept+.5*dist):.2f}" x2="{x(1.0)}" y2="{y(intercept+1.0*dist):.2f}" stroke="#1873a7" stroke-width="3.5" stroke-linecap="round"/>')
    break_even=result['sensitivity']['break_even_price_eur_km']
    out.append(f'<line x1="{x(break_even):.2f}" y1="35" x2="{x(break_even):.2f}" y2="292" stroke="#98a7b7" stroke-width="1.5" stroke-dasharray="4 5"/>')
    out.append(f'<circle cx="{x(break_even):.2f}" cy="{y(b_cost):.2f}" r="6" stroke="#fff" stroke-width="2.5" fill="#40546f"/>')
    p=.72; ca=intercept+p*dist
    out.append(f'<line id="chart-cursor" x1="{x(p):.2f}" x2="{x(p):.2f}" y1="35" y2="292" stroke="#178b75" stroke-width="1.5" stroke-dasharray="3 4"/>')
    out.append(f'<circle id="chart-marker" cx="{x(p):.2f}" cy="{y(ca):.2f}" r="7" fill="#1873a7" stroke="#fff" stroke-width="3"/>')
    out.append('</svg>')
    return ''.join(out)


def create_html(data:dict) -> str:
    student=data['student']; nodes=data['nodes']; single=data['single_vehicle']; two=data['two_vehicles']; econ=data['economic_comparison']; a=econ['scenario_A']; b=econ['scenario_B']; op=data['operation']; fleet=data['fleet_scenarios']; sens=data['sensitivity']
    demand=sum(n['demand_kg'] for n in nodes)
    routes_a=[single['route']];routes_b=two['routes']
    blue='#1873a7'; orange='#d89538'; green='#188e77'
    matrix_header=''.join(f'<th scope="col">{txt(n["name"])}</th>' for n in nodes)
    matrix_rows=''.join('<tr><th scope="row">'+txt(node['name'])+'</th>'+''.join(f'<td class="{("diag" if i==j else "")}">{km(num)}</td>' for j,num in enumerate(data['distance_km'][i]))+'</tr>' for i,node in enumerate(nodes))
    customer_rows=''.join(f'<tr><td><span class="node-index">{txt(n["id"])}</span></td><th scope="row">{txt(n["name"])}</th><td>{int(n["demand_kg"])} kg</td><td>Cliente</td></tr>' for n in nodes[1:])
    seqA=' <span class="route-arrow">→</span> '.join(txt(x) for x in single['route']['cities'])
    routesB=''.join(f'<div class="vehicle-item"><div class="vehicle-head"><span class="vehicle-indicator v{i}"></span><strong>Veicolo {i+1}</strong><span class="load-pill">{int(r["load_kg"])} / {fleet["B"]["capacity_kg_per_vehicle"]} kg</span></div><p class="route-sequence">'+ ' <span class="route-arrow">→</span> '.join(txt(x) for x in r['cities'])+f'</p><div class="vehicle-stats"><span>{km(r["distance_km"])} km</span><span>{hour_minutes(b["vehicle_hours"][i])}</span><span>{r["customers_served"]} clienti</span></div></div>' for i,r in enumerate(routes_b))
    sensitivity_rows=''.join(f'<tr class="{("selected-row" if r["is_base_price"] else "")}"><td>{number_it(r["price_A_eur_km"], 6 if r["is_break_even_price"] else 2)} €/km</td><td>{euro(r["cost_A_eur"])}</td><td>{euro(r["cost_B_eur"])}</td><td>{("Pareggio" if r["is_break_even_price"] else "Un veicolo" if r["cheaper"]=="A" else "Due veicoli")}</td></tr>' for r in sens['records'])
    total_a=a['total_eur'];total_b=b['total_eur']
    pctA=[100*a[k]/total_a for k in ('fixed_eur','distance_cost_eur','driver_cost_eur')];pctB=[100*b[k]/total_b for k in ('fixed_eur','distance_cost_eur','driver_cost_eur')]
    def segment(values):
        return ''.join(f'<span class="seg seg-{i}" style="width:{v:.4f}%" aria-hidden="true"></span>' for i,v in enumerate(values))
    chart=svg_sensitivity(data)
    htmlsrc=f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Pianificazione dei percorsi di consegna agroalimentare tra Bari e cinque comuni limitrofi. Confronto tecnico ed economico fra uno e due veicoli.">
  <title>Pianificazione delle consegne | Adriatica Fresco Distribuzione</title>
  <link rel="stylesheet" href="style.css">
  <script src="app.js" defer></script>
</head>
<body>
  <a href="#contenuto" class="skip-link">Vai al contenuto</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a href="#inizio" class="brand" aria-label="Torna all'inizio"><span class="brand-symbol" aria-hidden="true">AF</span><span class="brand-name"><strong>ADRIATICA FRESCO</strong><small>Distribuzione · Bari</small></span></a>
      <nav class="main-nav" aria-label="Sezioni del progetto"><a href="#contesto">Contesto</a><a href="#percorsi">Percorsi</a><a href="#economia">Costi</a><a href="#dati">Dati</a><a href="#metodo">Metodo</a></nav>
      <span class="header-tag">Project Work 23</span>
    </div>
  </header>
  <main id="contenuto">
    <section class="hero" id="inizio">
      <div class="wrap hero-layout"><div class="hero-copy"><p class="eyebrow"><span class="eyebrow-dot"></span> CASO DI STUDIO · INFORMATICA PER LE AZIENDE DIGITALI</p>
        <h1>Pianificare le consegne,<br><em>confrontare i costi.</em></h1>
        <p class="hero-intro">Uno strumento per pianificare la distribuzione agroalimentare e confrontare due configurazioni di flotta: un unico veicolo o due mezzi refrigerati.</p>
        <div class="hero-actions"><a class="btn btn-primary" href="#percorsi">Esamina i percorsi <span aria-hidden="true">↗</span></a><a class="btn btn-outline" href="#economia">Analisi dei costi</a></div>
        <p class="hero-footnote">Deposito a Bari · 5 località di consegna · Enumerazione completa</p></div>
        <div class="hero-panel" aria-label="Sintesi dei risultati"><span class="panel-kicker">IL CONFRONTO IN BREVE</span><div class="hero-numbers"><div><span class="number-label">Minimo costo giornaliero</span><strong>{euro(total_a)}</strong><small>Scenario A · un veicolo</small></div><div><span class="number-label">Fine consegne più rapida</span><strong>{hour_minutes(b['completion_hours'])}</strong><small>Scenario B · due veicoli</small></div></div><div class="hero-panel-footer"><span class="bar-label">Differenza di costo</span><strong>{euro(total_b-total_a)}</strong><span class="tiny-sub">a favore del veicolo unico</span></div></div>
      </div>
    </section>
    <section class="metrics-section" aria-label="Indicatori principali"><div class="wrap metrics-grid">
      <div class="metric"><span class="metric-icon" aria-hidden="true">◌</span><span class="metric-caption">Clienti serviti</span><strong>05</strong><small>Località nell'area barese</small></div>
      <div class="metric"><span class="metric-icon" aria-hidden="true">▤</span><span class="metric-caption">Carico giornaliero</span><strong>{integer_it(demand)}<span class="metric-unit"> kg</span></strong><small>Distribuzione programmata</small></div>
      <div class="metric"><span class="metric-icon" aria-hidden="true">↗</span><span class="metric-caption">Distanza minima A</span><strong>{km(single['minimum_distance_km'])}<span class="metric-unit"> km</span></strong><small>Un solo giro</small></div>
      <div class="metric"><span class="metric-icon" aria-hidden="true">◎</span><span class="metric-caption">Distanza minima B</span><strong>{km(two['minimum_distance_km'])}<span class="metric-unit"> km</span></strong><small>Somma di due giri</small></div>
    </div></section>
    <section class="section" id="contesto"><div class="wrap">
      <div class="section-head"><div><p class="section-kicker">01 / IL CONTESTO</p><h2>Un problema logistico concreto</h2></div><p>Il caso riguarda un'impresa agroalimentare simulata con deposito a Bari, che distribuisce prodotti freschi e refrigerati a cinque punti vendita situati in comuni limitrofi.</p></div>
      <div class="context-grid"><article class="content-card context-main"><div class="card-topline"><span class="pill">Caso aziendale simulato</span><span class="small-label">AREA METROPOLITANA DI BARI</span></div><h3>Adriatica Fresco Distribuzione S.r.l.</h3><p>La distribuzione riguarda latticini, ortofrutta selezionata, prodotti da forno confezionati e preparazioni gastronomiche. Ogni punto vendita riceve una consegna completa, senza frazionamento del carico.</p><div class="context-points"><div><span>Deposito</span><strong>Bari</strong></div><div><span>Tipologia</span><strong>Consegne programmate</strong></div><div><span>Mezzi</span><strong>Refrigerati</strong></div></div></article>
      <article class="content-card assumptions"><h3>Vincoli operativi</h3><ul class="check-list"><li>Partenza e ritorno al deposito</li><li>Ogni cliente visitato una sola volta</li><li>Carico entro la capacità del mezzo</li><li>Due mezzi obbligatori nello scenario B</li><li>Tempi di servizio: {op['service_minutes_per_customer']} minuti per cliente</li></ul><p class="callout-note">Le distanze sono stime stradali tra centri comunali, normalizzate in forma simmetrica. Non rappresentano percorsi viari rilevati in tempo reale.</p></article></div>
    </div></section>
    <section class="section section-muted" id="percorsi"><div class="wrap"><div class="section-head"><div><p class="section-kicker">02 / LA PIANIFICAZIONE</p><h2>Due scenari, percorsi ottimi</h2></div><p>Il programma valuta tutti gli itinerari ammissibili e individua quelli che minimizzano la distanza complessiva, verificando la capacità di trasporto.</p></div>
      <div class="scenario-layout">
        <article class="scenario-card"><div class="scenario-header"><div><span class="scenario-label">SCENARIO A</span><h3>Un veicolo</h3><p>Capacità: {integer_it(fleet['A']['capacity_kg_per_vehicle'])} kg</p></div><div class="scenario-emblem emblem-a">01</div></div><div class="route-visual">{svg_map(nodes,routes_a,[blue],'a')}</div><div class="scenario-figcaption"><span class="dot-blue"></span> Giro unico, con rientro a Bari</div><div class="route-block"><span class="route-title">SEQUENZA OTTIMA</span><p class="route-sequence">{seqA}</p></div><div class="scenario-statrow"><div><small>Chilometri</small><strong>{km(single['minimum_distance_km'])}</strong></div><div><small>Carico</small><strong>{int(single['route']['load_kg'])} kg</strong></div><div><small>Durata</small><strong>{hour_minutes(a['completion_hours'])}</strong></div></div></article>
        <article class="scenario-card"><div class="scenario-header"><div><span class="scenario-label">SCENARIO B</span><h3>Due veicoli</h3><p>Capacità: {fleet['B']['capacity_kg_per_vehicle']} kg ciascuno</p></div><div class="scenario-emblem emblem-b">02</div></div><div class="route-visual">{svg_map(nodes,routes_b,[green,orange],'b')}</div><div class="scenario-figcaption"><span class="dot-green"></span> Mezzo 1 <span class="dot-orange"></span> Mezzo 2 · giri in parallelo</div><div class="two-routes">{routesB}</div><div class="scenario-statrow"><div><small>Km complessivi</small><strong>{km(two['minimum_distance_km'])}</strong></div><div><small>Ore-autista</small><strong>{number_it(b['total_driver_hours'])} h</strong></div><div><small>Fine consegne</small><strong>{hour_minutes(b['completion_hours'])}</strong></div></div></article>
      </div><p class="note-under">Gli archi dei grafi collegano schematicamente i centri comunali e indicano l'ordine delle visite. La lunghezza dei segmenti non rappresenta la distanza stradale usata dal programma.</p>
      <div class="method-strip"><div><span class="strip-number">{single['evaluated_routes']}</span><span>Sequenze valutate con un mezzo</span></div><div><span class="strip-number">{two['feasible_partitions']}</span><span>Ripartizioni di clienti ammissibili</span></div><div><span class="strip-number">{two['evaluated_route_pairs']}</span><span>Coppie di giri esaminate</span></div><div><span class="strip-number">{number_it(econ['completion_reduction_with_B_percent'])}%</span><span>Riduzione del tempo di completamento con due mezzi</span></div></div>
    </div></section>
    <section class="section" id="economia"><div class="wrap"><div class="section-head"><div><p class="section-kicker">03 / IL CONFRONTO ECONOMICO</p><h2>Quanto costa ogni soluzione?</h2></div><p>Il costo giornaliero comprende disponibilità del mezzo, chilometri percorsi e tempo di lavoro degli autisti. Tutti i prezzi sono parametri assunti per il caso di studio.</p></div>
      <div class="comparison-layout"><article class="content-card expense-card"><h3>Composizione dei costi</h3><p class="minor-text">La stessa funzione economica è applicata ai due scenari.</p><div class="bar-comparison"><div class="bar-title"><strong>Scenario A</strong><strong>{euro(total_a)}</strong></div><div class="stacked-bar" role="img" aria-label="Scenario A: noleggio {euro(a['fixed_eur'])}, chilometri {euro(a['distance_cost_eur'])}, personale {euro(a['driver_cost_eur'])}">{segment(pctA)}</div><div class="bar-title second-bar"><strong>Scenario B</strong><strong>{euro(total_b)}</strong></div><div class="stacked-bar" role="img" aria-label="Scenario B: noleggio {euro(b['fixed_eur'])}, chilometri {euro(b['distance_cost_eur'])}, personale {euro(b['driver_cost_eur'])}">{segment(pctB)}</div></div><div class="bar-legend"><span><i class="legend-block l0"></i>Noleggio</span><span><i class="legend-block l1"></i>Chilometri</span><span><i class="legend-block l2"></i>Personale</span></div><div class="table-scroller"><table class="data-table costs-table"><caption>Voci di costo giornaliero</caption><thead><tr><th>Voce</th><th>Un veicolo</th><th>Due veicoli</th></tr></thead><tbody><tr><td>Noleggio</td><td>{euro(a['fixed_eur'])}</td><td>{euro(b['fixed_eur'])}</td></tr><tr><td>Chilometri</td><td>{euro(a['distance_cost_eur'])}</td><td>{euro(b['distance_cost_eur'])}</td></tr><tr><td>Autisti</td><td>{euro(a['driver_cost_eur'])}</td><td>{euro(b['driver_cost_eur'])}</td></tr><tr class="total-row"><th scope="row">Totale</th><td>{euro(total_a)}</td><td>{euro(total_b)}</td></tr></tbody></table></div></article>
      <article class="content-card verdict-card"><span class="pill pill-blue">Risultato nel caso base</span><h3>Il mezzo unico ha un costo inferiore.</h3><p>La differenza economica è molto contenuta: <strong>{euro(total_b-total_a)} al giorno</strong>. Con due mezzi si percorrono {km(two['minimum_distance_km']-single['minimum_distance_km'])} km in più, ma si termina prima.</p><div class="verdict-feature"><small>Risparmio temporale con due veicoli</small><strong>{number_it(econ['completion_reduction_with_B_percent'])}%</strong></div><p class="fine-note">La scelta operativa dipende dal valore attribuito alla rapidità di consegna, oltre che ai costi diretti stimati.</p></article></div>
      <article class="content-card sensitivity-card"><div class="sensitivity-head"><div><span class="section-kicker">ANALISI DI SENSIBILITÀ</span><h3>Quando cambia la convenienza?</h3><p>Modifica il costo chilometrico del veicolo grande. La flotta a due veicoli e gli altri parametri restano invariati.</p></div><div class="break-even"><small>Prezzo teorico di pareggio</small><strong>{number_it(sens['break_even_price_eur_km'],6)} <span>€/km</span></strong></div></div>
      <div class="slider-layout"><div class="slider-control"><label for="km-price">Costo chilometrico dello scenario A</label><div class="price-readout"><output id="km-price-output" for="km-price">0,72 €/km</output><span>da 0,50 a 1,00 €/km</span></div><input id="km-price" type="range" min="0.50" max="1.00" step="0.01" value="0.72" aria-describedby="price-result"><div class="slider-labels"><span>0,50</span><span>1,00</span></div></div><div class="interactive-summary" id="price-result" aria-live="polite"><div><small>Costo A</small><strong id="interactive-cost-a">{euro(total_a)}</strong></div><div><small>Costo B</small><strong id="interactive-cost-b">{euro(total_b)}</strong></div><p id="interactive-verdict">Con il prezzo selezionato conviene un veicolo.</p></div></div>
      <div class="chart-wrap">{chart}</div><div class="line-legend"><span><i class="line-swatch sw-a"></i>Costo scenario A</span><span><i class="line-swatch sw-b"></i>Costo scenario B</span><span><i class="line-swatch sw-p"></i>Punto di pareggio</span></div>
      <details class="table-toggle"><summary>Consulta la tabella dei prezzi analizzati</summary><div class="table-scroller"><table class="data-table sensitivity-table"><caption>Costi al variare del costo chilometrico del mezzo grande</caption><thead><tr><th>Costo A per km</th><th>Costo totale A</th><th>Costo totale B</th><th>Soluzione più economica</th></tr></thead><tbody>{sensitivity_rows}</tbody></table></div></details>
      <p class="fine-note">Le soglie sono calcolate con valori non arrotondati. I costi mostrati a video sono arrotondati al centesimo; scostamenti di pochi centesimi in prossimità del pareggio dipendono da tale arrotondamento.</p></article>
    </div></section>
    <section class="section section-muted" id="dati"><div class="wrap"><div class="section-head"><div><p class="section-kicker">04 / L'ISTANZA</p><h2>I dati utilizzati dal programma</h2></div><p>Sei nodi in totale: un deposito e cinque località servite. La matrice delle distanze è simmetrica ed è la stessa utilizzata dal codice Python.</p></div><div class="data-layout"><article class="content-card"><h3>Clienti e quantità</h3><div class="table-scroller"><table class="data-table"><caption>Domande giornaliere dei cinque clienti</caption><thead><tr><th>Nodo</th><th>Località</th><th>Quantità</th><th>Ruolo</th></tr></thead><tbody><tr><td><span class="node-index depot-index">D</span></td><th scope="row">Bari</th><td>—</td><td>Deposito</td></tr>{customer_rows}</tbody><tfoot><tr><th colspan="2">Domanda totale</th><td>{integer_it(demand)} kg</td><td></td></tr></tfoot></table></div></article><article class="content-card parameters"><h3>Parametri del modello</h3><dl><div><dt>Veicolo A</dt><dd>{integer_it(fleet['A']['capacity_kg_per_vehicle'])} kg · {euro(fleet['A']['fixed_cost_eur_per_vehicle_day'])}/giorno</dd></div><div><dt>Veicoli B</dt><dd>2 × {fleet['B']['capacity_kg_per_vehicle']} kg · {euro(fleet['B']['fixed_cost_eur_per_vehicle_day'])}/mezzo/giorno</dd></div><div><dt>Costo chilometrico A / B</dt><dd>{number_it(fleet['A']['variable_cost_eur_km'])} / {number_it(fleet['B']['variable_cost_eur_km'])} €/km</dd></div><div><dt>Costo orario autista</dt><dd>{euro(op['driver_eur_hour'])}/h</dd></div><div><dt>Velocità media ipotizzata</dt><dd>{number_it(op['speed_kmh_assumed'],0)} km/h</dd></div><div><dt>Tempo di servizio</dt><dd>{op['service_minutes_per_customer']} min/cliente</dd></div></dl></article></div>
      <article class="content-card matrix-card"><div class="table-heading"><div><h3>Matrice delle distanze</h3><p>Valori in chilometri, arrotondati al decimo.</p></div><span class="pill">6 × 6 nodi</span></div><div class="table-scroller"><table class="data-table matrix-table"><caption>Distanze stradali normalizzate, in chilometri</caption><thead><tr><th scope="col">Da / a</th>{matrix_header}</tr></thead><tbody>{matrix_rows}</tbody></table></div><p class="fine-note">I valori sono ricavati da stime pubbliche tra centri comunali e successivamente simmetrizzati. Le fonti delle coppie sono registrate in <code>data/fonti_distanze.csv</code>. In una pianificazione reale sarebbero necessari indirizzi puntuali e distanze verificate sulla rete stradale.</p></article>
    </div></section>
    <section class="section" id="metodo"><div class="wrap"><div class="section-head"><div><p class="section-kicker">05 / METODO E LIMITI</p><h2>Come vengono calcolati i risultati</h2></div><p>Un'istanza di dimensioni contenute consente di confrontare tutte le soluzioni possibili, senza approssimazioni nella ricerca dell'ottimo rispetto ai dati disponibili.</p></div><div class="method-cards"><article class="content-card"><span class="step-badge">01</span><h3>Enumerazione</h3><p>Il problema a un veicolo corrisponde a un TSP con cinque clienti: sono esaminate tutte le 5! = 120 sequenze. Con due mezzi si generano le partizioni ammissibili e le permutazioni dei clienti per ogni mezzo.</p></article><article class="content-card"><span class="step-badge">02</span><h3>Controllo dei vincoli</h3><p>Ogni cliente deve comparire in un solo giro. Il programma scarta le ripartizioni superiori ai 600 kg per mezzo e verifica partenza e rientro al deposito.</p></article><article class="content-card"><span class="step-badge">03</span><h3>Valutazione economica</h3><p>Per ogni configurazione: costo fisso dei veicoli + chilometri × prezzo unitario + ore-autista × costo orario. Il confronto utilizza i percorsi a distanza minima.</p></article></div><div class="bottom-notes"><div><h3>Ambito di validità</h3><p>Il risultato è ottimo per il dataset inserito. Non sono considerati traffico in tempo reale, finestre di consegna, penali, variazioni dei tempi di scarico o differenze di percorrenza tra direzioni.</p></div><div><h3>Riproducibilità</h3><p>Dati, codice Python e risultati sono mantenuti nel progetto. Dalla cartella principale, eseguire <code>python src/main.py</code> e <code>python src/export_html.py</code> per ricalcolare i dati e ricreare questa pagina.</p></div></div></div></section>
  </main>
  <footer class="site-footer"><div class="wrap footer-inner"><div><strong>Adriatica Fresco Distribuzione</strong><p>Caso didattico di pianificazione della distribuzione agroalimentare.</p></div><div class="footer-author"><span>Antonio Rosellini</span><span>Informatica per le Aziende Digitali (L-31) · Traccia 23</span></div></div></footer>
  <script type="application/json" id="dashboard-config">{json.dumps({'distanceA': a['total_distance_km'], 'fixedA': a['fixed_eur'], 'driverHoursA': a['total_driver_hours'], 'driverHourly': op['driver_eur_hour'], 'costB': (fleet['B']['vehicles']*fleet['B']['fixed_cost_eur_per_vehicle_day']+b['total_distance_km']*fleet['B']['variable_cost_eur_km']+b['total_driver_hours']*op['driver_eur_hour']), 'breakEven': sens['break_even_price_eur_km']},ensure_ascii=False).replace('<',r'\u003c')}</script>
</body>
</html>
"""
    return htmlsrc


def main()->int:
    parser=argparse.ArgumentParser(description='Generazione della pagina HTML locale')
    parser.add_argument('--results', type=Path, default=ROOT/'output'/'risultati.json')
    parser.add_argument('--dest', type=Path, default=ROOT/'web'/'index.html')
    args=parser.parse_args()
    try:
        data=json.loads(args.results.read_text(encoding='utf-8'))
        content=create_html(data)
        args.dest.parent.mkdir(parents=True, exist_ok=True)
        args.dest.write_text(content,encoding='utf-8')
    except (OSError,KeyError,ValueError,json.JSONDecodeError) as exc:
        parser.exit(1, f'Errore nella generazione della pagina: {exc}\n')
    print('Pagina HTML creata:',args.dest.resolve())
    return 0

if __name__=='__main__':
    raise SystemExit(main())
