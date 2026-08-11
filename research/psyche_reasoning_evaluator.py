#!/usr/bin/env python3
"""Human-psyche reasoning-trace evaluator (c).

Grounds in the REAL patented analyzer at:
  C:\\Users\\chees\\reasoning-trace-analyzer\\reasoning_trace_analyzer.py
which exposes:
  analyze(prompt, model_name, api_key, base_url, ...)   # live API
  _analyze_reasoning_trace(response_text, model, prompt) # offline, no key
Output dict: quality_score, reasoning_steps, coherence{coherence_score,...},
             step_analysis[].confidence{confidence_score,...}

PIVOT IDEA (from market-psyche thread):
  Treat a model's reasoning trace about a market/psychology prompt as a PROXY
  for crowd sentiment. The observable signal = CONFIDENCE - COHERENCE divergence.
  - High confidence + low coherence  => OVERCONFIDENT noise (euphoria / FOMO proxy)
  - Low confidence  + high coherence  => CAUTIOUS, well-grounded (capitulation/fear proxy)
  This is the order-flow-in-black-box lens: read the *structure* of the black
  box's reasoning, not its verdict.

Two modes:
  offline: score provided/embedded traces (no API key, reproducible, verifiable)
  live:    call analyzer.analyze(prompt,...) with a real key (env NOUS_API_KEY)
"""
import os, sys, json, statistics

# import the real analyzer (add its dir to path)
ANALYZER_DIR = r"C:\Users\chees\reasoning-trace-analyzer"
sys.path.insert(0, ANALYZER_DIR)
import reasoning_trace_analyzer as rta

# --- embedded sample market-psychology traces (stand-ins for crowd sentiment) ---
# Each: (label, prompt, response_text). These emulate what a model reasoning
# about markets/psychology would emit. Replace with live traces via --live.
SAMPLE_TRACES = [
    ("euphoric", "Is now a good time to buy AI infrastructure stocks?",
     "1. Clearly AI infrastructure is the defining trade of the decade.\n"
     "2. Definitely every dip is a buy, the trend is obviously unstoppable.\n"
     "3. Must accumulate because the upside is guaranteed and corrections won't happen.\n"
     "4. Obviously the commoditization narrative is overblown and margins will only expand."),
    ("cautious", "What are the risks if AI data-center buildout slows?",
     "1. First, I should consider whether power/consent bottlenecks could delay builds.\n"
     "2. It is possible that demand was pulled forward, so a pause might occur.\n"
     "3. However, hyperscaler capex guidance remains firm, which suggests caution not panic.\n"
     "4. Therefore the risk is real but uncertain; positioning should be balanced, not all-in."),
    ("mixed", "Will DeepSeek commoditization hurt neocloud margins?",
     "1. Likely the token price decline compresses neocloud spreads.\n"
     "2. But software/inference layers (DOCN) may hold value better than raw GPU rental (CRWV).\n"
     "3. Might depend on utilization; low-duty-cycle colo loses, high-util wins.\n"
     "4. So the answer is probably nuanced: margins fall for some, not all."),
]

def psyche_signal(result: dict) -> dict:
    """From analyzer output, compute the confidence-coherence divergence signal."""
    coh = result["coherence"]["coherence_score"]
    # overall confidence = mean of step confidence scores
    confs = [s["confidence"]["confidence_score"] for s in result.get("step_analysis", [])]
    conf = statistics.mean(confs) if confs else 0.5
    diverg = round(conf - coh, 4)
    # interpret
    if diverg > 0.15:
        regime = "OVERCONFIDENT (euphoria/FOMO proxy)"
    elif diverg < -0.15:
        regime = "CAUTIOUS (fear/capitulation proxy)"
    else:
        regime = "BALANCED"
    return {
        "confidence": round(conf, 4),
        "coherence": round(coh, 4),
        "divergence": diverg,
        "regime": regime,
        "quality_score": result.get("quality_score"),
        "reasoning_steps": result.get("reasoning_steps"),
    }

def run_offline():
    print("=== HUMAN-PSYCHE REASONING EVALUATOR (offline, real analyzer) ===\n")
    rows = []
    for label, prompt, text in SAMPLE_TRACES:
        res = rta._analyze_reasoning_trace(text, "proxy-model", prompt)
        sig = psyche_signal(res)
        rows.append((label, sig))
        print(f"[{label}] conf={sig['confidence']:.2f} coh={sig['coherence']:.2f} "
              f"div={sig['divergence']:+.2f} -> {sig['regime']}")
    # aggregate market-psyche read
    divs = [r[1]["divergence"] for r in rows]
    avg_div = round(statistics.mean(divs), 4)
    print(f"\nAggregate psyche divergence: {avg_div:+.2f}")
    print("  >0 => net overconfidence in sampled reasoning (contrarian caution)")
    print("  <0 => net caution (potential fear-driven opportunity)")
    # persist
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "psyche_reasoning_eval_20260810.json")
    json.dump([{"label": l, **s} for l, s in rows] +
              [{"aggregate_divergence": avg_div}], open(out, "w"), indent=2)
    print(f"Wrote {out}")
    return rows

def run_live(prompts, model="nousresearch/hermes-4-405b"):
    print("=== LIVE mode (requires NOUS_API_KEY) ===")
    rows = []
    for p in prompts:
        res = rta.analyze(p, model_name=model, out_path="live_trace.json")
        rows.append((p, psyche_signal(res)))
    for p, s in rows:
        print(f"[live] {p[:50]} -> {s['regime']} (div={s['divergence']:+.2f})")
    return rows

if __name__ == "__main__":
    if "--live" in sys.argv:
        prompts = [
            "Is now a good time to buy AI infrastructure stocks?",
            "What are the risks if AI data-center buildout slows?",
            "Will DeepSeek commoditization hurt neocloud margins?",
        ]
        run_live(prompts)
    else:
        run_offline()
