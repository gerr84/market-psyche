# market-psyche

Empirical study of **information-diffusion timing** in equities — measuring
*how long the market takes to fully price a news event*, and *which way the
under-reaction runs*.

## Hypothesis
Markets under-react to news and assimilate it slowly; the lag length and
direction differ by name and news type. "People don't react right away."

## Scope (v1 → v2)
- **v1** — empirical earnings-reaction windows. For each name, measure forward
  drift at +1d / +5d / +20d from every verified earnings date (our own Yahoo
  daily pulls). Derive each name's best-lag "assimilation window."
- **v2** — signed + significance-weighted. Adds a t-stat / win-rate gate so we
  don't over-claim on thin samples; classifies each name's post-print psyche as
  UP / DOWN / NONE and the clock state as OPEN-UP / OPEN-DOWN / CLOSED.

## Key finding (2026-08-09)
Basket-level: average **absolute** repricing after earnings = **+14.14% over 20
sessions (t = +5.99, highly significant)** → the timing window is REAL.
But **signed** drift is NOT significant (t = +1.34) → direction is idiosyncratic
(NET/FTNT/BE drift up; DHI/PHM drift down on rate-beta). The "when" is answerable;
the "which way" is a separate, regime-dependent bet. See
`research/20260809_psyche_drift_windows.md`.

## Files
- `psyche_drift_windows.py` — v1 engine
- `psyche_drift_windows_v2.py` — v2 engine (signed + significance)
- `research/` — JSON artifacts, HTML dashboards, dated findings note

## Run
Background terminal (inline network is blocked on the dev host):
```
python psyche_drift_windows_v2.py
```
Writes `research/psyche_drift_v2_YYYYMMDD.json` + HTML dashboard.

## Discipline
- Refuse fake data: any failed pull emits null, never 0.0.
- Earnings dates web-verified across ≥2 sources (NET/FTNT fully; BE/DHI/PHM
  prior quarters estimated, flagged).
- Not a trade signal without OOS walk-forward + regime gate.
