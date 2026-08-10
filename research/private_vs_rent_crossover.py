#!/usr/bin/env python3
"""Cost-benefit: private/colo AI vs renting from DigitalOcean (DOCN).

Answers: when does owning a private H100 node (colo) beat renting DOCN?
Real constants (dated, sourced):
  - H100 8-GPU node capex ~ $300,000 (DGX-class, ~$35k/GPU all-in) [cloudzero/haink 2026]
  - DOCN H100 on-demand $4.41/GPU/hr; reserved 12mo $3.26/GPU/hr [DO pricing 2026]
  - DOCN bills full rate even when powered off (reserves capacity) [DO billing docs]
  - Colo power all-in ~$0.10/kWh; PUE 1.5; H100 node ~10kW IT -> 15kW facility
    [texaselectricbroker 2026; LinkedIn PUE 1.5]
  - Colo space+network ~$1,500/mo; maintenance ~4% capex/yr
  - Amortize capex over 36 months
"""
# --- inputs (real, dated) ---
CAPEX = 300_000.0          # 8x H100 node
NGPU = 8
AMORT_MONTHS = 36
POWER_KW_IT = 10.0         # H100 node IT draw
PUE = 1.5
KWH_PRICE = 0.10           # colo all-in $/kWh
COLO_SPACE = 1500.0        # $/mo rack+net
MAINT_PCT = 0.04           # of capex / yr
DO_ONDEMAND = 4.41         # $/GPU/hr
DO_RESERVED = 3.26         # $/GPU/hr (12mo)
HOURS_24_7 = 730           # hrs/month

amort_mo = CAPEX / AMORT_MONTHS
maint_mo = CAPEX * MAINT_PCT / 12

def own_monthly(hours_on):
    """Monthly cost of owning+colo, given GPU-hours ON per month (power only when on)."""
    power_mo = POWER_KW_IT * PUE * hours_on * KWH_PRICE
    return amort_mo + maint_mo + COLO_SPACE + power_mo

def rent_monthly(hours_on, rate):
    """DOCN: bills for hours_on (and if you keep reserved 24/7, you pay 730)."""
    return rate * NGPU * hours_on

# --- crossover: own flat-ish vs rent linear ---
# Find hours/day where own == rent (on-demand) and (reserved)
print("=== PRIVATE (colo) vs RENT DOCN — 8x H100 node ===")
print(f"  Capex ${CAPEX:,.0f} | amort ${amort_mo:,.0f}/mo | maint ${maint_mo:,.0f}/mo | colo ${COLO_SPACE:,.0f}/mo")
print(f"  Power {POWER_KW_IT}kW IT x PUE {PUE} @ ${KWH_PRICE}/kWh\n")

print(f"{'hrs/day':>8s} {'own$/mo':>10s} {'rent ond$':>10s} {'rent res$':>10s} {'cheaper':>10s}")
crossover_ond = crossover_res = None
for hpd in [2,4,6,8,10,11,12,14,16,24]:
    h = hpd * 30
    o = own_monthly(h)
    r_on = rent_monthly(h, DO_ONDEMAND)
    r_re = rent_monthly(h, DO_RESERVED)
    cheaper = "OWN" if o < r_on else "RENT"
    print(f"{hpd:>8d} {o:>10,.0f} {r_on:>10,.0f} {r_re:>10,.0f} {cheaper:>10s}")
    if crossover_ond is None and o <= r_on: crossover_ond = hpd
    if crossover_res is None and o <= r_re: crossover_res = hpd

print("\n=== CROSSOVER ===")
print(f"  Own beats DOCN on-demand when usage > ~{crossover_ond} hrs/day")
print(f"  Own beats DOCN reserved  when usage > ~{crossover_res} hrs/day")

# --- the 'kept reserved 24/7' case (DOCN bills when off) ---
own_24_7 = own_monthly(HOURS_24_7)
rent_24_7_on = rent_monthly(HOURS_24_7, DO_ONDEMAND)
rent_24_7_re = rent_monthly(HOURS_24_7, DO_RESERVED)
print(f"\n=== IF YOU KEEP A NODE RESERVED 24/7 (DOCN bills full even off) ===")
print(f"  Own (colo) 24/7:      ${own_24_7:,.0f}/mo")
print(f"  Rent DOCN on-demand:  ${rent_24_7_on:,.0f}/mo  -> own saves ${rent_24_7_on-own_24_7:,.0f}/mo ({ (rent_24_7_on/own_24_7-1)*100:.0f}% more)")
print(f"  Rent DOCN reserved:   ${rent_24_7_re:,.0f}/mo  -> own saves ${rent_24_7_re-own_24_7:,.0f}/mo")

# --- payback horizon ---
savings_24_7 = rent_24_7_on - own_24_7
payback_mo = CAPEX / savings_24_7 if savings_24_7 > 0 else float('inf')
print(f"\n  At 24/7: owning saves ${savings_24_7:,.0f}/mo -> capex payback in {payback_mo:.1f} months")

print("\n=== VERDICT ===")
print("  OWN/colo BEATS renting DOCN when:")
print("   (1) sustained usage > ~11 hrs/day (crossover from our numbers)")
print("   (2) you'd otherwise keep a DOCN node reserved 24/7 (they bill when off ->")
print("       owning ~2.2x cheaper at full tilt)")
print("   (3) data sovereignty / latency / compliance / dedicated-config needs")
print("  RENT DOCN wins when: low/intermittent (<11h/day), bursty, short horizon,")
print("   zero-capex/no-ops preference.")
print("  -> Hot-take 'renting always wins' is WRONG at high utilization; the")
print("     real lever is UTILIZATION, same as the neocloud thesis.")
