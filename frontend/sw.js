/* Cache the small app shell; cache vendors and API responses opportunistically. */
const CACHE_NAME = "aura-flood-v18";
const APP_SHELL = [
  "/",
  "/index.html",
  "/alerts.html",
  "/styles.css",
  "/app.js",
  "/manifest.json",
];
const VENDOR_ASSETS = [
  "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
];

async function markOfflineResponse(response) {
  const type = response.headers.get("content-type") || "";
  if (!type.includes("application/json")) return response;
  const data = await response.json();
  data.offline_cache = true;
  if (data.data_status && typeof data.data_status === "object") {
    if (data.data_status.forecast !== "SIMULATED") data.data_status.forecast = "CACHED OFFLINE";
  } else if (data.data_status && !String(data.data_status).includes("SIMULATED")) {
    data.data_status = `CACHED OFFLINE · originally ${data.data_status}`;
  }
  if (typeof data.forecast_source === "string" && !data.forecast_source.includes("SIMULATED")) {
    data.forecast_source = `CACHED OFFLINE · originally ${data.forecast_source}`;
  }
  if (data.rainfall && data.rainfall.source && !data.rainfall.simulated) {
    data.rainfall.source = `CACHED OFFLINE · originally ${data.rainfall.source}`;
  }
  if (data.rainfall?.imd_observation?.available) data.rainfall.imd_observation.offline_cache = true;
  if (data.source && !data.simulated && data.data_status !== "SIMULATED") {
    data.source = `CACHED OFFLINE · originally ${data.source}`;
  }
  if (data.imd_observation?.available) data.imd_observation.offline_cache = true;
  if (data.historical_context) {
    data.historical_context.current_rain_status = "unavailable";
    data.historical_context.rain_indicated_by_live_model = false;
    data.historical_context.rain_status = "Cached offline weather; fresh live rain check is not available";
    data.historical_context.warning = false;
    data.historical_context.warning_text = null;
  }
  return new Response(JSON.stringify(data), {
    status: response.status,
    headers: { "Content-Type": "application/json", "X-Aura-Offline-Cache": "true" },
  });
}

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(async cache => {
        await cache.addAll(APP_SHELL);
        await Promise.all(VENDOR_ASSETS.map(async asset => {
          try {
            const response = await fetch(asset);
            if (response.ok || response.type === "opaque") await cache.put(asset, response);
          } catch (error) {
            console.warn(`Optional vendor asset was not cached: ${asset}`, error);
          }
        }));
      })
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key.startsWith("aura-flood-") && key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin === self.location.origin && request.mode === "navigate") {
    event.respondWith(
      fetch(request).then(response => {
        if (!response.ok) return response;
        return caches.open(CACHE_NAME)
          .then(cache => cache.put(request, response.clone()))
          .then(() => response);
      }).catch(async () => {
        const cachedPage = await caches.match(request);
        if (cachedPage) return cachedPage;
        return caches.match("/index.html");
      }),
    );
    return;
  }
  if (url.origin === self.location.origin && url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(request).then(response => {
        if (response.ok) {
          return caches.open(CACHE_NAME)
            .then(cache => cache.put(request, response.clone()))
            .then(() => response);
        }
        return response;
      }).catch(async error => {
        const cached = await caches.match(request);
        if (!cached) throw error;
        return markOfflineResponse(cached);
      }),
    );
    return;
  }
  if (url.origin !== self.location.origin) {
    event.respondWith(
      caches.match(request).then(cached => {
        const update = fetch(request).then(response => {
          if (response.ok || response.type === "opaque") {
            return caches.open(CACHE_NAME)
              .then(cache => cache.put(request, response.clone()))
              .then(() => response);
          }
          return response;
        });
        return cached || update.catch(async error => {
          const stale = await caches.match(request);
          if (!stale) throw error;
          return markOfflineResponse(stale);
        });
      }),
    );
    return;
  }
  event.respondWith(
    fetch(request).then(response => {
      if (!response.ok) return response;
      return caches.open(CACHE_NAME)
        .then(cache => cache.put(request, response.clone()))
        .then(() => response);
    }).catch(async error => {
      const cached = await caches.match(request);
      if (!cached) throw error;
      return cached;
    }),
  );
});
