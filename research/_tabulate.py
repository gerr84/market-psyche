import json
d = json.load(open("research/valuation_snapshot_20260809.json"))
print("%-5s %9s %7s %7s %8s %7s %7s %7s %7s" % ("SYM", "price", "tPE", "fPE", "cap$B", "21d%", "60d%", "%52w", "day%"))
for s, r in d["symbols"].items():
    print("%-5s %9s %7s %7s %8s %7s %7s %7s %7s" % (
        s, r.get("price"), r.get("trailingPE"), r.get("forwardPE"),
        r.get("marketCap_B"), r.get("ret_21d_%"), r.get("ret_60d_%"),
        r.get("pct_of_52w_range"), r.get("day_chg_%")))
