"""One-off patch of site/index.html: PWA head tags, manifest link, install prompt in the menu."""
p = 'site/index.html'
s = open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep('<title>Strand</title>',
    '<title>Strand</title>\n<meta name="theme-color" content="#8a2f1d">\n<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n<meta name="apple-mobile-web-app-title" content="Strand">\n'
    '<link rel="manifest" href="manifest.webmanifest">\n<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n<link rel="icon" href="icons/icon.svg" type="image/svg+xml">')

# state
rep("alertEx={}, offlineState='';", "alertEx={}, offlineState='', deferredInstall=null;")

# menu: install row at the top when not already installed
rep("""function renderMenu(){$('#menu').innerHTML='<div class="sw'+(walkOn?' on':'')+'" data-act="walk">""",
    """function standalone(){return window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true}
function installRow(){if(standalone())return '';if(deferredInstall)return '<div class="actions" style="margin-bottom:10px"><button class="btn acc" data-act="install">⬇ Install Strand</button></div>';
  if(/iPhone|iPad|iPod/.test(navigator.userAgent))return '<div class="stat" style="margin:0 0 10px">To install: Share ⎙ → Add to Home Screen. It then opens full-screen and keeps its data.</div>';return ''}
function renderMenu(){$('#menu').innerHTML=installRow()+'<div class="sw'+(walkOn?' on':'')+'" data-act="walk">""")

# actions
rep("if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}",
    "if(a==='walk'){toggleWalk();return}if(a==='locate'){locate(true);return}\n  if(a==='install'){if(deferredInstall){deferredInstall.prompt();deferredInstall.userChoice.then(function(){deferredInstall=null;renderMenu()})}return}")

# events: Chrome/Android/desktop offer an install prompt; defer it to the menu rather than the browser's own bar
rep("if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(function(){});",
    "if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(function(){});\n"
    "window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();deferredInstall=e;if(D)renderMenu()});\n"
    "window.addEventListener('appinstalled',function(){deferredInstall=null;if(D)renderMenu()});")
open(p, 'w', encoding='utf-8').write(s)
print('patched')
