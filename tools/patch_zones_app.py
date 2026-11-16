"""One-off patch of site/index.html: zones and drill-down sub-tours (Explore inside)."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# ---------- styles
rep('.leg{font-size:12px;color:var(--muted);padding:0 0 4px 38px}',
    '.leg{font-size:12px;color:var(--muted);padding:0 0 4px 38px}\n'
    '.zpin{min-width:30px;height:30px;padding:0 6px;border-radius:15px;background:#1d1a16;color:#f3c96b;border:2px solid #f3c96b;display:flex;align-items:center;justify-content:center;gap:3px;font:bold 12px Georgia,serif;box-shadow:0 2px 6px rgba(0,0,0,.45);white-space:nowrap}\n'
    '#subbar{position:fixed;top:52px;left:0;right:0;z-index:7;display:none;align-items:center;gap:8px;padding:8px 12px;background:#1d1a16;color:#f3c96b;font-size:14px;box-shadow:0 2px 10px rgba(0,0,0,.3)}\n'
    '#subbar.show{display:flex}#subbar b{color:#fff;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#subbar .btn{margin:0;padding:4px 10px;box-shadow:none;background:#2a251c;color:#f3c96b;border-color:#5a4a2a}\n'
    'body.inside #journey{display:none}\n'
    '.inside-box{border:2px solid #f3c96b;border-radius:12px;padding:10px 12px;margin:10px 0;background:var(--chip)}.inside-box b{display:block}\n'
    '.obj{width:100%;max-height:260px;object-fit:contain;border-radius:10px;background:var(--chip);margin:6px 0}')

# ---------- shell
rep('<div id="journey"></div>', '<div id="journey"></div>\n<div id="subbar"></div>')

# ---------- state
rep("FOOD=[], hasVid={},", "FOOD=[], hasVid={}, ZONES={}, zoneKid={}, SUB=null, subMask=null, zoneMins=60,")

# ---------- load zones before routing; zone children leave the clusters, parents get a badge
rep("then(function(){return foodReady}).then(function(){if(!resumeOrStart())route()});",
    "then(function(){return foodReady}).then(function(){return fetch('data/zones.json').then(function(r){return r.ok?r.json():{}}).then(buildZones).catch(function(){})}).then(function(){if(!resumeOrStart())route()});")
rep("function refreshPins(){cluster.clearLayers();cluster.addLayers(Object.keys(D.places).filter(active).map(function(id){return markers[id]}))}",
    "function refreshPins(){cluster.clearLayers();cluster.addLayers(Object.keys(D.places).filter(function(id){return active(id)&&!zoneKid[id]&&markers[id]}).map(function(id){return markers[id]}))}")

# ---------- routes: in/<n> is the n-th stop of the sub-tour
rep("else if(h[0]==='plan')showPlanner(h[1]);else showHome()}",
    "else if(h[0]==='plan')showPlanner(h[1]);else if(h[0]==='in'&&SUB)showInside(+h[1]);else showHome();subBar()}")

# ---------- place page: the Explore inside box under the story
rep("   '<div id=\"story\"></div>'+vidStrip(vidsNear(pl.lat,pl.lon,id))+tourStrip(id)",
    "   '<div id=\"story\"></div>'+zoneBox(id)+vidStrip(vidsNear(pl.lat,pl.lon,id))+tourStrip(id)")

# ---------- tour strip: a stop that is a zone offers to go inside
rep("+(fv.length?'<button class=\"btn acc\" data-act=\"vid:'+fv[0].i+'\">▶ Watch the guide here</button>':'')",
    "+(fv.length?'<button class=\"btn acc\" data-act=\"vid:'+fv[0].i+'\">▶ Watch the guide here</button>':'')+(ZONES[id]?'<button class=\"btn acc\" data-act=\"zone-go:'+id+'\">⤵ Explore inside</button>':'')")

# ---------- planner: a zone counts as one stop with a longer visit
rep("function dwell(pl){var k=iconOf(pl);if(pl.vid)return 6;", "function dwell(pl){var k=iconOf(pl);if(pl.vid)return 6;if(pl.id&&ZONES[pl.id])return Math.min(60,20+ZONES[pl.id].items.length*2);")

# ---------- walk alerts pause inside a zone
rep("function walkCheck(){if(!myPos||", "function walkCheck(){if(SUB||!myPos||")

# ---------- reopening the app returns to the sub-tour first
rep("function resumeOrStart(){var a=null;try{a=JSON.parse(localStorage.getItem('strand.active')||'null')}catch(e){}",
    "function resumeOrStart(){var a=null;try{a=JSON.parse(localStorage.getItem('strand.active')||'null')}catch(e){}\n"
    "  var sb=null;try{sb=JSON.parse(localStorage.getItem('strand.sub')||'null')}catch(e){}if(sb&&ZONES[sb.z]){if(a&&a.stops&&a.stops.every(function(i){return D.places[i]})){activeTour={key:'resume',name:a.name,desc:a.desc,stops:a.stops};drawTour(activeTour)}SUB=sb;maskZone(sb.z);location.hash='#in/'+sb.i;return true}")

# ---------- actions
rep("function act(a,btn){",
    "function act(a,btn){if(a.slice(0,8)==='zone-go:'){enterZone(a.slice(8));return}if(a.slice(0,6)==='zmins:'){zoneMins=+a.slice(6);showPlace(cur.id);return}\n"
    "  if(a==='sub-exit'){exitZone();return}if(a==='sub-listen'){speak(subSpeech(),btn);return}\n  ")

# ---------- the zone machinery, before the planner block
rep("/* Plan my visit: a few taps,", r"""/* Zones: a place that holds many stops (tools/pull_zones.py): its own parts, the pins packed around a square, objects
   in its collection, people buried there. Explore inside starts a sub-tour: a banner says you are in it, the map dims
   everything else, Next/Back step through by tap (GPS is no use indoors), Exit returns to the main tour's next stop. */
function buildZones(Z){var CEM=/cemetery|abbey|cathedral|church|chapel|churchyard|burial/;
  Object.keys(Z).forEach(function(zid){var z=Z[zid];
    if(z.l&&!D.places[zid]){D.places[zid]={l:z.l,d:'A square crowded with statues and memorials',lat:z.lat,lon:z.lon,t:['square'],f:0,n:0,g:'outdoors'};var m=L.marker([z.lat,z.lon],{title:z.l});m.on('click',function(){location.hash='#l/'+zid});markers[zid]=m}
    var items=[],peopleIn={};
    (z.places||[]).forEach(function(q){if(!D.places[q])return;items.push({k:'pl',id:q,sc:Math.log(2+(D.places[q].f||0))+1});zoneKid[q]=zid;(byPlace[q]||[]).forEach(function(l){peopleIn[l.pe]=1})});
    (z.objects||[]).forEach(function(o){items.push({k:'ob',o:o,sc:Math.log(1+o.sl)*1.6})});
    if(D.places[zid]&&CEM.test((D.places[zid].t||[]).join(' ').toLowerCase()))(byPlace[zid]||[]).forEach(function(l){if(l.r==='buried'&&!peopleIn[l.pe]&&D.people[l.pe]){peopleIn[l.pe]=1;items.push({k:'pe',id:l.pe,sc:Math.log(2+(D.people[l.pe].f||0))})}});
    items.sort(function(a,b){return b.sc-a.sc});if(items.length>=3)ZONES[zid]={items:items.slice(0,80)}});
  /* big cemeteries and churches with many burials but no zone yet */
  Object.keys(D.places).forEach(function(q){if(ZONES[q]||!CEM.test((D.places[q].t||[]).join(' ').toLowerCase()))return;var ps=(byPlace[q]||[]).filter(function(l){return l.r==='buried'&&D.people[l.pe]});
    if(ps.length>=8){var seen={},items=[];ps.forEach(function(l){if(seen[l.pe])return;seen[l.pe]=1;items.push({k:'pe',id:l.pe,sc:Math.log(2+(D.people[l.pe].f||0))})});items.sort(function(a,b){return b.sc-a.sc});ZONES[q]={items:items.slice(0,80)}}});
  Object.keys(ZONES).forEach(function(zid){var m=markers[zid];if(!m)return;var n=ZONES[zid].items.length;m.setIcon(L.divIcon({className:'',html:'<div class="zpin">⤵ '+n+'</div>',iconSize:[46,30],iconAnchor:[23,15]}))});
  refreshPins()}
function itemMins(it){return it.k==='ob'?4:it.k==='pe'?3:6}
function itemName(it){return it.k==='ob'?it.o.l:it.k==='pe'?D.people[it.id].l:D.places[it.id].l}
function pickItems(zid,mins){var out=[],t=0;ZONES[zid].items.forEach(function(it){if(t+itemMins(it)<=mins){out.push(it);t+=itemMins(it)}});return out}
function zoneBox(id){var z=ZONES[id];if(!z)return '';var pick=pickItems(id,zoneMins),total=z.items.reduce(function(a,it){return a+itemMins(it)},0);
  return '<div class="inside-box"><b>⤵ Explore inside: '+z.items.length+' stops, about '+fmtMins(total)+' for all</b><span class="dim">'+esc(z.items.slice(0,5).map(itemName).join(', '))+(z.items.length>5?'…':'')+'</span>'+
   '<div class="chips" style="margin-top:8px">'+[30,60,120].map(function(m){return '<span class="chip'+(zoneMins===m?' on':'')+'" data-act="zmins:'+m+'">'+fmtMins(m)+'</span>'}).join('')+'<span class="chip'+(zoneMins>=999?' on':'')+'" data-act="zmins:999">Everything</span></div>'+
   '<div class="actions"><button class="btn acc" data-act="zone-go:'+id+'">Go inside: '+pick.length+' stops</button></div></div>'}
function fmtMins(m){return m<60?m+' min':(Math.round(m/30)/2)+' h'}
function enterZone(zid){var items=pickItems(zid,zoneMins);if(!items.length)items=ZONES[zid].items.slice(0,5);
  var from=activeTour&&activeTour.stops.indexOf(zid)>=0?zid:null;
  SUB={z:zid,items:items.map(function(it){return it.k==='ob'?{k:'ob',o:it.o}:{k:it.k,id:it.id}}),i:0,from:from};saveSub();maskZone(zid);location.hash='#in/0'}
function saveSub(){if(SUB)localStorage.setItem('strand.sub',JSON.stringify(SUB));else localStorage.removeItem('strand.sub')}
function maskZone(zid){if(subMask){map.removeLayer(subMask);subMask=null}var c=D.places[zid];if(!c)return;var r=0.08;
  SUB&&SUB.items.forEach(function(it){if(it.k==='pl'&&D.places[it.id])r=Math.max(r,dist(c.lat,c.lon,D.places[it.id].lat,D.places[it.id].lon)+0.03)});r=Math.min(r,0.6);
  var ring=[];for(var a=0;a<=360;a+=10){var rad=a*Math.PI/180;ring.push([c.lat+r/111.2*Math.cos(rad),c.lon+r/(111.2*Math.cos(c.lat*Math.PI/180))*Math.sin(rad)])}
  subMask=L.polygon([[[85,-180],[85,180],[-85,180],[-85,-180]],ring],{stroke:true,color:'#f3c96b',weight:2,fillColor:'#000',fillOpacity:.45,interactive:false}).addTo(map);
  map.fitBounds(L.latLngBounds(ring),{padding:[30,30],maxZoom:18});document.body.classList.add('inside')}
function subBar(){var b=$('#subbar');if(!SUB||!ZONES[SUB.z]){b.classList.remove('show');document.body.classList.remove('inside');return}var z=D.places[SUB.z];
  var here=location.hash.indexOf('#in/')===0;
  b.innerHTML='<b>⤵ Inside '+esc(z.l)+' · '+(here?'stop '+(SUB.i+1)+' of '+SUB.items.length:'paused')+'</b>'+(here?'':'<button class="btn" data-go="in/'+SUB.i+'">Back inside</button>')+'<button class="btn" data-act="sub-exit">Exit</button>';b.classList.add('show');document.body.classList.add('inside')}
function exitZone(){var z=SUB&&SUB.z,from=SUB&&SUB.from;SUB=null;saveSub();if(subMask){map.removeLayer(subMask);subMask=null}subBar();
  if(from&&activeTour){var k=activeTour.stops.indexOf(from);location.hash='#l/'+(activeTour.stops[k+1]||from)}else location.hash=z?'#l/'+z:''}
function showInside(i){if(!SUB)return;i=Math.max(0,Math.min(SUB.items.length-1,i||0));SUB.i=i;saveSub();if(!subMask)maskZone(SUB.z);cur={kind:'in',id:SUB.z};panel.classList.remove('collapsed');
  var it=SUB.items[i],zl=D.places[SUB.z].l,last=i===SUB.items.length-1,h='',pic='',sub='',wtitle='';
  if(it.k==='ob'){var o=it.o;sub=(o.d?o.d+' · ':'')+'in the collection of '+zl;if(o.i)pic='<img class="obj" src="'+img(o,640)+'" alt="">';wtitle=o.w||''}
  else if(it.k==='pe'){var pp=D.people[it.id];sub=(pp.d||'')+' · buried here';if(pp.i)pic='<img class="obj" src="'+img(pp,480)+'" alt="">';wtitle=pp.w||''}
  else{var q=D.places[it.id];sub=q.d||'';select([q.lat,q.lon]);map.panTo([q.lat,q.lon])}
  h='<h1>'+esc(itemName(it))+'</h1><p class="sub">'+esc(sub)+'</p>'+pic+'<div id="insidetext" class="extract dim">…</div>'+
   (it.k==='pl'?vidStrip(vidsNear(D.places[it.id].lat,D.places[it.id].lon,it.id)):'')+
   '<div class="actions">'+(i>0?'<button class="btn" data-go="in/'+(i-1)+'">◀ Back</button>':'')+(last?'<button class="btn acc" data-act="sub-exit">Finish and leave</button>':'<button class="btn acc" data-go="in/'+(i+1)+'">Next ➜</button>')+
   '<button class="btn" data-act="sub-listen">▶ Listen</button>'+(it.k==='pl'?'<button class="btn" data-go="l/'+it.id+'">Full page</button>':it.k==='pe'?'<button class="btn" data-go="p/'+it.id+'">Their life</button>':'')+'</div>'+
   '<h2>Coming up</h2>'+SUB.items.slice(i+1,i+4).map(function(n,j){return '<div class="row"><span class="num">'+(i+j+2)+'</span><span class="who">'+link('in',i+j+1,itemName(n))+'</span></div>'}).join('');
  content.innerHTML=h;content.scrollTop=0;subBar();
  var put=function(t){var el=$('#insidetext');if(el&&SUB&&SUB.i===i){el.className='extract';el.textContent=t||''}};
  if(it.k==='pl'){fetch('data/story/'+it.id+'.json').then(function(r){return r.ok?r.json():{}}).then(function(x){put(x.t||D.places[it.id].d||'')}).catch(function(){put('')})}
  else if(wtitle){fetch('https://en.wikipedia.org/api/rest_v1/page/summary/'+encodeURIComponent(wtitle.replace(/ /g,'_'))).then(function(r){return r.json()}).then(function(w){put(w.extract||'')}).catch(function(){put('')})}else put('')}
function subSpeech(){var it=SUB&&SUB.items[SUB.i];if(!it)return '';var el=$('#insidetext');return itemName(it)+'. '+(el?el.textContent:'')}
/* Plan my visit: a few taps,""")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
