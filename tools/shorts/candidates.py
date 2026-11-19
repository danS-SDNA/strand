"""Find candidate pictures on Wikimedia Commons for every beat, and draw one numbered contact sheet per short.

    python -X utf8 tools/shorts/candidates.py <work-dir>

For each beat: up to 6 files from a Commons search (and, for beats with 'cat', that category too), photos and
paintings only, at least 800 px on the short side of the result we will use. Writes <work-dir>/<short>-sheet.jpg and
<work-dir>/<short>-candidates.json (file name, size, artist, licence) so a person can choose by number.
"""
import io, json, pathlib, re, sys, time, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
UA = "strand-prototype/0.1 (https://dans-sdna.github.io/strand/)"
API = "https://commons.wikimedia.org/w/api.php?"


def get(url):
    """GET with Wikimedia's etiquette: a descriptive agent, and back off on 429 (Retry-After when given)."""
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 5 * (attempt + 1)
            time.sleep(min(wait, 60))


def files_for(beat):
    titles = []
    q = {"action": "query", "format": "json", "list": "search", "srnamespace": 6, "srlimit": 10, "srsearch": beat["search"] + " filetype:bitmap"}
    titles += [h["title"] for h in json.loads(get(API + urllib.parse.urlencode(q)))["query"]["search"]]
    if beat.get("cat"):
        q = {"action": "query", "format": "json", "list": "categorymembers", "cmtype": "file", "cmlimit": 20, "cmtitle": "Category:" + beat["cat"]}
        titles += [m["title"] for m in json.loads(get(API + urllib.parse.urlencode(q)))["query"]["categorymembers"]]
    titles = [t for t in dict.fromkeys(titles) if re.search(r"\.(jpe?g|png|tiff?)$", t, re.I)]
    if not titles:
        return []
    q = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 330,
         "titles": "|".join(titles[:30])}
    pages = json.loads(get(API + urllib.parse.urlencode(q)))["query"]["pages"].values()
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii or min(ii.get("width", 0), ii.get("height", 0)) < 800:
            continue
        md = ii.get("extmetadata", {})
        artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
        out.append({"file": p["title"][5:], "w": ii["width"], "h": ii["height"], "thumb": ii["thumburl"],
                    "artist": artist[:120], "licence": md.get("LicenseShortName", {}).get("value", "")})
    return out[:6 if not beat.get("cat") else 10]


def sheet(cands, path):
    cell, cols = 240, 6
    rows = (len(cands) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell, rows * (cell + 26)), "white")
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype("arialbd.ttf", 20)
    except OSError:
        f = ImageFont.load_default()
    for i, c in enumerate(cands):
        try:
            t = Image.open(io.BytesIO(get(c["thumb"]))).convert("RGB")
            t.thumbnail((cell - 6, cell - 6))
            x, y = (i % cols) * cell, (i // cols) * (cell + 26)
            img.paste(t, (x + 3, y + 3))
            d.rectangle([x, y + cell, x + cell, y + cell + 26], fill="black")
            d.text((x + 6, y + cell + 2), f"{i}  b{c['beat']}  {c['w']}x{c['h']}", fill="yellow", font=f)
        except Exception as e:
            print("  thumb failed", c["file"], e)
        time.sleep(0.4)
    img.save(path, quality=80)


def main():
    work = pathlib.Path(sys.argv[1]); work.mkdir(parents=True, exist_ok=True)
    spec = json.loads((ROOT / "tools/shorts/shorts.json").read_text(encoding="utf-8"))
    only = sys.argv[2:] or None
    for s in spec["shorts"]:
        if only and s["id"] not in only:
            continue
        cands = []
        for bi, b in enumerate(s["beats"]):
            for c in files_for(b):
                c["beat"] = bi
                if c["file"] not in {x["file"] for x in cands}:
                    cands.append(c)
            time.sleep(0.3)
        (work / f"{s['id']}-candidates.json").write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
        sheet(cands, work / f"{s['id']}-sheet.jpg")
        print(s["id"], len(cands), "candidates")


if __name__ == "__main__":
    main()
