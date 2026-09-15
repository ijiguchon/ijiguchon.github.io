/* 교인 앱(/gmc) 서비스워커 — 은퇴(kill switch).
   교인 앱은 교회 홈페이지(www.ijiguchon.org)로 합쳐졌습니다.
   이미 설치된 앱이 이 파일을 받으면: 옛 캐시(gmc-*) 삭제 → 스스로 등록 해제 → 열린 창을 새로고침(→ 홈으로 이동). */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (event) {
  event.waitUntil((async function () {
    try {
      var keys = await caches.keys();
      await Promise.all(keys.filter(function (k) { return k.indexOf('gmc-') === 0; }).map(function (k) { return caches.delete(k); }));
    } catch (_) {}
    try { await self.registration.unregister(); } catch (_) {}
    try {
      var clients = await self.clients.matchAll({ type: 'window' });
      clients.forEach(function (c) { if (c.navigate) c.navigate(c.url).catch(function () {}); });
    } catch (_) {}
  })());
});
