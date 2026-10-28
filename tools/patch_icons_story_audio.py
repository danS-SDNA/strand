"""One-off patch of site/index.html: place icons, story block, Listen buttons, spoken Lead-me.
Kept so the change is reviewable; safe to delete once committed."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, old[:70]
    s = s.replace(old, new, count)


# --- styles: icon squares, story block, listen button
rep('.actions .btn{margin:0;box-shadow:none}',
    '.actions .btn{margin:0;box-shadow:none}\n'
    '.ic{flex:none;width:44px;height:44px;border-radius:8px;background:#b08556;display:flex;align-items:center;justify-content:center}.ic svg{width:28px;height:28px;fill:none;stroke:#1a1410;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}\n'
    '.ic.sm{width:26px;height:26px;border-radius:6px;vertical-align:middle;display:inline-flex;margin-right:6px}.ic.sm svg{width:17px;height:17px;stroke-width:2}\n'
    '.story{margin:8px 0 4px;padding:12px 14px;border-left:3px solid var(--acc);background:var(--chip);border-radius:0 10px 10px 0;font-size:15.5px;line-height:1.5}\n'
    '.story .src{display:block;margin-top:6px;font-size:12px;color:var(--muted)}\n'
    '.btn.on{border-color:var(--acc);color:var(--acc)}')

# --- icon classifier + svg set, inserted before RELTEXT
rep("var RELTEXT=", r"""var ICONS={statue:'<path d="M9 21h6M10 21v-4h4v4M7 17h10M9 13l1-7h4l1 7M11 6V4h2v2"/>',
 memorial:'<path d="M5 21h14M8 21V9l4-5 4 5v12M12 10v7"/>',
 grave:'<path d="M6 21h12M8 21V9a4 4 0 0 1 8 0v12M10 12h4M12 10v6"/>',
 plaque:'<rect x="4" y="6" width="16" height="12" rx="1"/><path d="M8 10h8M8 13h6"/>',
 church:'<path d="M6 21V12l6-5 6 5v9M12 3v4M10 5h4M10 21v-5h4v5"/>',
 house:'<path d="M4 11l8-7 8 7M6 10v11h12V10M10 21v-6h4v6"/>',
 palace:'<path d="M4 21V9h3v3h3V8h4v4h3V9h3v12M10 21v-5h4v5M4 21h16"/>',
 theatre:'<path d="M4 6h16v12H4zM4 9h16M8 6v3M12 6v3M16 6v3M9 13h.01M15 13h.01M9.5 16c1.5 1 3.5 1 5 0"/>',
 museum:'<path d="M3 9l9-5 9 5M5 9v10M9 9v10M15 9v10M19 9v10M3 19h18M3 9h18"/>',
 pub:'<path d="M7 5h9v14H7zM16 9h3v6h-3M7 9h9"/>',
 hospital:'<path d="M5 21V5h14v16M5 21h14M12 8v6M9 11h6"/>',
 school:'<path d="M3 9l9-4 9 4-9 4-9-4zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5M21 9v5"/>',
 station:'<path d="M7 4h10v12H7zM7 9h10M9 13h.01M15 13h.01M8 16l-2 4M16 16l2 4M7 20h10"/>',
 bridge:'<path d="M2 15h20M4 15V9M20 15V9M4 9c4-5 12-5 16 0M8 15v-4M12 15v-5M16 15v-4"/>',
 park:'<path d="M12 21v-5M12 16l-5-6h3L7 6h4L12 2l1 4h4l-3 4h3z"/>',
 street:'<path d="M6 21l3-18M18 21l-3-18M12 5v3M12 11v3M12 17v3"/>',
 water:'<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/>',
 building:'<path d="M4 21V5h10v16M14 11h6v10M4 21h16M7 8h2M7 12h2M7 16h2M17 15h.01M17 18h.01"/>'};
var ICONRULES=[['grave',/cemetery|tomb|grave|mausoleum|crypt|catacomb/],['statue',/statue|bust|sculpture|relief|mural|obelisk|work of art|equestrian/],['water',/fountain|lake|pond|river|canal|dock|basin/],['plaque',/plaque/],['memorial',/memorial|monument|cenotaph|cross/],
 ['church',/church|chapel|cathedral|abbey|synagogue|mosque|temple|priory|minster/],['hospital',/hospital|infirmary|asylum|clinic|hospice/],['school',/school|college|university|academy|institute|education|polytechnic/],['station',/station|railway|underground|tube/],['bridge',/bridge/],
 ['theatre',/theat|cinema|opera|concert|music venue|nightclub|music hall|playhouse/],['museum',/museum|gallery|library|archive/],['pub',/\bpub\b|public house|inn\b|tavern|restaurant|hotel|club|shop|cafe|coffee/],['palace',/palace|castle|court|parliament|government|town hall|guildhall/],
 ['park',/park|garden|square|common|heath|green\b|wood/],['street',/street|road|lane|avenue|alley|mews|row\b|crescent|place\b|terrace/],['house',/house|home|residence|mansion|villa|apartment|flat|cottage|lodge/]];
function iconOf(pl){var t=(pl.t||[]).join(' | ').toLowerCase()+' | '+(pl.d||'').toLowerCase();for(var i=0;i<ICONRULES.length;i++)if(ICONRULES[i][1].test(t))return ICONRULES[i][0];return 'building'}
function icon(pl,sm){return '<span class="ic'+(sm?' sm':'')+'" title="'+esc((pl.t||[])[0]||'')+'"><svg viewBox="0 0 24 24">'+ICONS[iconOf(pl)]+'</svg></span>'}
var RELTEXT=""")

# --- nearby rows and search place rows get icons
rep("""return '<div class="row"><span class="who">'+link('l',x[1],p.l)+'<br><span class="dim">'+esc(topNames(x[1],2).join(', '))""",
    """return '<div class="row">'+icon(p)+'<span class="who">'+link('l',x[1],p.l)+'<br><span class="dim">'+esc(topNames(x[1],2).join(', '))""")
rep("""return '<div class="row"><span class="who">'+link('l',i,D.places[i].l)+'</span><span class="yrs">'+(byPlace[i]||[]).length""",
    """return '<div class="row">'+icon(D.places[i])+'<span class="who">'+link('l',i,D.places[i].l)+'</span><span class="yrs">'+(byPlace[i]||[]).length""")
# person page "In London" rows
rep("""return '<div class="row"><span class="who">'+link('l',l.pl,pl.l)+' <span class="rel">'+RELTEXT[l.r]""",
    """return '<div class="row">'+icon(pl)+'<span class="who">'+link('l',l.pl,pl.l)+' <span class="rel">'+RELTEXT[l.r]""")
# lead-me cards: icon beside the name
rep("""<b>'+esc(c.p.l)+'</b><div class="ppl">""", """<b>'+icon(c.p,1)+esc(c.p.l)+'</b><div class="ppl">""")

# --- place page: story block at top, Listen button
rep("""  content.innerHTML='<h1>'+esc(pl.l)+'</h1><p class="sub">'+esc(pl.d||pl.t.join(', '))+' · <a target="_blank" href="https://www.wikidata.org/wiki/'+id+'">wikidata</a></p>'+
   '<div class="actions"><button class="btn acc" data-act="lead">➜ Lead me on from here</button></div>'+""",
    """  content.innerHTML='<h1>'+icon(pl,1)+esc(pl.l)+'</h1><p class="sub">'+esc(pl.d||pl.t.join(', '))+' · <a target="_blank" href="https://www.wikidata.org/wiki/'+id+'">wikidata</a></p>'+
   '<div id="story"></div><div class="actions"><button class="btn acc" data-act="lead">➜ Lead me on from here</button><button class="btn" data-act="listen">▶ Listen</button></div>'+""")
rep("""   '<h2>Nearby</h2>'+nearby(pl.lat,pl.lon,8,id);
  content.scrollTop=0}""",
    """   '<h2>Nearby</h2>'+nearby(pl.lat,pl.lon,8,id);
  content.scrollTop=0;loadStory(id)}
/* Story: a short synthesis written per place at build time (tools/synthesise.py); spoken by the phone's own voice */
var storyIdx=null,storyText={};
function loadStory(id){if(!storyIdx){fetch('data/story/_index.json').then(function(r){return r.ok?r.json():{}}).then(function(x){storyIdx=x;loadStory(id)}).catch(function(){storyIdx={}});return}
  if(!storyIdx[id]||!(cur&&cur.id===id))return;
  fetch('data/story/'+id+'.json').then(function(r){return r.json()}).then(function(x){if(!(cur&&cur.id===id))return;storyText[id]=x.t;var el=$('#story');if(el)el.innerHTML='<div class="story">'+esc(x.t)+'<span class="src">Drawn from Wikipedia and Wikidata; details worth checking on the spot.</span></div>'})}
function placeSpeech(id){var pl=D.places[id];if(storyText[id])return storyText[id];var ppl=placePeople(id).slice(0,4);
  return pl.l+'. '+(pl.d?pl.d+'. ':'')+ppl.map(function(o){return o.p.l+', '+(o.p.d||'')+', '+o.rels.join(' and ')}).join('. ')+'.'}
var speaking=false;
function speak(text,btn){if(!window.speechSynthesis){alert('No speech on this device');return}
  if(speaking){speechSynthesis.cancel();speaking=false;if(btn)btn.classList.remove('on');return}
  var u=new SpeechSynthesisUtterance(text);u.lang='en-GB';u.rate=0.95;var v=speechSynthesis.getVoices().filter(function(v){return /en[-_]GB/i.test(v.lang)})[0];if(v)u.voice=v;
  u.onend=u.onerror=function(){speaking=false;if(btn)btn.classList.remove('on')};speaking=true;if(btn)btn.classList.add('on');speechSynthesis.cancel();speechSynthesis.speak(u)}
/* Heading: on a phone, Lead me can say "ahead" / "to your left" instead of compass points */
var heading=null;
function relDir(b){if(heading==null)return compass(b);var d=((b-heading)%360+360)%360;if(d<30||d>330)return 'straight ahead';if(d<75)return 'ahead to your right';if(d<120)return 'to your right';if(d<165)return 'behind you to the right';if(d<195)return 'behind you';if(d<240)return 'behind you to the left';if(d<285)return 'to your left';return 'ahead to your left'}
function onOrient(e){var h=e.webkitCompassHeading!=null?e.webkitCompassHeading:(e.absolute&&e.alpha!=null?360-e.alpha:null);if(h!=null)heading=h}
function startCompass(cb){if(window.DeviceOrientationEvent&&typeof DeviceOrientationEvent.requestPermission==='function'){DeviceOrientationEvent.requestPermission().then(function(s){if(s==='granted')window.addEventListener('deviceorientation',onOrient);setTimeout(cb,400)}).catch(cb)}
  else{window.addEventListener('deviceorientationabsolute',onOrient);window.addEventListener('deviceorientation',onOrient);setTimeout(cb,400)}}
var leadPicks=[];
function leadSpeech(){if(!leadPicks.length)return 'Nothing new within range.';return 'From '+origin().label+'. '+leadPicks.map(function(c){var names=topNames(c.id,3);return fmt(c.d).replace(' m',' metres').replace(' km',' kilometres')+' '+relDir(c.b)+': '+c.p.l+(names.length?', with '+names.join(', '):'')}).join('. ')+'.'}""")
# lead(): remember picks, add Listen
rep("""  content.innerHTML='<h1>Lead me</h1>""", """  leadPicks=picks;content.innerHTML='<h1>Lead me</h1>""")
rep("""'<div class="actions"><button class="btn" data-act="further">Further afield</button>""",
    """'<div class="actions"><button class="btn" data-act="listen-lead">▶ Listen</button><button class="btn" data-act="further">Further afield</button>""")
rep("""function act(a){if(a==='lead')lead();""",
    """function act(a,btn){if(a==='listen'){speak(placeSpeech(cur.id),btn)}else if(a==='listen-lead'){if(speaking){speak('',btn);return}startCompass(function(){speak(leadSpeech(),btn)})}else if(a==='lead')lead();""")
open(p, 'w', encoding='utf-8').write(s)
print('patched')
