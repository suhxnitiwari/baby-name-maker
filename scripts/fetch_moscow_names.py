# Downloads the Moscow Government open datasets of names given to newborns, by month since 2015 (Moscow civil registry,
# Управление ЗАГС города Москвы), into raw/ru/:
#   data.mos.ru dataset 2009  "Сведения о наиболее популярных женских именах среди новорожденных" (7704111479-FemaleNames)
#   data.mos.ru dataset 2011  "Сведения о наиболее популярных мужских именах среди новорожденных"
# Each row is one name in one month: Name (Имя), NumberOfPersons (Количество человек), Year (Год), Month (Месяц).
# Licence: open data under Russian Government decree No. 583 of 10 July 2013; reuse is free with a link to data.mos.ru
# (data.mos.ru/about/terms).
#
# data.mos.ru, op.mos.ru and apidata.mos.ru refuse connections from outside Russia. If this script can't reach them, open
# https://data.mos.ru/opendata/2009 and https://data.mos.ru/opendata/2011, choose Export → JSON (or CSV), and save the
# files (zipped or not) as raw/ru/moscow-names-2009.<json|csv|zip> and raw/ru/moscow-names-2011.<json|csv|zip>.
# With an apidata.mos.ru key in MOS_API_KEY the script reads the rows through the API instead.
#
#   python3 scripts/fetch_moscow_names.py
import json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RAW = os.path.join(ROOT, "raw", "ru")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
DATASETS = {"2009": "girls", "2011": "boys"}

def get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def via_api(ds, key):
    rows, skip = [], 0
    while True:
        page = json.loads(get(f"https://apidata.mos.ru/v1/datasets/{ds}/rows?api_key={key}&$top=1000&$skip={skip}"))
        rows += page
        if len(page) < 1000: return rows
        skip += 1000

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    key = os.environ.get("MOS_API_KEY")
    for ds, who in DATASETS.items():
        if any(os.path.exists(os.path.join(RAW, f"moscow-names-{ds}.{x}")) for x in ("json", "csv", "zip")):
            print(f"  {ds} ({who}): already in raw/ru"); continue
        try:
            if key:
                data = json.dumps(via_api(ds, key), ensure_ascii=False).encode()
                ext = "json"
            else:
                data = get(f"https://data.mos.ru/opendata/export/{ds}/json")
                ext = "zip" if data[:2] == b"PK" else "json"
            open(os.path.join(RAW, f"moscow-names-{ds}.{ext}"), "wb").write(data)
            print(f"  {ds} ({who}): {len(data):,} bytes")
        except Exception as e:
            print(f"  {ds} ({who}): could not download ({e}). Export it from https://data.mos.ru/opendata/{ds} "
                  f"and save it as raw/ru/moscow-names-{ds}.json, .csv or .zip", file=sys.stderr)
