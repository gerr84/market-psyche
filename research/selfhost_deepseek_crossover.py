#!/usr/bin/env python3
"""When does a company self-host a frontier open-weight model (DeepSeek-V4-Flash-0731 class)?

Reframes the private-vs-rent question into REQUESTS/DAY and COMPANY SIZE.
Anchors (real, dated 2026):
  - 671B MoE on 8xH100 (640GB FP8): ~821 tok/s output [GitHub deploy benchmark]
  - 8xH100 capex ~$300k; own colo ~$11,913/mo [prior model]
  - 8xH100 DOCN reserved $19,038/mo; on-demand $25,754/mo; Spheron dedicated ~$11,520/mo
  - Hosted API for Flash-class (Fireworks-style) est $0.10-0.50/1M out tok (multi-tenant cheap)
NOTE: DeepSeek-V4-Flash-0731 exact size unverified; 671B is the conservative (max-GPU) anchor.
A smaller 'Flash' model would need 1-2x H100 -> lower crossover.
"""
CAPEX_8H100 = 300_000.0
OWN_8H100_MO = 11_913.0      # colo own, 24/7 [prior model]
DOCN_RES_MO = 19_038.0       # 8xH100 reserved
DOCN_OND_MO = 25_754.0       # 8xH100 on-demand
SPHERON_MO = 11_520.0        # 8xH100 dedicated
HOURS_MO = 730
TPUT_OUT = 821.0             # tok/s output, 671B on 8xH100
API_PER_1M = 0.40            # hosted Flash API est $/1M out tok (cheap, multi-tenant)

# tokens a single 24/7 node delivers/month (output side, GPU-bound)
TOK_PER_NODE_MO = TPUT_OUT * HOURS_MO * 3600   # ~2.16B out tok/mo

# avg request shape
AVG_OUT = 300.0              # output tokens per request (enterprise chat/RAG/agent step)
AVG_IN = 1000.0

print("=== SELF-HOST 671B-CLASS (8xH100) — unit economics ===")
print(f"  Node delivers ~{TOK_PER_NODE_MO/1e9:.2f}B output tok/mo @ {TPUT_OUT:.0f} tok/s")
print(f"  = ~{TOK_PER_NODE_MO/AVG_OUT/1e3:.0f}K requests/mo (@{AVG_OUT:.0f} out tok/req) at full tilt\n")

print("  Cost per 1M OUTPUT tokens:")
print(f"    Own colo 8xH100:      ${OWN_8H100_MO/TOK_PER_NODE_MO*1e6:.2f}")
print(f"    Spheron dedicated:    ${SPHERON_MO/TOK_PER_NODE_MO*1e6:.2f}")
print(f"    DOCN reserved 8x:     ${DOCN_RES_MO/TOK_PER_NODE_MO*1e6:.2f}")
print(f"    DOCN on-demand 8x:    ${DOCN_OND_MO/TOK_PER_NODE_MO*1e6:.2f}")
print(f"    Hosted API (Flash):   ${API_PER_1M:.2f}  (multi-tenant, ~10-14x cheaper than own)")

# --- crossover vs RENTING GPUs (DOCN) in requests/day ---
# own beats DOCN when node active > ~11 hrs/day (prior model). Convert to req/day.
# active hrs/day * TPUT * 3600 = out tok/day; /AVG_OUT = req/day
def req_per_day(active_hrs):
    return active_hrs * TPUT_OUT * 3600 / AVG_OUT

print("\n=== CROSSOVER vs RENTING 8xH100 (DOCN) ===")
for h in [8,11,16,24]:
    print(f"  {h:>2} hrs/day active = ~{req_per_day(h)/1e3:.0f}K requests/day  -> {'OWN' if h>=11 else 'RENT'}")

# --- crossover vs HOSTED API in $/mo ---
# own cost $OWN_8H100_MO/mo regardless of volume (fixed). API cost = API_PER_1M * out_tok.
# own beats API only if API $/1M > own $/1M (~$5.5). Since API ~$0.40, own NEVER wins on $.
api_vol_for_own = OWN_8H100_MO / API_PER_1M * 1e6   # out tok/mo needed for API to cost = own
print("\n=== vs HOSTED API (Flash) ===")
print(f"  Own cost is FIXED ${OWN_8H100_MO:,.0f}/mo (one node, 24/7).")
print(f"  API equals that cost only at {api_vol_for_own/1e9:.1f}B out tok/mo = {api_vol_for_own/AVG_OUT/1e6:.1f}M requests/mo.")
print(f"  Since API ~${API_PER_1M}/1M << own ~${OWN_8H100_MO/TOK_PER_NODE_MO*1e6:.2f}/1M, API wins on $ at ANY volume.")
print(f"  Self-host vs API justified ONLY by: sovereignty/compliance, dedicated latency/SLA,")
print(f"  or capacity you can't get from the API.")

print("\n=== COMPANY-SIZE FRAMING (671B anchor) ===")
print("  < ~50K req/day (<<11h active): RENT GPUs or USE API. Self-host not sensible.")
print("  ~50-100K req/day + compliance: consider self-host (colo) on sovereignty grounds.")
print("  > ~100K req/day (>=11h active): self-host 8xH100 BEATS renting DOCN on $.")
print("  > ~230K req/day (24/7 full tilt): max utilization, own ~1.6x cheaper than DOCN reserved.")

print("\n=== If V4-Flash-0731 is SMALLER (e.g. 70B, 1-2x H100) ===")
print("  Capex drops to ~$40-80k; own fixed cost ~$2-4k/mo; crossover vs DOCN drops to")
print("  ~15-30K req/day. A SMALLER company self-hosts sooner. Still loses vs cheap API on $.")

print("\n=== VERDICT ===")
print("  Universal answer depends on UTILIZATION + ALTERNATIVE:")
print("   vs rent-GPUs(DOCN): sensible above ~100K req/day (>=11h active) OR compliance.")
print("   vs hosted-API: sensible ONLY for sovereignty/latency/capacity, never on pure $.")
print("   This is the SAME utilization lever as the neocloud + decentralized theses.")
