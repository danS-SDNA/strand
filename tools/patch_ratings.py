"""One-off patch of site/index.html: ratings (what a place is good for, an optional overall star rating,
copper / silver / gold by number of ratings), stored by worker/ratings."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
p = ROOT / "site/index.html"
s = p.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep(".zpin{", ".rsum{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:2px 0 8px}.rstar{font-weight:bold}.tier{font-size:11px;font-weight:bold;letter-spacing:.05em;padding:2px 7px;border-radius:999px;color:#1d1a16}\n"
    ".tier.copper{background:#d39a6a}.tier.silver{background:#cfd4da}.tier.gold{background:#f3c96b}.rtag{font-size:13px;padding:3px 9px;border-radius:999px;background:var(--chip);border:1px solid var(--line)}\n"
    ".ratebox{border:1px dashed var(--line);border-radius:12px;padding:10px 12px;margin:10px 0}.stars span{font-size:30px;cursor:pointer;color:var(--line);padding:0 2px}.stars span.on{color:#e0a530}\n"
    ".rmini{font-size:12px;color:#b07a10;font-weight:bold;white-space:nowrap}\n.zpin{")

rep("FOOD=[], hasVid={},", "FOOD=[], RATINGS={}, myRates={}, rateTimer=null, hasVid={},")
rep("var AI_URL=", "var RATE_URL='https://strand-ratings.rackdigaback.workers.dev';try{myRates=JSON.parse(localStorage.getItem('strand.rated')||'{}')}catch(e){}\nvar AI_URL=")

# summary loads with the zones (non-blocking for routing)
rep("return fetch('data/zones.json')", "loadRatings();return fetch('data/zones.json')")

# place page: summary under the title, rate box after the actions
rep("""  content.innerHTML='<h1>'+icon(pl,1)+esc(pl.l)+'</h1><p class="sub">'+esc(pl.d||pl.t.join(', '))+' · <a target="_blank" href="https://www.wikidata.org/wiki/'+id+'">wikidata</a></p>'+""",
    """  content.innerHTML='<h1>'+icon(pl,1)+esc(pl.l)+'</h1><p class="sub">'+esc(pl.d||pl.t.join(', '))+' · <a target="_blank" href="https://www.wikidata.org/wiki/'+id+'">wikidata</a></p><div id="rsum">'+ratingSummary(id)+'</div>'+""")
rep("'<h2>'+ppl.length+' people</h2>'", "'<div id=\"ratebox\">'+rateBox(id)+'</div><h2>'+ppl.length+' people</h2>'")

# nearby rows: a small star for places people rate highly
rep("""return '<div class="row">'+icon(p)+'<span class="who">'+link('l',x[1],p.l)+'<br><span class="dim">'""",
    """return '<div class="row">'+icon(p)+'<span class="who">'+link('l',x[1],p.l)+ratingMini(x[1])+'<br><span class="dim">'""")

# planner: well-rated places get a gentle lift once there are enough ratings to trust
rep("  return interest*fame*dull*film*(pl.vid||(storyIdx&&storyIdx[id])?1:0.5)}",
    "  var rr=ratingOf(id),liked=rr&&rr.ns>=5?Math.min(1.3,Math.max(0.8,1+(rr.bayes-3.8)*0.25)):1;\n"
    "  return interest*fame*dull*film*liked*(pl.vid||(storyIdx&&storyIdx[id])?1:0.5)}")

# actions
rep("function act(a,btn){",
    "function act(a,btn){if(a.slice(0,5)==='rate:'){rateAct(a.slice(5));return}\n  ")

# the ratings functions, before the zones block
rep("/* Zones: a place that holds many stops", r"""/* Ratings (worker/ratings): what a place is good for, plus an optional overall "worth the stop?" star rating.
   Strengths are shown, never weaknesses: a low average shows as "rated by n" rather than as low stars. The average
   starts near the overall norm and moves as ratings arrive (5 imagined ratings at 3.8), so one 5-star cannot beat
   two hundred at 4.7. Tiers by count: copper 1-10, silver 11-50, gold 51+. Only people who were there rate: on the
   spot by GPS, or after ticking "I've been here". One rating per phone per place; an empty rating withdraws it. */
var RTAGS=[['history','History'],['culture','Art & culture'],['wow','Worth a look'],['quirky','Quirky'],['kids','Good with kids'],['peaceful','Peaceful']];
function loadRatings(){fetch(RATE_URL+'/summary').then(function(r){return r.ok?r.json():{places:{}}}).then(function(j){RATINGS=j.places||{};if(cur&&cur.kind==='l'){var el=$('#rsum');if(el)el.innerHTML=ratingSummary(cur.id)}}).catch(function(){})}
function ratingOf(id){var r=RATINGS[id];if(!r||!r.n)return null;var C=5,M=3.8;return {n:r.n,ns:r.ns,avg:r.ns?r.s/r.ns:0,bayes:(C*M+r.s)/(C+r.ns),t:r.t||{},tier:r.n>=51?'gold':r.n>=11?'silver':'copper'}}
function ratingSummary(id){var r=ratingOf(id);if(!r)return '';var h='';
  if(r.ns>=3&&r.bayes>=3.5)h+='<span class="rstar">★ '+r.bayes.toFixed(1)+'</span>';
  h+='<span class="tier '+r.tier+'">'+r.tier.toUpperCase()+'</span><span class="dim">'+r.n+' rating'+(r.n>1?'s':'')+'</span>';
  RTAGS.map(function(t){return [t,(r.t[t[0]]||0)]}).filter(function(x){return x[1]>=1&&x[1]/r.n>=0.3}).sort(function(a,b){return b[1]-a[1]}).slice(0,3).forEach(function(x){
    h+='<span class="rtag">'+(r.n>=5?'Loved for '+x[0][1].toLowerCase()+' · '+Math.round(100*x[1]/r.n)+'%':x[0][1]+' · '+x[1])+'</span>'});
  return '<div class="rsum">'+h+'</div>'}
function ratingMini(id){var r=ratingOf(id);return r&&r.ns>=5&&r.bayes>=4.2&&r.tier!=='copper'?' <span class="rmini">★'+r.bayes.toFixed(1)+'</span>':''}
function nearHere(id){var pl=D.places[id];return myPos&&pl&&dist(myPos[0],myPos[1],pl.lat,pl.lon)<0.15}
function rateBox(id){if(!/^(Q\d+|z:)/.test(id))return '';var mine=myRates[id];
  if(!mine&&!nearHere(id)&&!(rateBox.open===id))return '<div class="ratebox"><span class="dim">Been here?</span> <button class="btn" data-act="rate:open">Rate it</button></div>';
  var m=mine||{s:null,t:[]};
  return '<div class="ratebox"><b>Worth the stop?</b><div class="stars">'+[1,2,3,4,5].map(function(k){return '<span class="'+(m.s&&k<=m.s?'on':'')+'" data-act="rate:s:'+k+'">★</span>'}).join('')+'</div>'+
   '<div class="lab">Good for (tap any)</div><div class="chips">'+RTAGS.map(function(t){return '<span class="chip'+(m.t.indexOf(t[0])>=0?' on':'')+'" data-act="rate:t:'+t[0]+'">'+t[1]+'</span>'}).join('')+'</div>'+
   '<div class="stat" id="ratestat" style="margin-top:6px">'+(mine?'Saved. Thank you.':'Only for places you have visited.')+(mine?' <span class="lnk" data-act="rate:clear">Remove my rating</span>':'')+'</div></div>'}
function deviceId(){var d=localStorage.getItem('strand.dev');if(!d){d=Math.random().toString(36).slice(2)+Date.now().toString(36);localStorage.setItem('strand.dev',d)}return d}
function rateAct(a){var id=cur&&cur.id;if(!id)return;if(a==='open'){rateBox.open=id;$('#ratebox').innerHTML=rateBox(id);return}
  var m=myRates[id]||{s:null,t:[]};
  if(a.slice(0,2)==='s:'){var k=+a.slice(2);m.s=m.s===k?null:k}else if(a.slice(0,2)==='t:'){var t=a.slice(2),i=m.t.indexOf(t);if(i>=0)m.t.splice(i,1);else m.t.push(t)}else if(a==='clear'){m={s:null,t:[]}}
  var empty=!m.s&&!m.t.length;if(empty)delete myRates[id];else myRates[id]=m;localStorage.setItem('strand.rated',JSON.stringify(myRates));
  if(empty)rateBox.open=id;$('#ratebox').innerHTML=rateBox(id);
  clearTimeout(rateTimer);rateTimer=setTimeout(function(){var st=$('#ratestat');if(st)st.textContent='Saving…';
    fetch(RATE_URL+'/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({device:deviceId(),place:id,stars:m.s,tags:m.t})}).then(function(r){return r.json().then(function(j){return [r.status,j]})}).then(function(x){
      var st=$('#ratestat');if(st)st.textContent=x[0]===200?(empty?'Removed.':'Saved. Thank you.'):(x[1].error||'Could not save just now');loadRatings()}).catch(function(){var st=$('#ratestat');if(st)st.textContent='Offline: saved on this phone, will need another tap later'})},700)}
/* Zones: a place that holds many stops""")
p.write_text(s, encoding="utf-8")
print("patched")
