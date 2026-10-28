"""Write a short spoken-style story for each place, from Wikipedia leads of the place and its people.

    python -X utf8 tools/synthesise.py --limit 300          # most-visited places first
    python -X utf8 tools/synthesise.py --ids Q17526711 ...

Uses the local `claude` CLI (subscription, no API key) in print mode, ten places per call.
Wikipedia summaries are cached under data/raw/wp/. Output: site/data/story/{qid}.json {"t": "..."}
and site/data/story/_index.json {qid: 1}. Existing stories are kept; delete one to redo it.
"""
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; WP = RAW / "wp"; WP.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "site" / "data" / "story"; OUT.mkdir(parents=True, exist_ok=True)
UA = "strand-prototype/0.1 (dan.s@systemsdna.com)"
MODEL = "claude-sonnet-5-5"
BATCH = 10
RELTEXT = {"commemorated": "commemorated here", "depicted": "depicted here", "buried": "buried here", "died": "died here",
           "born": "born here", "lived": "lived here", "designed": "designed it", "named after": "gives it its name",
           "founded": "founded it", "commissioned": "commissioned it", "made": "made it", "owned": "owned it"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def wp_summary(title):
    """Lead paragraph of an English Wikipedia article, cached. None when there is no article."""
    key = hashlib.md5(title.encode("utf-8")).hexdigest()
    f = WP / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8")).get("extract")
    try:
        d = get("https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_")))
        out = {"title": title, "extract": d.get("extract")}
    except Exception:
        out = {"title": title, "extract": None}
    f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.05)
    return out["extract"]


def place_titles(qids):
    """enwiki titles for places (index.json carries them only for people), cached in one file."""
    f = RAW / "place-enwiki.json"
    cache = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    need = [q for q in qids if q not in cache]
    for i in range(0, len(need), 50):
        chunk = need[i:i + 50]
        try:
            d = get("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks&sitefilter=enwiki&ids=" + "|".join(chunk))
            for q in chunk:
                cache[q] = d.get("entities", {}).get(q, {}).get("sitelinks", {}).get("enwiki", {}).get("title")
        except Exception as e:
            print("  wikidata", e, file=sys.stderr)
        time.sleep(0.2)
    f.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def span(s, e):
    return f" ({s or '?'}–{e or '?'})" if (s or e) else ""


def brief(idx, by_place, titles, qid):
    pl = idx["places"][qid]
    people = {}
    for l in by_place.get(qid, []):
        p = idx["people"].get(l["pe"])
        if not p:
            continue
        o = people.setdefault(l["pe"], {"p": p, "rels": []})
        o["rels"].append(RELTEXT.get(l["r"], l["r"]) + span(l.get("s"), l.get("e")))
    top = sorted(people.values(), key=lambda o: -(o["p"].get("f") or 0))[:6]
    lines = [f"PLACE: {pl['l']}", f"description: {pl.get('d') or ', '.join(pl.get('t', []))}"]
    t = titles.get(qid)
    if t:
        ex = wp_summary(t)
        if ex:
            lines.append("about the place: " + ex[:900])
    for o in top:
        p = o["p"]
        lines.append(f"PERSON: {p['l']} ({p.get('b') or '?'}–{p.get('x') or '?'}), {p.get('d') or ''}; relation to this place: {'; '.join(o['rels'])}")
        if p.get("w"):
            ex = wp_summary(p["w"].replace("_", " "))
            if ex:
                lines.append("  about them: " + ex[:700])
    return "\n".join(lines)


PROMPT = """You write the short spoken introduction a knowledgeable friend would give while standing at a place in London.
For each PLACE below write 70-110 words, in plain spoken English, present tense for what is here now, to be read aloud by a phone.
Open with what the visitor is looking at. Say why the people named matter here, using only facts in the material supplied.
Never invent dates, quotes, anecdotes or directions. If the material is thin, say less rather than pad. No headings, no lists, no markdown.
Return ONLY a JSON array: [{{"id": "<QID>", "t": "<text>"}}, ...], one entry per place, same ids as given.

{body}"""


def run_batch(items):
    body = "\n\n".join(f"=== {q} ===\n{b}" for q, b in items)
    cmd = [shutil.which("claude") or "claude", "-p", "--model", MODEL, "--output-format", "json", "--restricted", "--strict-mcp-config", "--disallowedTools", "Read,Glob,Grep,Edit,Write,WebFetch,WebSearch,Agent,Bash", "--max-turns", "2"]
    r = subprocess.run(cmd, input=PROMPT.format(body=body), capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT), timeout=600)
    if r.returncode != 0:
        print("  claude failed:", r.stderr[:400], file=sys.stderr); return {}
    env = json.loads(r.stdout)
    text = env.get("result") if isinstance(env, dict) else str(env)
    m = re.search(r"\[.*\]", text or "", re.S)
    if not m:
        print("  no JSON in reply:", (text or "")[:200], file=sys.stderr); return {}
    try:
        arr = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        print("  bad JSON:", e, file=sys.stderr); return {}
    return {x["id"]: x["t"].strip() for x in arr if x.get("id") and x.get("t")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--dry", action="store_true", help="print briefs, call nothing")
    a = ap.parse_args()
    idx = json.loads((ROOT / "site" / "data" / "index.json").read_text(encoding="utf-8"))
    by_place = {}
    for l in idx["links"]:
        by_place.setdefault(l["pl"], []).append(l)
    done = {f.stem for f in OUT.glob("Q*.json")}
    if a.ids:
        todo = [q for q in a.ids if q in idx["places"]]
    else:
        # places worth a story first: known people, several of them
        rank = sorted(idx["places"], key=lambda q: -((idx["places"][q].get("f") or 0) * 2 + (idx["places"][q].get("n") or 0) * 50))
        todo = [q for q in rank if q not in done][:a.limit]
    titles = place_titles(todo)
    print(f"{len(todo)} places to write, {len(done)} already done")
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = [(q, brief(idx, by_place, titles, q)) for q in chunk]
        if a.dry:
            for q, b in items:
                print(f"\n=== {q} ===\n{b}")
            continue
        got = run_batch(items)
        for q, t in got.items():
            (OUT / f"{q}.json").write_text(json.dumps({"t": t}, ensure_ascii=False), encoding="utf-8")
        print(f"  batch {i // BATCH + 1}: {len(got)}/{len(chunk)} written", flush=True)
    index = {f.stem: 1 for f in OUT.glob("Q*.json")}
    (OUT / "_index.json").write_text(json.dumps(index), encoding="utf-8")
    print(f"stories: {len(index)}")


if __name__ == "__main__":
    main()
