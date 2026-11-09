"""One-off patch of site/index.html: guide shorts pinned on the map, a Videos section on place pages,
a floating player (picture-in-picture inside the app), video cards on walk alerts."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep('.q{margin:14px 0 4px;font-weight:bold}',
    '.q{margin:14px 0 4px;font-weight:bold}\n'
    '#pip{position:fixed;right:10px;bottom:72px;z-index:12;width:min(210px,52vw);aspect-ratio:9/16;background:#000;border-radius:14px;overflow:hidden;box-shadow:0 8px 28px rgba(0,0,0,.45);display:none;touch-action:none}\n'
    '#pip.show{display:block}#pip.big{width:min(340px,86vw)}#pip iframe{width:100%;height:100%;border:0}\n'
    '#pip .bar{position:absolute;top:0;left:0;right:0;height:30px;display:flex;justify-content:space-between;align-items:center;padding:0 6px;background:linear-gradient(rgba(0,0,0,.65),transparent);cursor:move;z-index:2}\n'
    '#pip .bar span{color:#fff;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:1;padding:0 4px}#pip .bar button{background:rgba(0,0,0,.4);color:#fff;border:0;border-radius:6px;width:26px;height:24px;cursor:pointer;font-size:14px}\n'
    '@media(min-width:900px){#pip{right:470px;bottom:12px}}\n'
    '.vids{display:flex;gap:8px;overflow-x:auto;padding:2px 0 6px;scrollbar-width:none}.vid{flex:none;width:96px;cursor:pointer}.vid .th{width:96px;height:150px;border-radius:10px;background:#222 center/cover;position:relative}\n'
    '.vid .th::after{content:"▶";position:absolute;inset:auto 6px 6px auto;width:26px;height:26px;border-radius:50%;background:rgba(0,0,0,.6);color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center}\n'
    '.vid .vt{font-size:12px;line-height:1.25;margin-top:4px;max-height:3.75em;overflow:hidden}.vid .vc{font-size:11px;color:var(--muted)}\n'
    '.vpin{width:26px;height:26px;border-radius:7px;background:#1a1410;color:#fff;border:2px solid #b08556;display:flex;align-items:center;justify-content:center;font-size:11px;box-shadow:0 1px 4px rgba(0,0,0,.4)}')

rep('<div id="toast"></div>', '<div id="toast"></div>\n<div id="pip"><div class="bar"><span id="piptitle"></span><button id="pipsize" title="Bigger">⤢</button><button id="pipopen" title="Open in YouTube">↗</button><button id="pipclose" title="Close">✕</button></div></div>')

# state + settings
rep("planned=[], PA={", "VIDS=[], vidsAt={}, vidLayer=null, pipCur=null, planned=[], PA={")
rep("var DEF={speak:true,", "var DEF={videos:true,")

# load videos after the index
rep("  computeThemes();\n", """  computeThemes();
  fetch('data/videos.json').then(function(r){return r.ok?r.json():[]}).then(function(v){VIDS=v;v.forEach(function(x,i){x.i=i;(x.pl||[]).forEach(function(q){(vidsAt[q]=vidsAt[q]||[]).push(x)})});drawVids();if(cur&&cur.kind==='l')showPlace(cur.id)}).catch(function(){});
""")

# place page: a Videos section under the story
rep("""'<div id="story"></div>'+tourStrip(id)""", """'<div id="story"></div>'+vidStrip(vidsNear(pl.lat,pl.lon,id))+tourStrip(id)""")

# menu switch
rep("""  '<h2>Voice</h2>'+seg('rate',""", """  '<h2>Guide videos</h2>'+sw('videos','Show guide shorts on the map','Short films by London guides, pinned where they were made')+
  '<h2>Voice</h2>'+seg('rate',""")
rep("if(k==='offline')offline(S[k]);return}", "if(k==='offline')offline(S[k]);if(k==='videos')drawVids();return}")

# actions
rep("if(a==='walk'){toggleWalk();return}", "if(a==='walk'){toggleWalk();return}if(a.slice(0,4)==='vid:'){play(VIDS[+a.slice(4)]);return}")

# walk alert: offer a nearby short
rep("t.setAttribute('data-go','l/'+best.id);t.classList.add('show');",
    "var vn=vidsNear(best.p.lat,best.p.lon,best.id);if(vn.length)t.innerHTML+='<br><span class=\"btn\" style=\"margin-top:6px;display:inline-block;padding:4px 10px\" onclick=\"event.stopPropagation();play(VIDS['+vn[0].i+'])\">▶ A guide filmed here</span>';t.setAttribute('data-go','l/'+best.id);t.classList.add('show');")

# functions, before the planner block
rep("/* Plan my visit: a few taps,",
    r"""/* Guide videos: shorts by London guides pinned where they were filmed (tools/pull_videos.py). Played in a floating
   in-app player so the map stays usable; YouTube's own embed, nothing re-hosted. */
function vidsNear(lat,lon,id){var out=(vidsAt[id]||[]).slice();VIDS.forEach(function(v){if(out.indexOf(v)<0&&dist(lat,lon,v.lat,v.lon)<0.06)out.push(v)});return out}
function thumb(v){return v.p==='yt'?'https://i.ytimg.com/vi/'+v.v+'/hqdefault.jpg':''}
function vidStrip(vs){if(!vs.length)return '';return '<h2>Guides filmed here</h2><div class="vids">'+vs.map(function(v){return '<div class="vid" data-act="vid:'+v.i+'"><div class="th" style="background-image:url('+thumb(v)+')"></div><div class="vt">'+esc(v.t.replace(/#\w+/g,'').trim())+'</div><div class="vc">'+esc(v.c)+'</div></div>'}).join('')+'</div>'}
function drawVids(){if(vidLayer){map.removeLayer(vidLayer);vidLayer=null}if(!S.videos||!VIDS.length)return;
  vidLayer=L.layerGroup(VIDS.map(function(v){return L.marker([v.lat,v.lon],{icon:L.divIcon({className:'',html:'<div class="vpin">▶</div>',iconSize:[26,26],iconAnchor:[13,13]}),zIndexOffset:800,title:v.t}).on('click',function(){if(v.pl&&v.pl[0])location.hash='#l/'+v.pl[0];play(v)})})).addTo(map)}
function vidSrc(v){return v.p==='ig'?'https://www.instagram.com/reel/'+v.v+'/embed':'https://www.youtube-nocookie.com/embed/'+v.v+'?autoplay=1&playsinline=1&rel=0&modestbranding=1'}
function vidUrl(v){return v.p==='ig'?'https://www.instagram.com/reel/'+v.v+'/':'https://www.youtube.com/shorts/'+v.v}
function play(v){if(!v)return;pipCur=v;var p=$('#pip');var f=p.querySelector('iframe');if(f)f.remove();f=document.createElement('iframe');f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen';f.allowFullscreen=true;f.src=vidSrc(v);p.appendChild(f);
  $('#piptitle').textContent=v.c;p.classList.add('show');if(speaking){speechSynthesis.cancel();speaking=false}}
$('#pipclose').onclick=function(){var p=$('#pip');p.classList.remove('show','big');var f=p.querySelector('iframe');if(f)f.remove();pipCur=null};
$('#pipsize').onclick=function(){$('#pip').classList.toggle('big')};
$('#pipopen').onclick=function(){if(pipCur)window.open(vidUrl(pipCur),'_blank')};
(function(){var p=$('#pip'),bar=p.querySelector('.bar'),sx,sy,ox,oy,drag=false;
  bar.addEventListener('pointerdown',function(e){if(e.target.tagName==='BUTTON')return;drag=true;bar.setPointerCapture(e.pointerId);var r=p.getBoundingClientRect();sx=e.clientX;sy=e.clientY;ox=r.left;oy=r.top});
  bar.addEventListener('pointermove',function(e){if(!drag)return;var x=Math.max(0,Math.min(innerWidth-p.offsetWidth,ox+e.clientX-sx)),y=Math.max(0,Math.min(innerHeight-p.offsetHeight,oy+e.clientY-sy));p.style.left=x+'px';p.style.top=y+'px';p.style.right='auto';p.style.bottom='auto'});
  bar.addEventListener('pointerup',function(){drag=false})})();
/* Plan my visit: a few taps,""")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
