#!/usr/bin/env python3
"""
market_psyche_alpaca_papertrade.py  -- paper / dry-run auto-trader

Drives ORDER INTENTS from the market-reasoning signals we built in this repo:
  - ROTATION SCORE (soft/hard)  from research/news_watcher/digest_market.md
  - PSYCHE divergence           from research/psyche_rotation_20260811.json
  - TIMELINE buckets            from research/timeline_pull_20260811.json

Modes (SAFE BY DEFAULT):
  --dry-run   (default)  No Alpaca client. Prints + logs order intents + rationale.
  --paper              Connects to Alpaca PAPER endpoint. Requires APCA_API_KEY_ID +
                       APCA_API_SECRET_KEY in env. If absent, refuses to trade.
  --live               Connects to Alpaca LIVE. Requires keys. Intentionally same
                       gating; no live orders without keys present.

NEVER submits without keys. This file is committed but defaults to dry-run so it
cannot place real orders on its own.

NOT FINANCIAL ADVICE. This is a signal-driven order generator, not a validated
alpha strategy. Use paper only until the signal is OOS-backtested.
"""
import os, sys, json, re, argparse, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DIGEST = os.path.join(HERE, "news_watcher", "digest_market.md")
PSYCHE = os.path.join(HERE, "psyche_rotation_20260811.json")
TIMELINE = os.path.join(HERE, "timeline_pull_20260811.json")
ORDERS_LOG = os.path.join(HERE, "alpaca_papertrade_orders.jsonl")

# Universe by bucket (from our analysis)
SW_SEC   = ["FTNT","PANW","CRWD","NET","ZS","SNOW","OKTA","S"]
SEMI     = ["NVDA","AMD","MU","TSM","LRCX","AMAT","ASML","ARM","MRVL"]
NEOCLOUD = ["DOCN","AKAM","MDB","CRWV"]

PAPER_BOOK = 100_000.0      # paper book size
MAX_POS = 8                 # max concurrent positions
BUY_FRAC = 0.06             # fraction of book per buy (measured sizing)
SELL_FRAC = 0.06            # fraction per trim
EARNINGS_BLACKOUT_DAYS = 2  # skip new buys inside this window

def parse_rotation_score():
    try:
        txt = open(DIGEST).read()
        m = re.search(r"ROTATION SCORE \(soft/hard\):\s*([\d.]+|inf)", txt)
        s = m.group(1)
        rot = float('inf') if s == 'inf' else float(s)
        sm = re.search(r"Soft-layer hits \(software/cyber\):\s*(\d+)", txt)
        hd = re.search(r"Hard-layer hits \(semis/memory\):\s*(\d+)", txt)
        return rot, int(sm.group(1) if sm else 0), int(hd.group(1) if hd else 0)
    except Exception:
        return 0.0, 0, 0

def parse_psyche():
    try:
        d = json.load(open(PSYCHE))
        return d.get("divergence", 0.0), d.get("regime", "UNKNOWN")
    except Exception:
        return 0.0, "UNKNOWN"

def load_timeline():
    try:
        return json.load(open(TIMELINE))
    except Exception:
        return {}

def in_blackout(sym, tl):
    """True if symbol has an earnings date within EARNINGS_BLACKOUT_DAYS."""
    today = dt.date.today()
    for bucket in tl.values():
        for r in bucket:
            if r.get("sym") == sym and r.get("earn"):
                try:
                    ed = dt.datetime.strptime(r["earn"], "%Y-%m-%d").date()
                    if 0 <= (ed - today).days <= EARNINGS_BLACKOUT_DAYS:
                        return True
                except Exception:
                    pass
    return False

def decide(rot, soft, hard, div, regime, tl):
    """Return list of order intents: {action, symbol, side, qty_frac, why}."""
    intents = []
    # Rotation tilt: score>1 => favor SW/SEC + NEOCLOUD software; <1 => favor SEMI.
    rot_long = SW_SEC + [s for s in NEOCLOUD if s != "CRWV"]  # software/cyber + software-layer neocloud
    rot_short_underweight = []  # we don't short in paper v1; just underweight
    if rot > 1.0:
        bias_long = rot_long
        bias_avoid = SEMI
        why_bias = f"ROTATION SCORE {rot} (>1): market rotating INTO software/cyber; long SW/SEC + software-layer neocloud, avoid fresh SEMI buys"
    elif rot < 1.0:
        bias_long = SEMI
        bias_avoid = SW_SEC
        why_bias = f"ROTATION SCORE {rot} (<1): rotating INTO semis; long SEMI, avoid fresh SW/SEC buys"
    else:
        bias_long = SW_SEC
        bias_avoid = []
        why_bias = "ROTATION SCORE ~1: balanced; default SW/SEC lean"

    # Psyche gates sizing: CAUTIOUS/coherent => measured (full frac). Overconfident => halve.
    frac = BUY_FRAC * (0.5 if div > 0.15 else 1.0)
    psy_why = f"psyche div={div:+.2f} {regime} -> sizing x{frac/BUY_FRAC:.2f}"

    for sym in bias_long:
        if in_blackout(sym, tl):
            intents.append({"action":"SKIP","symbol":sym,"side":"buy","qty_frac":0.0,
                            "why":f"{why_bias}; {sym} in earnings blackout (<= {EARNINGS_BLACKOUT_DAYS}d) -> skip"})
            continue
        intents.append({"action":"BUY","symbol":sym,"side":"buy","qty_frac":frac,
                        "why":f"{why_bias}; {psy_why}"})
    # Underweight / trim names in the avoid bucket that we'd otherwise hold
    for sym in bias_avoid:
        intents.append({"action":"HOLD/TRIM","symbol":sym,"side":"sell","qty_frac":SELL_FRAC,
                        "why":f"{why_bias}; trim exposure (no new buy)"})
    return intents

def log_intent(intent, mode):
    rec = {"ts": dt.datetime.utcnow().isoformat(), "mode": mode, **intent}
    with open(ORDERS_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec

def submit_alpaca(intents):
    """Only called when --paper/--live AND keys present. Returns (submitted, rejected)."""
    key = os.environ.get("APCA_API_KEY_ID")
    sec = os.environ.get("APCA_API_SECRET_KEY")
    if not (key and sec):
        return [], intents  # no keys -> reject all (safe)
    # Imported lazily so dry-run never needs the client
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest
        client = TradingClient(key, sec, paper=(mode == "paper"))
    except Exception as e:
        print(f"  [reject] Alpaca client init failed: {e}", file=sys.stderr)
        return [], intents
    submitted, rejected = [], []
    for it in intents:
        if it["action"] != "BUY":
            continue
        try:
            req = MarketOrderRequest(symbol=it["symbol"], qty=1, side=OrderSide.BUY,
                                     time_in_force=TimeInForce.DAY)
            client.submit_order(req)
            submitted.append(it)
        except Exception as e:
            it["error"] = str(e)
            rejected.append(it)
    return submitted, rejected

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dry-run","paper","live"], default="dry-run")
    args = ap.parse_args()
    mode = args.mode

    rot, soft, hard = parse_rotation_score()
    div, regime = parse_psyche()
    tl = load_timeline()

    print(f"=== market_psyche Alpaca paper-trader ({mode}) ===")
    print(f"ROTATION SCORE={rot} (soft={soft} hard={hard}) | psyche div={div:+.2f} {regime}")
    print(f"PAPER BOOK=${PAPER_BOOK:,.0f} | MAX_POS={MAX_POS} | BUY_FRAC={BUY_FRAC}")
    print("-"*70)

    intents = decide(rot, soft, hard, div, regime, tl)
    buys = [i for i in intents if i["action"] == "BUY"]
    print(f"Order intents: {len(intents)} ({len(buys)} BUY, "
          f"{len([i for i in intents if i['action']=='SKIP'])} SKIP, "
          f"{len([i for i in intents if i['action']=='HOLD/TRIM'])} TRIM)")
    print("-"*70)

    for it in intents:
        rec = log_intent(it, mode)
        tag = rec["action"]
        print(f"[{tag:9}] {it['symbol']:5} {it.get('side',''):4} frac={it.get('qty_frac',0):.3f}  {it['why']}")

    if mode == "dry-run":
        print("-"*70)
        print("DRY-RUN: no Alpaca client, no orders placed. Log -> " + ORDERS_LOG)
        print(f"Generated {len(buys)} BUY intents across the rotation-long bucket.")
        return

    # paper / live
    submitted, rejected = submit_alpaca(intents)
    print("-"*70)
    print(f"Submitted to Alpaca ({mode}): {len(submitted)} | Rejected: {len(rejected)}")
    for r in rejected:
        print(f"  REJECT {r['symbol']}: {r.get('error','?')}")

if __name__ == "__main__":
    main()
