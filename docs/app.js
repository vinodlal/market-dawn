/* Bank Nifty Predictor — plain-JS front end for the Today + Calendar tabs. */

const DATA_LATEST = "../data/latest.json";
const DATA_BACKTEST = "../data/backtest_log.json";

let backtestByDate = {};   // "YYYY-MM-DD" -> row
let calMonth = null;       // Date pointing at the 1st of the shown month

// ---------------------------------------------------------------------------
// utilities
// ---------------------------------------------------------------------------
function fmt(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}
function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstChild;
}
function badgeClass(rec) {
  if (rec === "Buy Zone") return "buy";
  if (rec === "Sell Zone") return "sell";
  return "neutral";
}

// ---------------------------------------------------------------------------
// tab switching
// ---------------------------------------------------------------------------
function showTab(name) {
  document.getElementById("view-today").classList.toggle("hidden", name !== "today");
  document.getElementById("view-calendar").classList.toggle("hidden", name !== "calendar");
  document.getElementById("tab-today").classList.toggle("active", name === "today");
  document.getElementById("tab-calendar").classList.toggle("active", name === "calendar");
  if (name === "calendar" && !calMonth) loadCalendar();
}

// ---------------------------------------------------------------------------
// Today tab
// ---------------------------------------------------------------------------
async function loadToday() {
  try {
    const res = await fetch(DATA_LATEST, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    renderToday(d);
  } catch (e) {
    document.getElementById("today-loading").textContent =
      "Could not load latest recommendation. Pull to refresh once data is published.";
  }
}

function renderToday(d) {
  document.getElementById("subhead").textContent = "Last updated " + (d.date || "—");
  const corr = d.correlations || {};
  const macro = (d.macro_today || []);

  const macroHtml = macro.length
    ? `<div class="card macro"><h3>Scheduled event today</h3>${macro.map(m => `<div>${m.label}</div>`).join("")}</div>`
    : "";

  const html = `
    <div class="card" style="text-align:center">
      <span class="badge ${badgeClass(d.recommendation)}">${d.recommendation}</span>
      <div class="score">Composite score: <b>${d.score}</b> / 100</div>
      <div class="close">Bank Nifty close: <b>${fmt(d.banknifty_close)}</b></div>
      <div class="zones">
        <div class="zone buy"><div class="lbl">Buy zone</div><div class="val">${fmt(d.buy_zone?.[0])}–${fmt(d.buy_zone?.[1])}</div></div>
        <div class="zone sell"><div class="lbl">Sell zone</div><div class="val">${fmt(d.sell_zone?.[0])}–${fmt(d.sell_zone?.[1])}</div></div>
      </div>
    </div>
    ${macroHtml}
    <div class="card">
      <h3>Why</h3>
      <ul class="reasons">${(d.reasons || []).map(r => `<li>${r}</li>`).join("")}</ul>
    </div>
    <div class="card">
      <h3>Signals</h3>
      <div class="pcr-row"><span>Put/Call ratio (ATM ±5)</span><b>${d.pcr ?? "—"}</b></div>
      <table class="mini" style="margin-top:10px">
        <tr><td>Bank Nifty vs VIX (20d)</td><td>${corr.vix_20d ?? "—"}</td></tr>
        <tr><td>Bank Nifty vs Crude (20d)</td><td>${corr.crude_20d ?? "—"}</td></tr>
        <tr><td>Bank Nifty vs USDINR (20d)</td><td>${corr.usdinr_20d ?? "—"}</td></tr>
      </table>
    </div>`;
  const c = document.getElementById("today-content");
  c.innerHTML = html;
  c.classList.remove("hidden");
  document.getElementById("today-loading").classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Calendar tab
// ---------------------------------------------------------------------------
async function loadCalendar() {
  try {
    const res = await fetch(DATA_BACKTEST, { cache: "no-store" });
    if (!res.ok) throw new Error(res.status);
    const d = await res.json();
    backtestByDate = {};
    (d.days || []).forEach(r => { backtestByDate[r.date] = r; });
    // default to the most recent month with data
    const dates = Object.keys(backtestByDate).sort();
    const anchor = dates.length ? new Date(dates[dates.length - 1] + "T00:00:00") : new Date();
    calMonth = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
    renderCalendar(d.summary || {});
  } catch (e) {
    document.getElementById("cal-loading").textContent =
      "No accuracy history yet. It appears after the backtest has run for a few days.";
  }
}

function monthHitRate(year, month) {
  let hit = 0, scored = 0;
  for (const [date, r] of Object.entries(backtestByDate)) {
    const dt = new Date(date + "T00:00:00");
    if (dt.getFullYear() === year && dt.getMonth() === month && !r.outlier_flag) {
      scored++;
      if (r.zone_hit) hit++;
    }
  }
  return scored ? Math.round((hit / scored) * 100) : null;
}

function renderCalendar(summary) {
  const year = calMonth.getFullYear();
  const month = calMonth.getMonth();
  const monthName = calMonth.toLocaleString("en-US", { month: "long", year: "numeric" });
  const overall = summary.overall_hit_rate != null ? Math.round(summary.overall_hit_rate * 100) + "%" : "—";
  const dir = summary.directional_accuracy != null ? Math.round(summary.directional_accuracy * 100) + "%" : "—";
  const monthRate = monthHitRate(year, month);

  const firstDow = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const dows = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  let cells = dows.map(d => `<div class="dow">${d}</div>`).join("");
  for (let i = 0; i < firstDow; i++) cells += `<div class="cell empty"></div>`;

  for (let day = 1; day <= daysInMonth; day++) {
    const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const r = backtestByDate[iso];
    if (!r) { cells += `<div class="cell empty"><div class="d">${day}</div></div>`; continue; }
    let cls = "clickable", pct = "";
    if (r.outlier_flag) { cls += " outlier"; pct = "excl"; }
    else if (r.zone_hit) { cls += " hit"; pct = `${Math.round(r.zone_accuracy_pct)}%`; }
    else { cls += " miss"; pct = "miss"; }
    cells += `<div class="cell ${cls}" onclick="showDay('${iso}')"><div class="d">${day}</div><div class="p">${pct}</div></div>`;
  }

  document.getElementById("cal-content").innerHTML = `
    <div class="cal-summary">
      <div class="stat"><div class="n">${overall}</div><div class="l">Overall hit</div></div>
      <div class="stat"><div class="n">${monthRate != null ? monthRate + "%" : "—"}</div><div class="l">This month</div></div>
      <div class="stat"><div class="n">${dir}</div><div class="l">Direction</div></div>
      <div class="stat"><div class="n">${summary.outliers ?? 0}</div><div class="l">Outliers</div></div>
    </div>
    <div class="cal-nav">
      <button onclick="changeMonth(-1)">‹</button>
      <span class="month">${monthName}</span>
      <button onclick="changeMonth(1)">›</button>
    </div>
    <div class="cal-grid">${cells}</div>
    <div style="margin-top:10px;font-size:11px;color:var(--muted)">
      Green = price entered predicted zone · Red = missed · Gray = excluded outlier
    </div>`;
  document.getElementById("cal-content").classList.remove("hidden");
  document.getElementById("cal-loading").classList.add("hidden");
  window._calSummary = summary;
}

function changeMonth(delta) {
  calMonth = new Date(calMonth.getFullYear(), calMonth.getMonth() + delta, 1);
  renderCalendar(window._calSummary || {});
}

function showDay(iso) {
  const r = backtestByDate[iso];
  if (!r) return;
  const dirTxt = r.directional_correct === null ? "n/a (neutral)"
    : (r.directional_correct ? "correct" : "wrong");
  const status = r.outlier_flag ? "Excluded (outlier)" : (r.zone_hit ? "Hit" : "Miss");
  const reasons = (r.reasons || []).map(x => `<li>${x}</li>`).join("");
  document.getElementById("popover").innerHTML = `
    <button class="close-x" onclick="closePopover()">×</button>
    <h3>${iso}</h3>
    <div class="row"><span class="k">Prediction</span><b>${r.recommendation}</b></div>
    <div class="row"><span class="k">Predicted zone</span><b>${fmt(r.active_zone?.[0])}–${fmt(r.active_zone?.[1])}</b></div>
    <div class="row"><span class="k">Actual close</span><b>${fmt(r.actual_close)}</b></div>
    <div class="row"><span class="k">Day move</span><b>${r.daily_move_pct}%</b></div>
    <div class="row"><span class="k">Zone result</span><b>${status}</b></div>
    <div class="row"><span class="k">Direction</span><b>${dirTxt}</b></div>
    ${r.outlier_flag ? `<div style="font-size:12px;color:var(--muted);margin-top:6px">${r.outlier_reason}</div>` : ""}
    <h3 style="margin-top:12px">Reasoning that day</h3>
    <ul class="reasons">${reasons}</ul>`;
  document.getElementById("overlay").classList.add("show");
}
function closePopover() { document.getElementById("overlay").classList.remove("show"); }

// ---------------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------------
loadToday();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("service-worker.js").catch(() => {}));
}
