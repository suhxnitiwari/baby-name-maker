# ISTAT (Italy) "Conta nomi": first names given to babies born in Italy (resident population), by year and sex, 1999 onward,
# from the web service behind istat.it/dati/calcolatori/contanomi (index2022.php, JSONP). One file per year and sex:
#   raw/it-istat-contanomi/YYYY-[fm].json  = {"year", "sex", "complete": bool, "rows": [[NAME, count], ...]}
#
# For 2022 onward the service returns the full list (every name, down to 1 baby). For 1999-2021 it returns an empty
# answer as soon as the list reaches one particular row (most likely a badly encoded name in ISTAT's older table), so for
# those years the longest list it will return is kept, found by doubling and then halving the limit, and "complete" is false.
#
#   python3 scripts/fetch_istat_names.py [YEAR ...]
import json, os, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(HERE), "raw", "it-istat-contanomi")
WS = "https://www.istat.it/wp-content/themes/EGPbs5-child/contanomi/nati/index2022.php"
UA = {"User-Agent": "Lullabyte name builder (https://github.com/suhxnitiwari)"}
FULL = 200_000

def call(**q):
    url = WS + "?" + "&".join(f"{k}={v}" for k, v in q.items()) + "&callback=callback"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r: t = r.read().decode("utf-8")
            break
        except Exception as e:
            print(f"    {q}: {e}; retrying", flush=True); time.sleep(10 * (attempt + 1))
    else: raise SystemExit("ISTAT service kept failing")
    time.sleep(0.5)
    body = t[t.index("(") + 1:t.rindex(")")]
    return json.loads(body) if body.strip() else None

def rows(d):
    return [[r["name"], r["count"]] for k, v in d.items() if k != "years" for r in v if r.get("name") and r.get("count")]

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    url = WS + "?type=years&callback=callbackY"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: t = r.read().decode()
    years = json.loads(t[t.index("(") + 1:t.rindex(")")])
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}   # optional: just these years (to run several fetches side by side)
    for y in years:
        if only and y not in only: continue
        for sx in "fm":
            p = os.path.join(RAW, f"{y}-{sx}.json")
            if os.path.exists(p): continue
            d = call(type="list", limit=FULL, year=y, gender=sx)
            complete = d is not None
            if not complete:
                lo, hi = 10, None   # lo answers, hi doesn't
                while hi is None:
                    n = lo * 2
                    if call(type="list", limit=n, year=y, gender=sx) is None: hi = n
                    else: lo = n
                while hi - lo > 1:
                    m = (lo + hi) // 2
                    if call(type="list", limit=m, year=y, gender=sx) is None: hi = m
                    else: lo = m
                d = call(type="list", limit=lo, year=y, gender=sx)
            rs = rows(d)
            json.dump({"year": y, "sex": sx, "complete": complete, "rows": rs}, open(p, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {y} {sx}: {len(rs):,} names{'' if complete else ' (cut off by the service)'}", flush=True)
