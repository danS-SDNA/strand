"""Merge data/raw/*.json into site/data/index.json + site/data/people/{qid}.json."""
import json, re, pathlib, collections, urllib.parse, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; OUT = ROOT / "site" / "data"; PEOPLE = OUT / "people"
PEOPLE.mkdir(parents=True, exist_ok=True)

def load(name): return json.loads((RAW / name).read_text(encoding="utf-8"))
def point(wkt):
    m = re.match(r"Point\((-?[\d.]+) (-?[\d.]+)\)", wkt or "")
    return (round(float(m.group(2)), 5), round(float(m.group(1)), 5)) if m else None
def year(d):
    m = re.match(r"(-?\d+)-", d or ""); return int(m.group(1)) if m else None

AREA_WORDS = ("district", "area", "borough", "neighbourhood", "neighborhood", "suburb", "town", "city", "village",
              "parish", "ward", "locality", "settlement", "region", "county", "constituency", "postcode", "human settlement",
              "metropolitan", "quarter", "division", "hamlet", "cadastral", "urban area")
types = collections.defaultdict(list)
for r in load("place-types.json"): types[r["place"]].append((r["type"] or "").lower())
def is_area(pid):
    return any(w in t for t in types.get(pid, []) for w in AREA_WORDS)

places, people, links = {}, {}, []
dropped = collections.Counter()
for f in sorted(RAW.glob("rel-*.json")):
    rel = f.stem[4:].replace("_", " ")
    if rel in ("studied", "worked"): continue
    for r in json.loads(f.read_text(encoding="utf-8")):
        pid, qid = r["place"], r["person"]
        if not pid or not qid: continue
        if is_area(pid): dropped[r["placeLabel"]] += 1; continue
        pt = point(r["coord"])
        if not pt: continue
        if pid not in places:
            places[pid] = {"l": r["placeLabel"], "d": r["placeDesc"], "lat": pt[0], "lon": pt[1], "t": sorted(set(types.get(pid, [])))[:3]}
        people.setdefault(qid, {"l": r["personLabel"]})
        links.append({"pl": pid, "pe": qid, "r": rel, "s": year(r["start"]), "e": year(r["end"])})

# de-dup links
seen = set(); uniq = []
for l in links:
    k = (l["pl"], l["pe"], l["r"], l["s"], l["e"])
    if k in seen: continue
    seen.add(k); uniq.append(l)
links = uniq

detail = {}
for r in load("people-detail.json"):
    d = detail.setdefault(r["person"], {})
    d.setdefault("label", r["label"]); d.setdefault("desc", r["desc"]); d.setdefault("birth", r["birth"]); d.setdefault("death", r["death"])
    if r["article"] and "article" not in d: d["article"] = r["article"].rsplit("/", 1)[-1]
    if r["image"] and "image" not in d: d["image"] = r["image"]
fame = {}
if (RAW / "people-fame.json").exists():
    for r in load("people-fame.json"): fame[r["person"]] = r["n"]
else:
    print("WARNING: people-fame.json missing; fame = 0")
labfix = json.loads((RAW / "people-labels-fix.json").read_text(encoding="utf-8")) if (RAW / "people-labels-fix.json").exists() else {}
for qid, p in people.items():
    d = detail.get(qid, {})
    if qid in labfix: p["l"] = labfix[qid]
    if re.match(r"^Q\d+$", p["l"] or "") and d.get("label") and not re.match(r"^Q\d+$", d["label"]): p["l"] = d["label"]
    p["d"] = (d.get("desc") or "")[:140]; p["b"] = year(d.get("birth")); p["x"] = year(d.get("death"))
    if d.get("article"): p["w"] = d["article"]
    if d.get("image"):
        f = urllib.parse.unquote(d["image"].rsplit("/", 1)[-1]).replace(" ", "_")
        p["i"] = f; p["h"] = hashlib.md5(f.encode("utf-8")).hexdigest()[:2]   # upload.wikimedia.org thumb path   # Commons file name; render via Special:FilePath?width=
    p["f"] = fame.get(qid, 0)
by_place = collections.defaultdict(set)
for l in links: by_place[l["pl"]].add(l["pe"])
for pid, pl in places.items():
    ps = by_place[pid]
    pl["f"] = max([people[q]["f"] for q in ps] + [0]); pl["n"] = len(ps)

events = collections.defaultdict(list)
PMAP = {"P19": "born", "P20": "died", "P119": "buried", "P551": "lived", "P69": "studied", "P108": "worked at", "P937": "worked in"}
for r in load("people-events.json"):
    pt = point(r["coord"])
    if not pt or r["person"] not in people: continue
    events[r["person"]].append({"k": PMAP.get(r["p"], r["p"]), "pl": r["place"], "l": r["placeLabel"], "lat": pt[0], "lon": pt[1],
                                "s": year(r["start"]), "e": year(r["end"]), "w": year(r["when"]), "in": r["place"] in places})
positions = collections.defaultdict(list)
for r in load("people-positions.json"):
    if r["person"] in people and r["pos"]:
        positions[r["person"]].append({"l": r["pos"], "s": year(r["start"]), "e": year(r["end"])})
assoc = collections.defaultdict(list)
RMAP = {"P26": "spouse", "P40": "child", "P22": "father", "P25": "mother", "P3373": "sibling", "P3342": "significant person",
        "P1066": "student of", "P802": "student", "P1327": "partner", "P451": "partner", "P1038": "relative"}
for r in load("people-associates.json"):
    if r["person"] in people and r["other"]:
        assoc[r["person"]].append({"r": RMAP.get(r["rel"], r["rel"]), "id": r["other"], "l": labfix.get(r["other"], r["otherLabel"]), "in": r["other"] in people})

def dedup(xs):
    out, seen = [], set()
    for x in xs:
        k = json.dumps(x, sort_keys=True)
        if k not in seen: seen.add(k); out.append(x)
    return out
for qid in people:
    (PEOPLE / f"{qid}.json").write_text(json.dumps({"ev": dedup(events[qid]), "pos": dedup(positions[qid]), "as": dedup(assoc[qid])}, ensure_ascii=False), encoding="utf-8")
(OUT / "index.json").write_text(json.dumps({"places": places, "people": people, "links": links}, ensure_ascii=False), encoding="utf-8")
print(f"places {len(places)} people {len(people)} links {len(links)}; index {((OUT/'index.json').stat().st_size/1e6):.1f} MB")
print("dropped area pins:", dropped.most_common(12))
