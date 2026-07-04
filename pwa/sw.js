const CACHE = "seacut-pwa-v3";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (u.origin === location.origin) {
    // 앱 셸: 캐시 우선(오프라인 강변에서도 열림)
    e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
  }
  // 지도 타일·leaflet 등 외부 리소스는 기본 네트워크 처리
});
