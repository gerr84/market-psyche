#!/usr/bin/env python3
"""Valuation + momentum snapshot for watchlist/holdings.

Pulls crumb-authed Yahoo v7 quote (price, trailingPE, forwardPE, marketCap,
52w high/low, day change) + v8 daily bars (no crumb) for 21d/60d returns and
position in the 52-week range.

Symbols: MCK, D (Dominion Energy), ABNB, NFLX (valuation opinion -> evidence)
         NET, FTNT, ANET (returns/breadth context + psyche re-check).

Refuse fake: any failed pull emits null / quote_ok=False, never 0.0.
Background terminal only (inline net is blocked on this host).
"""
import json
import time
import urllib.request
import urllib.parse
import http.cookiejar
import datetime as dt
import os

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = os.path.dirname(os.path.abspath(__file__))
TODAY = "2026-08-09"
SYMS = ["MCK", "D", "ABNB", "NFLX", "NET", "FTNT", "ANET"]

_S = {"opener": None, "crumb": None}


def _session():
    if _S["opener"] and _S["crumb"]:
        return _S["opener"], _S["crumb"]
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA), ("Accept", "*/*")]
    for seed in ("https://fc.yahoo.com", "https://finance.yahoo.com"):
        try:
            op.open(seed, timeout=15).read()
        except Exception:
            pass
        if len(cj):
            break
    crumb = None
    for h in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            crumb = op.open(f"https://{h}/v1/test/getcrumb", timeout=15).read().decode().strip()
            if crumb and "<" not in crumb:
                break
        except Exception:
            crumb = None
    _S["opener"], _S["crumb"] = op, crumb
    return op, crumb


def get_quote(sym):
    op, crumb = _session()
    for h in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            q = {"symbols": sym}
            if crumb:
                q["crumb"] = crumb
            url = f"https://{h}/v7/finance/quote?" + urllib.parse.urlencode(q)
            data = json.loads(op.open(url, timeout=20).read().decode())
            res = data.get("quoteResponse", {}).get("result", [])
            if res:
                return res[0]
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                _S["opener"] = _S["crumb"] = None
                break
        except Exception:
            continue
    return None


def get_daily(sym, start="2025-05-01", end="2026-08-09"):
    p1 = int(dt.datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    p2 = int(dt.datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d&events=history")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Pragma": "no-cache"})
    with urllib.request.urlopen(req, timeout=25) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    ts = j["chart"]["result"][0]["timestamp"]
    q = j["chart"]["result"][0]["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(ts):
        c = q["close"][i]
        if c is None:
            continue
        bars.append((dt.datetime.utcfromtimestamp(t).date().isoformat(), float(c)))
    return bars


def _cap_b(cap):
    if not isinstance(cap, (int, float)):
        return None
    return round(cap / 1e9, 1)


def main():
    out = {"date": TODAY, "symbols": {}, "note": "D=Dominion Energy (assumed); verify if different ticker intended."}
    for s in SYMS:
        row = {"symbol": s}
        q = get_quote(s)
        if q:
            row["price"] = q.get("regularMarketPrice")
            row["trailingPE"] = q.get("trailingPE")
            row["forwardPE"] = q.get("forwardPE")
            row["marketCap_B"] = _cap_b(q.get("marketCap"))
            row["52w_high"] = q.get("fiftyTwoWeekHigh")
            row["52w_low"] = q.get("fiftyTwoWeekLow")
            row["day_chg_%"] = q.get("regularMarketChangePercent")
            row["quote_ok"] = True
        else:
            row["quote_ok"] = False
        try:
            bars = get_daily(s)
            dates = [b[0] for b in bars]
            closes = [b[1] for b in bars]

            def ret(k):
                if len(closes) > k:
                    return round((closes[-1] / closes[-1 - k] - 1) * 100, 2)
                return None

            row["ret_21d_%"] = ret(21)
            row["ret_60d_%"] = ret(60)
            lo, hi, px = row.get("52w_low"), row.get("52w_high"), row.get("price")
            if lo and hi and px:
                row["pct_of_52w_range"] = round((px - lo) / (hi - lo) * 100, 1)
        except Exception as e:
            row["daily_err"] = str(e)
        out["symbols"][s] = row
        time.sleep(0.5)

    stamp = TODAY.replace("-", "")
    path = os.path.join(OUT, f"valuation_snapshot_{stamp}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {path}\n")
    print(f"{'SYM':5s}{'price':>9s}{'tPE':>8s}{'fPE':>8s}{'cap$B':>8s}"
          f"{'21d%':>7s}{'60d%':>7s}{'%52w':>7s}{'day%':>7s}")
    for s, row in out["symbols"].items():
        print(f"{s:5s}{str(row.get('price')):>9s}{str(row.get('trailingPE')):>8s}"
              f"{str(row.get('forwardPE')):>8s}{str(row.get('marketCap_B')):>8s}"
              f"{str(row.get('ret_21d_%')):>7s}{str(row.get('ret_60d_%')):>7s}"
              f"{str(row.get('pct_of_52w_range')):>7s}{str(row.get('day_chg_%')):>7s}")
    return out


if __name__ == "__main__":
    main()
