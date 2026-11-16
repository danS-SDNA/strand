"""One-off patch of site/index.html: video walks (guide film spots as tour stops) and two regex repairs."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# (the backspace-for-\b repair was applied to index.html directly beforehand: temple, minster, eat, paul, state)

# --- icon for a guide film spot
rep("var ICONS={cafe:", "var ICONS={video:'<rect x=\"3\" y=\"5\" width=\"18\" height=\"14\" rx=\"2\"/><path d=\"M10 9l5 3-5 3z\"/>',\n cafe:")

# --- state + default
rep("PA={len:'day',pace:'normal',fame:'mix',themes:{},cats:{},from:'here',breaks:{}};",
    "PA={len:'day',pace:'normal',fame:'mix',themes:{},cats:{},from:'here',breaks:{},vids:'some'};")
rep("if(!PA.breaks)PA.breaks={}}catch(e){}", "if(!PA.breaks)PA.breaks={};if(!PA.vids)PA.vids='some'}catch(e){}")
rep("FOOD=[], foodLayer=null,", "FOOD=[], hasVid={}, foodLayer=null,")

# --- film spots never clustered, listed, led to or alerted on (their own ▶ pins already show)
rep("function active(id){var p=D.places[id];return !p.food&&!excluded[p.g]}",
    "function active(id){var p=D.places[id];return !p.food&&!p.vid&&!excluded[p.g]}")

# --- after videos load: a film with no Strand place within 100 m becomes a spot of its own; note which places have films
rep("drawVids();if(cur&&cur.kind==='l')showPlace(cur.id)}).catch(function(){});",
    "drawVids();filmSpots();if(cur&&cur.kind==='l')showPlace(cur.id)}).catch(function(){});")

# --- offline download skips film spots (no story files)
rep("concat(Object.keys(D.places).filter(function(i){return !D.places[i].food}).map(",
    "concat(Object.keys(D.places).filter(function(i){return !D.places[i].food&&!D.places[i].vid}).map(")

# --- place page for a film spot reuses the simple page, which now shows the films too
rep("  if(pl.food){showFood(id);return}", "  if(pl.food||pl.vid){showFood(id);return}")
rep("   tourStrip(id)+'<div class=\"actions\"><button class=\"btn acc\" data-act=\"lead\">➜ Lead me on from here</button>'+(draft.stops.indexOf(id)<0?",
    "   vidStrip(vidsNear(pl.lat,pl.lon,id))+tourStrip(id)+'<div class=\"actions\"><button class=\"btn acc\" data-act=\"lead\">➜ Lead me on from here</button>'+(draft.stops.indexOf(id)<0?")

# --- tour strip: a Watch button wherever the stop has a film
rep("function tourStrip(id){if(!activeTour)return '';var i=activeTour.stops.indexOf(id);if(i<0)return '';var n=activeTour.stops.length;",
    "function tourStrip(id){if(!activeTour)return '';var i=activeTour.stops.indexOf(id);if(i<0)return '';var n=activeTour.stops.length;var pv=D.places[id],fv=pv?vidsNear(pv.lat,pv.lon,id):[];")
rep("  return '<div class=\"actions\"><span class=\"chip\">'+esc(activeTour.name)+' · stop '+(i+1)+' of '+n+'</span>'",
    "  return '<div class=\"actions\"><span class=\"chip\">'+esc(activeTour.name)+' · stop '+(i+1)+' of '+n+'</span>'+(fv.length?'<button class=\"btn acc\" data-act=\"vid:'+fv[0].i+'\">▶ Watch the guide here</button>':'')")

# --- planner question
rep("   '<div class=\"q\">Breaks</div>'+",
    "   '<div class=\"q\">Guide films</div>'+chipsQ('vids',[['off','Leave them out'],['some','Include spots guides filmed'],['only','A video walk: only those spots']])+\n   '<div class=\"q\">Breaks</div>'+")

# --- scoring: film spots are candidates when films are wanted; a video walk keeps only spots with a film
rep("function planScore(id){var pl=D.places[id];if(!active(id)||",
    "function planScore(id){var pl=D.places[id];if(pl.food)return 0;if(pl.vid){if(PA.vids==='off'||!hasVid[id])return 0}else if(PA.vids==='only'&&!hasVid[id])return 0;if((!pl.vid&&!active(id))||")
rep("  return interest*fame*dull*(storyIdx&&storyIdx[id]?1:0.5)}",
    "  var film=hasVid[id]?(PA.vids==='some'?2.5:PA.vids==='only'?3:1):1;if(pl.vid&&interest<1)interest=1;\n"
    "  return interest*fame*dull*film*(pl.vid||(storyIdx&&storyIdx[id])?1:0.5)}")
# watching takes a few minutes; film spots are further apart, so allow longer hops on a video walk
rep("function dwell(pl){var k=iconOf(pl);return {", "function dwell(pl){var k=iconOf(pl);if(pl.vid)return 6;return (PA.vids!=='off'&&pl.id&&hasVid[pl.id]?3:0)+({")
rep("statue:8,plaque:6,memorial:8,street:6,water:10,bridge:8,house:10,building:10}[k]||10}",
    "statue:8,plaque:6,memorial:8,street:6,water:10,bridge:8,house:10,building:10}[k]||10)}")
rep("if(d>(stops.length?1.2:1.5))return;", "if(d>(stops.length?(PA.vids==='only'?1.6:1.2):1.5))return;")
rep("var walk=d/pace[0]*60,cost=walk+dwell(pl)*pace[1];", "pl.id=c.id;var walk=d/pace[0]*60,cost=walk+dwell(pl)*pace[1];")

# --- naming: a video walk says so and credits the guides
rep("      planned.push({name:(L[1]>1?'Day '+(day+1)+': ':'')+'From '+first.l,",
    "      var films=[];r.stops.forEach(function(i){var q=D.places[i];vidsNear(q.lat,q.lon,i).forEach(function(v){var c=v.c.replace(/\\s*\\(.*\\)$/,'');if(films.indexOf(c)<0)films.push(c)})});\n"
    "      if(films.length&&PA.vids!=='off')names.push('films by '+films.slice(0,3).join(', '));\n"
    "      planned.push({name:(L[1]>1?'Day '+(day+1)+': ':'')+(PA.vids==='only'?'Video walk from ':'From ')+first.l,")

# --- the function that builds film spots
rep("/* Food and drink: OpenStreetMap venues", r"""/* Film spots: a guide video with no Strand place within 100 m becomes a place of its own ('v' ids), so a tour can
   stop there; hasVid marks every place, real or not, that has a film within 100 m. */
function filmSpots(){var n=0;VIDS.forEach(function(v){if(v.pl&&v.pl.length&&D.places[v.pl[0]])return;
    var near=Object.keys(D.places).some(function(i){var q=D.places[i];return !q.food&&dist(v.lat,v.lon,q.lat,q.lon)<0.1});if(near)return;
    var id='v'+(n++);D.places[id]={l:(v.w||v.t).replace(/\s*\(.*\)$/,''),d:'Filmed here by '+v.c.replace(/\s*\(.*\)$/,''),lat:v.lat,lon:v.lon,t:['guide film'],f:0,n:0,vid:1,ic:'video',g:'video'}});
  hasVid={};Object.keys(D.places).forEach(function(i){var q=D.places[i];if(q.food)return;if(vidsAt[i]||VIDS.some(function(v){return dist(q.lat,q.lon,v.lat,v.lon)<0.1}))hasVid[i]=1})}
/* Food and drink: OpenStreetMap venues""")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
