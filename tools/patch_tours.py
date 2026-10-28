"""One-off patch of site/index.html: pulsing current-place marker, tours (draft, save, share, curated)."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# --- styles
rep('.tease{font-size:13px;color:var(--muted);margin-top:2px}',
    '.tease{font-size:13px;color:var(--muted);margin-top:2px}\n'
    '.pulse{width:26px;height:26px;border-radius:50%;background:rgba(200,40,20,.35);border:2px solid #c8281a;animation:pulse 1.8s ease-out infinite}\n'
    '@keyframes pulse{0%{transform:scale(.5);opacity:1}100%{transform:scale(2.2);opacity:0}}\n'
    '.stop{width:28px;height:28px;border-radius:50%;background:#8a2f1d;color:#fff;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;font:bold 13px Georgia,serif}\n'
    '.num{flex:none;width:28px;height:28px;border-radius:50%;background:var(--acc);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:13px;margin-top:2px}\n'
    '.mini{display:flex;gap:4px}.mini .btn{padding:3px 8px;font-size:13px}\n'
    '.form input,.form textarea{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit;margin:4px 0}.form .cnt{font-size:12px;color:var(--muted);text-align:right}\n'
    '.leg{font-size:12px;color:var(--muted);padding:0 0 4px 38px}')

# --- state
rep("alerted={}, lastAlert=0, wakeLock=null;",
    "alerted={}, lastAlert=0, wakeLock=null, selMarker=null, tourLayer=null, curated=[], activeTour=null, draft={name:'',desc:'',stops:[]}, myTours=[];\n"
    "try{draft=JSON.parse(localStorage.getItem('strand.draft')||'null')||draft;myTours=JSON.parse(localStorage.getItem('strand.tours')||'[]')}catch(e){}")

# --- current place: pulsing marker, always on top of clusters
rep("function showPlace(id){var pl=D.places[id];cur={kind:'l',id:id};hop('l',id,pl.l);panel.classList.remove('collapsed');",
    "function select(latlng){if(selMarker)map.removeLayer(selMarker);selMarker=latlng?L.marker(latlng,{icon:L.divIcon({className:'',html:'<div class=\"pulse\"></div>',iconSize:[26,26],iconAnchor:[13,13]}),interactive:false,zIndexOffset:1000}).addTo(map):null}\n"
    "function showPlace(id){var pl=D.places[id];cur={kind:'l',id:id};hop('l',id,pl.l);panel.classList.remove('collapsed');select([pl.lat,pl.lon]);")
rep("function showPerson(id,ctxPlace){var p=D.people[id];cur={kind:'p',id:id};hop('p',id,p.l);panel.classList.remove('collapsed');",
    "function showPerson(id,ctxPlace){var p=D.people[id];cur={kind:'p',id:id};hop('p',id,p.l);panel.classList.remove('collapsed');select(ctxPlace&&D.places[ctxPlace]?[D.places[ctxPlace].lat,D.places[ctxPlace].lon]:null);")

# --- place page: tour buttons and stop position
rep("""'<div id="story"></div><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me on from here</button><button class="btn" data-act="listen">▶ Listen</button></div>'+""",
    """'<div id="story"></div>'+tourStrip(id)+'<div class="actions"><button class="btn acc" data-act="lead">➜ Lead me on from here</button><button class="btn" data-act="listen">▶ Listen</button>'+(draft.stops.indexOf(id)<0?'<button class="btn" data-act="tour-add">+ Tour</button>':'<button class="btn on" data-act="tour-open">✓ In tour ('+draft.stops.length+')</button>')+'</div>'+""")

# --- routes
rep("if(h[0]==='p'&&D.people[h[1]])showPerson(h[1],h[2]);else if(h[0]==='l'&&D.places[h[1]])showPlace(h[1]);else showHome()}",
    "if(h[0]==='p'&&D.people[h[1]])showPerson(h[1],h[2]);else if(h[0]==='l'&&D.places[h[1]])showPlace(h[1]);else if(h[0]==='t')showTour(h.slice(1).join('/'));else showHome()}")

# --- menu: tours section
rep("""'<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>'}""",
    """'<h2>Tours</h2>'+curated.map(function(t){return '<div class="row"><span class="who">'+link('t',t.id,t.name)+'<br><span class="dim">'+t.stops.length+' stops</span></span></div>'}).join('')+
  myTours.map(function(t,i){return '<div class="row"><span class="who">'+link('t','m'+i,t.name)+'<br><span class="dim">'+t.stops.length+' stops · mine</span></span></div>'}).join('')+
  '<div class="actions" style="margin-top:8px"><button class="btn" data-act="tour-open">'+(draft.stops.length?'✎ Tour in progress ('+draft.stops.length+')':'+ New tour')+'</button></div>'+
  '<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>'}""")

# --- load curated tours alongside the index
rep("  map.addLayer(cluster);refreshPins();renderMenu();",
    "  map.addLayer(cluster);refreshPins();renderMenu();\n  fetch('data/tours.json').then(function(r){return r.ok?r.json():[]}).then(function(t){curated=t.filter(function(x){return x.stops.every(function(i){return D.places[i]})});renderMenu()}).catch(function(){});")

# --- actions
rep("if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}",
    """if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}
  if(a==='tour-add'){draft.stops.push(cur.id);saveDraft();showPlace(cur.id);return}if(a==='tour-open'){location.hash='#t/draft';return}
  if(a.slice(0,5)==='stop:'){var x=a.slice(5).split(':'),i=+x[1];if(x[0]==='up'&&i>0){var tmp=draft.stops[i];draft.stops[i]=draft.stops[i-1];draft.stops[i-1]=tmp}else if(x[0]==='down'&&i<draft.stops.length-1){var tmp2=draft.stops[i];draft.stops[i]=draft.stops[i+1];draft.stops[i+1]=tmp2}else if(x[0]==='del')draft.stops.splice(i,1);saveDraft();showTour('draft');return}
  if(a==='tour-save'){var nm=$('#tname').value.trim().slice(0,40),ds=words($('#tdesc').value,100);if(!nm){alert('Give the tour a name');return}
    if(draft.stops.length<2){alert('A tour needs at least two stops');return}myTours.push({name:nm,desc:ds,stops:draft.stops.slice()});localStorage.setItem('strand.tours',JSON.stringify(myTours));draft={name:'',desc:'',stops:[]};saveDraft();renderMenu();location.hash='#t/m'+(myTours.length-1);return}
  if(a==='tour-clear'){if(confirm('Discard this tour?')){draft={name:'',desc:'',stops:[]};saveDraft();renderMenu();showTour('draft')}return}
  if(a==='tour-share'){var t=activeTour;var code=b64(JSON.stringify([t.name,t.desc,t.stops]));var url=location.origin+location.pathname+'#t/x/'+code;
    if(navigator.share)navigator.share({title:t.name,url:url}).catch(function(){});else{navigator.clipboard.writeText(url).then(function(){alert('Link copied')},function(){prompt('Copy this link',url)})}return}
  if(a==='tour-keep'){myTours.push({name:activeTour.name,desc:activeTour.desc,stops:activeTour.stops.slice()});localStorage.setItem('strand.tours',JSON.stringify(myTours));renderMenu();location.hash='#t/m'+(myTours.length-1);return}
  if(a.slice(0,9)==='tour-del:'){var k=+a.slice(9);if(confirm('Delete this tour?')){myTours.splice(k,1);localStorage.setItem('strand.tours',JSON.stringify(myTours));renderMenu();location.hash=''}return}
  if(a==='tour-edit'){draft={name:activeTour.name,desc:activeTour.desc,stops:activeTour.stops.slice()};saveDraft();location.hash='#t/draft';return}
  if(a==='tour-stop'){activeTour=null;drawTour(null);if(cur&&cur.kind==='l')showPlace(cur.id);else location.hash='';return}
  """)

# --- tour functions, before the lead() comment
rep("/* Lead me: three directions worth walking, diverse in bearing, ranked by who is there */",
    """/* Tours: an ordered list of places. Draft on the phone; saved on the phone; shared as a link that carries the whole tour;
   curated ones ship in data/tours.json and are committed by hand, which is the approval process. */
function saveDraft(){localStorage.setItem('strand.draft',JSON.stringify(draft))}
function words(t,n){var w=t.trim().split(/\\s+/).filter(Boolean);return w.slice(0,n).join(' ')}
function b64(x){return btoa(unescape(encodeURIComponent(x))).replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'')}
function unb64(x){return decodeURIComponent(escape(atob(x.replace(/-/g,'+').replace(/_/g,'/'))))}
function tourOf(key){if(key==='draft')return {key:key,name:draft.name,desc:draft.desc,stops:draft.stops,editable:true};
  if(key.slice(0,2)==='x/'){try{var a=JSON.parse(unb64(key.slice(2)));return {key:key,name:String(a[0]).slice(0,40),desc:words(String(a[1]||''),100),stops:a[2].filter(function(i){return D.places[i]}),shared:true}}catch(e){return null}}
  if(key[0]==='m'){var t=myTours[+key.slice(1)];return t?{key:key,name:t.name,desc:t.desc,stops:t.stops,mine:+key.slice(1)}:null}
  for(var i=0;i<curated.length;i++)if(curated[i].id===key)return {key:key,name:curated[i].name,desc:curated[i].desc,stops:curated[i].stops,curated:true};return null}
function drawTour(t){if(tourLayer){map.removeLayer(tourLayer);tourLayer=null}if(!t||!t.stops.length)return;
  var pts=t.stops.map(function(i){return [D.places[i].lat,D.places[i].lon]});
  tourLayer=L.layerGroup([L.polyline(pts,{color:'#8a2f1d',weight:3,dashArray:'6 6',opacity:.8})].concat(t.stops.map(function(id,i){return L.marker(pts[i],{icon:L.divIcon({className:'',html:'<div class="stop">'+(i+1)+'</div>',iconSize:[28,28],iconAnchor:[14,14]}),zIndexOffset:900}).on('click',function(){location.hash='#l/'+id})}))).addTo(map);
  if(pts.length>1)map.fitBounds(pts,{padding:[40,40],maxZoom:16});else map.flyTo(pts[0],16)}
function tourStrip(id){if(!activeTour)return '';var i=activeTour.stops.indexOf(id);if(i<0)return '';var n=activeTour.stops.length;
  return '<div class="actions"><span class="chip">'+esc(activeTour.name)+' · stop '+(i+1)+' of '+n+'</span>'+(i>0?'<button class="btn" data-go="l/'+activeTour.stops[i-1]+'">◀</button>':'')+(i<n-1?'<button class="btn acc" data-go="l/'+activeTour.stops[i+1]+'">Next stop ➜</button>':'<button class="btn" data-act="tour-stop">End tour</button>')+'</div>'}
function showTour(key){var t=tourOf(key);if(!t){location.hash='';return}cur=null;select(null);panel.classList.remove('collapsed');activeTour=t.stops.length?t:null;drawTour(t);
  var total=0;for(var i=1;i<t.stops.length;i++){var a=D.places[t.stops[i-1]],b=D.places[t.stops[i]];total+=dist(a.lat,a.lon,b.lat,b.lon)}
  var rows=t.stops.map(function(id,i){var pl=D.places[id];var leg=i?'<div class="leg">↓ '+fmt(dist(D.places[t.stops[i-1]].lat,D.places[t.stops[i-1]].lon,pl.lat,pl.lon))+'</div>':'';
    return leg+'<div class="row"><span class="num">'+(i+1)+'</span>'+icon(pl)+'<span class="who">'+link('l',id,pl.l)+'<br><span class="dim">'+esc(topNames(id,2).join(', '))+'</span></span>'+(t.editable?'<span class="mini"><button class="btn" data-act="stop:up:'+i+'">▲</button><button class="btn" data-act="stop:down:'+i+'">▼</button><button class="btn" data-act="stop:del:'+i+'">✕</button></span>':'')+'</div>'}).join('');
  var head=t.editable?'<h1>'+(t.stops.length?'Your tour':'New tour')+'</h1><p class="sub">'+(t.stops.length?t.stops.length+' stops, '+fmt(total)+' on foot. Open any place and press + Tour to add it.':'Open any place and press + Tour. Stops are numbered on the map in the order you add them; reorder here.')+'</p>':
    '<h1>'+esc(t.name)+'</h1><p class="sub">'+t.stops.length+' stops, '+fmt(total)+' on foot'+(t.curated?' · curated':t.shared?' · shared with you':'')+'</p>'+(t.desc?'<div class="story">'+esc(t.desc)+'</div>':'');
  var acts=t.editable?(t.stops.length>=2?'<div class="form"><input id="tname" maxlength="40" placeholder="Tour name (40 characters)" value="'+esc(t.name)+'"><textarea id="tdesc" rows="3" placeholder="What this tour is, 100 words at most" oninput="this.nextElementSibling.textContent=this.value.trim().split(/\\\\s+/).filter(Boolean).length+\\' / 100 words\\'">'+esc(t.desc)+'</textarea><div class="cnt">'+(t.desc?t.desc.split(/\\s+/).length:0)+' / 100 words</div></div>':'')+
      '<div class="actions">'+(t.stops.length?'<button class="btn acc" data-go="l/'+t.stops[0]+'">Start at stop 1</button>':'')+(t.stops.length>=2?'<button class="btn" data-act="tour-save">Save</button>':'')+(t.stops.length?'<button class="btn" data-act="tour-clear">Discard</button>':'')+'</div>':
    '<div class="actions">'+(t.stops.length?'<button class="btn acc" data-go="l/'+t.stops[0]+'">Start at stop 1</button>':'')+'<button class="btn" data-act="tour-share">Share link</button>'+(t.shared?'<button class="btn" data-act="tour-keep">Keep this tour</button>':'')+(t.mine!=null?'<button class="btn" data-act="tour-edit">Edit</button><button class="btn" data-act="tour-del:'+t.mine+'">Delete</button>':'')+'</div>';
  content.innerHTML=head+acts+rows;content.scrollTop=0}
/* Lead me: three directions worth walking, diverse in bearing, ranked by who is there */""")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
