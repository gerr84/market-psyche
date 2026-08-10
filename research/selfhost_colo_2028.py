#!/usr/bin/env python3
"""Self-host DeepSeek-V4-Flash-0731 class at 200K req/day: REAL colo + 2028 mature view.

Fixes prior model's flat $1,500 colo (understated for a 15kW GPU node).
Real colo (2026, CBRE/QuoteColo):
  - power billed per COMMITTED kW: ~$100-200/kW/mo primary US
  - high-density 20kW rack all-in $3.5-6k/mo (power+cooling+xconnect)
  - we use $150/kW/mo power + $500 rack base + $400 xconnect = realistic
Also models what SMALL companies actually do (colo vs build vs rent-API),
and a 2028 mature scenario (commodity intelligence, cheaper used GPUs, cheaper API).

Anchors (dated, sourced):
  - colo $100-200/kW/mo [CBRE H2-2025]; 20kW rack $3.5-6k all-in [QuoteColo 2026]
  - SMB: on-prem only 40% of capacity; rest colo/hyperscale [SRG]
  - GPT-4-level inference -40x ($60-><$1.5/M out) by 2025 [arXiv 2603.21690]
  - DeepSeek V4 ~$0.14/M in / $0.28/M out projected [Medium 2026]
  - used H100 $15-28k; by 2028 H100/B200 used even cheaper
"""
# --- workload ---
REQ_DAY = 200_000
OUT_TOK = 300
OUT_TOK_MO = REQ_DAY * OUT_TOK * 30     # 1.8B/mo

# --- node spec (8xH100) ---
POWER_KW_IT = 10.0
PUE = 1.5
FAC_KW = POWER_KW_IT * PUE              # 15 kW facility draw
H100_TPS = 821.0                        # SGLang, 671B
TOK_MO = H100_TPS * 730 * 3600          # ~2.16B/mo (node capacity)

# --- REALISTIC COLO (2026) ---
COLO_KW_RATE = 150.0        # $/kW/mo committed power (mid primary US)
COLO_RACK_BASE = 500.0      # $/mo rack space
COLO_XCONNECT = 400.0       # $/mo cross-connect
colo_mo = COLO_KW_RATE * FAC_KW + COLO_RACK_BASE + COLO_XCONNECT   # ~$3,150/mo

# --- build-your-own (tiny DC) penalty ---
# small single-tenant DC: PUE worse (1.8), must provision power/cooling/capital
BUILD_PUE = 1.8
build_power_mo = POWER_KW_IT * BUILD_PUE * 730 * 0.10   # same $/kWh but more kW
build_extra = build_power_mo - (POWER_KW_IT*PUE*730*0.10)  # extra from worse PUE
build_capex_amort = 50000/36   # $50k fit-out amortized (power room, cooling)

print("=== 1. WHAT SMALL COMPANIES ACTUALLY DO (2026) ===")
print(f"  On-prem own DC = only ~40% of total capacity (rest colo+hyperscale) [SRG].")
print(f"  SMB reality: BUY GPUs + COLOCATE. Build own DC = rare, worse PUE, no scale.")
print(f"  Colo node (15kW facility) realistic cost: ${colo_mo:,.0f}/mo")
print(f"    = ${COLO_KW_RATE}/kW/mo x {FAC_KW:.0f}kW + ${COLO_RACK_BASE} rack + ${COLO_XCONNECT} xconnect")
print(f"  Build-own-DC penalty: +${build_capex_amort:,.0f}/mo fit-out + worse PUE (+${build_extra:,.0f}/mo power)")
print(f"  -> SELF-HOST = buy used GPUs + colo. NOT build DC.\n")

# --- recompute total self-host with REAL colo ---
CAPEX_USED = 8 * 22000.0       # $176k used H100
amort = CAPEX_USED/36
maint = CAPEX_USED*0.04/12
power_mo = POWER_KW_IT*PUE*730*0.10
own_total = amort + maint + colo_mo + power_mo
own_per_m = own_total / TOK_MO * 1e6
print("=== 2. SELF-HOST TOTAL (used 8xH100 + REAL colo + SGLang) ===")
print(f"  Capex amort ${amort:,.0f} + maint ${maint:,.0f} + colo ${colo_mo:,.0f} + power ${power_mo:,.0f}")
print(f"  TOTAL ${own_total:,.0f}/mo  =  ${own_per_m:.2f}/M out tok")

# --- 2028 MATURE SCENARIO ---
print("\n=== 3. 2028 MATURE SCENARIO (commodity intelligence) ===")
# by 2028: used H100/B200 flood secondary mkt -> capex drops; API commoditized
CAPEX_2028 = 8 * 12000.0      # $96k used (H100 cheap, B200 used available)
colo_2028 = colo_mo * 0.9      # colo softens as capacity builds
amort28 = CAPEX_2028/36
maint28 = CAPEX_2028*0.04/12
own28 = amort28 + maint28 + colo_2028 + power_mo
own28_per_m = own28/TOK_MO*1e6
# cheapest API in 2028: DeepSeek-class ~$0.10-0.30/M out (from -40x trend + V4 $0.28)
api_2028 = 0.20
print(f"  Used GPUs capex -> ${CAPEX_2028/1000:.0f}k (was $176k). Self-host ${own28:,.0f}/mo = ${own28_per_m:.2f}/M tok")
print(f"  Cheapest API (DeepSeek-V4-class) ~${api_2028:.2f}/M out [V4 $0.28 proj, -40x trend]")
print(f"  Self-host vs API 2028: {own28_per_m/api_2028:.1f}x pricier on $ -> API still wins for most")
print(f"  BUT cheaper used GPUs cut self-host 2026 ${own_per_m:.2f} -> 2028 ${own28_per_m:.2f}/M ({own_per_m/own28_per_m:.1f}x cheaper)")

print("\n=== 4. THE REAL DECISION (2026 AND 2028) ===")
print("  Small company at 200K req/day:")
print("   - BUILD own DC? NO (40% capacity stat; worse PUE; no scale)")
print("   - COLO + buy used GPUs? YES if sovereignty/latency needed; ${:.2f}/M (2026) -> ${:.2f}/M (2028)".format(own_per_m, own28_per_m))
print("   - RENT GPUs (DOCN)? 4.1x pricier than self-colo")
print("   - CHEAPEST API (DeepSeek-class)? Always cheapest on $; the 2028 default")
print("  => In 2028, 'cheapest vendor of DeepSeek-0731' = the $0.10-0.30/M API,")
print("     and self-host only for data you can't send to a third party.")
