"""Fetch labels for every QID-labelled person or associate (Wikidata 'mul' labels no longer surface as en in SPARQL)."""
import json, re, pathlib, urllib.request, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parents[1]; RAW = ROOT / "data" / "raw"
out = RAW / "people-labels-fix.json"
fix = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
ids = set()
for f in RAW.glob("rel-*.json"):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r["person"] and re.match(r"^Q\d+$", r["personLabel"] or ""): ids.add(r["person"])
for r in json.loads((RAW / "people-associates.json").read_text(encoding="utf-8")):
    if r["other"] and re.match(r"^Q\d+$", r["otherLabel"] or ""): ids.add(r["other"])
ids = sorted(i for i in ids if i not in fix)
print(len(ids), "to fetch")
for i in range(0, len(ids), 50):
    batch = ids[i:i+50]
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(batch), "props": "labels|sitelinks", "languages": "en|mul", "sitefilter": "enwiki", "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "strand-prototype/0.1 (dan.s@systemsdna.com)"})
    for q, e in json.load(urllib.request.urlopen(req, timeout=60)).get("entities", {}).items():
        labs = e.get("labels", {}); lab = (labs.get("en") or labs.get("mul") or {}).get("value") or e.get("sitelinks", {}).get("enwiki", {}).get("title")
        if lab: fix[q] = lab
out.write_text(json.dumps(fix, ensure_ascii=False), encoding="utf-8")
print(len(fix), "labels in fix file")
