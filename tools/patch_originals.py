"""One-off patch: Strand originals (own MP4 shorts) in the app, and the service worker leaves video alone."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "site/index.html"
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep("#pip.show{display:block}", "#pip.show{display:block}#pip video{width:100%;height:100%;object-fit:cover;background:#000;display:block}")
rep(".vid .th.ig{", ".vid .th.org{border:2px solid #f3c96b}.vid .th.org::before{content:\"STRAND\";position:absolute;left:6px;top:6px;color:#f3c96b;font-size:11px;font-weight:bold;letter-spacing:.06em;text-shadow:0 1px 2px #000}\n.vid .th.ig{")

# originals first, then guide videos
rep("fetch('data/videos.json').then(function(r){return r.ok?r.json():[]})",
    "Promise.all([fetch('data/originals.json').then(function(r){return r.ok?r.json():[]}).catch(function(){return []}),fetch('data/videos.json').then(function(r){return r.ok?r.json():[]})]).then(function(a){return a[0].concat(a[1])})")

rep("function thumb(v){return v.p==='yt'?", "function thumb(v){return v.p==='mp4'?v.poster:v.p==='yt'?")
rep("function vidSrc(v){return v.p==='ig'?", "function vidSrc(v){return v.p==='mp4'?v.v:v.p==='ig'?")
rep("function vidUrl(v){return v.p==='ig'?", "function vidUrl(v){return v.p==='mp4'?v.v:v.p==='ig'?")
rep("""<div class="th'+(v.p==='ig'?' ig':'')+'\"""", """<div class="th'+(v.p==='ig'?' ig':v.p==='mp4'?' org':'')+'\"""")

# the player: a <video> for our own files, the platform's embed for the rest
rep("var p=$('#pip');var f=p.querySelector('iframe');if(f)f.remove();f=document.createElement('iframe');f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;f.src=vidSrc(v);p.appendChild(f);",
    "var p=$('#pip');var f=p.querySelector('iframe,video');if(f)f.remove();if(v.p==='mp4'){f=document.createElement('video');f.src=v.v;f.poster=v.poster||'';f.controls=true;f.autoplay=true;f.playsInline=true;f.setAttribute('playsinline','')}else{f=document.createElement('iframe');f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;f.src=vidSrc(v)}p.appendChild(f);")
rep("$('#pipclose').onclick=function(){var p=$('#pip');p.classList.remove('show','big');var f=p.querySelector('iframe');if(f)f.remove();pipCur=null};",
    "$('#pipclose').onclick=function(){var p=$('#pip');p.classList.remove('show','big');var f=p.querySelector('iframe,video');if(f)f.remove();pipCur=null};")

# inside a zone: a museum object with its own Strand short offers it
rep("""   '<button class="btn" data-act="sub-listen">▶ Listen</button>'""",
    """   (it.k==='ob'&&VIDS.some(function(v){return v.obj===it.o.id})?'<button class="btn acc" data-act="vid:'+VIDS.filter(function(v){return v.obj===it.o.id})[0].i+'">▶ Watch the Strand short</button>':'')+'<button class="btn" data-act="sub-listen">▶ Listen</button>'""")
p.write_text(s, encoding="utf-8")

w = ROOT / "site/sw.js"
t = w.read_text(encoding="utf-8")
old = "  if (url.origin === location.origin) {"
assert t.count(old) == 1
t = t.replace(old, "  if (url.origin === location.origin && /\\.mp4$/.test(url.pathname)) return;  // video: range requests, leave to the browser\n" + old)
t = t.replace("var VERSION = 'strand-v6';", "var VERSION = 'strand-v7';")
a = "data" + chr(92) + "/zones" + chr(92) + ".json|"
assert a in t
t = t.replace(a, a + "data" + chr(92) + "/originals" + chr(92) + ".json|")
w.write_text(t, encoding="utf-8")
print("patched")
