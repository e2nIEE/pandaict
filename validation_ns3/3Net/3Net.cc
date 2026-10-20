#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ThreeNodeExample");

// Globale Paket-Zähler für jeden Link um Routing zu prüfen
float count01 = 0;
float count12 = 0;
float count02 = 0;

// Callback Funktionen
static void TxTrace01(Ptr<const Packet> packet) {
    count01++;
}

static void TxTrace12(Ptr<const Packet> packet) {
    count12++;
}

static void TxTrace02(Ptr<const Packet> packet) {
    count02++;
}


// *********************************
// 
//  UDP-Client ------ Packet-Sink
//       |                 |
//      n0 =============== n1
//      ||      p2p        ||
//      ||                 ||
//      ++====== n2 =======++   
//
// *********************************

int main(int argc, char *argv[])
{
    // set sim parameters
    // set Bandwidth of Links
    std::string Bandwidth01 = "1000Mbps";           // datarate of devices (in bits) analogous to pandaICTs LAN1000
    std::string Bandwidth12 = "1000Mbps";           // datarate of devices (in bits) analogous to pandaICTs LAN1000
    std::string Bandwidth02 = "1000Mbps";           // datarate of devices (in bits) analogous to pandaICTs LAN1000

    // set delay of links
    std::string Delay01 = "1000ms";                 // delay caused by connection. Can be understood as the length of the cable.
    std::string Delay12 = "1ms";                    // delay caused by connection. Can be understood as the length of the cable.
    std::string Delay02 = "5ms";                    // delay caused by connection. Can be understood as the length of the cable.

    int PacketSize = 20;                          // packetsize in Bytes
    int delta_t = 10;                             // Simulationsdauer. Parameter zur Berechung der Bandbreite aus dem Datenvolumen
    Time interPacketInterval = MilliSeconds(1);   // time between pakets. Analogous to prod_freq_ms in pandaICT

    // set time resolution
    Time::SetResolution(Time::NS);

    // create two nodes. 
    // Nodes are analogous to pandaICTs devices.
    NodeContainer nodes;
    nodes.Create(3);

    // set up p2p connections
    PointToPointHelper p2p01;
    p2p01.SetDeviceAttribute("DataRate", StringValue(Bandwidth01));
    p2p01.SetChannelAttribute("Delay", StringValue(Delay01));
    
    PointToPointHelper p2p12;
    p2p12.SetDeviceAttribute("DataRate", StringValue(Bandwidth12));
    p2p12.SetChannelAttribute("Delay", StringValue(Delay12));

    PointToPointHelper p2p02;
    p2p02.SetDeviceAttribute("DataRate", StringValue(Bandwidth02));
    p2p02.SetChannelAttribute("Delay", StringValue(Delay02));

    // connect nodes
    NetDeviceContainer d01 = p2p01.Install(nodes.Get(0), nodes.Get(1));
    NetDeviceContainer d12 = p2p12.Install(nodes.Get(1), nodes.Get(2));
    NetDeviceContainer d02 = p2p02.Install(nodes.Get(0), nodes.Get(2));

    // install internet stack. Adds a bunch of functionality to the nodes e.g. Routing, UDP/TCP, etc. 
    InternetStackHelper stack;
    stack.Install(nodes);

    // set up IP address-space: (base, mask)
    Ipv4AddressHelper address;

    // assign IP addresses to devices
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces1 = address.Assign(d01);

    address.SetBase("10.1.2.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces2 = address.Assign(d12);

    address.SetBase("10.1.3.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces3 = address.Assign(d02);

    // enable routing
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    // set up UDP-Server (PacketSink). 
    // Ipv4Address::GetAny() makes sure the Server accepts connection on all local IP-Addresses of node.
    uint16_t port = 9;
    Address sinkAddress(InetSocketAddress(Ipv4Address::GetAny(), port));

    // create packetSink Application (server), while specifying the name of the protocol to use to recieve traffic. And install on node 1
    PacketSinkHelper packetSinkHelper("ns3::UdpSocketFactory", sinkAddress);
    ApplicationContainer sinkApps = packetSinkHelper.Install(nodes.Get(1));
    
    // start/stop server app after 1s/13s
    sinkApps.Start(Seconds(1.0));
    sinkApps.Stop(Seconds(13.0));

    // set up UDP-Client to send packets to node 1 on port 9
    UdpClientHelper client(interfaces1.GetAddress(1), port);

    // set client parameters
    client.SetAttribute("MaxPackets", UintegerValue(0));              // upper bound for total packets sent
    client.SetAttribute("Interval", TimeValue(interPacketInterval));  // time to wait between packets
    client.SetAttribute("PacketSize", UintegerValue(PacketSize));     // size of the packets

    // install client on node 0
    ApplicationContainer clientApps = client.Install(nodes.Get(0));

    // save routing table after 2.5 seconds (sim-time)
    //Simulator::Schedule(Seconds(2.5), []() {
    //std::ofstream myfile;
    //myfile.open("routing_table.txt");
    //Ipv4GlobalRoutingHelper::PrintRoutingTableAllAt(Seconds(2.5), Create<OutputStreamWrapper>(&myfile));
    //});

    // start/stop client app after 2s/12s
    clientApps.Start(Seconds(2.0));
    clientApps.Stop(Seconds(12.0));

    // installiere FlowMonitor für Datenvolumenüberwachung
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    // count packets along the 3 routes
    d01.Get(0)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace01));
    d01.Get(1)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace01));

    d12.Get(0)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace12));
    d12.Get(1)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace12));

    d02.Get(0)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace02));
    d02.Get(1)->TraceConnectWithoutContext("MacTx", MakeCallback(&TxTrace02));

    // force simulation to stop after 20 seconds
    Simulator::Stop(Seconds(20));
    Simulator::Run();

    monitor->CheckForLostPackets();
    monitor->SerializeToXmlFile("results.xml", true, true);

    // get datavolume recieved at the server and print to console
    Ptr<PacketSink> sink = DynamicCast<PacketSink>(sinkApps.Get(0));
    int DataVolume = sink->GetTotalRx();                            // Get total bytes (!) recieved in the sink app
    std::cout << "Empfangene Bytes am Server: " << DataVolume << " Bytes" << std::endl;

    // calculate used bandwidth
    float used_Bandwidth;
    used_Bandwidth = DataVolume / delta_t;      // B -> B/s  
    used_Bandwidth = used_Bandwidth / 1000000;  // B/s -> MB/s
    used_Bandwidth = used_Bandwidth * 8;        // MB/s -> Mb/s

    // print used bandwidth
    std::cout << "Used Bandwidth: " << used_Bandwidth << " Mbps" << std::endl;

    // korrigiere counts aufgrund von internen Kopien bei ns3
    //count01 = count01 /2;
    //count12 = count12 /2;
    //count02 = count02 /2;

    // print packet count along the 3 routes
    std::cout << "\n----- Link Packet Counts -----\n";
    std::cout << "Link n0 <-> n1: " << count01 << " packets \n";
    std::cout << "Link n1 <-> n2: " << count12 << " packets \n";
    std::cout << "Link n0 <-> n2: " << count02 << " packets \n";

    // print packet count along the 3 routes
    std::cout << "\n----- Link Bandwidth -----\n";
    std::cout << "Link n0 <-> n1: " << count01 * PacketSize << " Byte \n";
    std::cout << "Link n1 <-> n2: " << count12 * PacketSize << " Byte \n";
    std::cout << "Link n0 <-> n2: " << count02 * PacketSize << " Byte \n";

    // print packet count along the 3 routes
    std::cout << "\n----- Link Bandwidth -----\n";
    std::cout << "Link n0 <-> n1: " << count01 * PacketSize * 8 / (delta_t*1000000) << " Mbps \n";
    std::cout << "Link n1 <-> n2: " << count12 * PacketSize * 8 / (delta_t*1000000) << " Mbps \n";
    std::cout << "Link n0 <-> n2: " << count02 * PacketSize * 8 / (delta_t*1000000) << " Mbps \n";

    Simulator::Destroy();
    return 0;
    }