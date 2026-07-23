# MarketDawn

A morning-first, self-improving **trading brief, recommender & paper-trading engine** for
Indian markets — Bank Nifty, Nifty, stocks, and options. It produces a pre-open market
brief, OI-driven futures calls, per-stock technical analysis with holding/futures/BTST
strategies, and a paper-trading ledger that grades every call against the actual tape and
auto-tunes its weights. **Signals only — it never places orders.**

- Engine & build plan: see [`CLAUDE.md`](CLAUDE.md) and the approved milestone plan.
- The engine (`core/`) is deterministic Python; the v1 Bank-Nifty pipeline in `scripts/`,
  `docs/`, and `data/` is kept as the **reference/baseline** to reconcile against.

> **Educational/informational only. Not SEBI-registered investment advice.**
> Crude & USDINR use futures proxies, not spot rates. This is a rule-based system,
> not a trained predictive model.

---

> ⚙️ **Below this line is the v1 reference documentation** for the original Bank Nifty
> pipeline. MarketDawn generalizes this logic; the v1 flow still works as documented.

---

## ⚠️ Step 0 — verify data sources FIRST (do this before trusting anything)

The pipeline is only as good as the account's data access. Before relying on it,
confirm all 5 sources work **for your Kite Connect account**:

```bash
cd scripts
pip install -r requirements.txt

# export the 5 secrets (PowerShell: $env:KITE_API_KEY="..."; etc.)
export KITE_API_KEY=...        KITE_API_SECRET=...
export KITE_USER_ID=...        KITE_PASSWORD=...
export KITE_TOTP_SECRET=...    # the TOTP *secret*, not a 6-digit code

python generate_token.py       # produces a fresh access token
python verify_sources.py       # must print 5/5 PASS
```

If any source FAILs, the usual causes are:
- the **Historical Data API** add-on is not active on your Kite subscription,
- the account lacks **F&O / currency / commodity** segment permission in Console,
- the instrument name changed.

Fix Kite Console segment settings before debugging code. **Do not rely on the
pipeline until `verify_sources.py` shows 5/5 PASS.**

---

## Local pipeline run (after Step 0 passes)

```bash
cd scripts
python generate_token.py       # 1. fresh access token -> kite_access_token.json (gitignored)
python fetch_data.py           # 2. raw data -> data/history/<today>.json
python analysis_engine.py      # 3. recommendation -> data/latest.json
python backtest.py             # 4. accuracy log -> data/backtest_log.json
python optimize_weights.py     # 5. (needs >=20 scored days) -> data/model_weights.json
```

## Secrets (GitHub → Settings → Secrets and variables → Actions)

| Secret | What it is |
| --- | --- |
| `KITE_API_KEY` | Kite Connect app API key |
| `KITE_API_SECRET` | Kite Connect app API secret |
| `KITE_USER_ID` | Zerodha client ID (e.g. `AB1234`) |
| `KITE_PASSWORD` | Kite login password |
| `KITE_TOTP_SECRET` | The TOTP *secret* (base32) from 2FA setup, not a live 6-digit code |

## Automation

- **`.github/workflows/daily-fetch.yml`** — cron `35 10 * * 1-5` (~16:05 IST,
  after close) + manual `workflow_dispatch`. token → fetch → analyze → backtest → commit.
- **`.github/workflows/weekly-optimize.yml`** — Saturday cron; re-tunes weights
  once ≥20 scored days exist (drift capped ±5 pts/cycle) and commits
  `model_weights.json`.

## PWA / GitHub Pages

1. Repo **Settings → Pages → Source = `main` branch, `/docs` folder**.
2. Open `https://<user>.github.io/<repo>/docs/` on iPhone Safari.
3. **Share → Add to Home Screen** → opens standalone (no browser chrome).

The app fetches `../data/latest.json` and `../data/backtest_log.json`
(network-first, cache fallback offline).

## Model at a glance

Composite score 0–100 (higher = more bullish), weighted (`data/model_weights.json`):

| Component | Weight | Bullish when |
| --- | --- | --- |
| S/R proximity | 40% | price near support |
| Gap zones | 25% | unfilled gap-up sits below as support |
| PCR (ATM ±5) | 20% | PCR > 1.2 (put-heavy) |
| VIX regime | 15% | *dampens* conviction when VIX rises as Bank Nifty falls |

- Score ≥ 65 → **Buy Zone** `[support, pivot]`
- Score ≤ 35 → **Sell Zone** `[pivot, resistance]`
- else → **Neutral** (both zones shown for reference)

## Backtesting & outliers

`backtest.py` replays each day using only data available at the prior close.
A day is flagged **outlier** (excluded from weight optimization, never deleted)
only if `|move| > max(3%, 2× 20-day realized vol)` **and** it is not a
`scheduled` event in `data/macro_flags.json`. Scheduled events (RBI policy,
budget, expiry) stay in scoring — they were foreseeable.

Maintain `data/macro_flags.json` by hand for known upcoming events; the app
surfaces same-day scheduled events on the Today tab.

## Repo layout

```
.github/workflows/   daily-fetch.yml, weekly-optimize.yml
scripts/             generate_token, verify_sources, fetch_data,
                     analysis_engine, backtest, optimize_weights, kite_utils
data/                latest.json, backtest_log.json, model_weights.json,
                     macro_flags.json, history/<date>.json
docs/                index.html, app.js, manifest.json, service-worker.js, icons/
```

> `data/` holds **real** Bank Nifty data bootstrapped via the Kite MCP
> (history 2026-03-27 → 2026-07-07). Refresh it going forward with the manual
> Kite-MCP flow (log in, pull the day's data, regenerate `latest.json` +
> `backtest_log.json`, commit) or wire up the unattended `generate_token.py`
> token flow for the daily GitHub Action.
