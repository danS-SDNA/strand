"""One-off patch of site/index.html after the first London test (21/11/2026):
a running tour that only Start sets, an always-on you-are-here dot, a calmer map, a panel arrow with swipe,
a menu that closes when you choose, no screen gaps after switching apps, and Save for later."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "site/index.html"
s = p.read_text(encoding="utf-8")


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:70])
    s = s.replace(old, new)


# ---------- styles: dvh for the panel, the arrow handle, the you-are-here dot, the menu close button
rep("box-shadow:0 -6px 24px rgba(0,0,0,.2);max-height:62vh;", "box-shadow:0 -6px 24px rgba(0,0,0,.2);max-height:62vh;max-height:62dvh;")
rep('#grip{flex:none;height:22px;display:flex;justify-content:center;align-items:center;cursor:pointer}',
    '#grip{flex:none;height:28px;display:flex;justify-content:center;align-items:center;cursor:pointer;touch-action:none;color:var(--muted);font-size:22px;line-height:1}')
rep('#grip::after{content:"";width:44px;height:5px;border-radius:3px;background:var(--line)}',
    '#grip::after{content:"⌄";transform:scaleX(1.6)}#panel.collapsed #grip::after{content:"⌃"}\n'
    '.me{width:22px;height:22px;border-radius:50%;background:#d62d20;border:3px solid #fff;box-shadow:0 0 0 2px #d62d20,0 2px 6px rgba(0,0,0,.4);position:relative}\n'
    '.me::after{content:"";position:absolute;inset:-12px;border-radius:50%;border:3px solid #d62d20;animation:mepulse 1.6s ease-out infinite}\n'
    '@keyframes mepulse{0%{transform:scale(.4);opacity:1}100%{transform:scale(1.4);opacity:0}}\n'
    '.mclose{float:right;font-size:22px;line-height:1;cursor:pointer;color:var(--muted);padding:0 2px 4px 10px}')

# ---------- state
rep("FOOD=[], RATINGS={},", "FOOD=[], runTour=null, meMarker=null, meRing=null, meWatch=null, SAVED=[], lastCalm=null, RATINGS={},")
rep("var DEF={startSheet:true,foodC:true,foodP:true,foodB:true,foodR:true,", "var DEF={calm:true,startSheet:true,foodC:false,foodP:false,foodB:false,foodR:false,")
rep("Object.keys(DEF).forEach(function(k){if(S[k]===undefined)S[k]=DEF[k]});",
    "Object.keys(DEF).forEach(function(k){if(S[k]===undefined)S[k]=DEF[k]});\n"
    "if(!S.calmV1){S.calmV1=1;S.calm=true;S.foodC=S.foodP=S.foodB=S.foodR=false;try{localStorage.setItem('strand.settings',JSON.stringify(S))}catch(e){}}\n"
    "try{SAVED=JSON.parse(localStorage.getItem('strand.saved')||'[]')}catch(e){}")

# ---------- 1. tours: viewing a tour never replaces the one you started
rep("function tourStrip(id){if(!activeTour)return '';var i=activeTour.stops.indexOf(id);if(i<0)return '';var n=activeTour.stops.length;",
    "function tourStrip(id){var T=runTour&&runTour.stops.indexOf(id)>=0?runTour:activeTour&&activeTour.stops.indexOf(id)>=0?activeTour:null;if(!T)return '';var i=T.stops.indexOf(id),n=T.stops.length;")
rep("""  return '<div class="actions"><span class="chip">'+esc(activeTour.name)+' · stop '+(i+1)+' of '+n+'</span>'""",
    """  return '<div class="actions"><span class="chip">'+esc(T.name)+' · stop '+(i+1)+' of '+n+(T===runTour?'':' · not started')+'</span>'""")
rep("""(i>0?'<button class="btn" data-go="l/'+activeTour.stops[i-1]+'">◀</button>':'')+(i<n-1?'<button class="btn acc" data-go="l/'+activeTour.stops[i+1]+'">Next stop ➜</button>':'<button class="btn" data-act="tour-stop">End tour</button>')+'</div>'}""",
    """(T!==runTour?'<button class="btn acc" data-act="tour-start:'+i+'">Start this tour here</button>':'')+(i>0?'<button class="btn" data-go="l/'+T.stops[i-1]+'">◀</button>':'')+(i<n-1?'<button class="btn'+(T===runTour?' acc':'')+'" data-go="l/'+T.stops[i+1]+'">Next stop ➜</button>':'')+(T===runTour?'<button class="btn" data-act="tour-stop">End tour</button>':'')+'</div>'}""")
rep("""'<div class="actions">'+(t.stops.length?'<button class="btn acc" data-go="l/'+t.stops[0]+'">Start at stop 1</button>':'')+(t.stops.length>=2?'<button class="btn""",
    """'<div class="actions">'+(t.stops.length?'<button class="btn acc" data-act="tour-start:0">Start at stop 1</button>':'')+(t.stops.length>=2?'<button class="btn""")
rep("""'<div class="actions">'+(t.stops.length?'<button class="btn acc" data-go="l/'+t.stops[0]+'">Start at stop 1</button>':'')+'<button class="btn" data-act="tour-shar""",
    """'<div class="actions">'+(t.stops.length?'<button class="btn acc" data-act="tour-start:0">Start at stop 1</button>':'')+'<button class="btn" data-act="tour-shar""")
rep("function saveActive(id){if(activeTour&&activeTour.stops.indexOf(id)>=0)localStorage.setItem('strand.active',JSON.stringify({name:activeTour.name,desc:activeTour.desc,stops:activeTour.stops,at:id}))}",
    "function saveActive(id){if(runTour&&runTour.stops.indexOf(id)>=0)localStorage.setItem('strand.active',JSON.stringify({name:runTour.name,desc:runTour.desc,stops:runTour.stops,at:id}))}")
rep("if(sb&&ZONES[sb.z]){if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour)}",
    "if(sb&&ZONES[sb.z]){if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){runTour=activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour)}")
rep("  if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour);location.hash='#l/'+a.at;return true}",
    "  if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){runTour=activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour);location.hash='#l/'+a.at;return true}")
rep("  if(a==='tour-stop'){activeTour=null;localStorage.removeItem('strand.active');drawTour(null);",
    "  if(a.slice(0,11)==='tour-start:'){var si=+a.slice(11);if(activeTour){runTour=activeTour;location.hash='#l/'+runTour.stops[si];saveActive(runTour.stops[si])}return}\n"
    "  if(a==='tour-stop'){runTour=null;activeTour=null;localStorage.removeItem('strand.active');drawTour(null);")
# zone exit returns to the RUNNING tour's next stop
rep("if(from&&activeTour){var k=activeTour.stops.indexOf(from);location.hash='#l/'+(activeTour.stops[k+1]||from)}",
    "var RT=runTour||activeTour;if(from&&RT){var k=RT.stops.indexOf(from);location.hash='#l/'+(RT.stops[k+1]||from)}")
rep("var from=activeTour&&activeTour.stops.indexOf(zid)>=0?zid:null;", "var RT0=runTour||activeTour,from=RT0&&RT0.stops.indexOf(zid)>=0?zid:null;")

# ---------- 2. you are here: its own marker (life-timeline markers no longer remove it), watched once allowed
rep("  if(!hereMarker){hereMarker=L.circleMarker([la,lo],{radius:8,color:'#2f5d8a'}).addTo(map)}else hereMarker.setLatLng([la,lo])}",
    "  var acc=Math.min(pos.coords.accuracy||30,300);\n"
    "  if(!meMarker){meRing=L.circle([la,lo],{radius:acc,color:'#d62d20',weight:1,fillColor:'#d62d20',fillOpacity:.08,interactive:false}).addTo(map);meMarker=L.marker([la,lo],{icon:L.divIcon({className:'',html:'<div class=\"me\"></div>',iconSize:[22,22],iconAnchor:[11,11]}),interactive:false,zIndexOffset:2000,keyboard:false}).addTo(map)}\n"
    "  else{meMarker.setLatLng([la,lo]);meRing.setLatLng([la,lo]).setRadius(acc)}}\n"
    "function watchMe(){if(meWatch!=null||!navigator.geolocation)return;meWatch=navigator.geolocation.watchPosition(function(pos){onFix(pos);if(walkOn)walkCheck()},function(){},{enableHighAccuracy:true,maximumAge:10000})}")
rep("  navigator.geolocation.getCurrentPosition(function(pos){onFix(pos);localStorage.setItem('strand.loc','1');",
    "  navigator.geolocation.getCurrentPosition(function(pos){onFix(pos);localStorage.setItem('strand.loc','1');watchMe();")
rep("  if(localStorage.getItem('strand.loc')==='1')locate(false);", "  if(localStorage.getItem('strand.loc')==='1'){locate(false);watchMe()}")

# ---------- 3. calm map: below street zoom only the notable places, busy-spot pins and films
rep("function refreshPins(){cluster.clearLayers();cluster.addLayers(Object.keys(D.places).filter(function(id){return active(id)&&!zoneKid[id]&&markers[id]}).map(function(id){return markers[id]}))}",
    "var CALM=null;function calmSet(){if(CALM)return CALM;CALM={};Object.keys(D.places).filter(function(i){return !D.places[i].food&&!D.places[i].vid}).sort(function(a,b){return (D.places[b].f||0)-(D.places[a].f||0)}).slice(0,450).forEach(function(i){CALM[i]=1});Object.keys(ZONES).forEach(function(i){CALM[i]=1});return CALM}\n"
    "function refreshPins(){var calm=S.calm&&map.getZoom()<17;lastCalm=calm;var C=calm?calmSet():null;cluster.clearLayers();cluster.addLayers(Object.keys(D.places).filter(function(id){return active(id)&&!zoneKid[id]&&markers[id]&&(!C||C[id]||(runTour&&runTour.stops.indexOf(id)>=0))}).map(function(id){return markers[id]}))}\n"
    "map.on('zoomend',function(){if(D&&(S.calm&&map.getZoom()<17)!==lastCalm)refreshPins()});")
rep("  else if(menuPage==='map')h=mhead('Show on the map')+",
    "  else if(menuPage==='map')h=mhead('Show on the map')+sw('calm','Calm map','Only the best-known places until you zoom in to street level')+")
rep("if(k.slice(0,4)==='food')drawFood();return}", "if(k.slice(0,4)==='food')drawFood();if(k==='calm')refreshPins();return}")

# ---------- 4. panel: swipe the handle; menu: closes when you choose, has a close button; gaps after switching apps
rep("$('#grip').onclick=function(){panel.classList.toggle('collapsed')};",
    "$('#grip').onclick=function(){panel.classList.toggle('collapsed')};\n"
    "(function(){var y0=null;$('#grip').addEventListener('pointerdown',function(e){y0=e.clientY});window.addEventListener('pointerup',function(e){if(y0==null)return;var dy=e.clientY-y0;y0=null;if(dy>30)panel.classList.add('collapsed');else if(dy<-30)panel.classList.remove('collapsed')})})();\n"
    "function settle(){setTimeout(function(){map.invalidateSize()},250)}\n"
    "document.addEventListener('visibilitychange',function(){if(!document.hidden)settle()});window.addEventListener('resize',settle);window.addEventListener('orientationchange',settle);window.addEventListener('pageshow',settle);")
rep("document.addEventListener('click',function(e){var t=e.target.closest('[data-go]');if(t){location.hash='#'+t.getAttribute('data-go');return}",
    "document.addEventListener('click',function(e){var t=e.target.closest('[data-go]');if(t){if(t.closest('#menu')){$('#menu').classList.remove('open');menuPage=''}location.hash='#'+t.getAttribute('data-go');return}")
rep("function mhead(t){return '<span class=\"mback\" data-act=\"menu:\">◀ Menu</span><h2 style=\"margin-top:2px\">'+t+'</h2>'}",
    "function mhead(t){return '<span class=\"mclose\" data-act=\"menu-close\">✕</span><span class=\"mback\" data-act=\"menu:\">◀ Menu</span><h2 style=\"margin-top:2px\">'+t+'</h2>'}")
rep("  if(!menuPage)h=installRow()+", "  if(!menuPage)h='<span class=\"mclose\" data-act=\"menu-close\">✕</span>'+installRow()+")
rep("function act(a,btn){", "function act(a,btn){if(a==='menu-close'){$('#menu').classList.remove('open');menuPage='';renderMenu();return}\n  if(a==='save'){toggleSave();return}\n  ")

# ---------- 5. save for later
rep("    mrow('tours','Tours',", "    mrow('saved','☆ Saved for later',SAVED.length?SAVED.length+' saved':'Nothing yet')+\n    mrow('tours','Tours',")
rep("  else if(menuPage==='tours')h=mhead('Tours')+",
    "  else if(menuPage==='saved')h=mhead('Saved for later')+(SAVED.length?SAVED.slice().reverse().map(function(x){var ok=x.k==='p'?D.people[x.id]:D.places[x.id];return ok?'<div class=\"row\">'+(x.k==='p'?avatar(D.people[x.id]):icon(D.places[x.id]))+'<span class=\"who\">'+link(x.k,x.id,x.l)+'<br><span class=\"dim\">saved '+new Date(x.ts).toLocaleDateString()+'</span></span></div>':''}).join(''):'<p class=\"stat\">Tap ☆ Save on any place or person to read it later.</p>');\n"
    "  else if(menuPage==='tours')h=mhead('Tours')+")
rep("""<button class="btn acc" data-act="lead">➜ Lead me on from here</button><button class="btn" data-act="listen">▶ Listen</button>""",
    """<button class="btn acc" data-act="lead">➜ Lead me on from here</button><button class="btn" data-act="listen">▶ Listen</button>'+saveBtn('l',id)+'""")
rep("""content.innerHTML='<h1>'+esc(p.l)+'</h1><p class="sub">'+yrs(p)+(p.d?' · '+esc(p.d):'')+'</p>""",
    """content.innerHTML='<h1>'+esc(p.l)+'</h1><p class="sub">'+yrs(p)+(p.d?' · '+esc(p.d):'')+'</p><div class="actions">'+saveBtn('p',id)+'</div>""")
rep("/* Zones: a place that holds many stops", r"""/* Save for later: a place or person to read about later, kept on the phone, listed under ☰ → Saved. */
function isSaved(k,id){return SAVED.some(function(x){return x.k===k&&x.id===id})}
function saveBtn(k,id){return '<button class="btn'+(isSaved(k,id)?' on':'')+'" data-act="save">'+(isSaved(k,id)?'★ Saved':'☆ Save')+'</button>'}
function toggleSave(){if(!cur)return;var k=cur.kind==='p'?'p':'l',id=cur.id;if(isSaved(k,id))SAVED=SAVED.filter(function(x){return !(x.k===k&&x.id===id)});else SAVED.push({k:k,id:id,l:(k==='p'?D.people[id]:D.places[id]).l,ts:Date.now()});
  try{localStorage.setItem('strand.saved',JSON.stringify(SAVED))}catch(e){}document.querySelectorAll('[data-act="save"]').forEach(function(b){b.outerHTML=saveBtn(k,id)});renderMenu()}
/* Zones: a place that holds many stops""")
p.write_text(s, encoding="utf-8")
print("patched")
