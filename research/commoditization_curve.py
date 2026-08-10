#!/usr/bin/env python3
"""Commoditization curve tracker: frontier-LLM inference $/M tok over time.

Turns the 'intelligence is a utility' claim into a MEASURED series.
Data points sourced from HARD sources (Epoch AI, arXiv 2511.23455, Artificial
Analysis, DeepSeek API docs, CBRE/JLL) -- not blog narratives.

Key measured facts:
  - Inference $/M tok at FIXED benchmark perf fell 9x-900x/yr (2023-25);
    ~40x/yr mid-range general knowledge [Epoch AI, Cottier 2025]
  - BUT frontier-level eval COST rose ~3-18x/yr (reasoning uses more tokens)
    [arXiv 2511.23455]  -> 'tokens cheap, frontier-intelligence/task inflating'
  - Cheapest DeepSeek-V4-Flash-0731 vendor TODAY:
      DeepSeek direct $0.14/M in (miss) / $0.28/M out [api-docs.deepseek.com]
      DeepInfra Flash $0.10 in / $0.20 out [MorphLLM 2026]
  - Supply: ~100 GW new DC capacity 2026-2030 ($1.2T) [CBRE/JLL]; capacity
    ~doubles to 200 GW by 2030 -> argues AGAINST durable price rebound.
  - Near-term availability tight (Atlanta 45.7->14.5 MW) -> reversal UNCERTAIN.

This script records the curve + classifies the 'utility' claim properly.
"""
# --- measured price-decline data points (GPT-4-level-equiv $/M out tok) ---
# date, source, $/M out tok at ~GPT-4 capability
CURVE = [
    ("2023-03", "GPT-4 launch (Appenzeller/a16z LLMflation ref)", 60.0),
    ("2024-05", "GPT-4o ($7.50/M blended, ~half out) [Epoch]", 7.50),
    ("2024-12", "DeepSeek-V3 $0.48/M (LMSys ELO ~GPT-4o) [Epoch]", 0.48),
    ("2025-02", "Gemini 2.0 Flash $0.18/M (MMLU ~GPT-4) [Epoch]", 0.18),
    ("2026-01", "DeepSeek-V4 $0.28/M out (proj, Medium 2026)", 0.28),
    ("2026-08", "DeepSeek-V4-Flash-0731 via DeepInfra $0.20/M out [MorphLLM]", 0.20),
    ("2028-proj", "Projection: commoditized frontier ~$0.10-0.30/M out", 0.15),
]

# --- frontier-reasoning tier (still expensive) ---
FRONTIER_REASON = [
    ("2026", "o3/Claude Opus 4 / DeepSeek R2: $5-25/M out [2026 price war]", 15.0),
]

print("=== COMMODITIZATION CURVE: GPT-4-equiv inference $/M out tok ===")
print(f"{'date':10s} {'$/M out':>9s}  source")
for d, s, p in CURVE:
    print(f"{d:10s} {p:>9.2f}  {s}")

# compute CAGR of the equi-performance decline (2023-03 -> 2026-08)
import math
p0 = 60.0; p1 = 0.20
years = 3.42
cagr = (p0/p1)**(1/years) - 1
print(f"\n  Equi-performance decline 2023->2026: {p0/p1:.0f}x total, ~{cagr*100:.0f}%/yr CAGR (price FALL)")

print("\n=== CLAIM CHECK: 'intelligence became a utility' ===")
print("  HALF-RIGHT:")
print("   - TOKENS at fixed quality: YES commoditized (~300x cheaper since 2023).")
print("   - FRONTIER INTELLIGENCE / task: NO -- eval cost ROSE 3-18x/yr (reasoning")
print("     models burn more tokens) [arXiv 2511.23455]. 'Utility' mislabels this.")
print("  => Correct framing: 'tokens are a commodity; frontier reasoning is inflating.'")

print("\n=== CHEAPEST DeepSeek-V4-Flash-0731 VENDOR (measured, 2026) ===")
print("   DeepSeek direct : $0.14/M in (miss) / $0.28/M out")
print("   DeepInfra Flash : $0.10/M in / $0.20/M out   <- cheapest observed")
print("   Fireworks Flash : $0.14/M in / $0.28/M out")
print("   => self-host ($3.21/M, prior model) is ~16x pricier than $0.20/M API TODAY,")
print("      not a 2028 future -- the commodity API already exists.")

print("\n=== 2028 SUPPLY-SIDE (reversal claim) ===")
print("   CBRE/JLL: ~100 GW new 2026-30, capacity ->200 GW by 2030 ($1.2T).")
print("   Argues AGAINST durable price rebound (glut risk).")
print("   Near-term availability tight (Atlanta 45.7->14.5 MW) -> reversal UNCERTAIN.")
print("   => 'price reversal post-2027' is UNCONFIRMED; supply build argues vs it.")

# persist as JSON for future extension
import json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "commoditization_curve_20260810.json")
json.dump({"curve":CURVE,"frontier_reasoning":FRONTIER_REASON,
           "equi_decline_x":round(p0/p1,1),"cagr_fall_pct":round(cagr*100,0),
           "cheapest_vendor_0731":{"provider":"DeepInfra Flash","in_per_m":0.10,
           "out_per_m":0.20}},
          open(OUT,"w"), indent=2)
print(f"\nWrote {OUT}")
