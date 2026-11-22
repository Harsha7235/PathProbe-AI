// ============================================================

// PATHPROBE AI

// Cisco Packet Tracer 9.x

//

// One-time topology collection

// UUID-based endpoint resolution

// WebView-side delivery retry

// No repeated topology scans

// ============================================================

var pathprobeWebView = null;

var pathprobeSnapshot = null;


// ============================================================

// MAIN

// ============================================================

function main() {

    try {

        dprint("PATHPROBE AI starting...");

        pathprobeWebView = webViewManager.createWebView(

            "PATHPROBE AI",

            "this-sm:Interface0.htm",

            430,

            700

        );

        try {

            pathprobeWebView.setDockWidgetWindowTitle(

                "PATHPROBE AI"

            );

        } catch (e) {}

        try {

            pathprobeWebView.setPreferredSize(430, 700);

        } catch (e) {}

        pathprobeWebView.dockToMainViewArea();

        pathprobeWebView.show();

        dprint("PATHPROBE AI is running.");

        dprint("Collecting topology once...");

        pathprobeSnapshot = collectNetworkStateOnce();

        dprint(

            "[PATHPROBE] API devices: " +

            pathprobeSnapshot.rawDeviceCount

        );

        dprint(

            "[PATHPROBE] Collected devices: " +

            pathprobeSnapshot.deviceCount

        );

        dprint(

            "[PATHPROBE] API links: " +

            pathprobeSnapshot.rawLinkCount

        );

        dprint(

            "[PATHPROBE] Collected links: " +

            pathprobeSnapshot.linkCount

        );

        dprint(

            "[PATHPROBE] Unresolved endpoints: " +

            pathprobeSnapshot.unresolvedEndpointCount

        );

        dprint(

            "[PATHPROBE] Collection errors: " +

            pathprobeSnapshot.collectionErrors.length

        );

        // Send this snapshot to the WebView.

        // The retry loop executes INSIDE the WebView.

        sendSnapshotToWebView(pathprobeSnapshot);

        dprint("PATHPROBE AI snapshot prepared.");

    } catch (error) {

        dprint(

            "PATHPROBE AI START ERROR: " +

            String(error)

        );

    }

}


// ============================================================

// SAFE API HELPERS

// ============================================================

function safeCount(fn) {

    try {

        var n = Number(fn());

        if (!isFinite(n) || n < 0) {

            return 0;

        }

        return Math.floor(n);

    } catch (e) {

        return 0;

    }

}

function safeDeviceName(device) {

    try {

        return String(device.getName());

    } catch (e) {

        return "Unknown device";

    }

}

function safeDeviceModel(device) {

    try {

        return String(device.getModel());

    } catch (e) {

        return "Unknown model";

    }

}

function safeDeviceUuid(device) {

    try {

        var value = device.getObjectUuid();

        if (value === null || value === undefined) {

            return null;

        }

        return String(value);

    } catch (e) {

        return null;

    }

}

function safePortName(port) {

    try {

        return String(port.getName());

    } catch (e) {

        return "Unknown port";

    }

}

function safePortUuid(port) {

    try {

        var value = port.getObjectUuid();

        if (value === null || value === undefined) {

            return null;

        }

        return String(value);

    } catch (e) {

        return null;

    }

}

function safePortState(port) {

    try {

        return !!port.isPortUp();

    } catch (e) {

        return null;

    }

}

function safeConnectionType(link) {

    try {

        return String(link.getConnectionType());

    } catch (e) {

        return "Unknown";

    }

}


// ============================================================

// ONE-TIME NETWORK COLLECTION

// ============================================================

function collectNetworkStateOnce() {

    var network = ipc.network();

    var rawDeviceCount = safeCount(function () {

        return network.getDeviceCount();

    });

    var rawLinkCount = safeCount(function () {

        return network.getLinkCount();

    });

    var state = {

        collectionTimestamp: new Date().toISOString(),

        rawDeviceCount: rawDeviceCount,

        rawLinkCount: rawLinkCount,

        deviceCount: 0,

        linkCount: 0,

        unresolvedEndpointCount: 0,

        faultCount: 0,

        devices: [],

        links: [],

        collectionErrors: [],

        metricsAvailability: {

            delay_ms: null,

            jitter_ms: null,

            packet_loss_pct: null,

            bandwidth_mbps: null,

            throughput_mbps: null,

            utilization_pct: null,

            reliability_pct: null,

            security_risk: null,

            queue_congestion: null,

            trust_score: null

        },

        diagnosis: {

            status: "UNKNOWN",

            title: "NETWORK STATE UNKNOWN",

            message: "Waiting for network evidence.",

            confidence: "UNKNOWN",

            evidence: [],

            affectedLinks: [],

            healthyLinks: []

        }

    };

    var portRecords = [];

    var portsByUuid = {};

    var devicesByUuid = {};

    // --------------------------------------------------------

    // PASS 1: INVENTORY ALL DEVICES AND PORTS

    // --------------------------------------------------------

    for (var i = 0; i < rawDeviceCount; i++) {

        try {

            var device = network.getDeviceAt(i);

            if (device == null) {

                state.collectionErrors.push(

                    "Device index " + i + " returned null."

                );

                continue;

            }

            var deviceName = safeDeviceName(device);

            var deviceModel = safeDeviceModel(device);

            var deviceUuid = safeDeviceUuid(device);

            var deviceInfo = {

                id: i,

                uuid: deviceUuid,

                name: deviceName,

                model: deviceModel,

                ports: []

            };

            var portCount = safeCount(

                (function (d) {

                    return function () {

                        return d.getPortCount();

                    };

                })(device)

            );

            for (var p = 0; p < portCount; p++) {

                try {

                    var port = device.getPortAt(p);

                    if (port == null) {

                        state.collectionErrors.push(

                            "Null port on " + deviceName +

                            " at index " + p

                        );

                        continue;

                    }

                    var portName = safePortName(port);

                    var portUuid = safePortUuid(port);

                    var portUp = safePortState(port);

                    var connected = false;

                    try {

                        connected = port.getLink() != null;

                    } catch (eLink) {}

                    var portInfo = {

                        name: portName,

                        uuid: portUuid,

                        connected: connected,

                        up: portUp

                    };

                    deviceInfo.ports.push(portInfo);

                    var record = {

                        ref: port,

                        uuid: portUuid,

                        deviceUuid: deviceUuid,

                        deviceName: deviceName,

                        portName: portName,

                        up: portUp

                    };

                    portRecords.push(record);

                    if (portUuid !== null) {

                        portsByUuid[portUuid] = record;

                    }

                } catch (portError) {

                    state.collectionErrors.push(

                        "Port read failed on " +

                        deviceName + ": " +

                        String(portError)

                    );

                }

            }

            state.devices.push(deviceInfo);

            if (deviceUuid !== null) {

                devicesByUuid[deviceUuid] = deviceInfo;

            }

        } catch (deviceError) {

            state.collectionErrors.push(

                "Device read failed at index " +

                i + ": " + String(deviceError)

            );

        }

    }

    // --------------------------------------------------------

    // PASS 2: INVENTORY ALL LINKS

    // --------------------------------------------------------

    for (var l = 0; l < rawLinkCount; l++) {

        try {

            var link = network.getLinkAt(l);

            if (link == null) {

                state.collectionErrors.push(

                    "Link index " + l + " returned null."

                );

                continue;

            }

            var port1 = null;

            var port2 = null;

            try {

                port1 = link.getPort1();

                port2 = link.getPort2();

            } catch (endpointError) {

                state.collectionErrors.push(

                    "Endpoint read failed for link " +

                    l + ": " + String(endpointError)

                );

            }

            var endpoint1 = resolveEndpoint(

                port1,

                portRecords,

                portsByUuid

            );

            var endpoint2 = resolveEndpoint(

                port2,

                portRecords,

                portsByUuid

            );

            if (!endpoint1 || !endpoint2) {

                state.unresolvedEndpointCount++;

            }

            var up1 = port1

                ? safePortState(port1)

                : null;

            var up2 = port2

                ? safePortState(port2)

                : null;

            var known = up1 !== null && up2 !== null;

            var linkUp = known

                ? (up1 && up2)

                : null;

            state.links.push({

                id: l,

                uuid: safeLinkUuid(link),

                type: safeConnectionType(link),

                endpoint1: {

                    device: endpoint1

                        ? endpoint1.deviceName

                        : "Unknown",

                    port: port1

                        ? safePortName(port1)

                        : "Unknown port",

                    up: up1

                },

                endpoint2: {

                    device: endpoint2

                        ? endpoint2.deviceName

                        : "Unknown",

                    port: port2

                        ? safePortName(port2)

                        : "Unknown port",

                    up: up2

                },

                up: linkUp,

                stateKnown: known,

                metrics: {

                    delay_ms: null,

                    jitter_ms: null,

                    packet_loss_pct: null,

                    bandwidth_mbps: null,

                    throughput_mbps: null,

                    utilization_pct: null,

                    reliability_pct: null,

                    security_risk: null,

                    queue_congestion: null,

                    trust_score: null

                }

            });

            if (known && linkUp === false) {

                state.faultCount++;

            }

        } catch (linkError) {

            state.collectionErrors.push(

                "Link read failed at index " +

                l + ": " + String(linkError)

            );

        }

    }

    state.deviceCount = state.devices.length;

    state.linkCount = state.links.length;

    state.diagnosis = diagnoseSnapshot(state);

    return state;

}


// ============================================================

// LINK UUID

// ============================================================

function safeLinkUuid(link) {

    try {

        var value = link.getObjectUuid();

        if (value === null || value === undefined) {

            return null;

        }

        return String(value);

    } catch (e) {

        return null;

    }

}


// ============================================================

// RESOLVE PORT TO DEVICE

// UUID FIRST; OBJECT IDENTITY FALLBACK

// ============================================================

function resolveEndpoint(port, records, portsByUuid) {

    if (port == null) {

        return null;

    }

    var uuid = safePortUuid(port);

    if (

        uuid !== null &&

        portsByUuid[uuid] !== undefined

    ) {

        return portsByUuid[uuid];

    }

    for (var i = 0; i < records.length; i++) {

        if (records[i].ref === port) {

            return records[i];

        }

    }

    // A final safe fallback: only use a port name if it matches

    // exactly one cached port. Do not guess when ambiguous.

    var targetName = safePortName(port);

    var match = null;

    var matches = 0;

    for (var j = 0; j < records.length; j++) {

        if (records[j].portName === targetName) {

            match = records[j];

            matches++;

        }

    }

    if (matches === 1) {

        return match;

    }

    return null;

}


// ============================================================

// LINK-STATE DIAGNOSIS

// ============================================================

function diagnoseSnapshot(state) {

    var result = {

        status: "UNKNOWN",

        title: "NETWORK STATE UNKNOWN",

        message: "",

        confidence: "LIMITED",

        evidence: [],

        affectedLinks: [],

        healthyLinks: []

    };

    result.evidence.push(

        "API devices: " + state.rawDeviceCount

    );

    result.evidence.push(

        "Collected devices: " + state.deviceCount

    );

    result.evidence.push(

        "API links: " + state.rawLinkCount

    );

    result.evidence.push(

        "Collected links: " + state.linkCount

    );

    result.evidence.push(

        "Unresolved endpoints: " +

        state.unresolvedEndpointCount

    );

    result.evidence.push(

        "Collection errors: " +

        state.collectionErrors.length

    );

    for (var i = 0; i < state.links.length; i++) {

        var link = state.links[i];

        if (link.stateKnown !== true) {

            continue;

        }

        if (link.up === true) {

            result.healthyLinks.push(link);

        } else {

            result.affectedLinks.push({

                id: link.id,

                device1: link.endpoint1.device,

                port1: link.endpoint1.port,

                device2: link.endpoint2.device,

                port2: link.endpoint2.port

            });

        }

    }

    if (state.linkCount === 0) {

        result.title = "NO LINKS COLLECTED";

        result.message =

            "No link records were collected.";

    } else if (state.unresolvedEndpointCount > 0) {

        result.status = "PARTIAL";

        result.title = "PARTIAL TOPOLOGY EVIDENCE";

        result.message =

            "Some link endpoints could not be resolved. " +

            "Path analysis may be incomplete.";

    } else if (result.affectedLinks.length > 0) {

        result.status = "FAULT";

        result.title = "LINK-STATE FAULT REPORTED";

        result.message =

            result.affectedLinks.length +

            " links report a DOWN endpoint.";

    } else {

        result.status = "LINKS_UP";

        result.title = "COLLECTED LINKS REPORT UP";

        result.message =

            "No collected link reports DOWN. " +

            "End-to-end reachability has not been tested.";

    }

    return result;

}


// ============================================================

// SEND SNAPSHOT TO WEBVIEW

//

// Retry happens inside the WebView, not by rescanning.

// ============================================================

function sendSnapshotToWebView(state) {
    // Keep the collected snapshot in the Script Engine. The HTML page
    // requests it after its JavaScript receiver has loaded. This avoids
    // injecting into a blank/loading WebView and losing the message.
    if (state == null) return;
    pathprobeSnapshot = state;
    dprint(
        "[PATHPROBE] Snapshot stored for WebView handshake. " +
        "Devices=" + state.deviceCount + ", links=" + state.linkCount
    );
}

// Called by Interface0.htm through $se("requestSnapshot") AFTER the
// WebView has loaded. This is a delivery request, not a topology rescan.
function requestSnapshot() {
    try {
        if (pathprobeWebView == null) {
            dprint("[PATHPROBE] Snapshot request received but WebView is missing.");
            return;
        }
        if (pathprobeSnapshot == null) {
            dprint("[PATHPROBE] Snapshot request received before collection completed.");
            return;
        }
        var payload = JSON.stringify(pathprobeSnapshot);
        var script =
            "(function(){" +
            "var s=" + payload + ";" +
            "if(typeof window.updateNetworkState==='function'){" +
                "window.updateNetworkState(s);" +
                "window.pathprobeSnapshotReceived=true;" +
                "console.log(\'PATHPROBE snapshot received\');" +
            "}else{console.error('PATHPROBE receiver not ready');}" +
            "})();";
        pathprobeWebView.evaluateJavaScriptAsync(script);
        dprint("[PATHPROBE] Snapshot delivery requested by dashboard.");
    } catch (error) {
        dprint("[PATHPROBE] Snapshot delivery error: " + String(error));
    }
}


// ============================================================

// CLEANUP

// ============================================================

function cleanUp() {

    dprint("PATHPROBE AI shutting down.");

    try {

        if (pathprobeWebView != null) {

            pathprobeWebView.close();

            pathprobeWebView = null;

        }

    } catch (e) {}

    pathprobeSnapshot = null;

}