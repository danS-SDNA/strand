"""One-off patch of site/index.html: settings section (alerts, voice), offline switch, vendored libraries, service worker."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


# --- vendored libraries instead of CDNs (needed offline)
rep('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">', '<link rel="stylesheet" href="vendor/leaflet/leaflet.min.css">')
rep('<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">', '<link rel="stylesheet" href="vendor/markercluster/MarkerCluster.css">')
rep('<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">', '<link rel="stylesheet" href="vendor/markercluster/MarkerCluster.Default.css">')
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>', '<script src="vendor/leaflet/leaflet.min.js"></script>')
rep('<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>', '<script src="vendor/markercluster/leaflet.markercluster.js"></script>')

# --- styles
rep('.leg{font-size:12px;color:var(--muted);padding:0 0 4px 38px}',
    '.leg{font-size:12px;color:var(--muted);padding:0 0 4px 38px}\n'
    '.chip.on{border-color:var(--acc);background:var(--bg);font-weight:bold}.lab{font-size:13px;color:var(--muted);margin:8px 0 3px}\n'
    '#menu{max-height:calc(100vh - 70px);overflow-y:auto}.stat{font-size:12px;color:var(--muted);margin:-2px 0 6px}')

# --- settings state
rep("draft={name:'',desc:'',stops:[]}, myTours=[];",
    "draft={name:'',desc:'',stops:[]}, myTours=[], alertEx={}, offlineState='';\n"
    "var DEF={speak:true,vibrate:true,rate:0.95,alertRadius:80,alertGap:40,alertFame:'known',alertStory:true,offline:false};var S={};\n"
    "try{S=JSON.parse(localStorage.getItem('strand.settings')||'{}');alertEx=JSON.parse(localStorage.getItem('strand.alertEx')||'{}')}catch(e){}\n"
    "Object.keys(DEF).forEach(function(k){if(S[k]===undefined)S[k]=DEF[k]});\n"
    "function saveS(){localStorage.setItem('strand.settings',JSON.stringify(S));localStorage.setItem('strand.alertEx',JSON.stringify(alertEx))}\n"
    "var FAMEMIN={anyone:0,known:40,famous:150};")

# --- menu: settings section
rep("""  '<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>'}""",
    """  '<h2>Alerts on a walk</h2><div class="lab">For these kinds of place</div><div class="chips">'+GROUPS.map(function(g){return '<span class="chip'+(alertEx[g[0]]?' off':'')+'" data-act="acat:'+g[0]+'">'+g[1]+'</span>'}).join('')+'</div>'+
  '<div class="lab">Whose places</div>'+seg('alertFame',[['anyone','Anyone'],['known','Well known'],['famous','Famous']])+
  sw('alertStory','Only places with a story','Skips pins that have just a name and a relation')+
  '<div class="lab">Within</div>'+seg('alertRadius',[[50,'50 m'],[80,'80 m'],[150,'150 m']])+
  '<div class="lab">At most one every</div>'+seg('alertGap',[[20,'20 s'],[40,'40 s'],[90,'90 s']])+
  sw('speak','Speak alerts','Off: the card and a buzz only')+sw('vibrate','Vibrate','')+
  '<h2>Voice</h2>'+seg('rate',[[0.85,'Slower'],[0.95,'Normal'],[1.1,'Faster']])+
  '<h2>Offline</h2>'+sw('offline','Keep London on this phone','About 30 MB: every place, person and story. The map itself is kept as you look at it.')+'<div class="stat" id="offstat">'+esc(offlineState)+'</div>'+
  '<div class="actions" style="margin-top:12px"><button class="btn" data-act="forget">Forget where I have been</button></div>'}
function seg(key,opts){return '<div class="chips">'+opts.map(function(o){return '<span class="chip'+(String(S[key])===String(o[0])?' on':'')+'" data-act="set:'+key+':'+o[0]+'">'+o[1]+'</span>'}).join('')+'</div>'}
function sw(key,label,small){return '<div class="sw'+(S[key]?' on':'')+'" data-act="set:'+key+':toggle"><span>'+label+(small?'<small>'+small+'</small>':'')+'</span><i></i></div>'}""")

# --- actions for settings
rep("if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}",
    """if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}
  if(a.slice(0,5)==='acat:'){var ag=a.slice(5);if(alertEx[ag])delete alertEx[ag];else alertEx[ag]=1;saveS();renderMenu();return}
  if(a.slice(0,4)==='set:'){var sp=a.slice(4).split(':'),k=sp[0],v=sp[1];if(v==='toggle')S[k]=!S[k];else S[k]=isNaN(+v)?v:+v;saveS();renderMenu();if(k==='offline')offline(S[k]);return}""")

# --- walk check honours the settings
rep("function worthAStop(id){var p=D.places[id];return (storyIdx&&storyIdx[id])||(p.f||0)>=60||(p.n||0)>=3}",
    "function worthAStop(id){var p=D.places[id];if(alertEx[p.g])return false;if(S.alertStory&&!(storyIdx&&storyIdx[id]))return false;return (p.f||0)>=FAMEMIN[S.alertFame]||(S.alertFame==='anyone')}")
rep("function walkCheck(){if(!myPos||Date.now()-lastAlert<40000)return;", "function walkCheck(){if(!myPos||Date.now()-lastAlert<S.alertGap*1000)return;")
rep("var d=dist(la,lo,p.lat,p.lon);if(d>0.08||!worthAStop(id))return;", "var d=dist(la,lo,p.lat,p.lon);if(d>S.alertRadius/1000||!worthAStop(id))return;")
rep("  if(navigator.vibrate)navigator.vibrate([120,60,120]);\n  function say(x){speak(line+'. '+(x||''))}",
    "  if(S.vibrate&&navigator.vibrate)navigator.vibrate([120,60,120]);\n  function say(x){if(S.speak)speak(line+'. '+(x||''))}")
rep("u.lang='en-GB';u.rate=0.95;", "u.lang='en-GB';u.rate=S.rate;")

# --- service worker + optional download
rep("$('#menubtn').onclick=function(){$('#menu').classList.toggle('open')};",
    """$('#menubtn').onclick=function(){$('#menu').classList.toggle('open')};
/* Offline: the service worker (sw.js) keeps the shell and anything seen; this prefetches every person and story when asked. */
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(function(){});
function offStat(t){offlineState=t;var el=$('#offstat');if(el)el.textContent=t}
function offline(on){if(!on){offStat('');caches&&caches.keys().then(function(ks){ks.forEach(function(k){caches.delete(k)})});localStorage.removeItem('strand.offlineDone');return}
  if(!('serviceWorker' in navigator)){offStat('This browser cannot keep pages offline');return}
  if(localStorage.getItem('strand.offlineDone')){offStat('Ready. Works without a signal; pictures and Wikipedia text need one.');return}
  navigator.serviceWorker.ready.then(function(){var urls=Object.keys(D.people).map(function(i){return 'data/people/'+i+'.json'}).concat(Object.keys(D.places).map(function(i){return 'data/story/'+i+'.json'}));
    var done=0,fail=0,i=0,total=urls.length;function next(){if(!S.offline)return;if(i>=total){if(done+fail>=total){localStorage.setItem('strand.offlineDone','1');offStat('Ready ('+done+' files'+(fail?', '+fail+' failed':'')+'). Works without a signal; pictures and Wikipedia text need one.')}return}
      var u=urls[i++];fetch(u).then(function(r){if(!r.ok)fail++;else done++}).catch(function(){fail++}).then(function(){if((done+fail)%50===0)offStat('Downloading '+(done+fail)+' of '+total+'…');next()})}
    offStat('Downloading 0 of '+total+'…');for(var k=0;k<6;k++)next()})}
if(S.offline&&localStorage.getItem('strand.offlineDone'))offlineState='Ready. Works without a signal; pictures and Wikipedia text need one.';""")
# resume an unfinished download after load
rep("  if(localStorage.getItem('strand.loc')==='1')locate(false);",
    "  if(localStorage.getItem('strand.loc')==='1')locate(false);\n  if(S.offline&&!localStorage.getItem('strand.offlineDone'))offline(true);")

open(p, 'w', encoding='utf-8').write(s)
print('patched')
