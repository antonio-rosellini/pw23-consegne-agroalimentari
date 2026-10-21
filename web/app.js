/* Confronto dei costi al variare del prezzo chilometrico dello scenario A. */
(() => {
  "use strict";
  const source = document.getElementById("dashboard-config");
  const range = document.getElementById("km-price");
  if (!source || !range) return;
  const values = JSON.parse(source.textContent);
  const formatted = new Intl.NumberFormat("it-IT", {style:"currency",currency:"EUR"});
  const short = new Intl.NumberFormat("it-IT", {minimumFractionDigits:2,maximumFractionDigits:2});
  const xMin=.5, xMax=1.0, yMin=216, yMax=268;
  const chartX = (v) => 68 + (v-xMin)/(xMax-xMin)*788;
  const chartY = (v) => 292 - (v-yMin)/(yMax-yMin)*251;
  const update = () => {
    const price = Number(range.value);
    const rawCostA = values.fixedA + price * values.distanceA + values.driverHourly * values.driverHoursA;
    const rawCostB = values.costB;
    document.getElementById("km-price-output").textContent = short.format(price) + " €/km";
    document.getElementById("interactive-cost-a").textContent = formatted.format(rawCostA);
    document.getElementById("interactive-cost-b").textContent = formatted.format(rawCostB);
    const verdict = price < values.breakEven - 0.0000001
      ? "Con il prezzo selezionato conviene un veicolo."
      : price > values.breakEven + 0.0000001
        ? "Con il prezzo selezionato convengono due veicoli."
        : "I costi delle due configurazioni sono equivalenti.";
    document.getElementById("interactive-verdict").textContent = verdict;
    const cursor=document.getElementById("chart-cursor");
    const marker=document.getElementById("chart-marker");
    if (cursor && marker) {
      const cx=chartX(price);
      cursor.setAttribute("x1",cx.toFixed(2));
      cursor.setAttribute("x2",cx.toFixed(2));
      marker.setAttribute("cx",cx.toFixed(2));
      marker.setAttribute("cy",chartY(rawCostA).toFixed(2));
    }
  };
  range.addEventListener("input",update);
  update();
})();
