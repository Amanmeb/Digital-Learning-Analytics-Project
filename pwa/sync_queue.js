// IndexedDB queue management for offline xAPI events
// Used by service_worker.js to store and sync xAPI statements
// when the device is offline or the school hotspot is not reachable

var DB_NAME = "camara_pwa_queue";
var DB_VERSION = 1;
var STORE_NAME = "xapi_events";

function openQueueDatabase() {
    // Opens or creates the IndexedDB database for the offline queue
    return new Promise(function (resolve, reject) {
        var request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = function (event) {
            var db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                var store = db.createObjectStore(STORE_NAME, {
                    keyPath: "id",
                    autoIncrement: true
                });
                store.createIndex("fingerprint", "fingerprint", { unique: true });
                store.createIndex("synced", "synced", { unique: false });
            }
        };

        request.onsuccess = function (event) {
            resolve(event.target.result);
        };

        request.onerror = function (event) {
            reject(event.target.error);
        };
    });
}

function calculateFingerprint(statement) {
    // Calculates a fingerprint matching the central formula
    // Formula: student_id|event_type|content_id|timestamp|school_id
    // Uses a simple string concatenation since this runs in browser
    // without access to a native SHA-256 library by default
    try {
        var context = statement.context || {};
        var extensions = context.extensions || {};
        var camaraExt = extensions["https://camara.org/xapi/context"] || {};

        var studentId = "";
        if (statement.actor && statement.actor.account) {
            studentId = statement.actor.account.name || "";
        }
        var eventType = "";
        if (statement.verb) {
            eventType = statement.verb.id || "";
        }
        var contentId = "";
        if (statement.object) {
            contentId = statement.object.id || "";
        }
        var timestamp = statement.timestamp || "";
        var schoolId = camaraExt.school_id || "";

        var raw = studentId + "|" + eventType + "|" + contentId + "|" +
            timestamp + "|" + schoolId;

        return raw;
    } catch (error) {
        return "";
    }
}

function addEvent(statement) {
    // Adds a new xAPI event to the offline queue
    // Returns a promise resolving to true if added, false if duplicate
    var fingerprint = calculateFingerprint(statement);

    return openQueueDatabase().then(function (db) {
        return new Promise(function (resolve, reject) {
            var transaction = db.transaction([STORE_NAME], "readwrite");
            var store = transaction.objectStore(STORE_NAME);
            var index = store.index("fingerprint");

            var checkRequest = index.get(fingerprint);

            checkRequest.onsuccess = function () {
                if (checkRequest.result) {
                    // Already exists -- duplicate, do not add again
                    resolve(false);
                    return;
                }

                var record = {
                    fingerprint: fingerprint,
                    statement: statement,
                    synced: 0,
                    created_at: new Date().toISOString()
                };

                var addRequest = store.add(record);

                addRequest.onsuccess = function () {
                    resolve(true);
                };

                addRequest.onerror = function () {
                    reject(addRequest.error);
                };
            };

            checkRequest.onerror = function () {
                reject(checkRequest.error);
            };
        });
    });
}

function getUnsynced() {
    // Returns all unsynced events from the queue
    return openQueueDatabase().then(function (db) {
        return new Promise(function (resolve, reject) {
            var transaction = db.transaction([STORE_NAME], "readonly");
            var store = transaction.objectStore(STORE_NAME);
            var request = store.getAll();

            request.onsuccess = function () {
                var allRecords = request.result || [];
                var unsynced = allRecords.filter(function (record) {
                    return record.synced === 0;
                });
                resolve(unsynced);
            };

            request.onerror = function () {
                reject(request.error);
            };
        });
    });
}

function markSynced(ids) {
    // Marks a list of record IDs as synced
    if (!ids || ids.length === 0) {
        return Promise.resolve();
    }

    return openQueueDatabase().then(function (db) {
        return new Promise(function (resolve, reject) {
            var transaction = db.transaction([STORE_NAME], "readwrite");
            var store = transaction.objectStore(STORE_NAME);
            var remaining = ids.length;

            ids.forEach(function (id) {
                var getRequest = store.get(id);

                getRequest.onsuccess = function () {
                    var record = getRequest.result;
                    if (record) {
                        record.synced = 1;
                        store.put(record);
                    }
                    remaining = remaining - 1;
                    if (remaining === 0) {
                        resolve();
                    }
                };

                getRequest.onerror = function () {
                    remaining = remaining - 1;
                    if (remaining === 0) {
                        resolve();
                    }
                };
            });
        });
    });
}

function getCount() {
    // Returns the count of unsynced events in the queue
    return getUnsynced().then(function (records) {
        return records.length;
    });
}

// Expose functions globally so service_worker.js can use them
self.CamaraSyncQueue = {
    addEvent: addEvent,
    getUnsynced: getUnsynced,
    markSynced: markSynced,
    getCount: getCount
};