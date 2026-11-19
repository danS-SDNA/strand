"""Render Strand originals: vertical shorts from archive pictures, a neural voice and word-timed captions.

    python -X utf8 tools/shorts/render.py [short-id ...]

For each short in tools/shorts/shorts.json:
  1. voice each beat with edge-tts (en-GB neural), keeping word timings;
  2. fetch each beat's chosen Commons picture (large thumbnail or original), cached in data/shorts/pics;
  3. draw 1080x1920 frames at 30 fps: a slow zoom and pan towards the beat's focus point, a cross-fade
     between beats, a title over the opening, captions that light up word by word, the picture's credit
     on screen, and an end card;
  4. encode with ffmpeg (bundled by imageio-ffmpeg): a 1080p master in data/shorts (for posting) and a
     720p copy plus a poster in site/media/shorts (for the app).
Credits for every picture are written next to the master as <id>-credits.txt (for a video description).
"""
import asyncio, io, json, math, pathlib, re, subprocess, sys, urllib.error, urllib.parse, urllib.request, wave, time
import edge_tts, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = json.loads((ROOT / "tools/shorts/shorts.json").read_text(encoding="utf-8"))
WORK = ROOT / "data" / "shorts"; PICS = WORK / "pics"; PICS.mkdir(parents=True, exist_ok=True)
SITE = ROOT / "site" / "media" / "shorts"; SITE.mkdir(parents=True, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
UA = "strand-prototype/0.1 (https://dans-sdna.github.io/strand/)"
W, H, FPS = 1080, 1920, 30
LEAD, GAP, FADE, TAIL = 0.7, 0.45, 0.5, 3.2      # seconds: before the first word, between beats, cross-fade, end card
RATE = "-4%"                                      # a touch slower than default: documentary pace
FONTS = "C:/Windows/Fonts/"
F_TITLE = ImageFont.truetype(FONTS + "georgiab.ttf", 84)
F_LABEL = ImageFont.truetype(FONTS + "seguisb.ttf", 34)
F_CAP = ImageFont.truetype(FONTS + "seguisb.ttf", 62)
F_CREDIT = ImageFont.truetype(FONTS + "segoeui.ttf", 26)
F_END1 = ImageFont.truetype(FONTS + "georgiab.ttf", 96)
F_END2 = ImageFont.truetype(FONTS + "segoeui.ttf", 40)
INK, PAPER, GOLD, VERM = (22, 19, 16), (251, 247, 239), (243, 201, 107), (198, 74, 46)


def get(url):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(min(int(e.headers.get("Retry-After") or 0) or 6 * (attempt + 1), 60))


def picture(file):
    """The chosen picture at a size that survives a 9:16 crop and a 12% zoom: a 3840 thumbnail, or the original."""
    out = PICS / re.sub(r"[^\w.-]+", "_", file)
    if out.exists():
        return Image.open(out).convert("RGB")
    q = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|size", "titles": "File:" + file, "iiurlwidth": 3840}
    ii = list(json.loads(get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(q)))["query"]["pages"].values())[0]["imageinfo"][0]
    url = ii["thumburl"] if ii["width"] > 3840 else ii["url"]
    data = get(url)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.save(out, quality=92)
    time.sleep(1)
    return img


def credit_line(b):
    a = re.sub(r"\s+", " ", (b.get("credit") or {}).get("artist", "")).strip()
    a = re.split(r" After:| Published by| Print made by:", a)[0].replace("Print made by: ", "").strip(" .,")
    if not a and "Old and New London" in b["pick"]:
        a = "Old and New London (1878), British Library"
    if not a:
        a = "Wikimedia Commons contributor"
    lic = (b.get("credit") or {}).get("licence", "")
    lic = "public domain" if lic.lower() in ("public domain", "no restrictions", "pd") else lic
    return f"{a[:60]} · {lic}"


async def voice(text, path):
    c = edge_tts.Communicate(text, SPEC.get("voice", "en-GB-RyanNeural"), rate=RATE, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
    return words


def to_wav(mp3, wav):
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(wav)], check=True)
    with wave.open(str(wav)) as w:
        return w.readframes(w.getnframes()), w.getnframes() / w.getframerate()


def chunks(words, text):
    """Caption groups: up to ~24 characters, breaking after punctuation, each with its words' times."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        line = " ".join(x["w"] for x in cur)
        nxt = words[i + 1]["w"] if i + 1 < len(words) else ""
        # edge-tts reports words without punctuation; read it back from the text to break naturally
        after = text.split(w["w"], 1)[1][:1] if w["w"] in text else ""
        if len(line) >= 18 or after in ",.:;!?" and len(line) > 6 or len(line + " " + nxt) > 26:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def cover(img, zoom, fx, fy, prog):
    """A 9:16 window of the picture, zoomed (1 -> zoom) and drifting towards the focus point as prog runs 0 -> 1."""
    iw, ih = img.size
    base_w, base_h = (ih * W / H, ih) if iw / ih > W / H else (iw, iw * H / W)
    z = 1 + (zoom - 1) * prog
    cw, ch = base_w / z, base_h / z
    # start centred on the picture, end centred on the focus point (clamped inside)
    sx, sy = iw / 2, ih / 2
    ex = min(max(fx * iw, cw / 2), iw - cw / 2); ey = min(max(fy * ih, ch / 2), ih - ch / 2)
    if iw / ih > 1.2:  # landscape: pan across from the far side instead of only zooming
        sx = min(max((1 - fx) * iw, cw / 2), iw - cw / 2)
    cx, cy = sx + (ex - sx) * prog, sy + (ey - sy) * prog
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = min(max(cy, ch / 2), ih - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((W, H), Image.BICUBIC, box=box, reducing_gap=2.0)


_TITLE_FONTS = {}


def fit_title(text, d):
    """The largest Georgia Bold up to 84 px that fits the frame with a 70 px margin each side."""
    if text not in _TITLE_FONTS:
        size = 84
        while size > 48 and d.textlength(text, font=ImageFont.truetype(FONTS + "georgiab.ttf", size)) > W - 140:
            size -= 2
        _TITLE_FONTS[text] = ImageFont.truetype(FONTS + "georgiab.ttf", size)
    return _TITLE_FONTS[text]


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0), 1))


def shade():
    """Darkening at top and bottom so white text always reads."""
    g = Image.new("L", (1, H))
    for y in range(H):
        top = max(0, 1 - y / 520) * 170
        bot = max(0, (y - (H - 820)) / 820) * 215
        g.putpixel((0, y), int(min(255, top + bot)))
    a = g.resize((W, H))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 255)); layer.putalpha(a)
    return layer


SHADE = shade()


def draw_caption(base, words, upto):
    d = ImageDraw.Draw(base)
    text = " ".join(w["w"] for w in words)
    # wrap to two lines if needed
    lines, line = [], []
    for i, w in enumerate(words):
        test = " ".join(x["w"] for x in line + [w])
        if d.textlength(test, font=F_CAP) > W - 160 and line:
            lines.append(line); line = []
        line.append(w)
    lines.append(line)
    y = H - 520 - (len(lines) - 1) * 80
    idx = 0
    for ln in lines:
        total = d.textlength(" ".join(x["w"] for x in ln), font=F_CAP)
        x = (W - total) / 2
        for w in ln:
            col = GOLD if idx == upto else (255, 255, 255) if idx < upto else (235, 235, 235)
            for dx, dy in ((3, 3), (0, 3), (3, 0)):
                d.text((x + dx, y + dy), w["w"], font=F_CAP, fill=(0, 0, 0))
            d.text((x, y), w["w"], font=F_CAP, fill=col)
            x += d.textlength(w["w"] + " ", font=F_CAP)
            idx += 1
        y += 80


def render(short):
    sid = short["id"]
    print(f"== {sid}")
    beats = short["beats"]
    audio, timeline, t = [], [], LEAD
    silence = lambda s: b"\x00\x00" * int(24000 * s)
    audio.append(silence(LEAD))
    for i, b in enumerate(beats):
        mp3 = WORK / f"{sid}-{i}.mp3"
        words = asyncio.run(voice(b["text"], mp3))
        pcm, dur = to_wav(mp3, WORK / f"{sid}-{i}.wav")
        audio.append(pcm)
        timeline.append({"start": t, "end": t + dur, "words": [dict(w, t=w["t"] + t) for w in words], "beat": b})
        t += dur
        if i < len(beats) - 1:
            audio.append(silence(GAP)); t += GAP
    audio.append(silence(TAIL)); total = t + TAIL
    wav = WORK / f"{sid}-voice.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(b"".join(audio))
    print(f"   voice {total:.1f}s")

    pics = [picture(b["pick"]) for b in beats]
    caps = [chunks(seg["words"], seg["beat"]["text"]) for seg in timeline]
    # each beat's picture is on screen from its start (minus the fade) to the next beat's start
    spans = []
    for i, seg in enumerate(timeline):
        s = 0 if i == 0 else seg["start"] - GAP / 2
        e = total if i == len(timeline) - 1 else timeline[i + 1]["start"] - GAP / 2
        spans.append((s, e))

    master = WORK / f"{sid}.mp4"
    cmd = [FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(master)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * FPS)
    poster = None
    for f in range(n):
        tt = f / FPS
        i = max(k for k, (s, e) in enumerate(spans) if s <= tt or k == 0)
        s, e = spans[i]
        b = timeline[i]["beat"]; fx, fy = b.get("focus", [0.5, 0.5])
        frame = cover(pics[i], 1.12, fx, fy, ease((tt - s) / max(e - s, 0.1)))
        if i + 1 < len(spans) and tt > spans[i + 1][0] - FADE:  # cross-fade into the next picture
            ns, ne = spans[i + 1]; nb = timeline[i + 1]["beat"]; nfx, nfy = nb.get("focus", [0.5, 0.5])
            nxt = cover(pics[i + 1], 1.12, nfx, nfy, 0)
            frame = Image.blend(frame, nxt, min(1, (tt - (ns - FADE)) / FADE))
        frame = frame.convert("RGBA"); frame.alpha_composite(SHADE); frame = frame.convert("RGB")
        d = ImageDraw.Draw(frame)
        # label and title over the opening
        if tt < timeline[0]["end"]:
            a = 1 if tt < timeline[0]["end"] - 0.6 else max(0, (timeline[0]["end"] - tt) / 0.6)
            if a > 0:
                lab = "STRAND · LONDON"
                d.text(((W - d.textlength(lab, font=F_LABEL)) / 2, 150), lab, font=F_LABEL, fill=tuple(int(c * a) for c in GOLD))
                ft = fit_title(short["title"], d)
                tw = d.textlength(short["title"], font=ft)
                d.text(((W - tw) / 2 + 3, 203), short["title"], font=ft, fill=(0, 0, 0))
                d.text(((W - tw) / 2, 200), short["title"], font=ft, fill=tuple(int(255 * a) for _ in range(3)))
        # captions: the group being spoken, current word in gold
        seg = timeline[i]
        if seg["start"] - 0.1 <= tt <= seg["end"] + 0.25:
            for grp in caps[i]:
                if grp[0]["t"] - 0.05 <= tt <= grp[-1]["t"] + grp[-1]["d"] + 0.25:
                    upto = max([k for k, w in enumerate(grp) if w["t"] <= tt] or [0])
                    draw_caption(frame, grp, upto)
                    break
        # credit for the picture on screen
        cl = credit_line(b)
        d.text(((W - d.textlength(cl, font=F_CREDIT)) / 2, H - 120), cl, font=F_CREDIT, fill=(225, 225, 225))
        # end card
        if tt > total - TAIL + 0.2:
            a = min(1, (tt - (total - TAIL + 0.2)) / 0.6)
            ov = Image.new("RGBA", (W, H), INK + (int(225 * a),)); frame = frame.convert("RGBA"); frame.alpha_composite(ov); frame = frame.convert("RGB")
            d = ImageDraw.Draw(frame)
            if a > 0.3:
                for txt, font, y, col in (("Strand", F_END1, 760, PAPER), ("Follow the story on the map", F_END2, 900, GOLD),
                                          ("dans-sdna.github.io/strand", F_END2, 970, PAPER), ("Pictures: Wikimedia Commons · see credits", F_CREDIT, 1080, (200, 200, 200))):
                    d.text(((W - d.textlength(txt, font=font)) / 2, y), txt, font=font, fill=col)
        if poster is None and tt >= min(2.0, timeline[0]["end"] - 0.5):
            poster = frame.copy()
        enc.stdin.write(frame.tobytes())
        if f % 300 == 0:
            print(f"   frame {f}/{n}", flush=True)
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        raise SystemExit(f"ffmpeg failed for {sid}")
    # app copy: 720p, smaller; poster for the card
    app = SITE / f"{sid}.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(master), "-vf", "scale=720:1280:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "29", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(app)], check=True)
    poster.resize((360, 640), Image.LANCZOS).save(SITE / f"{sid}.jpg", quality=85)
    lines = [short["title"], "", "Narration: Microsoft neural voice (en-GB Ryan). Script: Strand, from Wikipedia and Wikidata.", "", "Pictures (Wikimedia Commons):"]
    for b in beats:
        lines.append(f"- {credit_line(b)} — https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(b['pick'].replace(' ', '_'))}")
    (WORK / f"{sid}-credits.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"   {master.stat().st_size/1e6:.1f} MB master, {app.stat().st_size/1e6:.1f} MB app copy, {total:.1f}s")
    return {"id": sid, "secs": round(total, 1)}


if __name__ == "__main__":
    only = sys.argv[1:]
    for s in SPEC["shorts"]:
        if not only or s["id"] in only:
            render(s)
