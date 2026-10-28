"""One-off patch of site/index.html: menu with category switches, distance-first home, Walk mode."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# --- styles
rep('.btn.on{border-color:var(--acc);color:var(--acc)}',
    '.btn.on{border-color:var(--acc);color:var(--acc)}\n'
    '#menu{position:fixed;top:52px;left:10px;z-index:8;width:min(340px,calc(100vw - 20px));background:var(--bg);border:1px solid var(--line);border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.25);padding:12px 14px;display:none}\n'
    '#menu.open{display:block}#menu h2{margin:10px 0 6px}#menu h2:first-child{margin-top:0}\n'
    '.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{padding:5px 10px;border-radius:999px;border:1px solid var(--line);background:var(--chip);font-size:13px;cursor:pointer;display:inline-flex;align-items:center;gap:5px}\n'
    '.chip.off{opacity:.4;text-decoration:line-through}.chip .ic{width:18px;height:18px;border-radius:4px}.chip .ic svg{width:12px;height:12px;stroke-width:2.2}\n'
    '.sw{display:flex;align-items:center;justify-content:space-between;padding:6px 0;cursor:pointer}.sw i{width:40px;height:22px;border-radius:11px;background:var(--line);position:relative;flex:none}.sw i::after{content:"";position:absolute;top:3px;left:3px;width:16px;height:16px;border-radius:50%;background:#fff;transition:left .15s}\n'
    '.sw.on i{background:var(--acc)}.sw.on i::after{left:21px}.sw small{display:block;color:var(--muted)}\n'
    '#toast{position:fixed;left:10px;right:10px;bottom:64px;z-index:9;background:var(--acc);color:#fff;padding:10px 14px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,.3);display:none;cursor:pointer}#toast.show{display:block}\n'
    '@media(min-width:900px){#toast{left:auto;right:12px;width:440px;bottom:auto;top:100px}}\n'
    '.tease{font-size:13px;color:var(--muted);margin-top:2px}')

# --- shell: menu button, menu panel, toast
rep('<div id="top"><input id="search"', '<div id="top"><button class="btn" id="menubtn" title="Menu">☰</button><input id="search"')
rep('<div id="journey"></div>',
    '<div id="journey"></div>\n<div id="menu"></div>\n<div id="toast"></div>')

# --- state
rep("myPos=null, leadRadius=1.2;",
    "myPos=null, leadRadius=1.2, excluded={}, walkOn=false, walkWatch=null, alerted={}, lastAlert=0, wakeLock=null;\n"
    "try{excluded=JSON.parse(localStorage.getItem('strand.excluded')||'{}')}catch(e){}\n"
    "var GROUPS=[['monuments','Statues & memorials','statue',{statue:1,memorial:1,plaque:1}],['graves','Graves','grave',{grave:1}],['churches','Churches','church',{church:1}],['homes','Homes & palaces','house',{house:1,palace:1}],\n"
    " ['venues','Theatres & venues','theatre',{theatre:1}],['museums','Museums & libraries','museum',{museum:1}],['pubs','Pubs & hotels','pub',{pub:1}],['outdoors','Parks, streets & water','park',{park:1,street:1,water:1,bridge:1}],['other','Other buildings','building',{building:1,hospital:1,school:1,station:1}]];\n"
    "function groupOf(k){for(var i=0;i<GROUPS.length;i++)if(GROUPS[i][3][k])return GROUPS[i][0];return 'other'}\n"
    "function active(id){return !excluded[D.places[id].g]}")

# --- markers: group per place, filterable cluster
rep("""  cluster=L.markerClusterGroup({disableClusteringAtZoom:17,maxClusterRadius:50,chunkedLoading:true});
  Object.keys(d.places).forEach(function(id){var p=d.places[id];
    var m=L.marker([p.lat,p.lon],{title:p.l});m.on('click',function(){location.hash='#l/'+id});markers[id]=m;cluster.addLayer(m)});
  map.addLayer(cluster);
  route();""",
    """  cluster=L.markerClusterGroup({disableClusteringAtZoom:17,maxClusterRadius:50,chunkedLoading:true});
  Object.keys(d.places).forEach(function(id){var p=d.places[id];p.g=groupOf(iconOf(p));
    var m=L.marker([p.lat,p.lon],{title:p.l});m.on('click',function(){location.hash='#l/'+id});markers[id]=m});
  map.addLayer(cluster);refreshPins();renderMenu();
  if(localStorage.getItem('strand.loc')==='1')locate(false);
  route();""")
rep("function route(){if(!D)return;",
    """function refreshPins(){cluster.clearLayers();cluster.addLayers(Object.keys(D.places).filter(active).map(function(id){return markers[id]}))}
function renderMenu(){$('#menu').innerHTML='<div class="sw'+(walkOn?' on':'')+'" data-act="walk"><span>Walk with me<small>Speaks up when you pass somewhere worth a stop</small></span><i></i></div>'+
  '<h2>Show</h2><div class="chips">'+GROUPS.map(function(g){return '<span class="chip'+(excluded[g[0]]?' off':'')+'" data-act="cat:'+g[0]+'"><span class="ic"><svg viewBox="0 0 24 24">'+ICONS[g[2]]+'</svg></span>'+g[1]+'</span>'}).join('')+'</div>'+
  '<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>'}
$('#menubtn').onclick=function(){$('#menu').classList.toggle('open')};
document.addEventListener('click',function(e){if(!e.target.closest('#menu,#menubtn'))$('#menu').classList.remove('open')});
function route(){if(!D)return;""")

# --- nearby / lead / search respect the switches
rep("function nearby(lat,lon,n,skip){var arr=Object.keys(D.places).filter(function(i){return i!==skip})",
    "function nearby(lat,lon,n,skip){var arr=Object.keys(D.places).filter(function(i){return i!==skip&&active(i)})")
rep("var cands=Object.keys(D.places).filter(function(i){return !visited[i]&&!(cur&&cur.kind==='l'&&cur.id===i)})",
    "var cands=Object.keys(D.places).filter(function(i){return active(i)&&!visited[i]&&!(cur&&cur.kind==='l'&&cur.id===i)})")
rep("var ll=Object.keys(D.places).filter(function(i){return D.places[i].l&&D.places[i].l.toLowerCase().indexOf(q)>=0})",
    "var ll=Object.keys(D.places).filter(function(i){return active(i)&&D.places[i].l&&D.places[i].l.toLowerCase().indexOf(q)>=0})")

# --- actions: categories, walk, forget from the menu
rep("function act(a,btn){",
    """function act(a,btn){if(a.slice(0,4)==='cat:'){var g=a.slice(4);if(excluded[g])delete excluded[g];else excluded[g]=1;localStorage.setItem('strand.excluded',JSON.stringify(excluded));refreshPins();renderMenu();if(!location.hash||location.hash==='#')showHome();return}
  if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}
  """)

# --- distance-first home
rep("""function showHome(){panel.classList.remove('collapsed');
  var STRONG=""",
    """function showHome(){panel.classList.remove('collapsed');
  if(myPos){aroundYou();return}
  var STRONG=""")
rep("""   '<h2>Start with</h2>'+top.map(function(o){return personRow(o.id)}).join('')}""",
    """   '<div class="actions"><button class="btn acc" data-act="locate">◎ What is around me</button></div><h2>Start with</h2>'+top.map(function(o){return personRow(o.id)}).join('')}
/* Around you: the home page once location is allowed. Distance order, story teasers, no typing needed. */
function aroundYou(){var la=myPos[0],lo=myPos[1];cur=null;panel.classList.remove('collapsed');
  content.innerHTML='<h1>Around you</h1><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me</button><button class="btn" data-act="locate">◎ Refresh</button></div>'+nearby(la,lo,20);
  content.scrollTop=0;teasers()}
function teasers(){var rows=document.querySelectorAll('#content .row [data-go^="l/"]');if(!storyIdx){fetch('data/story/_index.json').then(function(r){return r.ok?r.json():{}}).then(function(x){storyIdx=x;teasers()}).catch(function(){storyIdx={}});return}
  var n=0;rows.forEach(function(el){var id=el.getAttribute('data-go').slice(2);if(!storyIdx[id]||n++>=12)return;
    fetch('data/story/'+id+'.json').then(function(r){return r.json()}).then(function(x){storyText[id]=x.t;if(!el.isConnected)return;var t=x.t.split(/(?<=\\.)\\s/)[0];var d=document.createElement('div');d.className='tease';d.textContent=t.length>140?t.slice(0,137)+'…':t;el.parentNode.appendChild(d)})})}
function locate(fly){if(!navigator.geolocation){alert('No location on this device');return}
  navigator.geolocation.getCurrentPosition(function(pos){onFix(pos);localStorage.setItem('strand.loc','1');if(fly)map.flyTo(myPos,16);
    if(fly||!location.hash||location.hash==='#'){location.hash='';aroundYou()}},function(){if(fly)alert('No location available')},{enableHighAccuracy:true,timeout:8000,maximumAge:30000})}
function onFix(pos){var la=pos.coords.latitude,lo=pos.coords.longitude;myPos=[la,lo];
  if(pos.coords.heading!=null&&pos.coords.speed>0.7)heading=pos.coords.heading;
  if(!hereMarker){hereMarker=L.circleMarker([la,lo],{radius:8,color:'#2f5d8a'}).addTo(map)}else hereMarker.setLatLng([la,lo])}
/* Walk with me: watch the position; when within reach of somewhere worth a stop, vibrate, show a card and say one line. */
function toggleWalk(){walkOn=!walkOn;renderMenu();
  if(walkOn){startCompass(function(){});walkWatch=navigator.geolocation.watchPosition(function(pos){onFix(pos);walkCheck()},function(){},{enableHighAccuracy:true,maximumAge:5000});
    if(navigator.wakeLock)navigator.wakeLock.request('screen').then(function(l){wakeLock=l}).catch(function(){});speak('Walk with me is on. I will speak up when you pass somewhere worth a stop.')}
  else{if(walkWatch!=null)navigator.geolocation.clearWatch(walkWatch);walkWatch=null;if(wakeLock){wakeLock.release();wakeLock=null}}}
function worthAStop(id){var p=D.places[id];return (storyIdx&&storyIdx[id])||(p.f||0)>=60||(p.n||0)>=3}
function walkCheck(){if(!myPos||Date.now()-lastAlert<40000)return;var la=myPos[0],lo=myPos[1],best=null;
  Object.keys(D.places).forEach(function(id){if(visited[id]||alerted[id]||!active(id))return;var p=D.places[id];var d=dist(la,lo,p.lat,p.lon);if(d>0.08||!worthAStop(id))return;
    var sc=(Math.log(1+(p.f||0))*3+Math.log(1+(p.n||0)))/(0.05+d);if(!best||sc>best.sc)best={id:id,p:p,d:d,sc:sc}});
  if(!best)return;lastAlert=Date.now();alerted[best.id]=1;var b=bearing(la,lo,best.p.lat,best.p.lon);var names=topNames(best.id,2).filter(function(n){return best.p.l.indexOf(n)<0});
  var line=Math.round(best.d*1000/10)*10+' metres '+relDir(b)+': '+best.p.l+(names.length?', '+names.join(' and '):'');
  var t=$('#toast');t.innerHTML='<b>'+esc(best.p.l)+'</b><br>'+esc(line.replace(/^.*?: /,''))+' · tap for the story';t.setAttribute('data-go','l/'+best.id);t.classList.add('show');setTimeout(function(){t.classList.remove('show')},25000);
  if(navigator.vibrate)navigator.vibrate([120,60,120]);
  function say(x){speak(line+'. '+(x||''))}
  if(storyIdx&&storyIdx[best.id]){if(storyText[best.id])say(storyText[best.id].split(/(?<=\\.)\\s/)[0]);else fetch('data/story/'+best.id+'.json').then(function(r){return r.json()}).then(function(x){storyText[best.id]=x.t;say(x.t.split(/(?<=\\.)\\s/)[0])}).catch(function(){say('')})}else say('')}""")

# --- the ◎ button becomes locate(true); old handler removed
rep("""$('#near').onclick=function(){navigator.geolocation.getCurrentPosition(function(pos){var la=pos.coords.latitude,lo=pos.coords.longitude;myPos=[la,lo];cur=null;
  map.flyTo([la,lo],16);if(hereMarker)map.removeLayer(hereMarker);hereMarker=L.circleMarker([la,lo],{radius:8,color:'#2f5d8a'}).addTo(map);
  panel.classList.remove('collapsed');content.innerHTML='<h1>Around you</h1><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me</button></div>'+nearby(la,lo,20)},function(){alert('No location available')},{enableHighAccuracy:true,timeout:8000})};""",
    """$('#near').onclick=function(){locate(true)};""")
# speak(): a walk alert must not be cancelled by the toggle logic when nothing is playing
rep("if(speaking){speechSynthesis.cancel();speaking=false;if(btn)btn.classList.remove('on');return}",
    "if(speaking&&btn){speechSynthesis.cancel();speaking=false;btn.classList.remove('on');return}")
open(p, 'w', encoding='utf-8').write(s)
print('patched')
