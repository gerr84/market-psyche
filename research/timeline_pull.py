#!/usr/bin/env python3
"""Timeline grounding pull (2026-08-11).

Pulls live: price, prior-close chg%, YTD%, 52w range, and NEXT earnings date
for three buckets:
  - SW/SEC : software + cybersecurity growth (FTNT PANW CRWD NET ZS SNOW OKTA S)
  - SEMI   : semis + equipment (NVDA AMD MU TSM LRCX AMAT ASML ARM MRVL)
  - NEOCLOUD: DOCN + similar inference/software-growth (DOCN AKAM NET CRWV CFLT MDB)
Prints a compact table; writes JSON. NO fake numbers (null on failure).
"""
import sys, json, datetime as dt
try:
    import yfinance as yf
except Exception as e:
    print(f"yfinance unavailable: {e}", file=sys.stderr); sys.exit(2)

BUCKETS = {
    "SW/SEC": ["FTNT","PANW","CRWD","NET","ZS","SNOW","OKTA","S"],
    "SEMI":   ["NVDA","AMD","MU","TSM","LRCX","AMAT","ASML","ARM","MRVL"],
    "NEOCLOUD":["DOCN","AKAM","NET","CRWV","CFLT","MDB"],
}
YEAR = 2026
START = f"{YEAR}-01-02"

def earn_date(t):
    try:
        cal = t.calendar
        ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
        if ed:
            for d in ed:
                if d and d.year >= YEAR:
                    return d.strftime("%Y-%m-%d")
    except Exception:
        pass
    try:
        ts = t.info.get("nextEarningsDate") or t.info.get("earningsTimestamp")
        if ts:
            return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        pass
    return None

def row(sym):
    try:
        t = yf.Ticker(sym)
        h = t.history(start=START, auto_adjust=True)
        if h is None or len(h) == 0:
            return {"sym": sym, "price": None, "chg": None, "ytd": None, "lo52": None, "hi52": None, "earn": None}
        last = float(h["Close"].iloc[-1])
        prev_close = float(h["Close"].iloc[-2]) if len(h) > 1 else last
        chg = round((last/prev_close - 1)*100, 2)
        first = float(h["Close"].iloc[0])
        ytd = round((last/first - 1)*100, 1)
        lo = round(float(h["Low"].min()), 2)
        hi = round(float(h["High"].max()), 2)
        return {"sym": sym, "price": round(last,2), "chg": chg, "ytd": ytd,
                "lo52": lo, "hi52": hi, "earn": earn_date(t)}
    except Exception as e:
        return {"sym": sym, "price": None, "chg": None, "ytd": None, "lo52": None, "hi52": None, "earn": f"ERR:{e}"}

out = {}
for b, syms in BUCKETS.items():
    print(f"\n=== {b} ===")
    print(f"{'sym':6} {'price':>9} {'chg%':>7} {'ytd%':>7} {'52w_low':>9} {'52w_high':>9} {'next_earn':>12}")
    rows = []
    for s in syms:
        r = row(s); rows.append(r)
        print(f"{r['sym']:6} {str(r['price']):>9} {str(r['chg']):>7} {str(r['ytd']):>7} {str(r['lo52']):>9} {str(r['hi52']):>9} {str(r['earn']):>12}")
    out[b] = rows

json.dump(out, open("research/timeline_pull_20260811.json","w"), indent=2)
print("\nWrote research/timeline_pull_20260811.json")
