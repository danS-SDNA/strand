"""One-off patch of site/index.html: OSM food and drink, planner breaks, hierarchical menu, start sheet,
resume an active tour, and an optional AI box on the planner (shown only when an AI endpoint is set)."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# ---------- styles
rep('.q{margin:14px 0 4px;font-weight:bold}',
    '.q{margin:14px 0 4px;font-weight:bold}\n'
    '.mrow{display:flex;align-items:center;gap:10px;padding:10px 2px;border-bottom:1px solid var(--line);cursor:pointer}.mrow .ml{flex:1}.mrow small{display:block;color:var(--muted)}.mrow .go{color:var(--muted);font-size:18px}\n'
    '.mback{display:inline-block;margin:0 0 6px;color:var(--acc2);cursor:pointer}\n'
    '.fpin{width:18px;height:18px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff}\n'
    '.fpin.c{background:#6b4f2a}.fpin.p{background:#8a2f1d}.fpin.b{background:#5a3d6b}.fpin.r{background:#2f5d4a}.fpin.f{width:24px;height:24px;font-size:12px;border-color:#f3c96b}\n'
    '.opt{display:flex;align-items:center;gap:12px;padding:12px;margin:8px 0;border:1px solid var(--line);border-radius:12px;background:var(--chip);cursor:pointer}.opt b{display:block}.opt span.i{font-size:22px;width:30px;text-align:center}\n'
    '.opt.soon{opacity:.75}.skip{display:flex;justify-content:space-between;margin-top:10px;font-size:14px}.skip span{cursor:pointer;color:var(--acc2)}\n'
    '.aibox textarea{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}')

# ---------- icons for cafés and restaurants; an explicit icon wins
rep("var ICONS={statue:", "var ICONS={cafe:'<path d=\"M5 9h11v5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5zM16 10h2a2 2 0 0 1 0 4h-2M8 3v3M11 3v3M14 3v3\"/>',\n dining:'<path d=\"M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M16 3c-2 1-3 4-3 7h3v11\"/>',\n statue:")
rep("function iconOf(pl){", "function iconOf(pl){if(pl.ic)return pl.ic;")

# ---------- state
rep("VIDS=[], vidsAt={},", "FOOD=[], foodLayer=null, menuPage='', VIDS=[], vidsAt={},")
rep("var DEF={videos:true,", "var DEF={startSheet:true,foodC:true,foodP:true,foodB:true,foodR:true,videos:true,")
rep("PA={len:'day',pace:'normal',fame:'mix',themes:{},cats:{},from:'here'};",
    "PA={len:'day',pace:'normal',fame:'mix',themes:{},cats:{},from:'here',breaks:{}};")
rep("try{var _pa=JSON.parse(localStorage.getItem('strand.plan')||'null');if(_pa)PA=_pa}catch(e){}",
    "try{var _pa=JSON.parse(localStorage.getItem('strand.plan')||'null');if(_pa)PA=_pa;if(!PA.breaks)PA.breaks={}}catch(e){}\nvar AI_URL='';")

# ---------- food venues become places (ids f0..), never in clusters, lists, Lead me or alerts
rep("function active(id){return !excluded[D.places[id].g]}", "function active(id){var p=D.places[id];return !p.food&&!excluded[p.g]}")
rep("  computeThemes();\n", r"""  computeThemes();
  var foodReady=fetch('data/food.json').then(function(r){return r.ok?r.json():[]}).then(function(f){FOOD=f;var KW={c:['café','cafe'],p:['pub','pub'],b:['bar','pub'],r:['restaurant','dining']};
    f.forEach(function(v,i){var id='f'+i;v.id=id;D.places[id]={l:v.n,d:(v.f===2?'Famous pub':v.f===1?'Historic pub':KW[v.k][0][0].toUpperCase()+KW[v.k][0].slice(1))+(v.cu?' · '+v.cu:''),lat:v.lat,lon:v.lon,t:[KW[v.k][0]],f:0,n:0,food:v.k,famous:v.f||0,wd:v.wd,ic:v.k==='c'?'cafe':v.k==='r'?'dining':'pub',g:'food'}});
    drawFood()}).catch(function(){});
""")
rep("var urls=Object.keys(D.people).map(function(i){return 'data/people/'+i+'.json'}).concat(Object.keys(D.places).map(",
    "var urls=Object.keys(D.people).map(function(i){return 'data/people/'+i+'.json'}).concat(Object.keys(D.places).filter(function(i){return !D.places[i].food}).map(")
rep("$('#search').oninput=function(){var q=this.value.trim().toLowerCase();if(q.length<2||!D)return;panel.classList.remove('collapsed');",
    "$('#search').oninput=function(){var q=this.value.trim().toLowerCase();if(q.length<2||!D)return;panel.classList.remove('collapsed');var fq=FOOD.filter(function(v){return v.n.toLowerCase().indexOf(q)>=0}).sort(function(a,b){return (b.f||0)-(a.f||0)}).slice(0,8);")
s = s.replace("""  content.innerHTML='<h2>Places</h2>'+ll.map(""", """  content.innerHTML=(fq.length?'<h2>Food & drink</h2>'+fq.map(function(v){return '<div class="row">'+icon(D.places[v.id])+'<span class="who">'+link('l',v.id,v.n)+'<br><span class="dim">'+esc(D.places[v.id].d)+'</span></span></div>'}).join(''):'')+'<h2>Places</h2>'+ll.map(""", 1)

# ---------- place page: a food venue gets its own simple page; real places list food nearby
rep("function showPlace(id){var pl=D.places[id];cur={kind:'l',id:id};hop('l',id,pl.l);panel.classList.remove('collapsed');select([pl.lat,pl.lon]);",
    "function showPlace(id){var pl=D.places[id];cur={kind:'l',id:id};hop('l',id,pl.l);panel.classList.remove('collapsed');select([pl.lat,pl.lon]);saveActive(id);\n  if(pl.food){showFood(id);return}")
rep("   '<h2>Nearby</h2>'+nearby(pl.lat,pl.lon,8,id);\n  content.scrollTop=0;loadStory(id)}",
    "   '<h2>Nearby</h2>'+nearby(pl.lat,pl.lon,8,id)+foodNear(pl.lat,pl.lon,4,id);\n  content.scrollTop=0;loadStory(id)}")

# ---------- menu close: a re-render inside the menu must not count as a click outside it
rep("document.addEventListener('click',function(e){if(!e.target.closest('#menu,#menubtn'))$('#menu').classList.remove('open')});",
    "document.addEventListener('click',function(e){if(!e.target.isConnected)return;if(!e.target.closest('#menu,#menubtn')){$('#menu').classList.remove('open');if(menuPage){menuPage='';renderMenu()}}});")

# ---------- hierarchical menu
start = s.index("function renderMenu(){")
end = s.index("function seg(key,opts){")
s = s[:start] + r"""function mrow(page,label,small){return '<div class="mrow" data-act="menu:'+page+'"><span class="ml">'+label+(small?'<small>'+small+'</small>':'')+'</span><span class="go">›</span></div>'}
function mhead(t){return '<span class="mback" data-act="menu:">◀ Menu</span><h2 style="margin-top:2px">'+t+'</h2>'}
function renderMenu(){var m=$('#menu'),h='',off=GROUPS.filter(function(g){return excluded[g[0]]}).length,fk=['C','P','B','R'].filter(function(k){return S['food'+k]}).length;
  if(!menuPage)h=installRow()+'<div class="sw'+(walkOn?' on':'')+'" data-act="walk"><span>Walk with me<small>Speaks up when you pass somewhere worth a stop</small></span><i></i></div>'+
    '<div class="mrow" data-go="plan"><span class="ml">✦ Plan my visit<small>A few taps, then tours made for you</small></span><span class="go">›</span></div>'+
    mrow('tours','Tours',(curated.length+myTours.length)+' to walk'+(draft.stops.length?' · one in progress':''))+
    mrow('map','Show on the map',off?off+' kinds hidden':'Everything')+
    mrow('food','Food & drink',fk===4?'Cafés, pubs, bars, restaurants':fk?fk+' of 4 kinds':'Hidden')+
    mrow('alerts','Walk alerts',S.alertRadius+' m · '+({anyone:'anyone',known:'well known',famous:'famous'})[S.alertFame])+
    mrow('voice','Voice & sound',(S.speak?'Speaks':'Silent')+(S.vibrate?' · vibrates':''))+
    mrow('offline','Offline',S.offline?'Kept on this phone':'Off')+
    mrow('more','More','Start screen, history');
  else if(menuPage==='tours')h=mhead('Tours')+curated.map(function(t){return '<div class="row"><span class="who">'+link('t',t.id,t.name)+'<br><span class="dim">'+t.stops.length+' stops · curated</span></span></div>'}).join('')+
    myTours.map(function(t,i){return '<div class="row"><span class="who">'+link('t','m'+i,t.name)+'<br><span class="dim">'+t.stops.length+' stops · mine</span></span></div>'}).join('')+
    '<div class="actions" style="margin-top:8px"><button class="btn acc" data-go="plan">✦ Plan my visit</button><button class="btn" data-act="tour-open">'+(draft.stops.length?'✎ Tour in progress ('+draft.stops.length+')':'+ New tour')+'</button></div>';
  else if(menuPage==='map')h=mhead('Show on the map')+'<div class="chips">'+GROUPS.map(function(g){return '<span class="chip'+(excluded[g[0]]?' off':'')+'" data-act="cat:'+g[0]+'"><span class="ic"><svg viewBox="0 0 24 24">'+ICONS[g[2]]+'</svg></span>'+g[1]+'</span>'}).join('')+'</div>'+
    sw('videos','Guide videos','Short films by London guides, pinned where they were made');
  else if(menuPage==='food')h=mhead('Food & drink')+'<p class="stat">From OpenStreetMap. Shown when you zoom in; famous pubs show earlier. No ratings yet.</p>'+
    sw('foodC','Cafés','')+sw('foodP','Pubs','Famous and historic ones are ringed in gold')+sw('foodB','Bars','')+sw('foodR','Restaurants','');
  else if(menuPage==='alerts')h=mhead('Walk alerts')+'<div class="lab">For these kinds of place</div><div class="chips">'+GROUPS.map(function(g){return '<span class="chip'+(alertEx[g[0]]?' off':'')+'" data-act="acat:'+g[0]+'">'+g[1]+'</span>'}).join('')+'</div>'+
    '<div class="lab">Whose places</div>'+seg('alertFame',[['anyone','Anyone'],['known','Well known'],['famous','Famous']])+
    sw('alertStory','Only places with a story','Skips pins that have just a name and a relation')+
    '<div class="lab">Within</div>'+seg('alertRadius',[[50,'50 m'],[80,'80 m'],[150,'150 m']])+
    '<div class="lab">At most one every</div>'+seg('alertGap',[[20,'20 s'],[40,'40 s'],[90,'90 s']]);
  else if(menuPage==='voice')h=mhead('Voice & sound')+sw('speak','Speak alerts','Off: the card and a buzz only')+sw('vibrate','Vibrate','')+'<div class="lab">Speed</div>'+seg('rate',[[0.85,'Slower'],[0.95,'Normal'],[1.1,'Faster']]);
  else if(menuPage==='offline')h=mhead('Offline')+sw('offline','Keep London on this phone','About 30 MB: every place, person and story. The map itself is kept as you look at it.')+'<div class="stat" id="offstat">'+esc(offlineState)+'</div>';
  else if(menuPage==='more')h=mhead('More')+sw('startSheet','Ask what I want to do when I open the app','Skipped while you are in the middle of a tour')+
    '<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>';
  m.innerHTML=h}
""" + s[end:]

# ---------- actions
rep("if(a==='walk'){toggleWalk();return}",
    r"""if(a.slice(0,5)==='menu:'){menuPage=a.slice(5);renderMenu();$('#menu').scrollTop=0;return}
  if(a.slice(0,6)==='start:'){startAct(a.slice(6));return}
  if(a==='ai-plan'){aiPlan();return}
  if(a==='walk'){toggleWalk();return}""")
rep("if(k==='offline')offline(S[k]);if(k==='videos')drawVids();return}",
    "if(k==='offline')offline(S[k]);if(k==='videos')drawVids();if(k.slice(0,4)==='food')drawFood();return}")
rep("if(pq[0]==='themes'||pq[0]==='cats'){", "if(pq[0]==='themes'||pq[0]==='cats'||pq[0]==='breaks'){")
rep("  if(a==='tour-stop'){activeTour=null;drawTour(null);",
    "  if(a==='tour-stop'){activeTour=null;localStorage.removeItem('strand.active');drawTour(null);")

# ---------- planner: breaks question, AI box, coffee and pub in planDay
rep("""   '<div class="q">Start from</div>'+chipsQ('from',[['here','Where I am'],['map','The middle of the map']])+""",
    """   '<div class="q">Breaks</div>'+chipsQ('breaks',[['coffee','A coffee stop every couple of hours'],['pub','End at a famous pub']],1)+
   '<div class="q">Start from</div>'+chipsQ('from',[['here','Where I am'],['map','The middle of the map']])+
   (AI_URL?'<div class="q">Or say it in your own words</div><div class="aibox"><textarea id="aitext" rows="3" maxlength="300" placeholder="Two days, love Dickens and old pubs, not too much walking"></textarea><div class="actions"><button class="btn" data-act="ai-plan">✦ Plan from this</button><span class="stat" id="aistat"></span></div></div>':'')+""")
rep("function planDay(start,minutes,used,pace){var pos=start,left=minutes,stops=[],km=0;",
    "function nearestFood(lat,lon,kinds,used,maxKm,famousFirst){var best=null;FOOD.forEach(function(v){if(kinds.indexOf(v.k)<0||used[v.id])return;var d=dist(lat,lon,v.lat,v.lon);if(d>maxKm)return;var sc=d-(famousFirst?(v.f||0)*0.6:0);if(!best||sc<best.sc)best={id:v.id,d:d,sc:sc}});return best}\n"
    "function planDay(start,minutes,used,pace){var pos=start,left=minutes-(PA.breaks.pub?40:0),stops=[],km=0,sinceBreak=0;")
rep("    if(!best)break;used[best.id]=1;labels[D.places[best.id].l]=1;stops.push(best.id);",
    "    if(!best)break;used[best.id]=1;labels[D.places[best.id].l]=1;stops.push(best.id);sinceBreak+=best.cost;\n"
    "    if(PA.breaks.coffee&&sinceBreak>=110&&left>40){var cf=nearestFood(D.places[best.id].lat,D.places[best.id].lon,['c'],used,0.3,false);if(cf){used[cf.id]=1;stops.push(cf.id);var cc=cf.d/pace[0]*60+20;left-=cc;km+=cf.d;sinceBreak=0;pos=[D.places[cf.id].lat,D.places[cf.id].lon]}}")
rep("  return {stops:stops,km:km,mins:minutes-left}}",
    "  if(PA.breaks.pub&&stops.length){var pb=nearestFood(pos[0],pos[1],['p'],used,1,true)||nearestFood(pos[0],pos[1],['p','b'],used,2,false);if(pb){used[pb.id]=1;stops.push(pb.id);left-=pb.d/pace[0]*60+30;km+=pb.d}}\n"
    "  return {stops:stops,km:km,mins:minutes-left}}")
# the day's name and people: skip food stops for 'From X' and the names list
rep("if(r.stops.length){var first=D.places[r.stops[0]];",
    "if(r.stops.length){var first=D.places[r.stops.filter(function(i){return !D.places[i].food})[0]||r.stops[0]];")

# ---------- functions: food page, food layer, start sheet, active tour, AI
rep("/* Plan my visit: a few taps,", r"""/* Food and drink: OpenStreetMap venues (tools/pull_food.py), famous and historic pubs from Wikidata. */
function foodOn(k){return S['food'+k.toUpperCase()]}
function drawFood(){if(!foodLayer){foodLayer=L.layerGroup().addTo(map);map.on('moveend zoomend',drawFood)}foodLayer.clearLayers();var z=map.getZoom();if(z<14||!FOOD.length)return;
  var b=map.getBounds().pad(0.1),c=map.getCenter(),vs=FOOD.filter(function(v){return foodOn(v.k)&&(z>=16||(v.f===2&&v.k==='p'))&&b.contains([v.lat,v.lon])});
  vs.sort(function(a,b2){return dist(c.lat,c.lng,a.lat,a.lon)-dist(c.lat,c.lng,b2.lat,b2.lon)});
  vs.slice(0,220).forEach(function(v){L.marker([v.lat,v.lon],{icon:L.divIcon({className:'',html:'<div class="fpin '+v.k+(v.f===2?' f':'')+'">'+({c:'☕',p:'🍺',b:'🍸',r:'🍴'})[v.k]+'</div>',iconSize:v.f===2?[24,24]:[18,18],iconAnchor:v.f===2?[12,12]:[9,9]}),title:v.n,zIndexOffset:v.f===2?700:500}).on('click',function(){location.hash='#l/'+v.id}).addTo(foodLayer)})}
function foodNear(lat,lon,n,skip){var vs=FOOD.filter(function(v){return v.id!==skip&&foodOn(v.k)}).map(function(v){return [dist(lat,lon,v.lat,v.lon)-(v.f||0)*0.05,v]}).filter(function(x){return x[0]<0.35});
  vs.sort(function(a,b){return a[0]-b[0]});if(!vs.length)return '';
  return '<h2>Food & drink nearby</h2>'+vs.slice(0,n).map(function(x){var v=x[1],pl=D.places[v.id];return '<div class="row">'+icon(pl)+'<span class="who">'+link('l',v.id,v.n)+'<br><span class="dim">'+esc(pl.d)+'</span></span><span class="yrs">'+fmt(dist(lat,lon,v.lat,v.lon))+'</span></div>'}).join('')}
function showFood(id){var pl=D.places[id];map.flyTo([pl.lat,pl.lon],Math.max(map.getZoom(),17),{duration:.6});
  content.innerHTML='<h1>'+icon(pl,1)+esc(pl.l)+'</h1><p class="sub">'+esc(pl.d)+' · <a target="_blank" href="https://www.openstreetmap.org/?mlat='+pl.lat+'&mlon='+pl.lon+'#map=19/'+pl.lat+'/'+pl.lon+'">map</a>'+(pl.wd?' · <a target="_blank" href="https://www.wikidata.org/wiki/'+pl.wd+'">wikidata</a>':'')+'</p>'+
   tourStrip(id)+'<div class="actions"><button class="btn acc" data-act="lead">➜ Lead me on from here</button>'+(draft.stops.indexOf(id)<0?'<button class="btn" data-act="tour-add">+ Tour</button>':'<button class="btn on" data-act="tour-open">✓ In tour ('+draft.stops.length+')</button>')+'</div>'+
   '<h2>Worth seeing nearby</h2>'+nearby(pl.lat,pl.lon,8,id)+foodNear(pl.lat,pl.lon,3,id);content.scrollTop=0}
/* Start sheet: on opening the app, unless a tour is under way, offer the main ways in; Skip just starts. */
function saveActive(id){if(activeTour&&activeTour.stops.indexOf(id)>=0)localStorage.setItem('strand.active',JSON.stringify({name:activeTour.name,desc:activeTour.desc,stops:activeTour.stops,at:id}))}
function resumeOrStart(){var a=null;try{a=JSON.parse(localStorage.getItem('strand.active')||'null')}catch(e){}
  if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour);location.hash='#l/'+a.at;return true}
  if(!S.startSheet||location.hash.length>1)return false;try{if(sessionStorage.getItem('strand.started'))return false;sessionStorage.setItem('strand.started','1')}catch(e){}
  panel.classList.remove('collapsed');var meet=localStorage.getItem('strand.meetup');
  content.innerHTML='<h1>Where to today?</h1><p class="sub">Pick one, or skip and just explore.</p>'+
   '<div class="opt" data-act="start:around"><span class="i">◎</span><span><b>What is around me</b><span class="dim">Places nearby, closest first</span></span></div>'+
   '<div class="opt" data-act="start:walk"><span class="i">🚶</span><span><b>Walk with me</b><span class="dim">Wander; I will speak up when you pass something good</span></span></div>'+
   '<div class="opt" data-act="start:lead"><span class="i">➜</span><span><b>Lead me somewhere</b><span class="dim">Three directions worth walking</span></span></div>'+
   '<div class="opt" data-go="plan"><span class="i">✦</span><span><b>Plan my visit</b><span class="dim">A few taps, then tours made for you</span></span></div>'+
   '<div class="opt soon" data-act="start:meet"><span class="i">👥</span><span><b>Meet others on a tour</b><span class="dim">'+(meet?'Noted. We will tell you when meet-ups start.':'Coming soon. Tap if you would like it.')+'</span></span></div>'+
   '<div class="skip"><span data-act="start:skip">Skip</span><span data-act="start:never">Don\'t ask when I open the app</span></div>';return true}
function startAct(k){if(k==='around')locate(true);else if(k==='walk'){if(!walkOn)toggleWalk();locate(true)}else if(k==='lead')lead();
  else if(k==='meet'){localStorage.setItem('strand.meetup',new Date().toISOString());resumeOrStartShown()}
  else if(k==='never'){S.startSheet=false;saveS();renderMenu();showHome()}else showHome()}
function resumeOrStartShown(){try{sessionStorage.removeItem('strand.started')}catch(e){}resumeOrStart()}
/* AI planning (optional): when AI_URL is set, a sentence is turned into the same answers the taps give, by a small
   server that holds the model key (worker/ai-planner). The tours are still built here, from real places only. */
function aiPlan(){var t=($('#aitext').value||'').trim();if(t.length<4)return;var st=$('#aistat');st.textContent='Thinking…';var dev=localStorage.getItem('strand.dev');if(!dev){dev=Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem('strand.dev',dev)}
  fetch(AI_URL,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,device:dev,themes:THEMES.map(function(x){return x[0]}),cats:PLANCATS.map(function(x){return x[0]})})}).then(function(r){return r.json().then(function(j){return [r.status,j]})}).then(function(x){var j=x[1];
    if(x[0]!==200){st.textContent=j.error||'Not available just now';return}var a=j.answers||{};['len','pace','fame'].forEach(function(k){if(a[k])PA[k]=a[k]});PA.themes={};(a.themes||[]).forEach(function(k){PA.themes[k]=1});PA.cats={};(a.cats||[]).forEach(function(k){PA.cats[k]=1});PA.breaks={};(a.breaks||[]).forEach(function(k){PA.breaks[k]=1});
    localStorage.setItem('strand.plan',JSON.stringify(PA));makePlan();if(j.intro&&planned[0])planned[0].desc=j.intro+' '+planned[0].desc;location.hash='#plan/result'}).catch(function(){st.textContent='Not available just now'})}
/* Plan my visit: a few taps,""")

# ---------- open the start sheet (or resume) once data is loaded, instead of going straight to the route
rep("  fetch('data/tours.json').then(function(r){return r.ok?r.json():[]}).then(function(t){curated=t.filter(function(x){return x.stops.every(function(i){return D.places[i]})});renderMenu()}).catch(function(){}).then(route);",
    "  fetch('data/tours.json').then(function(r){return r.ok?r.json():[]}).then(function(t){curated=t.filter(function(x){return x.stops.every(function(i){return D.places[i]})});renderMenu()}).catch(function(){}).then(function(){return foodReady}).then(function(){if(!resumeOrStart())route()});")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
