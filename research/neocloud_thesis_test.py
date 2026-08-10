#!/usr/bin/env python3
"""Neocloud thesis test: software-inference vs raw-GPU capacity plays.

Hypothesis (from news + price probe): value migrated from raw GPU rental
(commoditizing, H100 -64%) to software-enabled inference (DOCN/NET rising).
If true: software-inference neoclouds should show STRONGER momentum and
more POSITIVE post-print drift than raw-GPU names (CRWV).

Uses the already-pulled neocloud_probe_20260810.json (our own data).
Classifies each name, computes group-relative 60d/250d momentum + a
simple post-earnings drift proxy from the psyche v2 json where available.
"""
import json, os

OUT = os.path.dirname(os.path.abspath(__file__))

# Classification (thesis-driven, explicit)
SOFTWARE_INFERENCE = {  # inference-as-software / integrated stack
    "NET": "edge+workers+agents (software inference)",
    "DOCN": "agentic inference cloud (software stack)",
    "AKAM": "Linode GPU droplets + edge (integrated)",
    "PLTR": "AI software/platform (demand bellwether)",
}
RAW_GPU = {  # pure GPU-capacity / rental exposure
    "CRWV": "pure GPUaaS, max debt, commodity-H100 exposed",
    "CLSK": "compute-adjacent (BTC-adjacent, not AI-infra core)",
}

probe = json.load(open(os.path.join(OUT, "neocloud_probe_20260810.json")))
psy = json.load(open(os.path.join(OUT, "psyche_drift_v2_20260809.json")))

def g(name, key):
    return probe["symbols"].get(name, {}).get(key)

print("=== NEOCLOUD THESIS: software-inference vs raw-GPU ===\n")
print(f"{'SYM':5s} {'group':22s} {'60d%':>7s} {'250d%':>8s} {'psyche':>8s}")
soft, raw = [], []
for s, desc in {**SOFTWARE_INFERENCE, **RAW_GPU}.items():
    grp = "SOFTWARE" if s in SOFTWARE_INFERENCE else "RAW-GPU"
    r60 = g(s, "ret_60d_%"); r250 = g(s, "ret_250d_%")
    psy_sign = "n/a"
    if s in psy["symbols"]:
        psy_sign = psy["symbols"][s].get("psyche_sign", "n/a")
    print(f"{s:5s} {grp+':':22s} {str(r60):>7s} {str(r250):>8s} {psy_sign:>8s}")
    (soft if grp == "SOFTWARE" else raw).append((r60, r250))

def avg(vals, idx):
    v = [x[idx] for x in vals if isinstance(x[idx], (int, float))]
    return round(sum(v) / len(v), 2) if v else None

print("\n=== GROUP AVERAGES ===")
print(f"  SOFTWARE-inference  60d avg: {avg(soft,0)}%   250d avg: {avg(soft,1)}%")
print(f"  RAW-GPU capacity     60d avg: {avg(raw,0)}%   250d avg: {avg(raw,1)}%")

s60, r60 = avg(soft, 0), avg(raw, 0)
s250, r250 = avg(soft, 1), avg(raw, 1)
print("\n=== VERDICT ===")
if s60 is not None and r60 is not None and s60 > r60:
    print(f"  SOFTWARE 60d momentum BEATS raw-GPU by {round(s60-r60,2)} pts -> thesis SUPPORTED (near-term)")
else:
    print(f"  SOFTWARE 60d momentum {s60} vs raw-GPU {r60} -> thesis NOT supported near-term")
if s250 is not None and r250 is not None and s250 > r250:
    print(f"  SOFTWARE 250d momentum BEATS raw-GPU by {round(s250-r250,2)} pts -> thesis SUPPORTED (structural)")
else:
    print(f"  SOFTWARE 250d momentum {s250} vs raw-GPU {r250} -> thesis NOT supported structurally")

print("\n  Note: recent 60d drawdown hit BOTH groups (AI-sector rotation / rate taper);")
print("  the 250d gap is the cleaner structural signal. CRWV pain = debt+commodity-GPU,")
print("  not empty data centers (per Q1'26 call: demand-linked to utilization/contracts).")
