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
import json, os, pathlib, re, shutil, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
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
        if ch.get("longVideos"):
            shorts = {o["v"] for o in out}
            try:
                root = ET.fromstring(get("https://www.youtube.com/feeds/videos.xml?channel_id=" + ch["id"], "application/atom+xml"))
                for e in root.findall("a:entry", NS):
                    vid = e.find("yt:videoId", NS).text
                    if vid in shorts or vid in set(ch.get("shortIds", [])):
                        continue
                    out.append({"p": "yt", "v": vid, "t": e.find("a:title", NS).text, "c": ch["name"], "wide": 1,
                                "desc": (e.find("m:group/m:description", NS).text or "")[:600], "d": (e.find("a:published", NS).text or "")[:10]})
            except Exception as e:
                print("  uploads feed failed", ch["name"], e, file=sys.stderr)
    return out


OEMBED = RAW / "oembed.json"


def oembed(vid, cache):
    """Title and author of a YouTube video from the public oEmbed endpoint, cached."""
    if vid not in cache:
        try:
            d = json.loads(get("https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote("https://www.youtube.com/shorts/" + vid)))
            cache[vid] = {"t": d["title"], "c": d["author_name"]}
        except Exception as e:
            print("  oembed failed", vid, e, file=sys.stderr); return None
        time.sleep(0.15)
    return cache[vid]


def from_list(items, have, oc):
    """Hand-listed videos. An entry may fix its own place (place, lat, lon) and carry a note shown with it;
    otherwise its place is worked out like any other. Instagram entries are never fetched."""
    out = []
    for it in items:
        if it["id"] in have:
            continue
        have.add(it["id"])
        v = {"p": it.get("platform", "yt"), "v": it["id"], "t": it.get("title", ""), "c": it.get("creator", ""), "desc": it.get("note", "")}
        for k in ("place", "lat", "lon", "note", "until"):
            if k in it: v[k] = it[k]
        if v["p"] == "yt" and not v["t"]:
            d = oembed(it["id"], oc)
            if not d: continue
            v["t"], v["c"] = d["t"], v["c"] or d["c"]
        out.append(v)
    return out


PROMPT = """Each item below is a short video by a London guide. Say WHERE IN LONDON it is filmed or what spot it is about,
using only the title and description. Name the specific place (a building, church, pub, street, alley, statue) as it is
commonly called, and the street or district. If it is not about one identifiable London spot (a general topic, a book
promotion, somewhere outside London, several places at once), set place to null. Do not guess.
Return ONLY a JSON array: [{{"v": "<id>", "place": "<name or null>", "area": "<street or district or null>"}}]

{body}"""


def kimi(prompt):
    """Fallback when the local claude CLI cannot answer (e.g. its login expired): Kimi K3 through Moonshot's
    OpenAI-compatible API with the operator's ONE_AI_KEY_MOONSHOT. Thinking off: ~3 s and a few hundred tokens."""
    key = os.environ.get("ONE_AI_KEY_MOONSHOT", "").strip()
    if not key:
        return ""
    body = json.dumps({"model": "kimi-k3", "max_tokens": 4000, "thinking": {"type": "disabled"},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.moonshot.ai/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        print("  kimi failed", e, file=sys.stderr); return ""


def locate(videos, cache):
    todo = [v for v in videos if v["v"] not in cache]
    used = {"claude": 0, "kimi": 0}
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        body = "\n\n".join(f"id: {v['v']}\ntitle: {v['t']}\ndescription: {v['desc'][:400]}" for v in chunk)
        cmd = [shutil.which("claude") or "claude", "-p", "--model", "claude-sonnet-5-5", "--output-format", "json", "--restricted",
               "--strict-mcp-config", "--disallowedTools", "Read,Glob,Grep,Edit,Write,WebFetch,WebSearch,Agent,Bash", "--max-turns", "2"]
        r = subprocess.run(cmd, input=PROMPT.format(body=body), capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT), timeout=600)
        try:
            env = json.loads(r.stdout) if r.returncode == 0 else {}
        except json.JSONDecodeError:
            env = {}
        text = "" if env.get("is_error") else (env.get("result") or "")
        if not re.search(r"\[.*\]", text, re.S):
            text = kimi(PROMPT.format(body=body))
            if text: used["kimi"] += 1
        else:
            used["claude"] += 1
        m = re.search(r"\[.*\]", text or "", re.S)
        if not m:
            print("  locate failed for a batch", r.stderr[:200], file=sys.stderr); continue
        for x in json.loads(m.group(0)):
            cache[x["v"]] = {"place": x.get("place"), "area": x.get("area")}
    print(f"  placed in {used['claude']} claude and {used['kimi']} kimi batches")
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
    placed_by_hand = {it["id"] for it in src["videos"] if "lat" in it}
    videos = [v for v in videos if v["v"] not in placed_by_hand]  # a hand placement wins over the feed's copy
    oc = json.loads(OEMBED.read_text(encoding="utf-8")) if OEMBED.exists() else {}
    items = list(src["videos"])
    for lst in src.get("idLists", []):  # whole catalogues read off a channel page, one id per line
        for line in (ROOT / lst).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                items.append({"platform": "yt", "id": line.strip()})
    videos += from_list(items, {v["v"] for v in videos}, oc)
    OEMBED.write_text(json.dumps(oc, ensure_ascii=False), encoding="utf-8")
    print(f"{len(videos)} videos")
    cf = RAW / "videos-located.json"
    cache = json.loads(cf.read_text(encoding="utf-8")) if cf.exists() else {}
    cache = locate([v for v in videos if "lat" not in v], cache)
    cf.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    out, skipped = [], []
    for v in videos:
        if "lat" in v:  # place fixed by hand
            out.append({k: v[k] for k in ("p", "v", "t", "c", "note", "until") if k in v} | {"w": v.get("place", ""), "pl": [], "lat": v["lat"], "lon": v["lon"], "how": "hand"})
            continue
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
        o = {"p": v["p"], "v": v["v"], "t": v["t"], "c": v["c"], "w": loc["place"], "pl": qids, "lat": round(lat, 6), "lon": round(lon, 6), "how": how}
        if v.get("wide"): o["wide"] = 1
        out.append(o)
    (ROOT / "site" / "data" / "videos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pinned {len(out)} of {len(videos)}: {sum(1 for o in out if o['how']=='place')} on Strand places, {sum(1 for o in out if o['how']=='geocoded')} geocoded, {sum(1 for o in out if o['how']=='hand')} placed by hand")
    for o in out:
        print(f"  {o['how']:8} {o['w']}  <-  {o['t'][:70]}")
    print(f"skipped {len(skipped)}:")
    for t in skipped:
        print("  ", t[:100])


if __name__ == "__main__":
    main()
