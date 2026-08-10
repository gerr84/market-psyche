import json, time, urllib.request, urllib.parse, http.cookiejar, datetime as dt, os
UA=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT=os.path.dirname(os.path.abspath(__file__))
SYMS=["CRWV","AKAM","DOCN","NET","CLSK","PLTR"]  # PLTR=AI-demand bellwether; CLSK=compute-adjacent
_S={"op":None,"crumb":None}
def _sess():
    if _S["op"] and _S["crumb"]: return _S["op"],_S["crumb"]
    cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders=[("User-Agent",UA),("Accept","*/*")]
    for s in ("https://fc.yahoo.com","https://finance.yahoo.com"):
        try: op.open(s,timeout=15).read()
        except Exception: pass
        if len(cj): break
    cr=None
    for h in ("query1.finance.yahoo.com","query2.finance.yahoo.com"):
        try:
            cr=op.open(f"https://{h}/v1/test/getcrumb",timeout=15).read().decode().strip()
            if cr and "<" not in cr: break
        except Exception: cr=None
    _S["op"],_S["crumb"]=op,cr; return op,cr
def quote(s):
    op,cr=_sess()
    for h in ("query1.finance.yahoo.com","query2.finance.yahoo.com"):
        try:
            q={"symbols":s}
            if cr: q["crumb"]=cr
            u=f"https://{h}/v7/finance/quote?"+urllib.parse.urlencode(q)
            d=json.loads(op.open(u,timeout=20).read().decode())
            r=d.get("quoteResponse",{}).get("result",[])
            if r: return r[0]
        except urllib.error.HTTPError as e:
            if e.code in (401,403): _S["op"]=_S["crumb"]=None; break
        except Exception: continue
    return None
def daily(s,start="2025-05-01",end="2026-08-10"):
    p1=int(dt.datetime.strptime(start,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    p2=int(dt.datetime.strptime(end,"%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1={p1}&period2={p2}&interval=1d&events=history"
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Pragma":"no-cache"})
    with urllib.request.urlopen(req,timeout=25) as r:
        j=json.loads(r.read().decode("utf-8","replace"))
    ts=j["chart"]["result"][0]["timestamp"]; q=j["chart"]["result"][0]["indicators"]["quote"][0]
    b=[(dt.datetime.utcfromtimestamp(t).date().isoformat(),float(c)) for i,t in enumerate(ts) if (c:=q["close"][i]) is not None]
    return b
out={"date":"2026-08-10","note":"neocloud utilization PROXY: price trend + fwd metrics (direct GPU util not public)","symbols":{}}
for s in SYMS:
    row={"symbol":s}; q=quote(s)
    if q:
        row["price"]=q.get("regularMarketPrice"); row["fPE"]=q.get("forwardPE")
        row["mktcap_B"]=round((q.get("marketCap") or 0)/1e9,1) if q.get("marketCap") else None
        row["day_%"]=q.get("regularMarketChangePercent"); row["quote_ok"]=True
    else: row["quote_ok"]=False
    try:
        b=daily(s); d=[x[0] for x in b]; c=[x[1] for x in b]
        def ret(k): return round((c[-1]/c[-1-k]-1)*100,2) if len(c)>k else None
        row["ret_21d_%"]=ret(21); row["ret_60d_%"]=ret(60); row["ret_250d_%"]=ret(250)
    except Exception as e: row["err"]=str(e)
    out["symbols"][s]=row; time.sleep(0.5)
p=os.path.join(OUT,"neocloud_probe_20260810.json")
json.dump(out,open(p,"w"),indent=2)
print("Wrote",p)
print(f"{'SYM':5s}{'price':>9s}{'fPE':>8s}{'capB':>8s}{'21d%':>7s}{'60d%':>7s}{'250d%':>8s}")
for s,r in out["symbols"].items():
    print(f"{s:5s}{str(r.get('price')):>9s}{str(r.get('fPE')):>8s}{str(r.get('mktcap_B')):>8s}{str(r.get('ret_21d_%')):>7s}{str(r.get('ret_60d_%')):>7s}{str(r.get('ret_250d_%')):>8s}")
