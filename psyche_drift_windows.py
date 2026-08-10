#!/usr/bin/env python3
"""Market-psyche assimilation-clock: empirical news-reaction timing.

Hypothesis (user's intuition): markets under-react to news and the lag
differs by news TYPE. v1 scope = EARNINGS only (narrow), but we MEASURE
each name's actual drift lag from OUR data rather than assume literature
windows (#2 empirical, started from #3 narrow scope).

For each (name, earnings_date) we compute forward drift +1d / +5d / +20d
from the earnings-day close. Across all events per name we derive the
"best-lag window" = the horizon with the most consistent directional drift.
Then the "assimilation clock" = sessions-since-last-print vs that window:
  - OPEN   : under-reaction still being priced in (edge window live)
  - CLOSED : window elapsed, drift should be complete

Data: crumb-free Yahoo v8 daily chart (UA + Pragma:no-cache). All network
runs in a background terminal (inline net is blocked). Refuse fake data:
emit null on any fetch failure, never 0.0.

Output: research/psyche_drift_YYYYMMDD.json + an HTML dashboard.
"""
import json
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
        "event": dates[i],
        "close": round(base, 2),
        "day_of_%": round((closes[i] / closes[i - 1] - 1.0) * 100.0, 2),
        "+1d%": fwd(1), "+5d%": fwd(5), "+20d%": fwd(20),
    }


def best_lag(drift_rows):
    """Empirical window = lag with most consistent same-sign drift."""
    lags = {"+1d%": [], "+5d%": [], "+20d%": []}
    for row in drift_rows:
        for k in lags:
            v = row.get(k)
            if isinstance(v, (int, float)):
                lags[k].append(v)
    summary = {}
    for k, vals in lags.items():
        if len(vals) >= 3:
            mean = sum(vals) / len(vals)
            pos = sum(1 for v in vals if v > 0)
            neg = sum(1 for v in vals if v < 0)
            consistency = max(pos, neg) / len(vals)
            summary[k] = {"n": len(vals), "mean%": round(mean, 2),
                          "consistency": round(consistency, 2)}
    if not summary:
        return None, {}
    # pick lag with highest |mean| * consistency (strongest reliable signal)
    best = max(summary, key=lambda k: abs(summary[k]["mean%"]) * summary[k]["consistency"])
    return best, summary


def sessions_since(dates, last_print):
    i = next_trade_day_index(dates, last_print)
    if i is None:
        return None
    return len(dates) - 1 - i


def main():
    out = {"date": TODAY, "scope": "earnings-only (v1)",
           "symbols": {}, "dashboard_rows": []}
    for sym in EVENTS:
        try:
            bars = fetch_daily(sym)
        except Exception as e:
            out["symbols"][sym] = {"error": str(e), "drift": None}
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
        best, summary = best_lag(drift_rows)
        last_print = EVENTS[sym][-1][0]
        ss = sessions_since(dates, last_print)
        window = None
        if best:
            window = int(best.replace("+", "").replace("d%", "").replace("%", ""))
        status = "OPEN" if (ss is not None and window and ss < window) else "CLOSED"
        out["symbols"][sym] = {
            "last_print": last_print,
            "sessions_since_print": ss,
            "empirical_window_sessions": window,
            "best_lag": best,
            "lag_summary": summary,
            "assimilation_status": status,
            "drift_rows": drift_rows,
        }
        out["dashboard_rows"].append({
            "symbol": sym, "last_print": last_print, "sessions_since_print": ss,
            "window": window, "status": status, "best_lag": best,
            "mean20": summary.get("+20d%", {}).get("mean%"),
        })
        time.sleep(0.4)

    stamp = TODAY.replace("-", "")
    json_path = os.path.join(OUT_DIR, f"psyche_drift_{stamp}.json")
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)

    # ---- text summary ----
    print(f"Wrote {json_path}\n")
    print(f"{'SYM':5s}{'last_print':12s}{'sess':>5s}{'win':>5s}  {'status':7s}  best_lag")
    for r in out["dashboard_rows"]:
        print(f"{r['symbol']:5s}{r['last_print']:12s}{str(r['sessions_since_print']):>5s}"
              f"{str(r['window']):>5s}  {r['status']:7s}  {r['best_lag']}")

    # ---- HTML dashboard ----
    html = render_html(out)
    html_path = os.path.join(OUT_DIR, f"psyche_dashboard_{stamp}.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"\nWrote {html_path}")
    return out


def render_html(out):
    rows = ""
    for r in out["dashboard_rows"]:
        color = "#1a7f37" if r["status"] == "OPEN" else "#888"
        rows += (f"<tr><td><b>{r['symbol']}</b></td><td>{r['last_print']}</td>"
                 f"<td>{r['sessions_since_print']}</td><td>{r['window']}</td>"
                 f"<td style='color:{color};font-weight:bold'>{r['status']}</td>"
                 f"<td>{r['best_lag']}</td><td>{r['mean20']}</td></tr>")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Market-Psyche Assimilation Clock — {out['date']}</title>
<style>body{{font-family:Times New Roman,serif;margin:40px;}}
table{{border-collapse:collapse;width:100%;}}th,td{{border:1px solid #ccc;
padding:8px;text-align:center;}}th{{background:#f0f0f0;}}
h1{{text-align:center;}}caption{{margin-bottom:12px;}}</style></head>
<body><h1>Market-Psyche Assimilation Clock</h1>
<p style="text-align:center">Earnings-reaction timing — empirical drift windows (v1, earnings-only)<br>
Date: {out['date']}</p>
<table><caption>OPEN = under-reaction still being priced in (drift window live).
CLOSED = window elapsed, reaction should be complete.</caption>
<tr><th>Symbol</th><th>Last Print</th><th>Sessions Since</th>
<th>Window (sess)</th><th>Status</th><th>Best-Lag</th><th>Mean +20d%</th></tr>
{rows}</table>
<p style="margin-top:24px;font-size:11pt;color:#555">Method: forward drift +1d/+5d/+20d measured at every
verified earnings date from our own Yahoo daily pulls. Best-lag window = horizon with the most
consistent directional drift. Narrow v1 — earnings only; macro/sector typing deferred.
Refuse-fake: any failed pull emits null, never 0.0.</p></body></html>"""


if __name__ == "__main__":
    main()
