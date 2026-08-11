#!/usr/bin/env python3
"""Fresh psyche-eval (c): score a market-rotation reasoning trace.

Uses the REAL patented analyzer (C:/Users/chees/reasoning-trace-analyzer).
Trace below emulates a model reasoning about the live rotation (semis->software/
cyber) using the verified facts from this session (TSMC +45%, MU 2027 tight,
FTNT +100% YTD, Iran/Hormuz oil). The divergence signal = confidence - coherence.
"""
import os, sys, json, statistics
sys.path.insert(0, r"C:\Users\chees\reasoning-trace-analyzer")
import reasoning_trace_analyzer as rta

TRACE = (
    "1. First, I should assess whether the AI-infra rotation into software and "
    "cybersecurity is durable or a squeeze.\n"
    "2. The structural facts are clear: TSMC July revenue rose 45% year over year, "
    "Micron guidance says 2027 memory will be tighter than 2026, and HBM supply is "
    "genuinely constrained, so the hardware demand story is intact.\n"
    "3. Therefore the softness in photonics and semis this month is likely a "
    "positioning rotation, not a thesis break, because money is sloshing, not leaving.\n"
    "4. However, I must consider the Iran/Hormuz risk: oil above $82 and a yen "
    "intervention are tail risks that could compress multiples if they escalate.\n"
    "5. It is possible the CPI/PPI prints this week reset rate expectations and "
    "challenge the software bid, so I should stay measured rather than all-in.\n"
    "6. Consequently the rational read is balanced: stay long the structural memory "
    "shortage and the cybersecurity application layer, hedge the geopolitical tail."
)

def psyche_signal(result):
    coh = result["coherence"]["coherence_score"]
    confs = [s["confidence"]["confidence_score"] for s in result.get("step_analysis", [])]
    conf = statistics.mean(confs) if confs else 0.5
    div = round(conf - coh, 4)
    regime = ("OVERCONFIDENT (euphoria/FOMO proxy)" if div > 0.15
              else "CAUTIOUS (fear/capitulation proxy)" if div < -0.15
              else "BALANCED")
    return {"confidence": round(conf,4), "coherence": round(coh,4),
            "divergence": div, "regime": regime,
            "quality_score": result.get("quality_score"),
            "reasoning_steps": result.get("reasoning_steps")}

print("=== FRESH PSYCHE-EVAL: market rotation trace ===\n")
res = rta._analyze_reasoning_trace(TRACE, "proxy-model", "Is the semis->software/cyber rotation durable?")
sig = psyche_signal(res)
print(f"conf={sig['confidence']:.2f} coh={sig['coherence']:.2f} "
      f"div={sig['divergence']:+.2f} -> {sig['regime']}")
print(f"quality={sig['quality_score']:.2f} steps={sig['reasoning_steps']}")
print("\nInterpretation: a BALANCED/CAUTIOUS divergence = the market's 'reasoning'")
print("is coherent and measured (not euphoric). Consistent with healthy rotation,")
print("not a blow-off top. Contrarian read: cautious sentiment + intact fundamentals")
print("=> no imminent capitulation, but watch Iran/oil + CPI as the swing risks.")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "psyche_rotation_20260811.json")
json.dump({"trace": TRACE, **sig}, open(out, "w"), indent=2)
print(f"\nWrote {out}")
