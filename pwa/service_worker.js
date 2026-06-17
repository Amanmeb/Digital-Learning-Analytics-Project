// Service Worker for Camara Learning PWA
// Caches Moodle pages for offline access
// Intercepts xAPI requests and stores them in IndexedDB when offline
// Syncs queued events to the school server when connection is detected
// Works on Android Chrome and Chromebook

importScripts("/pwa/sync_queue.js");

var CACHE_NAME = "camara-cache-v1";
var XAPI_PATH_PATTERN = "/xapi/statements";
var SYNC_INTERVAL_MS = 60000;

var URLS_TO_CACHE = [
    "/",
    "/pwa/offline.html",
    "/pwa/manifest.json"
];

// ------------------------------------------------------------
// Install -- cache the offline fallback page and core assets
// ------------------------------------------------------------

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(URLS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// ------------------------------------------------------------
// Activate -- clean up old cache versions
// ------------------------------------------------------------

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys().then(function (cacheNames) {
            return Promise.all(
                cacheNames.map(function (name) {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                    return null;
                })
            );
        })
    );
    self.clients.claim();
});

// ------------------------------------------------------------
// Fetch -- intercept requests
// xAPI requests are queued for sync, not sent directly when offline
// Other requests use cache-first strategy with network fallback
// ------------------------------------------------------------

self.addEventListener("fetch", function (event) {
    var url = event.request.url;

    // Check if this is an xAPI statements request
    // Matches by path pattern regardless of host
    // This handles hotspot, LAN, and any future LRS endpoint
    if (url.indexOf(XAPI_PATH_PATTERN) !== -1 &&
        event.request.method === "POST") {
        event.respondWith(handleXapiRequest(event.request));
        return;
    }

    // For navigation requests use network-first with offline fallback
    if (event.request.mode === "navigate") {
        event.respondWith(
            fetch(event.request).catch(function () {
                return caches.match("/pwa/offline.html");
            })
        );
        return;
    }

    // For all other requests use cache-first with network fallback
    event.respondWith(
        caches.match(event.request).then(function (cachedResponse) {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(event.request).then(function (networkResponse) {
                // Cache successful GET responses for future offline use
                if (event.request.method === "GET" &&
                    networkResponse.status === 200) {
                    var responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(function (cache) {
                        cache.put(event.request, responseClone);
                    });
                }
                return networkResponse;
            }).catch(function () {
                return caches.match("/pwa/offline.html");
            });
        })
    );
});

// ------------------------------------------------------------
// Handle xAPI statement requests
// Tries direct send first, queues locally if it fails
// This supports the online-and-offline scenarios automatically
// ------------------------------------------------------------

function handleXapiRequest(request) {
    var requestClone = request.clone();

    return fetch(request).then(function (response) {
        // Network request succeeded -- statement sent directly
        if (response.ok) {
            return response;
        }
        // Network responded but with an error -- queue it as backup
        return queueRequestBody(requestClone).then(function () {
            return new Response(
                JSON.stringify({ queued: true, reason: "server_error" }),
                { status: 200, headers: { "Content-Type": "application/json" } }
            );
        });
    }).catch(function () {
        // Network request failed entirely -- queue for later sync
        return queueRequestBody(requestClone).then(function () {
            return new Response(
                JSON.stringify({ queued: true, reason: "offline" }),
                { status: 200, headers: { "Content-Type": "application/json" } }
            );
        });
    });
}

function queueRequestBody(request) {
    // Parses the request body and adds each statement to the queue
    return request.json().then(function (body) {
        var statements = [];
        if (Array.isArray(body)) {
            statements = body;
        } else {
            statements = [body];
        }

        var addPromises = statements.map(function (statement) {
            return self.CamaraSyncQueue.addEvent(statement);
        });

        return Promise.all(addPromises);
    }).catch(function () {
        // Body could not be parsed -- nothing to queue
        return Promise.resolve();
    });
}

// ------------------------------------------------------------
// Background sync -- attempts to upload queued events
// Triggered by periodic timer and by sync event when supported
// ------------------------------------------------------------

function getSchoolServerUrl() {
    // Determines the school server URL based on current page origin
    // This works correctly whether on hotspot, LAN, or dev machine
    return self.location.origin;
}

function attemptSync() {
    return self.CamaraSyncQueue.getUnsynced().then(function (records) {
        if (records.length === 0) {
            return;
        }

        var serverUrl = getSchoolServerUrl();
        var statements = records.map(function (record) {
            return record.statement;
        });

        return fetch(serverUrl + XAPI_PATH_PATTERN, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(statements)
        }).then(function (response) {
            if (response.ok) {
                var ids = records.map(function (record) {
                    return record.id;
                });
                return self.CamaraSyncQueue.markSynced(ids);
            }
        }).catch(function () {
            // Sync failed -- will retry on next interval
            return Promise.resolve();
        });
    });
}

// Register periodic sync attempt using a simple interval
// Background Sync API requires a sync event registration from the page
// This interval acts as a reliable fallback on all browsers
setInterval(function () {
    attemptSync();
}, SYNC_INTERVAL_MS);

// Listen for the Background Sync API event when supported
self.addEventListener("sync", function (event) {
    if (event.tag === "camara-xapi-sync") {
        event.waitUntil(attemptSync());
    }
});

// Listen for manual sync trigger from the page
self.addEventListener("message", function (event) {
    if (event.data && event.data.type === "SYNC_NOW") {
        attemptSync();
    }
});