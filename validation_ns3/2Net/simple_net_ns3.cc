#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

using namespace ns3;

// **************************
//
//  UDP-Client  Packet-Sink
//      |             |
//      n1 ========= n2
//            p2p
//
// **************************

int main(int argc, char *argv[])
{
  // set simulation parameters
  std::string Bandwidth = "1000Mbps";           // datarate of devices (in bits) analogous to pandaICTs LAN1000
  std::string Delay = "0ms";                    // delay caused by connection. Can be understood as the length of the cable.
  int PacketSize = 20;                          // packetsize in Bytes
  int delta_t = 10;                             // Simulationsdauer. Parameter zur Berechung der Bandbreite aus dem Datenvolumen
  Time interPacketInterval = MilliSeconds(1);   // time between pakets. Analogous to prod_freq_ms in pandaICT

  // set time resolution
  Time::SetResolution(Time::NS);

  // create two nodes. 
  // Nodes are analogous to pandaICTs devices.
  NodeContainer nodes;
  nodes.Create(2);

  // set up p2p connection
  PointToPointHelper pointToPoint;
  pointToPoint.SetDeviceAttribute("DataRate", StringValue(Bandwidth));
  pointToPoint.SetChannelAttribute("Delay", StringValue(Delay));

  // install devices on nodes. 
  // Devices are unique in ns3 and have no comparable concept in pandaICT.
  NetDeviceContainer devices;
  devices = pointToPoint.Install(nodes);

  // install internet stack. Adds a bunch of functionality to the nodes e.g. Routing, UDP/TCP, and more. 
  InternetStackHelper stack;
  stack.Install(nodes);

  // set up IP address-space: (base, mask)
  Ipv4AddressHelper address;
  address.SetBase("10.1.1.0", "255.255.255.0");

  // assign IP addresses to devices
  Ipv4InterfaceContainer interfaces = address.Assign(devices);

  // set up and install UDP-Server (PacketSink) on node 1
  uint16_t port = 9;
  Address sinkAddress(InetSocketAddress(Ipv4Address::GetAny(), port));
  PacketSinkHelper packetSinkHelper("ns3::UdpSocketFactory", sinkAddress);
  ApplicationContainer sinkApps = packetSinkHelper.Install(nodes.Get(1));
  
  // start/stop server app after 1s/13s
  sinkApps.Start(Seconds(1.0));
  sinkApps.Stop(Seconds(13.0));

  // set up UDP-Client which sends packets to node 1 on port 9
  UdpClientHelper client(interfaces.GetAddress(1), port);

  // Set Client Parameters
  client.SetAttribute("MaxPackets", UintegerValue(0));              // upper bound for total packets sent
  client.SetAttribute("Interval", TimeValue(interPacketInterval));  // time to wait between packets
  client.SetAttribute("PacketSize", UintegerValue(PacketSize));     // size of the packets

  // Install Client on node 0
  ApplicationContainer clientApps = client.Install(nodes.Get(0));

  // start/stop client app after 1s/13s
  clientApps.Start(Seconds(2.0));
  clientApps.Stop(Seconds(12.0));

  Simulator::Run();

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