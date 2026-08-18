#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"

#include <iostream>
#include <map>

using namespace ns3;

int
main(int argc, char* argv[])
{
    uint32_t packetSize = 1024;
    uint32_t maxPackets = 1000;

    CommandLine cmd;
    cmd.AddValue("packetSize", "UDP packet size in bytes", packetSize);
    cmd.AddValue("maxPackets", "Maximum number of packets", maxPackets);
    cmd.Parse(argc, argv);

    // =========================================================
    // 1. CREATE NODES
    // =========================================================

    NodeContainer nodes;
    nodes.Create(3);

    Ptr<Node> client = nodes.Get(0);
    Ptr<Node> router = nodes.Get(1);
    Ptr<Node> server = nodes.Get(2);

    // =========================================================
    // 2. CREATE NETWORK LINKS
    // =========================================================

    PointToPointHelper pointToPoint;

    pointToPoint.SetDeviceAttribute(
        "DataRate",
        StringValue("10Mbps"));

    pointToPoint.SetChannelAttribute(
        "Delay",
        StringValue("10ms"));

    // Client <-> Router
    NetDeviceContainer clientRouter =
        pointToPoint.Install(client, router);

    // Router <-> Server
    NetDeviceContainer routerServer =
        pointToPoint.Install(router, server);

    // =========================================================
    // 3. INSTALL INTERNET STACK
    // =========================================================

    InternetStackHelper internet;
    internet.Install(nodes);

    // =========================================================
    // 4. ASSIGN IP ADDRESSES
    // =========================================================

    Ipv4AddressHelper address;

    // Client <-> Router
    address.SetBase(
        "10.1.1.0",
        "255.255.255.0");

    Ipv4InterfaceContainer clientRouterInterfaces =
        address.Assign(clientRouter);

    // Router <-> Server
    address.SetBase(
        "10.1.2.0",
        "255.255.255.0");

    Ipv4InterfaceContainer routerServerInterfaces =
        address.Assign(routerServer);

    // =========================================================
    // 5. ENABLE ROUTING
    // =========================================================

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // =========================================================
    // 6. UDP SERVER
    // =========================================================

    uint16_t port = 9000;

    UdpServerHelper serverHelper(port);

    ApplicationContainer serverApplication =
        serverHelper.Install(server);

    serverApplication.Start(Seconds(1.0));
    serverApplication.Stop(Seconds(15.0));

    // =========================================================
    // 7. UDP CLIENT
    // =========================================================

    UdpClientHelper clientHelper(
        routerServerInterfaces.GetAddress(1),
        port);

    clientHelper.SetAttribute(
        "MaxPackets",
        UintegerValue(maxPackets));

    clientHelper.SetAttribute(
        "Interval",
        TimeValue(MilliSeconds(10)));

    clientHelper.SetAttribute(
        "PacketSize",
        UintegerValue(packetSize));

    ApplicationContainer clientApplication =
        clientHelper.Install(client);

    clientApplication.Start(Seconds(2.0));
    clientApplication.Stop(Seconds(12.0));

    // =========================================================
    // 8. FLOW MONITOR
    // =========================================================

    FlowMonitorHelper flowHelper;

    Ptr<FlowMonitor> monitor =
        flowHelper.InstallAll();

    // =========================================================
    // 9. RUN SIMULATION
    // =========================================================

    Simulator::Stop(Seconds(15.0));

    Simulator::Run();

    // =========================================================
    // 10. COLLECT RESULTS
    // =========================================================

    monitor->CheckForLostPackets();

    Ptr<Ipv4FlowClassifier> classifier =
        DynamicCast<Ipv4FlowClassifier>(
            flowHelper.GetClassifier());

    std::map<FlowId, FlowMonitor::FlowStats> statistics =
        monitor->GetFlowStats();

    std::cout << "\n";
    std::cout << "========================================\n";
    std::cout << "       PATHPROBE-AI BASELINE\n";
    std::cout << "========================================\n";

    for (const auto& flow : statistics)
    {
        Ipv4FlowClassifier::FiveTuple tuple =
            classifier->FindFlow(flow.first);

        const auto& stat = flow.second;

        double throughput = 0.0;

        double duration =
            stat.timeLastRxPacket.GetSeconds() -
            stat.timeFirstTxPacket.GetSeconds();

        if (duration > 0)
        {
            throughput =
                (stat.rxBytes * 8.0) /
                duration /
                1000000.0;
        }

        double packetLoss = 0.0;

        if (stat.txPackets > 0)
        {
            packetLoss =
                ((stat.txPackets - stat.rxPackets) *
                 100.0) /
                stat.txPackets;
        }

        double averageDelay = 0.0;

        if (stat.rxPackets > 0)
        {
            averageDelay =
                stat.delaySum.GetMilliSeconds() /
                stat.rxPackets;
        }

        std::cout << "\n";
        std::cout << "Source          : "
                  << tuple.sourceAddress << "\n";

        std::cout << "Destination     : "
                  << tuple.destinationAddress << "\n";

        std::cout << "Packets Sent    : "
                  << stat.txPackets << "\n";

        std::cout << "Packets Received: "
                  << stat.rxPackets << "\n";

        std::cout << "Packet Loss     : "
                  << packetLoss << " %\n";

        std::cout << "Throughput      : "
                  << throughput << " Mbps\n";

        std::cout << "Average Delay   : "
                  << averageDelay << " ms\n";
    }

    std::cout << "\n";
    std::cout << "========================================\n";

    // Save FlowMonitor results.
    monitor->SerializeToXmlFile(
        "pathprobe_baseline.xml",
        true,
        true);

    Simulator::Destroy();

    return 0;
}
