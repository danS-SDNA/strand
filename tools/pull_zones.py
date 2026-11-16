"""Zones: places that hold many stops, for drill-down sub-tours.

    python -X utf8 tools/pull_zones.py              # -> site/data/zones.json

Three sources:
  1. Wikidata "part of" (P361) / "location" (P276) between Strand places  -> data/raw/part-of.json
  2. dense squares: a square or garden with 6+ pins within 90 m
  3. objects held by a venue (P276 location or P195 collection = a Strand museum, gallery, church,
     abbey, palace...), notable enough to have 3+ sitelinks, which have no coordinates of their own
     and so never became pins                                         -> data/raw/venue-objects.json
People buried at a cemetery, abbey or church are added in the page from the existing links.

The Wikidata query service is shared and was rationing to one request a minute (11/2026): each
query here is a single POST and its result is cached; delete the raw file to refetch.
"""
import collections, json, math, pathlib, re, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = "strand-prototype/0.1 (personal map prototype)"
idx = json.loads((ROOT / "site/data/index.json").read_text(encoding="utf-8"))
P = idx["places"]


def sparql(q, cache):
    f = RAW / cache
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    req = urllib.request.Request("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
                                 headers={"User-Agent": UA, "Accept": "application/sparql-results+json",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    for attempt in range(4):
        try:
            rows = json.loads(urllib.request.urlopen(req, timeout=180).read())["results"]["bindings"]
            f.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            return rows
        except Exception as e:
            print("  query attempt", attempt + 1, e); time.sleep(65)
    raise SystemExit("Wikidata query failed; rerun later")


def dist(a, b, c, d):
    x = (c - a) * 111.2; y = (d - b) * 111.2 * math.cos(math.radians(a)); return math.hypot(x, y)


def kinds(q):
    return " ".join(P[q].get("t", [])).lower() + " " + (P[q].get("d") or "").lower()


zones = {}
claimed = set()

# 1. part of / located in
po = json.loads((RAW / "part-of.json").read_text(encoding="utf-8")) if (RAW / "part-of.json").exists() else {}
for parent, kids in po.items():
    kids = [k for k in kids if k in P and k != parent]
    if len(kids) >= 3:
        zones[parent] = {"places": kids, "src": "part-of"}
        claimed.update(kids)

# 2. dense squares: a place typed as a square (its type, not its description)
for q in P:
    if not re.search(r"\bsquare\b|piazza", " ".join(P[q].get("t", [])).lower()) or q in zones:
        continue
    near = [k for k in P if k != q and k not in claimed and dist(P[q]["lat"], P[q]["lon"], P[k]["lat"], P[k]["lon"]) < 0.09
            and not re.search(r"\bstreet\b|\broad\b|underground|station", kinds(k))]
    if len(near) >= 6:
        zones[q] = {"places": near, "src": "square"}
        claimed.update(near)

# 2b. dense clusters with no square pin (Trafalgar Square was dropped as an area): seed on any place with 10+
# unclaimed pins within 90 m, name it from the members' descriptions ("... in Trafalgar Square")
synthetic = {}
for q in sorted(P, key=lambda k: -(P[k].get("f") or 0)):
    if q in claimed or q in zones:
        continue
    near = [k for k in P if k not in claimed and dist(P[q]["lat"], P[q]["lon"], P[k]["lat"], P[k]["lon"]) < 0.09
            and not re.search(r"\bstreet\b|\broad\b|underground|station|country|kingdom|empire", kinds(k))]
    if len(near) < 10:
        continue
    names = collections.Counter(m for k in near for m in re.findall(r"\b(?:in|on|at) ((?:[A-Z][\w']+ )+(?:Square|Gardens|Yard|Court|Place))", P[k].get("d") or ""))
    if not names:
        continue
    name = names.most_common(1)[0][0]
    zid = "z:" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if zid in synthetic:
        continue
    lat = sum(P[k]["lat"] for k in near) / len(near); lon = sum(P[k]["lon"] for k in near) / len(near)
    synthetic[zid] = {"l": name, "lat": round(lat, 6), "lon": round(lon, 6)}
    zones[zid] = {"places": near, "src": "cluster"}
    claimed.update(near)

# 3. objects held by venues (not museum networks or publishers: "Tate" the organisation would repeat Tate Britain)
venues = [q for q in P if not re.search(r"museum network|copyright collective|publisher"," ".join(P[q].get("t", [])).lower()) and re.search(r"museum|gallery|library|cathedral|abbey|palace|castle|church|chapel|collection|tower of london", kinds(q))]
venue_set = set(venues)
print(len(venues), "venues to ask about")
vals = " ".join("wd:" + q for q in venues)
rows = sparql(f"""SELECT ?o ?v ?sl ?oLabel ?oDescription ?img ?art WHERE {{
  VALUES ?v {{ {vals} }}
  ?o wdt:P276|wdt:P195 ?v . ?o wikibase:sitelinks ?sl . FILTER(?sl >= 3)
  FILTER NOT EXISTS {{ ?o wdt:P625 ?c }}
  OPTIONAL {{ ?o wdt:P18 ?img }}
  OPTIONAL {{ ?art schema:about ?o ; schema:isPartOf <https://en.wikipedia.org/> }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,mul". }} }}""", "venue-objects.json")
objs = collections.defaultdict(dict)
for r in rows:
    o = r["o"]["value"].rsplit("/", 1)[-1]; v = r["v"]["value"].rsplit("/", 1)[-1]
    if v not in venue_set:
        continue
    lab = r.get("oLabel", {}).get("value", "")
    if re.fullmatch(r"Q\d+", lab):
        continue
    it = objs[v].setdefault(o, {"id": o, "l": lab, "d": r.get("oDescription", {}).get("value", ""), "sl": int(r["sl"]["value"])})
    if r.get("img") and "i" not in it:
        f = urllib.parse.unquote(r["img"]["value"].rsplit("/", 1)[-1]).replace(" ", "_")
        import hashlib
        it["i"] = f; it["h"] = hashlib.md5(f.encode("utf-8")).hexdigest()[:2]
    if r.get("art") and "w" not in it:
        it["w"] = urllib.parse.unquote(r["art"]["value"].rsplit("/", 1)[-1])
for v, os_ in objs.items():
    top = sorted(os_.values(), key=lambda x: -x["sl"])[:60]
    z = zones.setdefault(v, {"places": [], "src": "objects"})
    z["objects"] = top

# 4. places within 300 m whose description names the venue ("covered quadrangle in the British Museum")
for q, z in list(zones.items()):
    if q not in P or len(P[q]["l"]) < 6:
        continue
    name = P[q]["l"].lower()
    for k in P:
        if k == q or k in claimed or k in zones:
            continue
        if name in (P[k].get("d") or "").lower() and dist(P[q]["lat"], P[q]["lon"], P[k]["lat"], P[k]["lon"]) < 0.3:
            z["places"].append(k); claimed.add(k)

out = {}
for q, z in zones.items():
    n = len(z["places"]) + len(z.get("objects", []))
    if n >= 3:
        out[q] = {"places": z["places"], "objects": z.get("objects", []), "src": z["src"]}
        if q in synthetic:
            out[q].update(synthetic[q])
(ROOT / "site/data/zones.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("zones", len(out), "| from part-of", sum(1 for z in out.values() if z["src"] == "part-of"),
      "| squares", sum(1 for z in out.values() if z["src"] == "square"), "| named clusters", sum(1 for z in out.values() if z["src"] == "cluster"), "| with objects", sum(1 for z in out.values() if z["objects"]),
      "| bytes", (ROOT / "site/data/zones.json").stat().st_size)
for q, z in sorted(out.items(), key=lambda kv: -(len(kv[1]["places"]) + len(kv[1]["objects"])))[:18]:
    print(f"  {len(z['places']):3} places {len(z['objects']):3} objects  {z.get('l') or P[q]['l']}  e.g. {'; '.join([o['l'] for o in z['objects'][:3]] or [P[k]['l'] for k in z['places'][:3]])[:90]}")
