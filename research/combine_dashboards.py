#!/usr/bin/env python3
"""Combine psyche-drift v2 + valuation snapshot into one HTML dashboard.

Reads research/psyche_drift_v2_20260809.json and
research/valuation_snapshot_20260809.json, emits a single printable HTML
that shows, per name: assimilation clock (status/sign/window) + valuation
(price/fPE/%52w/returns). No network. Local only.
"""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
TODAY = "20260809"

psy = json.load(open(os.path.join(OUT, f"psyche_drift_v2_{TODAY}.json")))
val = json.load(open(os.path.join(OUT, f"valuation_snapshot_{TODAY}.json")))

val_by = {s: r for s, r in val["symbols"].items()}

cols = []
for row in psy["dashboard_rows"]:
    s = row["symbol"]
    v = val_by.get(s, {})
    if row["status"] == "OPEN-UP":
        sc = "#1a7f37"
    elif row["status"] == "OPEN-DOWN":
        sc = "#b42318"
    elif row["status"] == "CLOSED" and row["sign"] == "DOWN":
        sc = "#b42318"
    else:
        sc = "#888"
    # valuation flag: near 52w high AND rich fPE = expensive
    p52 = v.get("pct_of_52w_range")
    fpe = v.get("forwardPE")
    if isinstance(p52, (int, float)) and isinstance(fpe, (int, float)):
        val_flag = "RICH" if (p52 >= 90 and fpe >= 30) else ("CHEAP" if (p52 <= 30 and fpe < 25) else "fair")
    else:
        val_flag = "n/a"
    cols.append((s, row, v, sc, val_flag))

rows = ""
for s, row, v, sc, val_flag in cols:
    vf_color = {"RICH": "#b42318", "CHEAP": "#1a7f37", "fair": "#555", "n/a": "#999"}[val_flag]
    rows += (f"<tr><td><b>{s}</b></td>"
             f"<td>{row['last_print']}</td><td>{row['sessions_since_print']}</td>"
             f"<td>{row['window']}</td>"
             f"<td style='color:{sc};font-weight:bold'>{row['status']}</td>"
             f"<td>{row['sign']}</td>"
             f"<td>{v.get('price')}</td><td>{v.get('forwardPE')}</td>"
             f"<td>{v.get('ret_60d_%')}</td><td>{v.get('pct_of_52w_range')}</td>"
             f"<td style='color:{vf_color};font-weight:bold'>{val_flag}</td></tr>")

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Market-Psyche Combined Dashboard — {TODAY}</title>
<style>body{{font-family:Times New Roman,serif;margin:40px;}}
table{{border-collapse:collapse;width:100%;}}th,td{{border:1px solid #ccc;
padding:7px;text-align:center;}}th{{background:#f0f0f0;}}
h1{{text-align:center;}}caption{{margin-bottom:12px;}}</style></head>
<body><h1>Market-Psyche Combined Dashboard</h1>
<p style="text-align:center">Assimilation clock + valuation/momentum &nbsp;|&nbsp; {TODAY}</p>
<table><caption>Status: OPEN-UP = under-reaction pricing IN (long tilt); OPEN-DOWN = playing OUT (caution);
CLOSED = window elapsed. Valuation: RICH = &ge;90% of 52w range AND fPE&ge;30;
CHEAP = &le;30% of range AND fPE&lt;25.</caption>
<tr><th>Sym</th><th>Last Print</th><th>Sess</th><th>Win</th><th>Clock</th>
<th>Sign</th><th>Price</th><th>fPE</th><th>60d%</th><th>%52w</th><th>Val</th></tr>
{rows}</table>
<p style="margin-top:22px;font-size:11pt;color:#555">Empirical only. Psyche windows from our own Yahoo daily
pulls; valuation from crumb-authed Yahoo quote. Refuse-fake: missing fields shown as None, not 0.0.
No trade signal without OOS walk-forward + regime gate.</p></body></html>"""

path = os.path.join(OUT, f"combined_dashboard_{TODAY}.html")
with open(path, "w") as f:
    f.write(html)
print(f"Wrote {path}")
