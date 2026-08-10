#!/usr/bin/env python3
"""Cheapest way to SELF-HOST a frontier open-weight model (DeepSeek-V4-Flash-0731
class = 671B MoE anchor) at >200K req/day.

Models real 2026 efficiency levers:
  - hardware: used H100 vs new H100 vs MI300X vs B200(alloc)
  - serving engine: vLLM vs SGLang (MoE efficiency)
  - colo power vs retail
  - aggressive batching (amortize fixed cost over tokens)
Anchors (dated, sourced in comments):
  - H100 new SXM5 $35-40k; USED $15-28k [cloudzero 2026]
  - MI300X 8-GPU node ~$642k new; 192GB/GPU (2.4x H100 mem) [hostrunway]
  - 671B on 8xH100 SGLang/MLA ~821 tok/s out [prior benchmark]
  - SGLang ~+30-50% vs vLLM on MoE [SGLang/Spheron 2026]
  - MI300X ~19% cheaper $/tok than H100 on DeepSeek R1 [InferenceX]
  - B200 ~2-5x cheaper $/tok than H100 (alloc-only) [NVIDIA/Spheron]
  - colo power $0.10/kWh, PUE 1.5 [prior]; DOCN reserved 8x $19,038/mo
"""
# --- workload ---
REQ_DAY = 200_000
OUT_TOK = 300
OUT_TOK_DAY = REQ_DAY * OUT_TOK          # 60M/day
HOURS_MO = 730
OUT_TOK_MO = OUT_TOK_DAY * 30            # ~1.8B/mo

# --- hardware + efficiency ---
COLO_SPACE = 1500.0
MAINT_PCT = 0.04
KWH = 0.10
PUE = 1.5

# node throughput (tok/s out) and capex (used vs new) and power
# 8xH100 base = 821 tok/s with SGLang; vLLM ~0.7x
H100_TPS_SGLANG = 821.0
H100_TPS_VLLM = 821.0 * 0.70
MI300_TPS = 821.0 * 1.19        # 19% cheaper $/tok => effective throughput/$ up 19%
B200_TPS = 821.0 * 3.0          # conservative: ~3x H100 token efficiency (NVIDIA says 2-5x)

# capex
H100_NEW = 8 * 38000.0          # $304k new SXM5
H100_USED = 8 * 22000.0         # $176k used (~mid of 15-28k)
MI300_8 = 642_000.0             # new 8-GPU node
B200_8 = 8 * 45000.0            # ~$360k (HGX B200 premium)

POWER_KW = {"H100": 10.0, "MI300X": 9.0, "B200": 10.0}  # IT draw per 8-GPU node

def config_cost(name, tps, capex, power_kw, engine_mult=1.0, amort=36, used=False):
    """Monthly cost of owning+colo a node sized to 200K req/day (need ~1 node)."""
    amort_mo = capex / amort
    maint_mo = capex * MAINT_PCT / 12
    # at 200K req/day we need throughput >= OUT_TOK_DAY/s = 60M/86400 = 694 tok/s
    # all configs exceed that, so 1 node; power at full tilt
    power_mo = power_kw * PUE * HOURS_MO * KWH
    total = amort_mo + maint_mo + COLO_SPACE + power_mo
    # effective $/M out tok
    eff_tps = tps * engine_mult
    tok_mo = eff_tps * HOURS_MO * 3600
    cost_per_m = total / tok_mo * 1e6
    return dict(name=name, capex=capex, total_mo=total, cost_per_m=cost_per_m,
                eff_tps=eff_tps, tok_mo=tok_mo)

print(f"Workload: {REQ_DAY:,} req/day x {OUT_TOK} out tok = {OUT_TOK_DAY/1e6:.0f}M out tok/day = {OUT_TOK_MO/1e9:.2f}B/mo")
print(f"Required throughput: {OUT_TOK_DAY/86400:.0f} tok/s (all 8-GPU nodes exceed this)\n")

configs = []
# A: new 8xH100 + vLLM (naive baseline)
configs.append(config_cost("A new 8xH100 + vLLM (naive)", H100_TPS_VLLM, H100_NEW, POWER_KW["H100"], engine_mult=1.0))
# B: USED 8xH100 + SGLang (pragmatic cheapest Hopper)
configs.append(config_cost("B USED 8xH100 + SGLang (pragmatic)", H100_TPS_SGLANG, H100_USED, POWER_KW["H100"], engine_mult=1.0))
# C: 8x MI300X + SGLang (AMD density)
configs.append(config_cost("C 8x MI300X + SGLang (AMD)", MI300_TPS, MI300_8, POWER_KW["MI300X"], engine_mult=1.0))
# D: B200 + SGLang (theoretical floor, alloc-only)
configs.append(config_cost("D 8x B200 + SGLang (alloc-only)", B200_TPS, B200_8, POWER_KW["B200"], engine_mult=1.0))

# SGLang uplift applied to A-equivalent for comparison note
print(f"{'config':42s} {'capex$k':>8s} {'$/mo':>9s} {'$/Mtok':>8s}")
for c in configs:
    print(f"{c['name']:42s} {c['capex']/1000:>8.0f} {c['total_mo']:>9,.0f} {c['cost_per_m']:>8.2f}")

# comparisons
docn_m = 19038.0
docn_per_m = 8.82   # from prior model
api_per_m = 0.40    # hosted Flash API

best = min(configs, key=lambda c: c['cost_per_m'])
print(f"\n=== RANKING (cheapest self-host $/M out tok) ===")
for i,c in enumerate(sorted(configs, key=lambda x:x['cost_per_m']),1):
    print(f"  {i}. {c['name']}: ${c['cost_per_m']:.2f}/M tok (${c['total_mo']:,.0f}/mo)")

print(f"\n=== VS ALTERNATIVES ===")
print(f"  DOCN reserved 8xH100:      ${docn_per_m:.2f}/M tok (${docn_m:,.0f}/mo)  -> self-host B beats by {docn_per_m/best['cost_per_m']:.1f}x")
print(f"  Hosted API (Flash):        ${api_per_m:.2f}/M tok  -> API still {best['cost_per_m']/api_per_m:.1f}x cheaper than self-host on $")
print(f"  => Self-host cheapest CONFIG is D (B200, alloc-only) ${best['cost_per_m']:.2f}/M tok;")
print(f"     cheapest OBTAINABLE is B (USED H100+SGLang) $3.74/M tok.")

print(f"\n=== REALITY CHECK ===")
print(f"  B200 would be ~3x cheaper/tok than H100 (NVIDIA: 2-5x) BUT allocation-only;")
print(f"  if obtainable, D ~ ${configs[3]['cost_per_m']/3:.2f}/M tok -> the true floor.")
print(f"  Serving ENGINE matters: SGLang vs vLLM swings cost ~30-40% on MoE.")
print(f"  At 200K req/day, ~1 node suffices; the lever is BUY USED + SGLang + colo,")
print(f"  NOT renting. But a Blackwell-backed API (Fireworks/Together) still wins on $.")
