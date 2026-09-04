/* Offline shell. The point is a friend's house with bad wifi: the app itself
   should open even when the network does not.

   Network-first, so a push to Pages lands the moment the reader is online and
   there is no stale-cache dance. Cross-origin requests (BGG art, YouTube) are
   left entirely alone -- caching those would be a lot of storage for images the
   browser already caches, and an opaque-response trap. */
const C = "gn-v1";
const SHELL = ["./", "./index.html", "./manifest.json", "./favicon.svg",
               "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== C).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  if (new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then(r => { const copy = r.clone();
                   caches.open(C).then(c => c.put(e.request, copy));
                   return r; })
      .catch(() => caches.match(e.request).then(r => r || caches.match("./index.html"))));
});
