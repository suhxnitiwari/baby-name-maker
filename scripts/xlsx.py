# Minimal .xlsx reader (no openpyxl): yields rows of cell values for a sheet.
import zipfile, re, xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

def col_index(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1

def rows(path, sheet_name):
    z = zipfile.ZipFile(path)
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid = next(s.get(R) for s in wb.iter("{%s}sheet" % NS["m"]) if s.get("name") == sheet_name)
    target = next(r.get("Target") for r in rels if r.get("Id") == rid).lstrip("/")
    target = target if target.startswith("xl/") else "xl/" + target
    for _, row in ET.iterparse(z.open(target)):
        if row.tag != "{%s}row" % NS["m"]:
            continue
        out = []
        for c in row.findall("m:c", NS):
            i = col_index(c.get("r")); v = c.find("m:v", NS); t = c.get("t")
            val = None
            if t == "s" and v is not None: val = ss[int(v.text)]
            elif t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
            elif v is not None: val = v.text
            while len(out) < i: out.append(None)
            out.append(val)
        yield out
        row.clear()
