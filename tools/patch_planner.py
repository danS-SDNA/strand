"""One-off patch of site/index.html: Plan my visit (tap-only questions, rule-based multi-day tours)."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep('.chip.on{border-color:var(--acc);background:var(--bg);font-weight:bold}',
    '.chip.on{border-color:var(--acc);background:var(--bg);font-weight:bold}\n'
    '.q{margin:14px 0 4px;font-weight:bold}.day{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:10px 0;background:var(--chip)}.day b{display:block}')

# state: planner answers and the last plan
rep("alertEx={}, offlineState='', deferredInstall=null;",
    "alertEx={}, offlineState='', deferredInstall=null, planned=[], PA={len:'day',pace:'normal',fame:'mix',themes:{},cats:{},from:'here'};\n"
    "try{var _pa=JSON.parse(localStorage.getItem('strand.plan')||'null');if(_pa)PA=_pa}catch(e){}")

# themes from people descriptions, computed once at load
rep("  map.addLayer(cluster);refreshPins();renderMenu();",
    "  computeThemes();\n  map.addLayer(cluster);refreshPins();renderMenu();")

# routes
rep("else if(h[0]==='t')showTour(h.slice(1).join('/'));",
    "else if(h[0]==='t')showTour(h.slice(1).join('/'));else if(h[0]==='plan')showPlanner(h[1]);")

# tourOf: planned days
rep("  if(key[0]==='m'){var t=myTours[+key.slice(1)];",
    "  if(key[0]==='p'&&planned[+key.slice(1)]){var pd=planned[+key.slice(1)];return {key:key,name:pd.name,desc:pd.desc,stops:pd.stops,planned:true}}\n  if(key[0]==='m'){var t=myTours[+key.slice(1)];")
rep("(t.shared?'<button class=\"btn\" data-act=\"tour-keep\">Keep this tour</button>':'')",
    "(t.shared||t.planned?'<button class=\"btn\" data-act=\"tour-keep\">Keep this tour</button>':'')+(t.planned?'<button class=\"btn\" data-go=\"plan/result\">◀ Back to the plan</button>':'')")

# entry points: home and menu
rep("""'<div class="actions"><button class="btn acc" data-act="locate">◎ What is around me</button></div><h2>Start with</h2>'""",
    """'<div class="actions"><button class="btn acc" data-act="locate">◎ What is around me</button><button class="btn" data-go="plan">✦ Plan my visit</button></div><h2>Start with</h2>'""")
rep("""  content.innerHTML='<h1>Around you</h1><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me</button><button class="btn" data-act="locate">◎ Refresh</button></div>'+nearby(la,lo,20);""",
    """  content.innerHTML='<h1>Around you</h1><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me</button><button class="btn" data-go="plan">✦ Plan my visit</button><button class="btn" data-act="locate">◎ Refresh</button></div>'+nearby(la,lo,20);""")
rep("""  '<div class="actions" style="margin-top:8px"><button class="btn" data-act="tour-open">'""",
    """  '<div class="actions" style="margin-top:8px"><button class="btn acc" data-go="plan">✦ Plan my visit</button><button class="btn" data-act="tour-open">'""")

# actions
rep("if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}",
    """if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}
  if(a.slice(0,3)==='pa:'){var pq=a.slice(3).split(':');if(pq[0]==='themes'||pq[0]==='cats'){if(PA[pq[0]][pq[1]])delete PA[pq[0]][pq[1]];else PA[pq[0]][pq[1]]=1}else PA[pq[0]]=pq[1];localStorage.setItem('strand.plan',JSON.stringify(PA));var sc=content.scrollTop;showPlanner();content.scrollTop=sc;return}
  if(a==='plan-go'){makePlan();location.hash='#plan/result';return}
  if(a==='plan-keepall'){planned.forEach(function(d){myTours.push({name:d.name,desc:d.desc,stops:d.stops.slice()})});localStorage.setItem('strand.tours',JSON.stringify(myTours));renderMenu();alert(planned.length+' tour'+(planned.length>1?'s':'')+' saved under ☰ → Tours');return}""")

# the planner itself, before the Lead-me comment
rep("/* Lead me: three directions worth walking, diverse in bearing, ranked by who is there */",
    r"""/* Plan my visit: a few taps, then tours built on the phone from the people behind each place. No AI, no server. */
var THEMES=[['writers','Writers & poets',/writer|poet|novelist|playwright|author|essayist|dramatist|journalist|diarist/],['science','Science & invention',/scientist|physicist|chemist|mathematician|engineer|inventor|biologist|astronomer|naturalist|physician|surgeon|nurse/],
 ['art','Art & architecture',/painter|sculptor|artist|architect|designer|illustrator|photographer/],['stage','Music & stage',/composer|musician|singer|actor|actress|comedian|dancer|conductor|songwriter|guitarist/],
 ['royal','Kings & queens',/\bking\b|queen|prince|princess|monarch|duke|duchess|\bearl\b|royal|emperor/],['politics','Politics & reform',/politician|prime minister|statesman|activist|reformer|suffrag|campaigner|revolutionary|philosopher|economist|abolition/],
 ['war','Soldiers & explorers',/military|officer|admiral|general\b|soldier|explorer|navigator|aviator|naval/],['faith','Faith & churches',/bishop|priest|cleric|saint|theologian|archbishop|preacher|nun\b|monk/]];
var PLANCATS=[['museums','Museums','museum'],['churches','Churches','church'],['pubs','Pubs','pub'],['outdoors','Parks & squares','park'],['graves','Graves','grave'],['monuments','Statues','statue']];
var LENS={hours:[2,1],half:[4,1],day:[7,1],two:[7,2],three:[7,3],week:[7,5]};var PACE={gentle:[3.5,1.3],normal:[4.5,1],brisk:[5.5,0.8]};
function computeThemes(){Object.keys(D.places).forEach(function(id){var th={};(byPlace[id]||[]).forEach(function(l){var p=D.people[l.pe];if(!p||!p.d)return;var d=p.d.toLowerCase(),w=Math.log(2+(p.f||0));THEMES.forEach(function(t){if(t[2].test(d))th[t[0]]=(th[t[0]]||0)+w})});D.places[id].th=th})}
function chipsQ(key,opts,multi){return '<div class="chips">'+opts.map(function(o){var on=multi?PA[key][o[0]]:PA[key]===o[0];return '<span class="chip'+(on?' on':'')+'" data-act="pa:'+key+':'+o[0]+'">'+o[1]+'</span>'}).join('')+'</div>'}
function showPlanner(sub){if(sub==='result'&&planned.length){showPlan();return}cur=null;select(null);panel.classList.remove('collapsed');
  content.innerHTML='<h1>Plan my visit</h1><p class="sub">A few taps and Strand builds walking tours around what you like. Nothing to type; your answers stay on this phone.</p>'+
   '<div class="q">How long are you here?</div>'+chipsQ('len',[['hours','A couple of hours'],['half','Half a day'],['day','A day'],['two','Two days'],['three','Three days'],['week','A week']])+
   '<div class="q">What are you into?</div>'+chipsQ('themes',THEMES.map(function(t){return [t[0],t[1]]}),1)+'<div style="height:6px"></div>'+chipsQ('cats',PLANCATS.map(function(c){return [c[0],c[1]]}),1)+
   '<div class="q">Famous or hidden?</div>'+chipsQ('fame',[['famous','The famous ones'],['mix','A mix'],['hidden','Off the beaten track']])+
   '<div class="q">Walking pace</div>'+chipsQ('pace',[['gentle','Gentle'],['normal','Normal'],['brisk','Brisk']])+
   '<div class="q">Start from</div>'+chipsQ('from',[['here','Where I am'],['map','The middle of the map']])+
   '<div class="actions" style="margin-top:16px"><button class="btn acc" data-act="plan-go">✦ Plan it</button></div>';content.scrollTop=0}
function dwell(pl){var k=iconOf(pl);return {museum:60,palace:40,church:20,pub:30,park:20,theatre:10,grave:10,hospital:10,school:10,station:5,statue:5,plaque:5,memorial:5,street:5,water:10,bridge:5,house:10,building:10}[k]||10}
function planScore(id){var pl=D.places[id];if(!active(id))return 0;var th=pl.th||{},want=Object.keys(PA.themes),cats=Object.keys(PA.cats);
  var interest=1;want.forEach(function(t){interest+=(th[t]||0)});if(cats.length&&cats.indexOf(pl.g)>=0)interest+=4;if((want.length||cats.length)&&interest===1)interest=0.15;
  var f=pl.f||0,fame=PA.fame==='famous'?Math.log(2+f):PA.fame==='hidden'?(f>300?0.2:2.5/Math.log(3+f)):Math.sqrt(Math.log(2+f));
  return interest*fame*(storyIdx&&storyIdx[id]?1:0.5)}
function planDay(start,minutes,used,pace){var pos=start,left=minutes,stops=[],km=0;
  var cands=Object.keys(D.places).filter(function(i){return !used[i]&&dist(start[0],start[1],D.places[i].lat,D.places[i].lon)<3}).map(function(i){return {id:i,s:planScore(i)}}).filter(function(c){return c.s>0});
  while(stops.length<14){var best=null;cands.forEach(function(c){if(used[c.id])return;var pl=D.places[c.id],d=dist(pos[0],pos[1],pl.lat,pl.lon);if(d>1.2)return;
      var walk=d/pace[0]*60,cost=walk+dwell(pl)*pace[1];if(cost>left)return;var v=c.s/(4+cost);if(!best||v>best.v)best={id:c.id,v:v,cost:cost,d:d}});
    if(!best)break;used[best.id]=1;stops.push(best.id);left-=best.cost;km+=best.d;pos=[D.places[best.id].lat,D.places[best.id].lon]}
  return {stops:stops,km:km,mins:minutes-left}}
function makePlan(){var L=LENS[PA.len],pace=PACE[PA.pace],used={},start;if(PA.from==='here'&&myPos)start=myPos.slice();else{var c=map.getCenter();start=[c.lat,c.lng]}
  planned=[];var starts=[start];for(var day=0;day<L[1];day++){var r=planDay(start,L[0]*60,used,pace);if(r.stops.length){var first=D.places[r.stops[0]];
      var names=[];r.stops.forEach(function(i){topNames(i,1).forEach(function(n){if(names.indexOf(n)<0&&names.length<4)names.push(n)})});
      planned.push({name:(L[1]>1?'Day '+(day+1)+': ':'')+'From '+first.l,desc:r.stops.length+' stops, about '+fmt(r.km)+' on foot and '+Math.round(r.mins/30)/2+' hours with time at each. With '+names.join(', ')+'.',stops:r.stops,km:r.km,mins:r.mins})}
    /* next day: the best unused place well away from earlier starts */
    var nb=null;Object.keys(D.places).forEach(function(i){if(used[i])return;var pl=D.places[i];if(starts.some(function(s){return dist(s[0],s[1],pl.lat,pl.lon)<2}))return;var sc=planScore(i);if(!nb||sc>nb.s)nb={i:i,s:sc}});
    if(!nb)break;start=[D.places[nb.i].lat,D.places[nb.i].lon];starts.push(start)}}
function showPlan(){cur=null;select(null);activeTour=null;drawTour(null);panel.classList.remove('collapsed');
  content.innerHTML='<h1>Your plan</h1><p class="sub">'+(planned.length?planned.length+' tour'+(planned.length>1?'s':'')+'. Open one to see it on the map; keep the ones you like.':'Nothing matched. Try fewer interests or a longer time.')+'</p>'+
   planned.map(function(d,i){return '<div class="day" data-go="t/p'+i+'"><b>'+esc(d.name)+'</b><span class="dim">'+esc(d.desc)+'</span></div>'}).join('')+
   '<div class="actions">'+(planned.length?'<button class="btn acc" data-act="plan-keepall">Keep all</button>':'')+'<button class="btn" data-go="plan">Change answers</button></div>';content.scrollTop=0}
/* Lead me: three directions worth walking, diverse in bearing, ranked by who is there */""")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
