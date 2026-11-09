"""Pull London guide shorts and pin each one to where it was filmed.

    python -X utf8 tools/pull_videos.py

Sources are tools/video_sources.json: guide channels (their shorts come from YouTube's public RSS
feed, the latest 15 each) and single videos (metadata from YouTube's oEmbed endpoint). Nothing is
scraped and no video is downloaded; the app embeds the official player.

Each video's title and description go to the local claude CLI, which names the specific London spot
it shows, or says it cannot tell. That name is matched to a Strand place; failing that it is
geocoded with OpenStreetMap's Nominatim (1 request a second, inside a London box). Answers are
cached in data/raw/videos-located.json. Output: site/data/videos.json.
"""
import json, pathlib, re, shutil, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; RAW.mkdir(parents=True, exist_ok=True)
UA = "strand-prototype/0.1 (dan.s@systemsdna.com)"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}
BOX = (-0.52, 51.28, 0.34, 51.70)  # Greater London, lon/lat


def get(url, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def from_feeds(channels):
    out = []
    for ch in channels:
        url = "https://www.youtube.com/feeds/videos.xml?playlist_id=UUSH" + ch["id"][2:]
        try:
            root = ET.fromstring(get(url, "application/atom+xml"))
        except Exception as e:
            print("  feed failed", ch["name"], e, file=sys.stderr); continue
        for e in root.findall("a:entry", NS):
            out.append({"p": "yt", "v": e.find("yt:videoId", NS).text, "t": e.find("a:title", NS).text,
                        "c": ch["name"], "desc": (e.find("m:group/m:description", NS).text or "")[:600],
                        "d": (e.find("a:published", NS).text or "")[:10]})
        time.sleep(0.5)
    return out


def from_list(items, have):
    out = []
    for it in items:
        if it["id"] in have:
            continue
        if it.get("platform", "yt") == "ig":
            out.append({"p": "ig", "v": it["id"], "t": it.get("title", ""), "c": it.get("creator", ""), "desc": it.get("note", "")})
            continue
        try:
            d = json.loads(get("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote("https://www.youtube.com/shorts/" + it["id"])))
            out.append({"p": "yt", "v": it["id"], "t": d["title"], "c": d["author_name"], "desc": it.get("note", "")})
        except Exception as e:
            print("  oembed failed", it["id"], e, file=sys.stderr)
    return out


PROMPT = """Each item below is a short video by a London guide. Say WHERE IN LONDON it is filmed or what spot it is about,
using only the title and description. Name the specific place (a building, church, pub, street, alley, statue) as it is
commonly called, and the street or district. If it is not about one identifiable London spot (a general topic, a book
promotion, somewhere outside London, several places at once), set place to null. Do not guess.
Return ONLY a JSON array: [{{"v": "<id>", "place": "<name or null>", "area": "<street or district or null>"}}]

{body}"""


def locate(videos, cache):
    todo = [v for v in videos if v["v"] not in cache]
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        body = "\n\n".join(f"id: {v['v']}\ntitle: {v['t']}\ndescription: {v['desc'][:400]}" for v in chunk)
        cmd = [shutil.which("claude") or "claude", "-p", "--model", "claude-sonnet-5-5", "--output-format", "json", "--restricted",
               "--strict-mcp-config", "--disallowedTools", "Read,Glob,Grep,Edit,Write,WebFetch,WebSearch,Agent,Bash", "--max-turns", "2"]
        r = subprocess.run(cmd, input=PROMPT.format(body=body), capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT), timeout=600)
        m = re.search(r"\[.*\]", (json.loads(r.stdout).get("result") if r.returncode == 0 else "") or "", re.S)
        if not m:
            print("  locate failed for a batch", r.stderr[:200], file=sys.stderr); continue
        for x in json.loads(m.group(0)):
            cache[x["v"]] = {"place": x.get("place"), "area": x.get("area")}
    return cache


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(the|st|saint|church of|london|ye|olde?)\b", " ", s.replace("’", "'"))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def geocode(q):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "viewbox": ",".join(map(str, BOX)), "bounded": 1})
    time.sleep(1.1)
    try:
        d = json.loads(get(url))
        return (float(d[0]["lat"]), float(d[0]["lon"])) if d else None
    except Exception:
        return None


def main():
    src = json.loads((ROOT / "tools" / "video_sources.json").read_text(encoding="utf-8"))
    idx = json.loads((ROOT / "site" / "data" / "index.json").read_text(encoding="utf-8"))
    by_label = {}
    for q, p in idx["places"].items():
        by_label.setdefault(norm(p["l"]), []).append(q)
    videos = from_feeds(src["channels"])
    videos += from_list(src["videos"], {v["v"] for v in videos})
    print(f"{len(videos)} videos")
    cf = RAW / "videos-located.json"
    cache = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    cache = locate(videos, cache)
    cf.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    out, skipped = [], []
    for v in videos:
        loc = cache.get(v["v"]) or {}
        if not loc.get("place"):
            skipped.append(v["t"]); continue
        key = norm(loc["place"])
        qids = by_label.get(key) or [q for k, qs in by_label.items() if len(key) > 6 and (key == k or (len(k) > 6 and (key in k or k in key))) for q in qs][:3]
        if qids:
            p = idx["places"][qids[0]]; lat, lon, how = p["lat"], p["lon"], "place"
        else:
            area = loc.get("area") or ""
            tries = [f"{loc['place']}, {area}", loc["place"], re.sub(r"\(.*?\)", "", loc["place"]).strip()]
            if re.search(r"\b(street|lane|court|road|yard|alley|passage|row|place|square|walk|hill|gate)\b", area, re.I):
                tries.append(area)  # the street itself is still a spot you can stand in
            g = None
            for q in dict.fromkeys(t for t in tries if t):
                g = geocode(q)
                if g:
                    break
            if not g:
                skipped.append(v["t"] + " (not found: " + loc["place"] + ")"); continue
            (lat, lon), how = g, "geocoded"
        if not (BOX[1] <= lat <= BOX[3] and BOX[0] <= lon <= BOX[2]):
            skipped.append(v["t"] + " (outside London)"); continue
        out.append({"p": v["p"], "v": v["v"], "t": v["t"], "c": v["c"], "w": loc["place"], "pl": qids, "lat": round(lat, 6), "lon": round(lon, 6), "how": how})
    (ROOT / "site" / "data" / "videos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pinned {len(out)}: {sum(1 for o in out if o['how']=='place')} on Strand places, {sum(1 for o in out if o['how']=='geocoded')} geocoded")
    for o in out:
        print(f"  {o['how']:8} {o['w']}  <-  {o['t'][:70]}")
    print(f"skipped {len(skipped)}:")
    for t in skipped:
        print("  ", t[:100])


if __name__ == "__main__":
    main()
