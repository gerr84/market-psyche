#!/usr/bin/env python3
"""alpha-news-watcher runner: data-center / sovereign-AI / neocloud monitor.

Adapts the alpha-news-watcher skill for the 'who builds DCs + any cancellations'
question. Fetches RSS + Reddit, scores by keyword x source credibility,
dedupes via SHA-256 state, emits a ranked digest. No network libs beyond
feedparser/bs4/yaml (present in venv).
"""
import os, sys, hashlib, datetime as dt
import yaml, feedparser

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources_datacenter.yaml")
STATE = os.path.join(HERE, "state_datacenter.json")
OUT = os.path.join(HERE, "digest_datacenter.md")

cfg = yaml.safe_load(open(SRC))
kw = cfg.get("keywords", {})
sw = cfg.get("source_weights", {})
min_score = cfg.get("min_score", 1.5)
lookback = cfg.get("lookback_hours", 168)
now = dt.datetime.utcnow()

# load prior seen hashes
seen = set()
if os.path.exists(STATE):
    try: seen = set(yaml.safe_load(open(STATE)).get("hashes", []))
    except Exception: seen = set()

def score(title, src_id):
    t = (title or "").lower()
    s = 0.0
    for k, w in kw.items():
        if k.lower() in t:
            s += w
    s *= sw.get(src_id, 1.0)
    return s

items = []
for s in cfg["sources"]:
    sid = s["id"]; url = s["url"]; stype = s.get("type", "rss")
    try:
        if stype == "reddit":
            d = feedparser.parse(url)
        else:
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
                items.append((sc, s["name"], title, e.get("link",""), h))
    except Exception as ex:
        print(f"  [warn] {sid}: {ex}", file=sys.stderr)

items.sort(reverse=True, key=lambda x: x[0])
seen.update(h for it in items for h in [it[4]])
yaml.safe_dump({"hashes": list(seen)[-500:]}, open(STATE,"w"))

with open(OUT,"w") as f:
    f.write(f"# Data-Center / Sovereign-AI Monitor — {now.isoformat()}Z\n\n")
    f.write(f"- Sources scanned: {len(cfg['sources'])}\n")
    f.write(f"- Candidate items (score >= {min_score}): {len(items)}\n\n")
    f.write("## High-signal items (ranked)\n\n")
    for sc, name, title, link, _ in items:
        f.write(f"- [{title}]({link}) ({name}, score={sc:.1f})\n")

print(f"Scanned {len(cfg['sources'])} sources, {len(items)} candidates >= {min_score}")
for sc, name, title, link, _ in items[:15]:
    print(f"  [{sc:.1f}] {name}: {title[:90]}")
print(f"Digest -> {OUT}")
