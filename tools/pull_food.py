"""Cafés, pubs, bars and restaurants from OpenStreetMap (ODbL) over the Strand box, via the Overpass API.

    python -X utf8 tools/pull_food.py      # -> data/raw/osm-food.json, then site/data/food.json

Kept per venue: name, kind, position, and the signals that make a pub 'famous': an OSM wikidata link,
a heritage or listed-building tag, an old start date, or being a Strand place already. No ratings: OSM
has none. Overpass is a shared community service: one query, cached, rerun only when needed.
"""
import json, math, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "osm-food.json"
UA = "strand-prototype/0.1 (dan.s@systemsdna.com)"
S, W, N, E = 51.45, -0.25, 51.58, 0.02
KINDS = {"cafe": "c", "pub": "p", "bar": "b", "restaurant": "r", "biergarten": "p"}

import os
EP = os.environ.get("OVERPASS", "https://overpass-api.de/api/interpreter")
TILES = RAW.parent / "osm-food-tiles"; TILES.mkdir(exist_ok=True)
if not RAW.exists():
    elements, ny, nx = [], 4, 6
    for iy in range(ny):
        for ix in range(nx):
            s_, n_ = S + (N - S) * iy / ny, S + (N - S) * (iy + 1) / ny
            w_, e_ = W + (E - W) * ix / nx, W + (E - W) * (ix + 1) / nx
            f = TILES / f"{iy}-{ix}.json"
            if not f.exists():
                q = f'[out:json][timeout:90];(nwr["amenity"~"^(cafe|pub|bar|restaurant|biergarten)$"]["name"]({s_},{w_},{n_},{e_}););out center tags;'
                for attempt in range(4):
                    try:
                        req = urllib.request.Request(EP, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": UA})
                        with urllib.request.urlopen(req, timeout=120) as r:
                            f.write_bytes(r.read()); break
                    except Exception as ex:
                        print("  tile", iy, ix, "attempt", attempt + 1, ex, file=sys.stderr); time.sleep(15 * (attempt + 1))
                time.sleep(3)
            if f.exists():
                elements += json.loads(f.read_text(encoding="utf-8"))["elements"]
            else:
                sys.exit(f"tile {iy}-{ix} failed; rerun to resume")
    seen = set(); uniq = []
    for e in elements:
        key = (e["type"], e["id"])
        if key not in seen:
            seen.add(key); uniq.append(e)
    RAW.write_text(json.dumps({"elements": uniq}), encoding="utf-8")
d = json.loads(RAW.read_text(encoding="utf-8"))
idx = json.loads((ROOT / "site/data/index.json").read_text(encoding="utf-8"))


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\b(the|ye|olde?)\b", " ", (s or "").lower())).strip()


# Famous and historic pubs: those with a Wikidata item (most are listed buildings). With an English
# article as well as a Commons page (2+ sitelinks) they count as famous (f=2), otherwise historic (f=1). tools: wd-pubs.json is a
# SPARQL result for pubs (Q212198 and subclasses) inside the same box.
wd = {}
wf = ROOT / "data" / "raw" / "wd-pubs.json"
for b in (json.loads(wf.read_text(encoding="utf-8"))["results"]["bindings"] if wf.exists() else []):
    q = b["item"]["value"].rsplit("/", 1)[-1]; lab = b["itemLabel"]["value"]
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"]["value"])
    if not m or re.fullmatch(r"Q\d+", lab) or q in wd:
        continue
    wd[q] = {"q": q, "n": lab, "lat": float(m.group(2)), "lon": float(m.group(1)), "sl": int(b["sl"]["value"]), "used": False}
grid = {}
for w in wd.values():
    grid.setdefault((round(w["lat"], 2), round(w["lon"], 2)), []).append(w)


def near_wd(name, lat, lon):
    nn = norm(name)
    for dy in (-0.01, 0, 0.01):
        for dx in (-0.01, 0, 0.01):
            for w in grid.get((round(lat + dy, 2), round(lon + dx, 2)), []):
                wn = norm(w["n"])
                if nn and wn and (nn == wn or (len(nn) > 4 and (nn in wn or wn in nn))) and abs(w["lat"] - lat) < 0.0015 and abs(w["lon"] - lon) < 0.0022:
                    return w
    return None


out = []
for e in d["elements"]:
    t = e.get("tags", {}); lat = e.get("lat") or e.get("center", {}).get("lat"); lon = e.get("lon") or e.get("center", {}).get("lon")
    if lat is None or not (S <= lat <= N and W <= lon <= E) or t.get("access") == "private":
        continue
    k = KINDS[t["amenity"]]
    v = {"n": t["name"], "k": k, "lat": round(lat, 6), "lon": round(lon, 6)}
    if k in ("p", "b"):
        w = near_wd(t["name"], lat, lon)
        if w:
            w["used"] = True; v["f"] = 2 if w["sl"] >= 2 else 1; v["wd"] = w["q"]
    if t.get("cuisine") and k == "r":
        v["cu"] = t["cuisine"].split(";")[0].replace("_", " ")
    out.append(v)
for w in wd.values():  # historic pubs Wikidata knows that OSM does not name in the same spot
    if not w["used"]:
        out.append({"n": w["n"], "k": "p", "lat": round(w["lat"], 6), "lon": round(w["lon"], 6), "f": 2 if w["sl"] >= 2 else 1, "wd": w["q"]})
(ROOT / "site/data/food.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
c = {}
for v in out: c[v["k"]] = c.get(v["k"], 0) + 1
print("venues", len(out), c, "famous", sum(1 for v in out if v.get("f") == 2), "historic", sum(1 for v in out if v.get("f") == 1),
      "bytes", (ROOT / "site/data/food.json").stat().st_size)
print("famous:", [v["n"] for v in out if v.get("f") == 2][:30])
