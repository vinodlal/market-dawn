/* Bank Nifty Predictor service worker.
 * cache-first for static assets; network-first for the JSON data feeds so the
 * app always tries fresh numbers, falling back to cache when offline.
 */
const CACHE = "bn-predictor-v2";
const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./app.js",
  "./manifest.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

// Network-first (fall back to cache offline) for the data feeds AND the app
// code/markup, so UI updates and fresh data land immediately when online.
// Only the rarely-changing icons/manifest stay cache-first.
const NETWORK_FIRST = [
  "/data/latest.json", "/data/backtest_log.json",
  "/index.html", "/app.js", "/docs/", "/docs/index.html", "/docs/app.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isNetworkFirst(url) {
  return NETWORK_FIRST.some((p) => url.pathname.endsWith(p) || url.pathname.includes(p.replace(/^\//, "")));
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  if (isNetworkFirst(url)) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // cache-first for everything else
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    }).catch(() => cached))
  );
});
