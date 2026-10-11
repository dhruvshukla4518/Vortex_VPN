/**
 * VORTEX VPN - Service Worker for PWA (Progressive Web App)
 * Enables offline shell caching and home-screen installation on mobile & desktop devices.
 */

const CACHE_NAME = "vortex-vpn-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/css/variables.css",
  "/css/base.css",
  "/css/layout.css",
  "/css/components.css",
  "/css/animations.css",
  "/js/state.js",
  "/js/api.js",
  "/js/vortex.js",
  "/js/map.js",
  "/js/charts.js",
  "/js/app.js",
  "/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {
        // Fallback gracefully if some asset is dynamic
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Let API requests bypass the cache
  if (event.request.url.includes("/api/")) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request).catch(() => {
        // Return offline page or index if available
        if (event.request.mode === "navigate") {
          return caches.match("/index.html");
        }
      });
    })
  );
});
