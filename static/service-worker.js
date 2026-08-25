const CACHE_NAME = "careil-shell-v39";
const SHELL = [
  "/static/modern-clinic.css",
  "/static/modern-clinic.js",
  "/static/img/therapy-hands-logo.png",
  "/static/img/app-icon-192.png",
  "/static/favicon.ico"
];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
  )));
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;
  if (event.request.mode === "navigate") return;
  const requestUrl = new URL(event.request.url);
  if (requestUrl.pathname.endsWith('.css') || requestUrl.pathname.endsWith('.js')) {
    event.respondWith(fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }).catch(() => caches.match(event.request)));
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
