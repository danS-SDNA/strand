"""List the rendered Strand originals for the app: site/data/originals.json.

    python -X utf8 tools/shorts/publish.py

One entry per short whose app copy exists in site/media/shorts, pinned at its place (a Strand place id, and
for a museum object the object's Wikidata id, so the British Museum sub-tour can offer it at that stop).
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = json.loads((ROOT / "tools/shorts/shorts.json").read_text(encoding="utf-8"))
PLACE = {"old-london-bridge": ["Q130206"], "highgate-graves": ["Q533697"], "rosetta-stone": ["Q6373"],
         "st-pauls": ["Q173882"], "postmans-park": ["Q6642119"], "temple-bar": []}  # Temple Bar is not a pin: placed by coordinates
OBJECT = {"rosetta-stone": "Q48584"}
out = []
for s in spec["shorts"]:
    mp4 = ROOT / "site/media/shorts" / f"{s['id']}.mp4"
    if not mp4.exists():
        continue
    out.append({"p": "mp4", "v": f"media/shorts/{s['id']}.mp4", "poster": f"media/shorts/{s['id']}.jpg", "t": s["title"],
                "c": "Strand", "w": s["place"], "pl": PLACE.get(s["id"], []), "obj": OBJECT.get(s["id"]), "lat": s["lat"], "lon": s["lon"],
                "how": "original"})
(ROOT / "site/data/originals.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "originals listed")
