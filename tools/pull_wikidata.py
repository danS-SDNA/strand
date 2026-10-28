"""Pull people-and-places for a city box from Wikidata into data/raw/*.json.
Usage: python tools/pull_wikidata.py [--phase places|people|all]
"""
import json, sys, time, urllib.parse, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UA = "strand-prototype/0.1 (dan.s@systemsdna.com)"
ENDPOINT = "https://query.wikidata.org/sparql"

# central London, generous
SW = "Point(-0.25 51.45)"
NE = "Point(0.02 51.58)"

BOX = f'''SERVICE wikibase:box {{ ?place wdt:P625 ?coord .
  bd:serviceParam wikibase:cornerSouthWest "{SW}"^^geo:wktLiteral .
  bd:serviceParam wikibase:cornerNorthEast "{NE}"^^geo:wktLiteral . }}'''

# admin-area types we never want as a pin (everyone "born in London" would land on Charing Cross)
ADMIN_TYPES = "wd:Q515 wd:Q3957 wd:Q532 wd:Q1549591 wd:Q179872 wd:Q2983893 wd:Q123705 wd:Q188509 wd:Q1115575 wd:Q3257686 wd:Q6023295 wd:Q7897276 wd:Q15284 wd:Q5119 wd:Q1637706"
NOT_ADMIN = f"FILTER(?place NOT IN (wd:Q84, wd:Q23306)) FILTER NOT EXISTS {{ ?place wdt:P31 ?t . VALUES ?t {{ {ADMIN_TYPES} }} }}"

RELATIONS = {
  "commemorated": "?place wdt:P547 ?person .",
  "depicted":     "?place wdt:P180 ?person .",
  "buried":       "?person p:P119 ?st . ?st ps:P119 ?place . OPTIONAL { ?st pq:P580 ?start } ",
  "died":         "?person wdt:P20 ?place .",
  "born":         "?person wdt:P19 ?place .",
  "lived":        "?person p:P551 ?st . ?st ps:P551 ?place . OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }",
  "designed":     "?place wdt:P84 ?person .",
  "named after":  "?place wdt:P138 ?person .",
  "founded":      "?place wdt:P112 ?person .",
  "commissioned": "?place wdt:P88 ?person .",
  "made":         "?place wdt:P170 ?person .",
  "owned":        "?place wdt:P127 ?person .",
  "studied":      "?person p:P69 ?st . ?st ps:P69 ?place . OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }",
  "worked":       "?person p:P108 ?st . ?st ps:P108 ?place . OPTIONAL { ?st pq:P580 ?start } OPTIONAL { ?st pq:P582 ?end }",
}

def sparql(q, tries=4):
    for i in range(tries):
        try:
            data = urllib.parse.urlencode({"query": q, "format": "json"}).encode()
            req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print(f"  retry {i+1}: {e}", flush=True)
            time.sleep(5 * (i + 1))
    raise SystemExit("sparql failed")

def v(b, k):
    return b[k]["value"] if k in b else None

def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None

def phase_places():
    for rel, pat in RELATIONS.items():
        out = RAW / f"rel-{rel.replace(' ', '_')}.json"
        if out.exists():
            print(f"{rel}: cached"); continue
        q = f"""SELECT ?person ?personLabel ?place ?placeLabel ?placeDescription ?coord ?start ?end WHERE {{
  {BOX}
  {pat}
  ?person wdt:P31 wd:Q5 .
  {NOT_ADMIN}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}"""
        t = time.time()
        rows = sparql(q)
        recs = [{"person": qid(v(b,"person")), "personLabel": v(b,"personLabel"),
                 "place": qid(v(b,"place")), "placeLabel": v(b,"placeLabel"), "placeDesc": v(b,"placeDescription"),
                 "coord": v(b,"coord"), "start": v(b,"start"), "end": v(b,"end"), "rel": rel} for b in rows]
        out.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
        print(f"{rel}: {len(recs)} rows in {time.time()-t:.0f}s", flush=True)

def all_people():
    ps = set()
    for f in RAW.glob("rel-*.json"):
        if f.stem in ("rel-studied", "rel-worked"): continue   # alumni/staff lists swamp the pins
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["person"]: ps.add(r["person"])
    return sorted(ps)

def phase_placetypes():
    out = RAW / "place-types.json"
    if out.exists(): print("placetypes: cached"); return
    places = set()
    for f in RAW.glob("rel-*.json"):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["place"]: places.add(r["place"])
    places = sorted(places); acc = []
    for batch in batched(places, 300):
        q = f"""SELECT ?place ?typeLabel WHERE {{ VALUES ?place {{ {vals(batch)} }} ?place wdt:P31 ?type .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
        acc += [{"place": qid(v(b,"place")), "type": v(b,"typeLabel")} for b in sparql(q)]
    out.write_text(json.dumps(acc, ensure_ascii=False), encoding="utf-8")
    print(f"placetypes: {len(places)} places, {len(acc)} type rows", flush=True)

def batched(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]

def phase_people():
    people = all_people()
    print(f"{len(people)} distinct people", flush=True)
    N = 150
    for name, build in [("detail", q_detail), ("events", q_events), ("positions", q_positions), ("associates", q_associates)]:
        out = RAW / f"people-{name}.json"
        if out.exists():
            print(f"{name}: cached"); continue
        acc = []
        for i, batch in enumerate(batched(people, N)):
            acc += build(batch)
            if i % 10 == 0: print(f"  {name} batch {i} -> {len(acc)} rows", flush=True)
        out.write_text(json.dumps(acc, ensure_ascii=False), encoding="utf-8")
        print(f"{name}: {len(acc)} rows", flush=True)

def vals(batch):
    return " ".join(f"wd:{p}" for p in batch)

def q_detail(batch):
    q = f"""SELECT ?person ?personLabel ?personDescription ?birth ?death ?image ?article WHERE {{
  VALUES ?person {{ {vals(batch)} }}
  OPTIONAL {{ ?person wdt:P569 ?birth }} OPTIONAL {{ ?person wdt:P570 ?death }} OPTIONAL {{ ?person wdt:P18 ?image }}
  OPTIONAL {{ ?article schema:about ?person ; schema:isPartOf <https://en.wikipedia.org/> }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
    return [{"person": qid(v(b,"person")), "label": v(b,"personLabel"), "desc": v(b,"personDescription"),
             "birth": v(b,"birth"), "death": v(b,"death"), "image": v(b,"image"), "article": v(b,"article")} for b in sparql(q)]

def q_events(batch):
    q = f"""SELECT ?person ?p ?place ?placeLabel ?coord ?start ?end ?when WHERE {{
  VALUES ?person {{ {vals(batch)} }}
  VALUES (?p ?ps) {{ (p:P19 ps:P19) (p:P20 ps:P20) (p:P119 ps:P119) (p:P551 ps:P551) (p:P69 ps:P69) (p:P108 ps:P108) (p:P937 ps:P937) }}
  ?person ?p ?st . ?st ?ps ?place . ?place wdt:P625 ?coord .
  OPTIONAL {{ ?st pq:P580 ?start }} OPTIONAL {{ ?st pq:P582 ?end }} OPTIONAL {{ ?st pq:P585 ?when }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
    return [{"person": qid(v(b,"person")), "p": qid(v(b,"p")), "place": qid(v(b,"place")), "placeLabel": v(b,"placeLabel"),
             "coord": v(b,"coord"), "start": v(b,"start"), "end": v(b,"end"), "when": v(b,"when")} for b in sparql(q)]

def q_positions(batch):
    q = f"""SELECT ?person ?posLabel ?start ?end WHERE {{
  VALUES ?person {{ {vals(batch)} }}
  ?person p:P39 ?st . ?st ps:P39 ?pos .
  OPTIONAL {{ ?st pq:P580 ?start }} OPTIONAL {{ ?st pq:P582 ?end }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
    return [{"person": qid(v(b,"person")), "pos": v(b,"posLabel"), "start": v(b,"start"), "end": v(b,"end")} for b in sparql(q)]

def q_associates(batch):
    q = f"""SELECT ?person ?rel ?other ?otherLabel WHERE {{
  VALUES ?person {{ {vals(batch)} }}
  VALUES ?rel {{ wdt:P26 wdt:P40 wdt:P22 wdt:P25 wdt:P3373 wdt:P3342 wdt:P1066 wdt:P802 wdt:P1327 wdt:P451 wdt:P1038 }}
  ?person ?rel ?other . ?other wdt:P31 wd:Q5 .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}"""
    return [{"person": qid(v(b,"person")), "rel": qid(v(b,"rel")), "other": qid(v(b,"other")), "otherLabel": v(b,"otherLabel")} for b in sparql(q)]

def phase_fame():
    out = RAW / "people-fame.json"
    if out.exists(): print("fame: cached"); return
    people = all_people(); acc = []
    for i, batch in enumerate(batched(people, 300)):
        q = f"""SELECT ?person ?n WHERE {{ VALUES ?person {{ {vals(batch)} }} ?person wikibase:sitelinks ?n . }}"""
        acc += [{"person": qid(v(b,"person")), "n": int(v(b,"n") or 0)} for b in sparql(q)]
        if i % 10 == 0: print(f"  fame batch {i} -> {len(acc)}", flush=True)
    out.write_text(json.dumps(acc), encoding="utf-8"); print(f"fame: {len(acc)} rows", flush=True)

if __name__ == "__main__":
    phase = sys.argv[sys.argv.index("--phase")+1] if "--phase" in sys.argv else "all"
    if phase in ("places", "all"): phase_places()
    if phase in ("placetypes", "all"): phase_placetypes()
    if phase in ("people", "all"): phase_people()
    if phase in ("fame", "all"): phase_fame()
