const CACHE_NAME = 'pokotenote-data-viewer-v1';
// キャッシュするファイルのリスト
// service-worker.jsファイルからの相対パスで指定
const urlsToCache = [
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
  // アイコンやCSSなども必要に応じて追加
];

// インストールイベント
self.addEventListener('install', (event) => {
  console.log('Service Worker installed.');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        // 指定されたファイルをすべてキャッシュする
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.log('Cache installation failed:', error);
      })
  );
});

// フェッチイベント
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }

      return fetch(event.request).then((response) => {

        // 成功したらキャッシュ
        const copy = response.clone();

        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, copy);
        });

        return response;
      });
    })
  );
});

// アクティベートイベント
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // CACHE_NAME (v1) 以外の古いキャッシュ(v0など)を削除する
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
