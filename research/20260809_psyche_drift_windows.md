# Market-Psyche Assimilation Clock — Empirical Earnings-Drift Study

**Date:** 2026-08-09
**Scope:** Earnings-only (narrow v1→v2). Basket = NET, FTNT, BE, DHI, PHM, PSKY.
**Question tested:** "People don't react to news right away — what's the right timing for the right type of news?"

## Method
- Daily bars pulled from Yahoo `v8/finance/chart` (crumb-free) for each name, 2024-06 → 2026-08-09.
- At every verified earnings date (NET/FTNT 9 events each, web-verified ≥2 sources; BE/DHI/PHM ~7 quarterly, PSKY 3),
  forward drift measured at +1d / +5d / +20d from the earnings-day close.
- Per-name empirical window = horizon with most consistent directional drift.
- Significance (v2): horizon graded *active* only if |t| ≥ 1.5 AND win-rate ≥ 0.6 (n ≥ 5).
- Basket-level pooled t-test on signed drift and on |drift| (direction-agnostic).
- Refuse-fake enforced: any fetch failure emits null, never 0.0.

## Per-name result (v2)
| Sym | Last Print | Sess Since | Window | Status | Sign | Best-Lag | Mean+20d% | t20 | Grade |
|-----|-----------|-----------|--------|--------|------|----------|-----------|-----|-------|
| NET | 2026-08-06 | 1 | 20 | OPEN-UP | UP | +20d% | +5.6 | 0.70 | WEAK |
| FTNT| 2026-07-29 | 7 | 1 | CLOSED | UP | +1d% | +10.74 | 1.04 | WEAK |
| BE  | 2026-07-28 | 8 | 5 | CLOSED | UP | +5d% | +7.81 | 0.88 | WEAK |
| DHI | 2026-07-21 | 13 | 5 | CLOSED | DOWN | +5d% | −4.65 | −1.17 | OK |
| PHM | 2026-07-22 | 12 | 1 | CLOSED | DOWN | +1d% | −2.30 | −0.64 | OK |
| PSKY| 2025-08-04 | 254 | 1 | CLOSED | NONE | +1d% | n/a | n/a | WEAK |

## Basket-level significance (pooled, all names)
| Horizon | n | Mean Signed | t | Mean |drift| | t(|drift|) |
|---------|---|-------------|---|-----------|-----------|
| +1d | 42 | +1.06% | +0.84 | 4.85% | +4.70 |
| +5d | 41 | +1.86% | +0.90 | 9.25% | +6.29 |
| +20d| 37 | +4.35% | +1.34 | 14.14% | +5.99 |

## Verdict (honest)
- **The timing window is REAL and measurable.** Across the basket, the average absolute repricing after earnings is
  **+14.14% over 20 sessions (t = +5.99, highly significant)**. Markets do NOT price earnings in immediately — the
  assimilation takes ~20 sessions for most names. This confirms the user's intuition with our own data.
- **The DIRECTION is idiosyncratic, not a reliable signal.** Signed drift is NOT significant at the basket level
  (t = +1.34 at +20d) and per-name t-stats are all < 1.5. NET/FTNT/BE tend to drift UP post-print; DHI/PHM tend DOWN
  (rate-beta — homebuilders bleed post-print in a steepening-curve regime). Direction must be sourced from the name's
  own print quality + macro regime, not assumed.
- **Practical read:** the "when" is answerable (≈20 sessions, name-specific 1–20). The "which way" is a separate,
  regime-dependent bet. A naive "buy the drift" edge is NOT supported by these 37–42 events — it would be trading
  variance, not signal.

## Limitations
- n = 37–42 events total; per-name n = 3–9. Thin for per-name significance (hence WEAK grades).
- Earnings-only. Macro (FOMC), sector headlines, and analyst actions NOT yet typed — deferred to v3.
- Prior-quarter dates for BE/DHI/PHM are estimated (verified=False), not web-cross-checked.
- No transaction costs; drift ≠ tradeable edge without OOS walk-forward + regime gate.

## Next
- v3(a): add macro/sector news lanes with their own (shorter) assimilation windows.
- v3(b): turn the clock into an actionable trigger gated by print-quality + regime (not raw drift).
- Or: fold the |drift| timing into the tradebot's post-earnings watch (awareness only, not a signal).
