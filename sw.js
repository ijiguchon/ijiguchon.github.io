/* ══════════════════════════════════════════════════════════
   시애틀지구촌교회 홈 (www.ijiguchon.org) — Service Worker
   · 페이지(HTML)      : network-first → 오프라인일 때만 캐시 (고친 내용이 바로 보이게)
   · 같은 출처 이미지  : 먼저 보여 주고 뒤에서 새로 받기(2026-09-29) — 새 VERSION 이면 캐시 전부 삭제
   · 폼 전송(POST)·외부 요청(Apps Script·Drive·YouTube 등) : 건드리지 않음
   · /gmc/ 는 교인 앱 자체 SW가 담당 → 건드리지 않음
   페이지는 network-first라 내용 수정 때 버전을 올릴 필요 없음.
   캐시 구조를 바꿀 때만 VERSION을 올리세요. (캐시 이름은 'home-' 으로 시작)
   ══════════════════════════════════════════════════════════ */
const VERSION = 'home-v20261002-025042';
const PAGE_CACHE = VERSION + '-pages';
const ASSET_CACHE = VERSION + '-assets';
const PRECACHE = ['/', '/manifest.json', '/favicon.ico', '/images/logo-mark.png', '/images/icon-192-em.png'];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(PAGE_CACHE);
    await Promise.allSettled(PRECACHE.map((u) => cache.add(new Request(u, { cache: 'reload' })).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    // 같은 출처의 교인 앱 캐시(gmc-*)는 지우지 않는다 — 내 것(home-*)의 옛 버전만 정리
    await Promise.all(keys.filter((k) => k.startsWith('home-') && !k.startsWith(VERSION)).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

async function networkFirst(request) {
  const cache = await caches.open(PAGE_CACHE);
  try {
    const fresh = await fetch(request, { cache: 'no-store' });
    if (fresh && fresh.ok) cache.put(request, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = (await cache.match(request)) || (await cache.match(request, { ignoreSearch: true }));
    if (cached) return cached;
    if (request.mode === 'navigate') {
      const home = await cache.match('/');
      if (home) return home;
    }
    throw err;
  }
}

async function cacheFirst(request, event) {
  // 사진: 먼저 보여 주고, 뒤에서 새로 받아 둔다(같은 이름으로 바꾼 사진도 다음 방문에 새것). 새 VERSION 이 켜지면 이 캐시는 통째로 지워진다.
  const cache = await caches.open(ASSET_CACHE);
  const cached = await cache.match(request);
  const refresh = fetch(request).then((fresh) => { if (fresh && fresh.ok) cache.put(request, fresh.clone()); return fresh; }).catch(() => null);
  if (event && event.waitUntil) event.waitUntil(refresh);
  return cached || (await refresh) || Response.error();
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  let url;
  try { url = new URL(request.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/gmc/')) return;
  if (request.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('.html')) {
    event.respondWith(networkFirst(request));
    return;
  }
  if (/\.(png|jpe?g|webp|gif|svg|ico)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request, event));
  }
});
