/* Strand service worker: the app shell and data are cached so the site opens without a network.
   Shell + indexes: network first, cache fallback (so updates arrive when online).
   People, stories, vendor libraries: cache first (immutable by id).
   Map tiles and Wikimedia images/summaries: cache as seen, capped. Nothing is prefetched here;
   the page drives the optional "keep on this phone" download through ordinary fetches. */
var VERSION = 'strand-v2';
var SHELL = ['./', 'index.html', 'vendor/leaflet/leaflet.min.css', 'vendor/leaflet/leaflet.min.js',
  'vendor/leaflet/images/marker-icon.png', 'vendor/leaflet/images/marker-icon-2x.png', 'vendor/leaflet/images/marker-shadow.png',
  'vendor/markercluster/leaflet.markercluster.js', 'vendor/markercluster/MarkerCluster.css', 'vendor/markercluster/MarkerCluster.Default.css',
  'data/index.json', 'data/tours.json', 'data/story/_index.json'];
var NETWORK_FIRST = /(\/|index\.html|data\/index\.json|data\/tours\.json|data\/story\/_index\.json)$/;
var TILE_CAP = 4000, MEDIA_CAP = 1500;

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== VERSION && k !== 'tiles' && k !== 'media'; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

function trim(name, cap) {
  return caches.open(name).then(function (c) {
    return c.keys().then(function (ks) { if (ks.length <= cap) return; return Promise.all(ks.slice(0, ks.length - cap).map(function (k) { return c.delete(k); })); });
  });
}
var trimCount = 0;

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin === location.origin) {
    if (NETWORK_FIRST.test(url.pathname)) {
      e.respondWith(fetch(req).then(function (r) { if (r.ok) { var copy = r.clone(); caches.open(VERSION).then(function (c) { c.put(req, copy); }); } return r; })
        .catch(function () { return caches.match(req, { ignoreSearch: true }); }));
    } else {
      e.respondWith(caches.match(req).then(function (hit) {
        return hit || fetch(req).then(function (r) { if (r.ok) { var copy = r.clone(); caches.open(VERSION).then(function (c) { c.put(req, copy); }); } return r; });
      }));
    }
    return;
  }
  var bucket = /tile\.openstreetmap\.org$/.test(url.host) ? 'tiles' : /wikimedia\.org$|wikipedia\.org$/.test(url.host) ? 'media' : null;
  if (!bucket) return;
  e.respondWith(caches.open(bucket).then(function (c) {
    return c.match(req).then(function (hit) {
      var net = fetch(req).then(function (r) {
        if (r.ok || r.type === 'opaque') { c.put(req, r.clone()); if (++trimCount % 200 === 0) trim(bucket, bucket === 'tiles' ? TILE_CAP : MEDIA_CAP); }
        return r;
      });
      return hit || net;
    });
  }));
});
