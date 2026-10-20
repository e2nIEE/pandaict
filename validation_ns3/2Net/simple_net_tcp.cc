#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-helper.h"

using namespace ns3;

// ***************************
// 
//  OnOff-Client  Packet-Sink
//      |             |
//      n1 ========== n2
//            p2p
//
// ***************************

int main(int argc, char *argv[])
{
    // set simulation parameters
    std::string Bandwidth = "1000Mbps";           // datarate of devices (in bits) analogous to pandaICTs LAN1000
    std::string Delay = "0ms";                    // delay caused by connection. Can be understood as the length of the cable.
    int PacketSize = 20;                          // packetsize in Bytes
    int delta_t = 10;                             // Simulationsdauer. Parameter zur Berechung der Bandbreite aus dem Datenvolumen
    Time interPacketInterval = MilliSeconds(1);   // time between pakets. Analogous to prod_freq_ms in pandaICT
    std::string DataRate = "160Kbps";

    // set time resolution
    Time::SetResolution(Time::NS);

    // enable logging for PacketSink
    LogComponentEnable("PacketSink", LOG_LEVEL_INFO);

    // create nodes
    NodeContainer nodes;
    nodes.Create(2);

    // set up p2p connection
    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue(Bandwidth));
    p2p.SetChannelAttribute("Delay", StringValue(Delay));

    // connect nodes and install net devices on them
    NetDeviceContainer devices;
    devices = p2p.Install(nodes);

    // install internet stack on nodes.
    InternetStackHelper stack;
    stack.Install(nodes);

    // set up IP-address space
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");

    // assign IP addresses to devices
    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    // 
    uint16_t port = 8080;
    Address sinkAddress(InetSocketAddress(interfaces.GetAddress(1), port));

    // set up and install PacketSink Server (TCP) on node 1
    PacketSinkHelper packetSinkHelper("ns3::TcpSocketFactory", sinkAddress);
    ApplicationContainer sinkApps = packetSinkHelper.Install(nodes.Get(1));

    // start/stop server after 1s/13s
    sinkApps.Start(Seconds(1.0));
    sinkApps.Stop(Seconds(12.0));

    // set up OnOffApplication
    OnOffHelper onoff("ns3::TcpSocketFactory", sinkAddress);

    // set client parameters
    onoff.SetAttribute("DataRate", StringValue(DataRate));
    onoff.SetAttribute("PacketSize", UintegerValue(PacketSize));
    onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1000]")); // setze OnTime >> 1 sodass App immer an
    onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));   // setze OffTime = 0 sodass -""-

    ApplicationContainer clientApps = onoff.Install(nodes.Get(0));

    // start/stop onoff app after 2s/12s
    clientApps.Start(Seconds(1.5));
    clientApps.Stop(Seconds(11.5));

    // installiere FlowMonitor für Datenvolumenüberwachung
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

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

    std::cout << "Used Bandwidth: " << used_Bandwidth << " Mbps" << std::endl;

    Simulator::Destroy();
    return 0;
}
