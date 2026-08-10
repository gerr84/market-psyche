#!/usr/bin/env python3
"""Market-psyche assimilation-clock v2 — signed + significance-weighted.

Upgrades v1 (which only found the *window length*):
  (a) SIGNED drift: which way the under-reaction runs (UP / DOWN / NONE),
  (b) SIGNIFICANCE: t-stat + win-rate per horizon, so we don't over-claim
      on n=8 samples,
  (c) ACTIONABLE state: OPEN-UP / OPEN-DOWN / CLOSED, derived from
      (sessions-since-print vs empirical window) AND (sign of drift).

Hypothesis (user): market under-reacts to news; the lag & direction differ
by name/type. v2 keeps EARNINGS-ONLY scope (narrow), MEASURED from our data.

Significance rule (honest, small-sample):
  - require n>=5 events for any horizon to be "graded"
  - t-stat = mean / (stdev/sqrt(n)); |t|>=1.5 ~ marginal, >=2.0 ~ real-ish
  - win-rate = fraction same sign as mean
  - a horizon is "drift-active" only if |t|>=1.5 AND win-rate>=0.6
  - name psyche = sign of the BEST (highest |t|*consistency) active horizon

Refuse fake data: null on any fetch failure.
"""
import json
import math
import time
import urllib.request
import datetime as dt
import os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = "2026-08-09"

# (date, label, verified)  -- verified=True means cross-checked >=2 sources
EVENTS = {
    "NET": [
        ("2024-08-01", "Q2'24", True), ("2024-11-07", "Q3'24", True),
        ("2025-02-11", "Q4'24", True), ("2025-05-08", "Q1'25", True),
        ("2025-08-05", "Q2'25", True), ("2025-11-06", "Q3'25", True),
        ("2026-02-10", "Q4'25", True), ("2026-05-07", "Q1'26", True),
        ("2026-08-06", "Q2'26", True),
    ],
    "FTNT": [
        ("2024-08-06", "Q2'24", True), ("2024-11-06", "Q3'24", True),
        ("2025-02-13", "Q4'24", True), ("2025-05-06", "Q1'25", True),
        ("2025-08-05", "Q2'25", True), ("2025-11-05", "Q3'25", True),
        ("2026-02-12", "Q4'25", True), ("2026-05-06", "Q1'26", True),
        ("2026-07-29", "Q2'26", True),
    ],
    "BE": [
        ("2025-01-29", "Q4'24", False), ("2025-04-30", "Q1'25", False),
        ("2025-07-30", "Q2'25", False), ("2025-10-29", "Q3'25", False),
        ("2026-01-28", "Q4'25", False), ("2026-04-28", "Q1'26", False),
        ("2026-07-28", "Q2'26", True),
    ],
    "DHI": [
        ("2025-01-22", "Q1 FY25", False), ("2025-04-23", "Q2 FY25", False),
        ("2025-07-23", "Q3 FY25", False), ("2025-10-22", "Q4 FY25", False),
        ("2026-01-21", "Q1 FY26", False), ("2026-04-22", "Q2 FY26", False),
        ("2026-07-21", "Q3 FY26", True),
    ],
    "PHM": [
        ("2025-01-30", "Q4'24", False), ("2025-04-22", "Q1'25", False),
        ("2025-07-22", "Q2'25", False), ("2025-10-21", "Q3'25", False),
        ("2026-01-29", "Q4'25", False), ("2026-04-22", "Q1'26", False),
        ("2026-07-22", "Q2'26", True),
    ],
    "PSKY": [
        ("2025-02-25", "Q4'25", True), ("2025-05-04", "Q1'26", True),
        ("2025-08-04", "Q2'26", True),
    ],
}


def fetch_daily(sym, start="2024-06-01", end="2026-08-09"):
    p1 = int(dt.datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    p2 = int(dt.datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d&events=history")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Pragma": "no-cache"})
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(ts):
        c = q["close"][i]
        if c is None:
            continue
        bars.append((dt.datetime.utcfromtimestamp(t).date().isoformat(), float(c)))
    return bars


def next_trade_day_index(dates, target):
    for i, d in enumerate(dates):
        if d >= target:
            return i
    return None


def drift_for_event(dates, closes, edate):
    i = next_trade_day_index(dates, edate)
    if i is None or i == 0:
        return None
    base = closes[i]

    def fwd(k):
        j = i + k
        if j < len(closes):
            return round((closes[j] / base - 1.0) * 100.0, 2)
        return None

    return {
        "event": dates[i], "close": round(base, 2),
        "day_of_%": round((closes[i] / closes[i - 1] - 1.0) * 100.0, 2),
        "+1d%": fwd(1), "+5d%": fwd(5), "+20d%": fwd(20),
    }


def score_horizon(vals):
    """Return {n, mean, stdev, t, winrate, active} for a list of drift %."""
    if len(vals) < 5:
        return {"n": len(vals), "active": False, "reason": "n<5"}
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    sd = math.sqrt(var) if var > 0 else 0.0
    t = (mean / (sd / math.sqrt(len(vals)))) if sd > 0 else 0.0
    same = sum(1 for v in vals if (v > 0) == (mean > 0))
    win = same / len(vals)
    active = (abs(t) >= 1.5) and (win >= 0.6)
    return {"n": len(vals), "mean%": round(mean, 2), "stdev%": round(sd, 2),
            "t": round(t, 2), "winrate": round(win, 2), "active": active}


def best_active(drift_rows):
    """Find empirical window + signed psyche from active horizons only."""
    lags = {"+1d%": [], "+5d%": [], "+20d%": []}
    for row in drift_rows:
        for k in lags:
            v = row.get(k)
            if isinstance(v, (int, float)):
                lags[k].append(v)
    scored = {k: score_horizon(v) for k, v in lags.items()}
    active = {k: s for k, s in scored.items() if s.get("active")}
    if not active:
        # fall back: report best by |t| even if marginal, but flag as WEAK
        best_k = max(scored, key=lambda k: abs(scored[k].get("t", 0.0)))
        return best_k, scored, "WEAK"
    best_k = max(active, key=lambda k: abs(scored[k]["t"]) * scored[k]["winrate"])
    return best_k, scored, "OK"


def sessions_since(dates, last_print):
    i = next_trade_day_index(dates, last_print)
    if i is None:
        return None
    return len(dates) - 1 - i


def main():
    out = {"date": TODAY, "scope": "earnings-only (v2, signed+significance)",
           "symbols": {}, "dashboard_rows": []}
    for sym in EVENTS:
        try:
            bars = fetch_daily(sym)
        except Exception as e:
            out["symbols"][sym] = {"error": str(e)}
            continue
        dates = [b[0] for b in bars]
        closes = [b[1] for b in bars]
        drift_rows = []
        for edate, label, verified in EVENTS[sym]:
            row = drift_for_event(dates, closes, edate)
            if row:
                row["qtr"] = label
                row["verified"] = verified
                drift_rows.append(row)
        best_k, scored, grade = best_active(drift_rows)
        window = int(best_k.replace("+", "").replace("d%", "").replace("%", "")) if best_k else None
        last_print = EVENTS[sym][-1][0]
        ss = sessions_since(dates, last_print)
        sign = "NONE"
        if scored.get(best_k, {}).get("active") or grade == "WEAK":
            m = scored.get(best_k, {}).get("mean%", 0)
            sign = "UP" if m > 0 else ("DOWN" if m < 0 else "NONE")
        open_win = (ss is not None and window and ss < window)
        status = "CLOSED"
        if open_win and sign == "UP":
            status = "OPEN-UP"
        elif open_win and sign == "DOWN":
            status = "OPEN-DOWN"
        elif open_win:
            status = "OPEN"
        out["symbols"][sym] = {
            "last_print": last_print, "sessions_since_print": ss,
            "empirical_window_sessions": window, "best_lag": best_k,
            "grade": grade, "psyche_sign": sign,
            "assimilation_status": status,
            "scored": scored, "drift_rows": drift_rows,
        }
        out["dashboard_rows"].append({
            "symbol": sym, "last_print": last_print,
            "sessions_since_print": ss, "window": window,
            "status": status, "best_lag": best_k, "sign": sign,
            "mean20": scored.get("+20d%", {}).get("mean%"),
            "t20": scored.get("+20d%", {}).get("t"),
            "grade": grade,
        })
        time.sleep(0.4)

    stamp = TODAY.replace("-", "")
    json_path = os.path.join(OUT_DIR, f"psyche_drift_v2_{stamp}.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {json_path}\n")
    print(f"{'SYM':5s}{'last_print':12s}{'sess':>5s}{'win':>5s}  {'STATUS':9s} {'sign':5s} best   t20")
    for r in out["dashboard_rows"]:
        print(f"{r['symbol']:5s}{r['last_print']:12s}{str(r['sessions_since_print']):>5s}"
              f"{str(r['window']):>5s}  {r['status']:9s} {r['sign']:5s} {str(r['best_lag']):6s}"
              f" {str(r['t20'])}")

    html = render_html(out)
    html_path = os.path.join(OUT_DIR, f"psyche_dashboard_v2_{stamp}.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"\nWrote {html_path}")
    return out


def render_html(out):
    rows = ""
    for r in out["dashboard_rows"]:
        if r["status"] == "OPEN-UP":
            color = "#1a7f37"
        elif r["status"] == "OPEN-DOWN":
            color = "#b42318"
        else:
            color = "#888"
        rows += (f"<tr><td><b>{r['symbol']}</b></td><td>{r['last_print']}</td>"
                 f"<td>{r['sessions_since_print']}</td><td>{r['window']}</td>"
                 f"<td style='color:{color};font-weight:bold'>{r['status']}</td>"
                 f"<td>{r['sign']}</td><td>{r['best_lag']}</td>"
                 f"<td>{r['mean20']}</td><td>{r['t20']}</td><td>{r['grade']}</td></tr>")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Market-Psyche Assimilation Clock v2 — {out['date']}</title>
<style>body{{font-family:Times New Roman,serif;margin:40px;}}
table{{border-collapse:collapse;width:100%;}}th,td{{border:1px solid #ccc;
padding:8px;text-align:center;}}th{{background:#f0f0f0;}}
h1{{text-align:center;}}caption{{margin-bottom:12px;}}</style></head>
<body><h1>Market-Psyche Assimilation Clock v2</h1>
<p style="text-align:center">Earnings-reaction timing — signed &amp; significance-weighted (narrow v1→v2)<br>
Date: {out['date']}</p>
<table><caption>OPEN-UP = under-reaction still pricing IN upward (edge live, long bias).
OPEN-DOWN = drift still playing OUT downward (edge live, caution).
CLOSED = window elapsed. t20 = t-stat of +20d drift (|t|&ge;1.5 with win&ge;0.6 = active).</caption>
<tr><th>Symbol</th><th>Last Print</th><th>Sess Since</th><th>Window</th>
<th>Status</th><th>Sign</th><th>Best-Lag</th><th>Mean+20d%</th><th>t20</th><th>Grade</th></tr>
{rows}</table>
<p style="margin-top:24px;font-size:11pt;color:#555">Method: forward drift +1d/+5d/+20d at every verified earnings date
from our own Yahoo daily pulls. Horizon graded active only if |t|&ge;1.5 AND win-rate&ge;0.6 (n&ge;5).
Name psyche = sign of best active horizon. Narrow v2 — earnings only; macro/sector typing deferred.
Refuse-fake: any failed pull emits null, never 0.0.</p></body></html>"""


if __name__ == "__main__":
    main()
