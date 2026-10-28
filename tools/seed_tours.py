"""Write site/data/tours.json: a few curated tours picked from the data by rule, as examples of the shape.

A curated tour is {id, name, desc, stops:[place qids]}; stops are walked in order. Add or edit by hand
and commit: the commit is the approval. Run: python -X utf8 tools/seed_tours.py
"""
import json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
idx = json.loads((ROOT / "site/data/index.json").read_text(encoding="utf-8"))
P = idx["places"]
by_place = {}
for l in idx["links"]:
    by_place.setdefault(l["pl"], []).append(l)


def dist(a, b):
    x = (b[0] - a[0]) * 111.2; y = (b[1] - a[1]) * 111.2 * math.cos(math.radians(a[0]))
    return math.hypot(x, y)


def kinds(q):
    return " | ".join(P[q].get("t", [])).lower() + " | " + (P[q].get("d") or "").lower()


def pick(centre, radius_km, pred, n):
    c = [q for q in P if dist(centre, (P[q]["lat"], P[q]["lon"])) <= radius_km and pred(q)]
    c.sort(key=lambda q: -(P[q].get("f") or 0))
    c = c[:n]
    # walk order: nearest-neighbour from the first (best-known) stop
    out, rest = [c[0]], c[1:]
    while rest:
        last = P[out[-1]]
        rest.sort(key=lambda q: dist((last["lat"], last["lon"]), (P[q]["lat"], P[q]["lon"])))
        out.append(rest.pop(0))
    return out


def rel(q, r):
    return any(l["r"] == r for l in by_place.get(q, []))


tours = [
    {"id": "westminster-statues", "name": "Statues of Westminster",
     "desc": "The statesmen, soldiers and reformers in bronze around Parliament Square and Whitehall, Churchill, Mandela, Gandhi, Cromwell and Lincoln among them. About a kilometre on foot.",
     "stops": pick((51.5007, -0.1268), 0.45, lambda q: ("statue" in kinds(q) or "sculpture" in kinds(q)) and rel(q, "depicted"), 10)},
    {"id": "highgate-village", "name": "Highgate village and cemetery",
     "desc": "Up the hill from Archway: the cemetery where Marx, George Eliot and Faraday lie, then the village, school and houses around it. Steep in places.",
     "stops": pick((51.5680, -0.1470), 0.7, lambda q: "street" not in kinds(q) and "road" not in kinds(q), 8)},
    {"id": "bloomsbury-squares", "name": "Around the Bloomsbury squares",
     "desc": "The British Museum, the colleges and the houses between Russell Square and Gordon Square, and the people tied to them. Flat and short between stops.",
     "stops": pick((51.5225, -0.1270), 0.55, lambda q: "street" not in kinds(q) and "road" not in kinds(q) and "square" not in kinds(q), 9)},
]
for t in tours:
    print(t["name"], len(t["stops"]))
    for q in t["stops"]:
        print("  ", q, P[q]["l"])
(ROOT / "site/data/tours.json").write_text(json.dumps(tours, ensure_ascii=False, indent=1), encoding="utf-8")
