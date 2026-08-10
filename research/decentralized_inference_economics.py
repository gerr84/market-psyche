#!/usr/bin/env python3
"""Empirical check of the '8x RTX 5090 decentralized inference = money incinerator' hot take.
Constants sourced from web (EIA Aug-2026 residential 18.44c/kWh; RTX 5090 TDP 575W jarvislabs;
vast.ai 5090 $0.27-0.44/hr; cloud A100 $1.99-2.79/hr, H100 $4-6.88/hr on-demand).
"""
# --- inputs (real, dated) ---
TDP_W = 575.0          # RTX 5090 TDP (spec)
N = 8
sys_overhead = 1.12    # PSU + CPU + fans ~12% on top of GPU draw
kwh_price_res = 0.1844 # US avg residential $/kWh (EIA Aug-2026)
kwh_price_com = 0.1354 # US avg commercial $/kWh
hours = 24 * 30        # ~month, 24/7

gpu_kw = TDP_W * N / 1000.0           # 4.6 kW GPU draw
total_kw = gpu_kw * sys_overhead       # ~5.15 kW realistic

# --- his electricity claim ---
elec_res = total_kw * hours * kwh_price_res
elec_com = total_kw * hours * kwh_price_com
print("=== ELECTRICITY (his '$600/mo') ===")
print(f"  GPU draw:        {gpu_kw:.2f} kW  ({N}x {TDP_W:.0f}W)")
print(f"  +12% overhead:    {total_kw:.2f} kW")
print(f"  Residential:     ${elec_res:,.0f}/mo  @ {kwh_price_res*100:.2f}c/kWh")
print(f"  Commercial:      ${elec_com:,.0f}/mo  @ {kwh_price_com*100:.2f}c/kWh")
print(f"  -> his $600 is {'about right' if 500<elec_res<750 else 'OFF'}: residential = ${elec_res:,.0f}")

# --- his '$2,000/mo required from users' (assume ~30% take / margin needed) ---
for take in (0.30, 0.25, 0.20):
    req = elec_res / take
    print(f"  need gross @ {int(take*100)}% take to cover elec(res): ${req:,.0f}/mo")

# --- cloud comparison: what does equivalent-capacity actually cost to RENT? ---
# 8x 5090 on vast.ai spot
price_5090 = 0.35  # midpoint of 0.27-0.44
rent_8x5090 = price_5090 * N * hours
# cloud A100 on-demand (better than 5090 for most inference)
rent_a100 = 2.40 * N * hours   # ~$2.40/hr midpoint
# H100 on-demand
rent_h100 = 5.50 * N * hours
print("\n=== WHAT USERS PAY TO RENT INSTEAD (cloud) ===")
print(f"  8x RTX 5090 @ ${price_5090}/hr (vast.ai):   ${rent_8x5090:,.0f}/mo")
print(f"  8x A100    @ $2.40/hr (on-demand):        ${rent_a100:,.0f}/mo")
print(f"  8x H100    @ $5.50/hr (on-demand):        ${rent_h100:,.0f}/mo")

# --- the actual arb: owner's elec cost vs what they can CHARGE ---
# If a decentralized operator charges vast.ai-equivalent ($0.35/hr/GPU):
gross_at_vaas = price_5090 * N * hours
net_vs_elec_res = gross_at_vaas - elec_res
print("\n=== OPERATOR ECONOMICS (if they charge vast.ai rate) ===")
print(f"  Gross @ $0.35/GPU/hr:   ${gross_at_vaas:,.0f}/mo")
print(f"  Less elec (res):       ${elec_res:,.0f}/mo")
print(f"  Residual (pre-capex, pre-staff, pre-cooling-PUE): ${net_vs_elec_res:,.0f}/mo")

print("\n=== VERDICT ===")
print("  His electricity math: REAL (residential ~${}/mo, he said $600).".format(round(elec_res)))
print("  His 'needs $2k/mo' math: DEPENDS on take rate; at 30pct take, ${}/mo gross.".format(round(elec_res/0.30)))
print("  The gap he misses: renters pay ${}/mo for 8x5090 on vast.ai ALONE ->".format(rent_8x5090))
print("    an operator CAN charge ~that and cover elec with ${}/mo to spare (pre other costs).".format(net_vs_elec_res))
print("  BUT: that residual must also cover CAPEX amortization (~$1.5-2k/GPU = $12-16k for 8),")
print("    staff, cooling PUE (1.1-1.4x), downtime, and customer acquisition.")
print("  Net: he's RIGHT that naive 'idle GPU Uber' is thin; WRONG that it's a pure")
print("    incinerator -- the real failure is no SLA-adjusted spot market, not the watts.")
