#!/usr/bin/env python3
"""Market rotation / semis / cyber / software / Iran monitor.

Reuses the alpha-news-watcher scoring engine from watcher_datacenter.py but
with a market-specific source set (sources_market.yaml). Tracks the
AI-infra-hardware -> software/cybersecurity rotation + macro (Iran/oil/yen/CPI).

Output: ranked digest + a simple ROTATION SCORE = (software+cyber+seminame hits)
vs (semis+memory hits) so we can see which way money is sloshing over time.
"""
import os, sys, hashlib, datetime as dt
import yaml, feedparser

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources_market.yaml")
STATE = os.path.join(HERE, "state_market.json")
OUT = os.path.join(HERE, "digest_market.md")

cfg = yaml.safe_load(open(SRC))
kw = cfg.get("keywords", {})
sw = cfg.get("source_weights", {})
min_score = cfg.get("min_score", 1.5)
lookback = cfg.get("lookback_hours", 168)
now = dt.datetime.utcnow()

seen = set()
if os.path.exists(STATE):
    try: seen = set(yaml.safe_load(open(STATE)).get("hashes", []))
    except Exception: seen = set()

# thematic buckets for rotation score
SOFT = ["rotation","rotate","software","IGV","cybersecurity","cyber","Fortinet",
        "FTNT","Palo","PANW","CrowdStrike","CRWD"]
HARD = ["semis","semiconductor","photonic","memory","HBM","Micron","MU","TSMC"]

def score(title, src_id):
    t = (title or "").lower()
    s = 0.0
    for k, w in kw.items():
        if k.lower() in t: s += w
    return s * sw.get(src_id, 1.0)

items = []; soft_hits = 0; hard_hits = 0
for s in cfg["sources"]:
    sid = s["id"]; url = s["url"]
    try:
        d = feedparser.parse(url)
        for e in d.entries:
            title = e.get("title", "")
            h = hashlib.sha256((sid + title).encode()).hexdigest()
            if h in seen: continue
            pub = e.get("published_parsed") or e.get("updated_parsed")
            if pub:
                age = (now - dt.datetime(*pub[:6])).total_seconds()/3600
                if age > lookback: continue
            sc = score(title, sid)
            if sc >= min_score:
                tl = title.lower()
                if any(k.lower() in tl for k in SOFT): soft_hits += 1
                if any(k.lower() in tl for k in HARD): hard_hits += 1
                items.append((sc, s["name"], title, e.get("link",""), h))
    except Exception as ex:
        print(f"  [warn] {sid}: {ex}", file=sys.stderr)

items.sort(reverse=True, key=lambda x: x[0])
seen.update(it[4] for it in items)
yaml.safe_dump({"hashes": list(seen)[-500:]}, open(STATE,"w"))

rot = round(soft_hits / hard_hits, 2) if hard_hits else (float('inf') if soft_hits else 0.0)
with open(OUT,"w") as f:
    f.write(f"# Market Rotation Monitor — {now.isoformat()}Z\n\n")
    f.write(f"- Sources: {len(cfg['sources'])}, candidates (>= {min_score}): {len(items)}\n")
    f.write(f"- Soft-layer hits (software/cyber): {soft_hits}\n")
    f.write(f"- Hard-layer hits (semis/memory): {hard_hits}\n")
    f.write(f"- ROTATION SCORE (soft/hard): {rot}  (>1 = rotating INTO software/cyber)\n\n")
    f.write("## High-signal items\n\n")
    for sc, name, title, link, _ in items:
        f.write(f"- [{title}]({link}) ({name}, {sc:.1f})\n")

print(f"Sources {len(cfg['sources'])}; candidates {len(items)}; soft={soft_hits} hard={hard_hits} rot={rot}")
for sc, name, title, link, _ in items[:15]:
    print(f"  [{sc:.1f}] {name}: {title[:85]}")
print(f"Digest -> {OUT}")
