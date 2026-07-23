# CLAUDE.md — repo map & working notes

Trading brief, recommender & paper-trading engine for Indian markets (Bank Nifty, Nifty,
stocks, options). Morning-first, self-improving, **signals only — no order execution**.
Full plan: `~/.claude/plans/this-is-a-new-humble-hamster.md`.

## Layout
- `core/` — the engine (deterministic Python, **zero LLM tokens**).
  - `providers/` — Kite (primary) + public/proxy + news; `verify_accuracy` is the data gate.
  - `features/` — pure indicator functions (levels, gaps, MAs, momentum, oi, basis, patterns…).
  - `strategies/` — pluggable strategy scorers + trade-plan templates.
  - `engine/` — confluence `score`, `regime` router, `decision` (EV+sizing), `signal`, `futures`, `stock`.
  - `trade_plan/` — entry/stop/target/size + options-strategy mapper.
  - `paper/` — virtual-trade `ledger` + `scoreboard` (feeds the optimizer).
  - `brief/` — market-status text, news digest, morning-brief assembly.
  - `alerts/` — Telegram push.
  - `backtest/` — replay harness, metrics, walk-forward weight optimizer.
  - `config/` — weight profiles, universe, macro/event calendar (**no secrets**).
- `api/` — FastAPI backend (from M8).
- `web/` — Next.js + TS frontend (from M8).
- `scripts/`, `docs/`, `data/` — **v1 reference/baseline** (do not delete; reconcile against
  `data/latest.json` in M3).
- `tests/` — pytest.

## Directives (see plan)
- **Data accuracy first** — no source is used for signals until `verify_accuracy` PASSes.
- **All timestamps IST** (`Asia/Kolkata`), stored/served with an explicit display layer.
- **Credentials never leak** — secrets stored **encrypted in the OS keyring** via
  `core/security/` (set with `python -m core.security.setup_credentials`); env vars for
  CI/host. No plaintext `.env` for secrets; gitleaks pre-commit; browser never sees keys.
- **Token-efficient** — deterministic engine; LLM optional (Haiku + cache, headlines-only);
  small modules, compact test reports, config-driven weights.
- **Milestone-gated** — build → test → confirm before the next (M0…M9).

## Dev
- `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`
- Secrets: copy `.env.example` → `.env`, fill in. `pre-commit install` to arm the secret guard.
- Tests: `pytest -q`.
