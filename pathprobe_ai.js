// ============================================================
// PATHPROBE AI
// Cisco Packet Tracer 9.x Script Module
// Phase 1 - Custom Interface Launcher
// ============================================================

var pathprobeWebView = null;


// ------------------------------------------------------------
// Module startup
// ------------------------------------------------------------
function main()
{
    dprint("=================================");
    dprint("PATHPROBE AI");
    dprint("Script Engine Started");
    dprint("Packet Tracer integration OK");
    dprint("Launching AI interface...");
    dprint("=================================");

    try
    {
        pathprobeWebView =
            webViewManager.createWebView(
                "PATHPROBE AI",
                "this-sm:pathprobe_ai_panel.htm",
                420,
                720
            );

        pathprobeWebView.show();

        dprint("PATHPROBE AI interface launched.");
    }
    catch (error)
    {
        dprint("ERROR launching PATHPROBE AI interface:");
        dprint(error);
    }
}


// ------------------------------------------------------------
// Module cleanup
// ------------------------------------------------------------
function cleanUp()
{
    dprint("PATHPROBE AI shutting down...");

    try
    {
        if (pathprobeWebView != null)
        {
            pathprobeWebView.close();
            pathprobeWebView = null;
        }
    }
    catch (error)
    {
        dprint("Cleanup warning:");
        dprint(error);
    }
}