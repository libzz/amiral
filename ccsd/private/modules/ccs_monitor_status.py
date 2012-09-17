# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# CRCnet Monitor Status Information Display
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# No usage or redistribution rights are granted for this file unless
# otherwise confirmed in writing by the copyright holder.
import sys
import time
import socket
import struct
import fcntl
import getopt
import iwtools

from crcnetd._utils.ccsd_common import *
from crcnetd._utils.ccsd_log import *
from crcnetd._utils.ccsd_clientserver import registerPage, registerDir, \
        registerRecurring
from crcnetd._utils.ccsd_config import config_get
from crcnetd._utils.ccsd_events import registerEvent, triggerEvent

from ccs_monitor_web import registerMenuItem, HTable, returnPage, \
    returnErrorPage, MENU_TOP, MENU_GROUP_GENERAL
import ccs_monitor_snmp as snmp

registerTableOID = snmp.registerTableOID
registerDynamicOID = snmp.registerDynamicOID

DEFAULT_NODEMAP_FILE = "/etc/ccsd/nodemap"
DEFAULT_AVERAGE_SIGNAL = 14
DEFAULT_GOOD_SIGNAL = 20

IWSPY_CHECK_INTERVAL = 300

class ccs_status_error(ccsd_error):
    pass

ccs_mod_type = CCSD_CLIENT

averaged_snr_stats = {}
DEFAULT_SNR_SAMPLES = 10
DEFAULT_SNR_WINDOW = 30
DEFAULT_SNR_REFRESH_RATE = 2

##############################################################################
# Utility Functions
##############################################################################

def getInterfaceWirelessStats(ifname, wiface):
    """Returns a set of averaged statistics for the wireless interface

    The average consists of the last N samples taken in the previous
    W second window if available. If they are not available you get 
    less of an average. Hence calling this function repeatedly within
    W seconds (prefably N times) will result in the best average.

    N defaults to 10 and is available via the config parameter snr_samples
    W defaults to 30 and is available via the config parameter snr_window
    """
    global averaged_snr_stats
    
    snr_samples = config_get("status", "snr_samples", DEFAULT_SNR_SAMPLES)
    snr_window = config_get("status", "snr_window", DEFAULT_SNR_WINDOW)
    
    if ifname not in averaged_snr_stats.keys():
        averaged_snr_stats[ifname] = []
        
    mode = wiface.get_mode()
    # Get some updated stats
    try:
        stats = wiface.get_stats()
    except:
        #log_warn("Could not retrieve statistics for %s" % ifname, \
        #        sys.exc_info())
        if mode != iwtools.IW_MODE_MASTER:
            return {"snr":0, "signal":0, "noise":0, "n":0}
        else:
            return {}
        
    # Append to the end of the list
    now = time.time()
    averaged_snr_stats[ifname].append((stats, now))
    
    # Remove extra entries
    while len(averaged_snr_stats[ifname]) > snr_samples:
        averaged_snr_stats[ifname].pop(0)
        
    # Remove expired entries    
    i = 0
    while len(averaged_snr_stats[ifname])>0:
        (ostats, ttime) = averaged_snr_stats[ifname][0]
        if (now-ttime) > snr_window:
            averaged_snr_stats[ifname].pop(0)
            continue
        else:
            break
        
    # Calculate averages
    if mode == iwtools.IW_MODE_MASTER:
        result = {}
    else:
        result = {"snr":0, "signal":0, "noise":0, "n":0}
    for (ostats, ttime) in averaged_snr_stats[ifname]:
        if wiface.get_mode() == iwtools.IW_MODE_MASTER:
            # Calculate statistics for each associated sta
            for sta,sta_stats in ostats.items():
                if sta not in result.keys(): 
                    result[sta] = {"snr":0, "signal":0, "noise":0, "n":0}
                result[sta]["snr"] += sta_stats["snr"]
                result[sta]["signal"] += sta_stats["signal"]
                result[sta]["noise"] += sta_stats["noise"]
                result[sta]["n"] += 1
        else:
            result["snr"] += ostats["snr"]
            result["signal"] += ostats["signal"]
            result["noise"] += ostats["noise"]
            result["n"] += 1
            
    if mode == iwtools.IW_MODE_MASTER:
        for sta,stats in result.items():
            stats["snr"] /= stats["n"]
            stats["signal"] /= stats["n"]
            stats["noise"] /= stats["n"]
            result[sta] = stats
    else:
        result["snr"] /= result["n"]
        result["signal"] /= result["n"]
        result["noise"] /= result["n"]

    return result

def getAsociatedClients(name):
    """Gets the number of associated clients on a Madwifi ap"""
    try:
        fd = open("/proc/net/madwifi/%s/associated_sta" % name)
        lines = fd.readlines()
        return (len(lines)/3)
    except:
        return -1

def getMadwifiBase(mac, interfaces):
    """Searches the provided list of interfaces for base madwifi interface 
       matching the supplied MAC address"""

    for iface in interfaces:
        # If the last 5 octets of the mac don't match, ignore
        if mac[3:] != iface["mac"][3:]:
            continue
        # If the iface is of type link/ieee802.11 rathern than link/ether
        # then it is the base interface
        fd = os.popen("/sbin/ip link ls dev %s" % iface["name"])
        lines = fd.readlines()
        fd.close()
        if lines[-1].find("link/ieee802.11") != -1:
            return  iface["name"]
    return None

def getAthStats(oiface, interfaces):
    """Gets stats from Athstats"""
    phy = -1
    crc = -1
    base = None
    try:
        mac = oiface["mac"]
        # Find the base interface
        base = getMadwifiBase(mac, interfaces)
        if not base: return phy, crc
        # Run athstats and retrieve output
        lines = os.popen("athstats -i %s" % base).readlines()
        if len(lines) == 0: return phy, crc
        # Parse athstats output
        for line in lines:
            # Look for key text
            if line.find("PHY errors") != -1:
                # Store PHY errors
                phy = int(line.strip().split()[0])
            elif line.find("rx failed due to bad CRC") != -1:
                # Store CRC errors
                crc = int(line.strip().split()[0])
            else:
                # Ignored line
                continue
            # Ignore the rest if we've found both values
            if phy != -1 and crc != -1:
                break
    except:
        log_error("Failed to fetch ath stats for %s" % oiface["name"], 
                sys.exc_info())
        phy = -1
        crc = -1
    return phy, crc

Cache = None
def getInterfaceDetails(returnAll=False):
    global Cache
    """Reads the interface informatin from /proc
       Uses a cache to speed up snmp requests"""

    # Early exit if we can serve from cache
    if Cache is not None and Cache["timeout"] > time.time():
        if returnAll:
            return Cache['dtrue']
        else:
            return Cache['dfalse']

    # Fetch the data and add to the cache
    Cache={}

   
    average_signal = config_get("status", "average_signal", \
            DEFAULT_AVERAGE_SIGNAL)
    good_signal = config_get("status", "good_signal", \
            DEFAULT_GOOD_SIGNAL)

    # Fetch data for shown interfaces, followed by all interfaces
    iterations = {"dfalse":False,"dtrue":True}
    for cachekey, willReturnAll in iterations.items():
        interfaces2 = []
        interfaces = getInterfaces(willReturnAll)
        for iface in interfaces:
            if iface["name"] in iwtools.interfaces:
                iface["wireless"] = True
                wiface = iwtools.get_interface(iface["name"])
                iface["stats"] = getInterfaceWirelessStats(iface["name"], wiface)
                iface["mode"] = wiface.get_mode()
                if iface["mode"] == iwtools.IW_MODE_MASTER:
                    iface["clients"] = getAsociatedClients(iface["name"])
                else:
                    iface["clients"] = -1
                res = getAthStats(iface, interfaces)
                iface["CRC"] = res[1]
                iface["PHY"] = res[0]
                iface["essid"] = wiface.get_essid()
                iface["channel"] = wiface.get_channel()
                iface["config"] = wiface.get_cur_config()
            else:
                iface["wireless"] = False
            if iface["wireless"] and iface["mode"] != iwtools.IW_MODE_MASTER:
                snr = iface["stats"]["snr"]
                if snr < average_signal:
                    iface["status"] = "CRITICAL"
                    iface["statusdesc"] = "Interface Up / Extremely Low Signal"
                elif snr >= average_signal and snr < good_signal:
                    iface["status"] = "WARNING"
                    iface["statusdesc"] = "Interface Up / Average Signal"
                elif snr >= good_signal:
                    iface["status"] = "OK"
                    iface["statusdesc"] = "Interface Up / Good Signal"
            else:
                iface["status"] = "OK"
                iface["statusdesc"] = "Interface Up"
            interfaces2.append(iface)   
        Cache[cachekey] = interfaces2

    # Timeout in 30 seconds
    Cache["timeout"] = time.time()+30

    # Choose what to return
    if returnAll:
        return Cache['dtrue']
    else:
        return Cache['dfalse']
    
def getIndexedDetails(ifindex, wirelessIndicesOnly=False):
    """Returns a list of interfaces and their indexes"""
    iface = None

    # Get list of interfaces
    try:
        ifaces = getInterfaceDetails(True)
    except:
        log_error("Error fetching wireless interfaces for SNMP!", \
                sys.exc_info())
        ifaces = []
    
    # Indexes
    ifindices = [] 
    for tiface in ifaces:
        if not tiface["wireless"] and wirelessIndicesOnly:
            continue
        if tiface["ifindex"] == -1:
            continue
        if ifindex == -1:
            ifindex = tiface["ifindex"]
        if tiface["ifindex"] == ifindex:
            iface = tiface
        ifindices.append(tiface["ifindex"])

    return ifaces, iface, ifindices

@registerRecurring(IWSPY_CHECK_INTERVAL)
def checkiwspy():
    """Called regularly to check that iwspy is correctly configured

    If an Orinoco interface (heuristically determined as any wireless interface
    that is not madwifi or hostap) does not have a MAC address added to iwspy,
    the arp table is looked up and the MAC of the host at the opposite end of
    the subnet is added. 

    If a MAC address is present it is checked against the ARP table and
    corrected if it is out of date.

    This procedure is required for SNR statistics to be collected for Orinoco
    card links.
    """

    for iface in iwtools.interfaces:
        # Skip madwifi and hostap interfaces
        if iwtools.is_madwifi(iface) or iwtools.is_hostap(iface): continue
        # Skip interfaces that are down
        state = getInterfaces(returnOne=iface)
        if len(state) != 1 or not state[0]["up"]: continue
        # Determine whether to start from the top of the bottom of the net
        cidr = state[0]["address"]
        if cidr == "": continue
        ip = ipnum(cidrToIP(cidr))
        bcast = cidrToBroadcast(cidr)
        network = cidrToNetwork(cidr)
        ldiff = ip - network
        udiff = bcast - ip
        if ldiff > udiff:
            # ip is closest to top, start at bottom
            start = network+1
            inc = 1
            end = bcast
        else:
            # ip is closet to the bottom, start at the top
            start = bcast-1
            inc = -1
            end = network
        # Short broadcast ping to populate ARP table
        log_command("/usr/sbin/fping -c2 -q %s &>/dev/null" % formatIP(bcast))
        # Get all MACs on the link
        macs = getLinkMACs(iface)
        if len(macs) == 0: continue
        # Walk from the opposite end of the network and use the first entry
        use = None
        while start != end:
            if start == ip: 
                start += inc
                continue # skip self
            if formatIP(start) in macs.keys():
                use = macs[formatIP(start)]
                break
            start += inc
        # Next interface if no usable macs found
        if use is None: continue
        # Otherwise update iwspy
        current = getiwspyMAC(iface)
        if use == current: continue
        log_command("/sbin/iwspy %s off 2>&1" % iface)
        log_command("/sbin/iwspy %s + %s" % (iface, use))
        log_info("Updated iwspy for interface '%s' to '%s'" % (iface, use))

##############################################################################
# Node Map
##############################################################################
class nodeMap:
    
    # These temporary files are all stored in the tmpdir
    mapfile = "crcnet-monitor.map"
    dotfile = "crcnet-monitor.dot"
    imgfile = "crcnet-monitor.gif"
    
    def __init__(self,local,gateway,rootnode):

        # Initialise data structures
        self.localhost = local
        self.gateway = gateway
        self.rootnode = rootnode
        self.nodes = {}
        self.nets = {}
        self.links = {}
        self.linkmap = {}     
        
        # Setup useful variables
        self.tmpdir = config_get(None, "tmpdir", DEFAULT_TMPDIR)
        self.mapfile = "%s/%s" % (self.tmpdir, self.mapfile)
        self.dotfile = "%s/%s" % (self.tmpdir, self.dotfile)
        self.imgfile = "%s/%s" % (self.tmpdir, self.imgfile)
        self.port = port = config_get(None, "port", DEFAULT_CLIENT_PORT)
        
        # Graph not generated yet
        self.generated = -1
        
    def LoadFile(self,filename):
        """Read in the nodemap file.

        This file contains all nodes 'name', 'short description', 
        'IP address' and 'Netmask' for each interface of the node.
        """

        if filename == None:
            raise ccs_status_error("Empty filename passed to nodeMap")

        try:
            infile = open(filename)
        except IOError:
            raise ccs_status_error("Specified nodeMap %s does not exist!" % \
                    filename)

        for line in infile.readlines():
            if line.startswith("#"):
                continue
            line = line.rstrip()
            elements = line.split("\"")
            
            host = elements[0]
            host = host.rstrip()
            longhost = elements[1]
            elements = elements[2]
            elements = elements.lstrip() 
            iplist = elements.split(" ")

            # have a host identifier, and a list of ip addresses
            # in ipaddr/cidr form
            
            # Store the node attributes here, saves adding them later on            
            if not self.nodes.has_key(host):
                self.nodes[host] = {}
                self.nodes[host]["name"] = host
                self.nodes[host]["fullname"] = longhost
                self.nodes[host]["ips"] = []
                self.nodes[host]["ipnets"] = []
                self.nodes[host]["type"] = "node"
                self.nodes[host]["reachable"] = None
                if host == self.gateway:
                    self.nodes[host]["style"] = "filled"
                else:
                    self.nodes[host]["style"] = "solid"
            
            for ip in iplist:
                self.nodes[host]["ipnets"].append(ip)
                (mip,net) = ip.split("/")
                self.nodes[host]["ips"].append(mip)
                
                network = cidrToNetwork(ip)
                if not self.nets.has_key(network):
                    self.nets[network] = []
                self.nets[network].append(host)
                
        # networks can have multiple nodes on them: graphs can't.
        # here we iterate over every network, and create a "link"
        # datatype, which only has two entries on it. We create
        # temporary nodes to deal with networks with multiple nodes 
        # on them - using the network number as the key.
        # doing this here saves doing it twice!
        # We need to associate with each node a list of links
        # they participate in
        
        linknum = 0
        for net in self.nets.keys():
            network = self.nets[net]
        
                
            if len(network) == 2:
                linknum = linknum + 1
                # just have the two nodes, this is fine
                
                self.nodeAppend(network[0],linknum)
                self.nodeAppend(network[1],linknum)
                self.linkAppend(linknum,network[0],network[1])
                
            elif len(network) > 2:
                netname = "n%d" % net
                self.nodes[netname] = {}
                self.nodes[netname]["type"] = "tmp"
                for i in (range(len(network))):
                    linknum = linknum + 1
                
                    self.nodeAppend(netname,linknum)
                    self.nodeAppend(network[i],linknum)
                    
                    self.linkAppend(linknum,netname, network[i])

        infile.close()

    def BuildAdjacency(self):
        """Build a list of hosts which are connected to each other"""

        self.adjacency = {}
        # for every node in the list
        
        for nodename in self.nodes.keys():
            
            self.adjacency[nodename] = []
            node = self.nodes[nodename]

            # get each link it is associated to
            for linknum in node["links"]:
                link = self.links[linknum]["hosts"]

                if len(link) > 2:
                    raise ccs_status_error("Error! Link has too many " \
                            "hosts (>2). Broken!")

                # for every host on each network that isn't the node
                # in question, append to the adjacency graph
                for adjnode in link:
                    if adjnode != nodename:
                        self.adjacency[nodename].append(adjnode)
     
    def WalkToGateway(self):
        """Walk from localhost to the gateway"""

        hops = self.FindShortestPath(self.adjacency, self.localhost,
                self.gateway)
        if hops is None:
            return

        for i in range(len(hops) - 1):
            link = None
            pair = "%s %s" % (hops[i],hops[i+1])
            if(self.linkmap.has_key(pair)):
                link = self.links[self.linkmap[pair]]
            else:
                pair = "%s %s" % (hops[i+1],hops[i])
                if(self.linkmap.has_key(pair)):
                    link = self.links[self.linkmap[pair]]

            if link:
                link["params"]["color"] = "black"
                link["params"]["style"] = "bold"
        
    def FindShortestPath(self,graph, start, end, path=[]):
        """Find a shortest path in the network between two nodes"""
        path = path + [start]
        if start == end:
            return path
        if not graph.has_key(start):
            return None
        shortest = None
        for node in graph[start]:
            if node not in path:
                newpath = self.FindShortestPath(graph, node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest

    def BreadthFirstPing(self, start):
        """fping the hosts to determine whether they are reachable or not."""
        if start not in self.nodes.keys():
            log_warn("Nodemap called with invalid start value: %s" % start)
            return

        val = {}
        self.reachable = {}
        id = 0
        for nodename in self.adjacency.keys():
            val[nodename] = None
            self.nodes[nodename]["reachable"] = None
        bfirst = []
        bfirst.append(start)
        while len(bfirst) > 0:
            k = bfirst.pop(0)
            id = id + 1
            val[k] = id

            if self.nodes[k]["type"] == "tmp":
                result = 1
            else:
                result = self.testHost(self.nodes[k]["ips"])
            if result > 0:
                self.nodes[k]["reachable"] = result
                 
                for t in self.adjacency[k]:
                    if val[t] == None:
                        bfirst.append(t)
                        val[t] = -1
            else:
                self.nodes[k]["reachable"] = 0

    def GetImageMap(self):
        """Return imagemap code for the generated image
        
        The imagemap code is stored in tmpdir/crcnet-monitor.map and is 
        generated when DrawGraph is called.
        """

        str = "\n<map name=\"map\">"
        
        # Get the size of the map we are returning a map for
        resize = 0
        size = self.getGraphDimensions()

        # If the size of the image bigger than the frame size, all the coords
        # need to be resize. 
        if size[0] > 900:
            resize = 1
        
        try:
            mapfd = open(self.mapfile)
            # resize == 1, we need to resize the image
            if resize == 1:
                for line in mapfd.readlines():
                    lowIndex = line.find('coords="')+len('coords="')
                    highIndex = line.find('">')
                    originalStr = line[lowIndex:highIndex]
                    list = originalStr.split(',')
                    tmpStr = ""
                    for i in range(0, len(list)):
                        # If wider than 900 pixel, then decrease the size. 
                        tmpInt = string.atoi(list[i]) * \
                                (float(900/float(size[0])))                
                        if i > 0:
                            tmpStr += ",%.00d"%tmpInt
                        else:
                            tmpStr += "%.00d"%tmpInt
                    str += string.replace(line, line[lowIndex:highIndex], \
                            tmpStr)
            else:
                for line in mapfd.readlines():
                    str += line
        except:
            log_warn("Could not read mapfile: %s" % self.mapfile)
            
        str = str + "</map>\n"
        return str

    def DrawGraph(self):
        """Generate the graph image and store in a temporary directory"""

        try: 
            outfile = open(self.dotfile, 'w')
        except IOError:
            raise ccs_status_error("Failed to open %s for writing" % \
                    self.dotfile)
        outfile.write('graph linkgraph {\n')
        outfile.write('\toverlap="false";\n')
        outfile.write('\tspline="true";\n')
        outfile.write('\troot="%s";\n' % self.rootnode) 
        outfile.write('\tsize="10,10";\n')

        nodelist = self.nodes.keys()
        nodelist.sort()
        for nodename in nodelist:
            node = self.nodes[nodename]

            if node["type"] == "tmp":
                outfile.write('\t"%s" [shape=ellipse,label="",width=0,' \
                        'height=0] ;\n' % (nodename))
            else:
                outfile.write('\t"%s" [color = %s, shape = record, label = ' \
                        '"{%s|%s}", style=%s, tooltip="%s", URL="%s"];\n' \
                        % ( node["name"], node["color"], node["status"],
                            node["name"], node["style"], node["fullname"],
                            node["url"]))

        for linknum in self.links.keys():
            link = self.links[linknum]
            linkstr = '\t"%s" -- "%s"' % ( link["hosts"][0], link["hosts"][1])

            linkparams = ""
            for param in link["params"].keys():
                linkparams = linkparams + " %s=%s" % \
                        (param, link["params"][param])
            if linkparams != "":
                linkstr = linkstr + "[" + linkparams + "]"
            linkstr = linkstr + ";\n"
            
            outfile.write(linkstr)    


        outfile.write('}\n')

        outfile.close()

        # Generate the image
        os.system("twopi -Tgif %s -o %s" % (self.dotfile, self.imgfile))
        # Generate imagemap code to accompany it
        os.system("twopi -Tcmap %s -o %s" % (self.dotfile, self.mapfile))
        
        # Record generation time
        self.generated = time.time()
        
    def getGraphDimensions(self):
        """Returns the dimensions of generated graph"""
        try:
            f = open(self.imgfile, 'rb')
            f.seek(6)
            list = []
            size = []
            for i in range(0, 4):
                list.append(ord(f.read(1)))
            size.append(list[0]+(list[1]<<8))
            size.append(list[2]+(list[3]<<8))
            f.close()
        except:
            log_warn("Could not read image to determine size: %s" % \
                    self.imgfile, sys.exc_info())
            return [0,0]
        return size
        
    def nodeAppend(self,nodename, link):
        """Adding all the nodes name into a list"""
        if self.nodes.has_key(nodename):
            tmpnode = self.nodes[nodename]
        else:
            log_error("Unknown node! %s" % nodename)
            raise ccs_status_error("Unknown node! %s" % nodename)
            return
         
        if not tmpnode.has_key("links"):
            tmpnode["links"] = []
        tmpnode["links"].append(link)
                
    def linkAppend(self,link, node1, node2):
        """Adding links between two nodes"""
        self.links[link] = {}
        self.links[link]["hosts"] = []
        self.links[link]["hosts"].append(node1)
        self.links[link]["hosts"].append(node2)
        self.links[link]["params"] = {}
        self.links[link]["params"]["color"] = "black"
        self.links[link]["params"]["style"] = "dashed"
        
        self.linkmap["%s %s" % (node1,node2)] = link
        self.linkmap["%s %s" % (node2,node1)] = link
       
    def testHost(self,IPlist):
        """Using fping to test whether a host is alive"""
        command = "fping -am  "
        command = command + " ".join(IPlist)
        
        result = os.popen("%s 2>/dev/null" % command).readlines()

        return len(result)
        
    def PingNodes(self):
        self.BreadthFirstPing(self.localhost)

        for nodename in self.nodes.keys():
            node = self.nodes[nodename]
            if node["type"] == "tmp":
                continue
            node["addr"] = node["ips"][0]
            node["url"] = "http://%s:%s/" % (node["addr"], self.port)
        
            if node["name"] == self.localhost:
                node["returnString"] = 'Localhost'
                node["color"] = 'yellow'
                node["style"] = 'filled'
                node["status"] = 'OK'
                node["reeachable"] = 10
                node["url"] = "/status/map" 
            else:
                if node["reachable"] > 0:
                    node["returnString"] = 'The host is UP'
                    node["status"] = 'OK'
                    node["color"] = "green"
                elif node["reachable"] == 0:
                    node["returnString"] = 'The host is DOWN'
                    node["status"] = "CRITICAL"
                    node["color"] = "red"
                    node["url"] = "javascript:void()"
                else:
                    node["returnString"] = 'The host is UNREACHABLE'
                    node["status"] = 'WARNING' 
                    node["color"] = "orange"
                    node["url"] = "javascript:void()"
             
    def GetNodeStatus(self):
        """Get node status information

        such as 'IP address', 'Host name', 'Conectivity UP/DOWN'.
        """
        
        list = {}
        # Filter out network nodes
        for name,node in self.nodes.items():
            if node["type"] == "tmp":
                continue
            list[name] = node
        
        return list

    def GenerateNetworkMap(self):
        """Test hosts and generate the map"""

        # Don't test more frequently than every minute
        if self.generated == -1 or (time.time() - self.generated) > 60:
            # Test all the nodes again
            self.PingNodes()
            # Draw the graph
            self.DrawGraph()

##############################################################################
# Initialisation
##############################################################################
networkmap = None
def ccs_init():
    
    registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
        "/status/interfaces", "Interface Status")
    registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
        "/status/routes", "Route Table")

    # Try and get values from the config file
    gateway = config_get("status", "gateway", None)
    root = config_get("status", "root", None)
    localnode = socket.gethostname()
    nodemap =  config_get("status", "nodemap", DEFAULT_NODEMAP_FILE)

    # Check that iwspy has MAC addresses
    checkiwspy()
        
    if (gateway == None or root == None or localnode == None):
        log_error("Missing required parameter for status module!")
        return
    
    # Try and initialise the map
    initialiseNetworkMap(nodemap, localnode, gateway, root)
    
def initialiseNetworkMap(nodemap, localnode, gateway, root):
    global networkmap
    
    log_info("Initialising status node map...")
    try:
        networkmap = nodeMap(localnode,gateway,root)
        networkmap.LoadFile(nodemap)
        networkmap.BuildAdjacency()
        networkmap.WalkToGateway()
        
        try:
            registerMenuItem(MENU_TOP, MENU_GROUP_GENERAL, \
                    "/status/map", "Status Map")
        except: 
            # Already loaded...
            pass
    except:
        log_error("Failed to initialise status node map...", sys.exc_info())
        return
    log_info("Status node map successfully loaded")

##############################################################################
# Content Pages
##############################################################################
def getStatusSummary():
    """Returns a short summary of the CPE status"""

    # Determine the default gateway from the route table and see if we
    # can ping it
    dg = getGatewayIP()
    if dg != "":
        # Got IP try and ping it
        command = "fping -am  %s" % dg
        result = os.popen("%s 2>/dev/null" % command).readlines()
        if len(result):
            gwstatus = "ok"
            gwtext = "OK - %s reachable" % dg
        else:
            gwstatus = "critical"
            gwtext = "CRITICAL - %s not reachable" % dg
    else:
        gwstatus = "critical"
        gwtext = "CRITICAL - No default gateway"
        
    output = """
<style>
TH:first-child {
    width: 14em;
}
</style>
"""
    output += "For more detailed status information use the links in the " \
            "menu on the left hand side of the page.<br /><br />"
    output += "<table>"
    output += "<tr>"
    output += "<th>Default Gateway:</th>"
    output += "<td class=\"status%s\">%s</td>" % \
            (gwstatus, gwtext)
    output += "</tr>"
    output += "</table><br />"

    try:
        ifaces = getInterfaceDetails()
        output += HTable(ifaces, ["name", "status"], ["Interface", "Status"])
    except:
        log_error("Failed to retrieve interface list", sys.exc_info())
        
    return output

def buildIfaceInfo(summary=False):
    """Builds the HTML interface information"""
 
    ifaces = getInterfaceDetails()
    
    output = ""
    
    for iface in ifaces:
        output += "<h2 style=\"margin-top: 15px;\">Interface '%s'</h2>" % \
                iface["name"]
        output += "<table>"
        output += "<tr>"
        output += "<th>IP Address:</th>"
        output += "<td width=\"25%%\">%s</td>" % iface["address"]
        output += "<th>Flags:</th><td>%s</td>" % ",".join(iface["flag_str"])
        output += "</tr>"
        output += "<tr>"
        output += "<th>MAC Address:</th>"
        output += "<td width=\"25%%\">%s</td>" % iface["mac"]
        output += "<th>Status:</th><td class=\"status%s\">%s</td>" % \
                (iface["status"].lower(), iface["statusdesc"])
        output += "</tr>"
        if iface["wireless"]:
            output += "<tr>"
            output += "<th>ESSID:</th>"
            output += "<td width=\"25%%\">%s</td>" % iface["essid"]
            output += "<th>Channel:</th><td>%s</td>" % iface["channel"]
            output += "</tr>"
            if iface["mode"] != iwtools.IW_MODE_MASTER:
                output += "<tr>"
                output += "<th>SNR:</th>"
                output += "<td width=\"25%%\">%s</td>" % iface["stats"]["snr"]
                output += "<th>Signal/Noise (dBm):</th><td>%s/%s</td>" % \
                        (iface["stats"]["signal"], \
                        iface["stats"]["noise"])
                output += "</tr>"
        output += "</table>"
        
        if iface["wireless"]:
            if iface["mode"] != iwtools.IW_MODE_MASTER:
                output += """<div id="ssmeter-%s" class="ssmeter">""" % \
                        iface["name"]
                output += getSSMeter(iface["stats"])
                output += "</div>"
                output += """<div style="clear: all;">&nbsp;</div>"""    
            else:
                for sta, stats in iface["stats"].items():
                    output += """<div id="ssmeter-%s" class="ssmeter">""" % \
                            iface["name"]
                    output += getSSMeter(stats, sta)
                    output += "</div>"
                    output += """<div style="clear: all;">&nbsp;</div>"""
            
    return output

@registerPage("/status/iface_ajax")
def ifacepage_ajax(request, method):

    try:
        ifacestr = buildIfaceInfo()
    except:
        (type, value, tb) = sys.exc_info()
        log_error("Failed to retreive interface list", (type, value, tb))
        request.send_response(500)
        request.end_headers()
        output = """<span class="error">Unable to retrieve interface list.""" \
                "<br /><br />%s</span>" % value
        request.wfile.write(output)
        return
    
    request.send_response(500)
    request.end_headers()
    request.wfile.write(ifacestr)

@registerPage("/status/interfaces")
def ifacepage(request, method):
    """Returns information about interfaces on this node"""
    
    snr_refresh_rate = config_get("status", "snr_refresh_rate", \
            DEFAULT_SNR_REFRESH_RATE)
    
    try:
        ifacestr = buildIfaceInfo()
    except:
        log_error("Error fetching interfaces!", sys.exc_info())
        returnErrorPage(request, "Unable to retrieve interface list!")
        return
        
    # Build interfaces information
    output = """<div class="content">
<style>
TH {
    width: 14em;
}
</style>
<div id="ifaceinfo">%s</div>
""" % ifacestr

    controlbox = """<div class="menu">
<h2>Update Status</h2><br />
<span id="updatestatus" class="statuscritical">Disabled</span><br /<br />
Every&nbsp;<input id="frequency" value="%s" onchange="javascript:updateFrequency();">&nbsp;sec(s)<br />
<br />
<a href="#" id="updatelink">Enable Updates</a>
</div><br />
""" % snr_refresh_rate

    returnPage(request, "Interface Status", output, menuadd=controlbox, \
            scripts=["/resources/ifacestatus.js"]) 

def getSSMeter(stats, sta=None):
    
    average_signal = config_get("status", "average_signal", \
            DEFAULT_AVERAGE_SIGNAL)
    good_signal = config_get("status", "good_signal", \
            DEFAULT_GOOD_SIGNAL)

    snr = stats["snr"]
    output = "<b>Signal Strength Meter"
    if sta is not None:
        output += " for station %s (SNR: %s, Signal/Noise (dBm) %s/%s)" % \
                (sta, snr, stats["signal"], stats["noise"])
    output += "</b><br />\n"

    for i in range(1,30):
        sclass = "none"
        eclass = ""
        if i <= snr:
            if i < average_signal:
                sclass="bad"
            elif i >= average_signal and i < good_signal:
                sclass="average"
            elif i >= good_signal:
                sclass="good"
        if i==29:
            eclass=" rightmost"
        output += """<div class="%s%s">&nbsp;</div>""" % (sclass, eclass)

    return output

@registerPage("/status/routes")
def routepage(request, method):
    """Returns the route table for this node"""
    
    try:
        routes = getRoutes()
    except:
        log_error("Error fetching routes!", sys.exc_info())
        returnErrorPage(request, "Unable to retrieve routing table!")
        return

    # Build the routes table
    output = """<div class="content">
<h2>CPE Routing Table</h2><br />
<br />
%s</div>""" % HTable(routes, \
            ["network", "netmask", "gateway", "flags", "metric", "iface"], \
            ["Destination", "Netmask", "Gateway", "Flags", "Metric", \
            "Interface"])

    returnPage(request, "Routing Table", output)    

@registerPage("/status/graph")
def statusgraph(request, method):
    """Returns the actual image data for the status graph"""
    global networkmap
    
    if networkmap is None:
        request.send_error(500, "Network status map not available!")
        return
    
    try:
        fd = open(networkmap.imgfile, "r")
        data = fd.read()
        fd.close()
    except:
        log_error("Unable to read graph file!", sys.exc_info())
        request.send_error(404, "Network status graph not available!")
        return

    request.send_response(200)
    request.send_header("Length", len(data))
    request.send_header("Content-Type", "image/gif")
    request.end_headers()
    request.wfile.write(data)

@registerEvent("statusMapRequested")
@registerPage("/status/map")
def statusmap(request, method):
    """Returns the HTML for the network status map display"""
    global networkmap
    
    # Fire an event to let any helpers update our map data before we continue
    triggerEvent(-1, "statusMapRequested")
    
    # End now if no map is available
    if networkmap is None:
        returnErrorPage(request, "Network status map not available!")
        return
   
    # Generate the map
    networkmap.GenerateNetworkMap()

    output = """<div class="content">"""
    
    # See if we need to resize the image to fit the browser window
    size = networkmap.getGraphDimensions()
    if size[0] > 900:
        width = 900
        height = size[1]* 900/size[0]
        fsnote = """<span class="note">Click graph to view fullsize """ \
                "image</span>"
    else:
        width = int(size[0]) 
        height = int(size[1])
        fsnote = ""
        
    # Display the image
    output += """<div id="statusgraph">
<a href="/status/graph">
<img width="%d" height="%d" src="/status/graph" alt="Status map not available" usemap="#map" />
</a><br />
%s
</div>""" % (width, height, fsnote)

    # Include the image map code
    output += networkmap.GetImageMap()

    # Tabular result information
    output += HTable(networkmap.GetNodeStatus(), ["name", "status", "addr", \
            "returnString"], ["Hostname", "Status", "IP Address", "Details"])

    output += "</div>"

    returnPage(request, "Status Map", output)

##############################################################################
# SNMP Information
##############################################################################
# Implement the basics of the IF-MIB
INTERFACES_MIB = (1,3,6,1,2,1,2)

# All interface properties
if_props = range(1,23)
# remove deprecated properties
if_props.remove(12)
if_props.remove(18)
if_props.remove(21)
# Register table
@registerTableOID(INTERFACES_MIB, if_props)
def ifaceinfo(parameter=None, index=None,Load=True):
    iface = None

    # Get list of interfaces
    ifaces, iface, ifindices = getIndexedDetails(index)

    if parameter==None and index==None:
        # Return list of interface indexes
        return ifindices

    # Check there is an interface object
    if iface is None:
        log_error("Invalid interface index passed to ifaceinfo")
        return None
    
    # Return the appropriate parameter
    if parameter==1:
        return snmp.Integer(index)
    elif parameter==2:
        return getIfaceDescription(iface)
    elif parameter==3:
        return getIfaceDescription(iface, True)
    elif parameter==4:
        return snmp.Integer(iface["mtu"])
    elif parameter==5:
        return getIfaceSpeed(iface)
    elif parameter==6:
        # Return bytes
        mac = ""
        for part in iface["mac"].split(":"):
            mac += chr(int(part, 16))
        return snmp.OctetString(mac)
    elif parameter==7 or parameter==8:
        if iface["up"]:
            return snmp.Integer(1)
        else:
            return snmp.Integer(2)
    elif parameter==9:
        return snmp.TimeTicks(0)
    elif parameter==10:
        return snmp.Counter(int(iface["rcv_stats"]["bytes"]))
    elif parameter==11:
        return snmp.Counter(int(iface["rcv_stats"]["packets"]))
    elif parameter==13:
        return snmp.Counter(int(iface["rcv_stats"]["drop"]))
    elif parameter==14:
        return snmp.Counter(int(iface["rcv_stats"]["errs"]))
    elif parameter==15:
        return snmp.Counter(0)
    elif parameter==16:
        return snmp.Counter(int(iface["tx_stats"]["bytes"]))
    elif parameter==17:
        return snmp.Counter(int(iface["tx_stats"]["packets"]))
    elif parameter==19:
        return snmp.Counter(int(iface["tx_stats"]["drop"]))
    elif parameter==20:
        return snmp.Counter(int(iface["tx_stats"]["errs"]))       
    elif parameter==22:
        return snmp.ObjectIdentifier("0.0")
    
    return None

def getIfaceDescription(iface, numeric=False):
    if iface["wireless"]:
        # Return 6 (csmacd Ethernet for normal wireless interfaces as the 
        # spec says it should be used for all ethernet-like interfaces
        return numeric and snmp.Integer(6) or \
                snmp.OctetString(iface["name"])
    elif iface["name"].startswith("lo"):
        return numeric and snmp.Integer(24) or snmp.OctetString(iface["name"])
    elif iface["name"].startswith("dummy"):
        return numeric and snmp.Integer(24) or \
                snmp.OctetString(iface["name"])
    elif iface["name"].endswith("-base") or iface["name"].startswith("wifi"):
        return numeric and snmp.Integer(71) or snmp.OctetString(iface["name"])
    elif iface["name"].startswith("sit") or iface["name"].startswith("tun"):
        return numeric and snmp.Integer(131) or \
                snmp.OctetString(iface["name"])
    elif iface["name"].startswith("ppp"):
        return numeric and snmp.Integer(23) or \
                snmp.OctetString(iface["name"])
    else:
        return numeric and snmp.Integer(6) or \
                snmp.OctetString(iface["name"])

def getIfaceSpeed(iface):
    # This function is pretty hax. But it seems netSNMP does the same thing.
    if iface["wireless"]:
        # Pretend all wireless is 10Mbps
        return snmp.Gauge(10000000)
    elif iface["name"].startswith("lo"):
        return snmp.Gauge(10000000)
    elif iface["name"].startswith("dummy"):
        return snmp.Gauge(10000000)
    elif iface["name"].endswith("-base") or iface["name"].startswith("wifi"):
        # Base interfaces don't transfer traffic themselves...
        return snmp.Gauge(0)
    elif iface["name"].startswith("sit") or iface["name"].startswith("tun"):
        # Bleh, 10Mbps?
        return snmp.Gauge(10000000)
    elif iface["name"].startswith("ppp"):
        # Bleh, 10Mbps?
        return snmp.Gauge(10000000)
    else:
        # Bleh, 10Mbps?
        return snmp.Gauge(10000000)


# Implement the basics of the CRCnet-MIB
CRCNET_WIFACES_MIB = (1,3,6,1,4,1,15120,1,1)

# All wireless interface properties
if_props = range(1,14)
# Register table
@registerTableOID(CRCNET_WIFACES_MIB, if_props)
def wifaceinfo(parameter=None, index=None, Load=True):
    iface = None

    # Get list of interfaces
    ifaces, iface, ifindices = getIndexedDetails(index, True)        
    if parameter==None and index==None:
        # Return list of interface indexes
        return ifindices

    # Check there is an interface object
    if iface is None:
        log_error("Invalid interface index passed to wifaceinfo")
        return None
    
    # Return the appropriate parameter
    if parameter==1:
        return snmp.Integer(index)
    elif parameter==2:
        return getIfaceDescription(iface)
    elif parameter==3:
        # Return bytes
        mac = ""
        for part in iface["mac"].split(":"):
            mac += chr(int(part, 16))
        return snmp.OctetString(mac)
    elif parameter==4:
        try:
            return snmp.IpAddress(iface["address"].split("/")[0])
        except:
            return snmp.IpAddress("0.0.0.0")
    elif parameter==5:
        if "snr" in iface["stats"].keys():
            return snmp.Integer(iface["stats"]["snr"])
        else:
            return snmp.Integer(0)
    elif parameter==6:
        if "signal" in iface["stats"].keys():
            return snmp.Integer(iface["stats"]["signal"])
        else:
            return snmp.Integer(0)
    elif parameter==7:
        if "noise" in iface["stats"].keys():
            return snmp.Integer(iface["stats"]["noise"])
        else:
            return snmp.Integer(0)
    elif parameter==8:
        return snmp.Integer(iface["channel"])
    elif parameter==9:
        return snmp.OctetString(iface["essid"])
    elif parameter==10:
        try:
            return snmp.Integer(int(iface["config"]["bitrate"]["value"]))
        except:
            return snmp.Integer(0)
    elif parameter==11:
        return snmp.Integer(iface["clients"])
    elif parameter==12:
        return snmp.Integer(iface["CRC"])
    elif parameter==13:
        return snmp.Integer(iface["PHY"])        
    return None

def dorate(lines, rate, parameter):    
    """This function processes the lines in a ratestats file in proc
       and returns requested data from it"""
    entries = []
    interface = None

    #Process lines
    for line in lines:
        line = line.strip('\n')
        if len(line.split(':')) > 1:
            if interface:
                entries.append(interface)
            mac = line
            interface = {}
            interface["mac"] = mac
            idata = []
            interface["data"] = idata
        elif line[:4] == "rate":
            pass
        else:
            parts = line.split('\t')
            crate = {}
            crate["rate"] = parts[0].strip(' *')    
            crate["tt"] = parts[1].strip(' ')    
            crate["perfect"] = parts[2].strip(' ')    
            crate["failed"] = parts[3].strip(' ')    
            crate["pkts"] = parts[4].strip(' ')    
            crate["avg_tries"] = parts[5].strip(' ')    
            crate["last_tx"] = parts[6].strip(' ')    
            if line[0] == '*':
                interface["crate"] = crate["rate"]
            idata.append(crate)
    if interface:
        entries.append(interface)

    #Find the relevent data
    found = None    
    for data in entries[0]["data"]:
        rate=float(rate)
        if rate==5.0:
            rate=5.5
        if float(data["rate"]) == rate:
            found = data
            break
    #Return results            
    if not found:
         return snmp.Integer(0)
    if parameter == 1:    
        return snmp.Integer(found["pkts"])
    elif parameter==2:
        return snmp.Integer(found["failed"])
    elif parameter==3:
        return snmp.Integer(float(found["avg_tries"])*100)
    else:
        return snmp.Integer(22)
    
CRCNET_MadWifi_MIB = (1,3,6,1,4,1,15120,1,1,2,1,14)
def getNextMadwifiOID(parameter, psize, rate, ifindex, ifindexes):
    """Returns the next OID in the madwifi table"""
    rates = [1, 2, 5, 6, 9, 11, 12, 18, 24, 36, 48, 54]
    psizes = [250, 1600, 3000]

    # Increment index
    try:
        newifindex = ifindexes[ifindexes.index(ifindex)+1]
    except:
        if psize == psizes[-1] and rate == rates[-1]:
            # END-OF-MIB
            return None
        newifindex = ifindexes[0]

    # Increment rate if we wrapped back to the first interface
    newrate = rate
    if newifindex == ifindexes[0] and newifindex != ifindex:
        try:
            newrate = rates[rates.index(rate)+1]
        except IndexError:
            newrate = 1
        
    # If rate wrapped to one, increment the packet size
    newpsize = psize
    if newrate == 1 and rate != 1:
        try:
            newpsize = psizes[psizes.index(psize)+1]
        except IndexError:
            newpsize = 250

    # Return the new OID
    return CRCNET_MadWifi_MIB + (parameter, newpsize, newrate, newifindex)

# Register table
@registerDynamicOID(CRCNET_MadWifi_MIB)
def madwifiRateInfo(oid, getNext, Load=True):
    """Provides a table with information about madwifi's rate control"""
    
    doneoid = False
    # Strip off the base of the oid
    base = oid[:len(CRCNET_MadWifi_MIB)]
    if base != CRCNET_MadWifi_MIB:
        log_warn("Invalid base OID passed to xx: %s" % str(oid))
        return None
    
    parts = oid[len(CRCNET_MadWifi_MIB):]
    if len(parts) != 4:
        # Base OID specified only
        part = -1
        if len(parts)==0:
            if not getNext:
                # Invalid OID
                log_warn("Invalid OID passed to xx: %s" % str(oid))
                return None
        else:
            part = parts[0]
        # Assume its the first request in a getNext stream
        parameter = 1
        psize = 250
        rate = 1
        ifindex = part
    else:
        parameter = parts[0]
        psize = parts[1]
        rate = parts[2]
        ifindex = parts[3]
        doneoid = True
            
    # Get list of interfaces
    iface = None
    ifaces, iface, ifindices = getIndexedDetails(ifindex, True)      
    if not iface:
        return None
    if ifindex == -1:
        ifindex = iface["ifindex"]
        
    # If we are on a get next stream get the next oid
    if doneoid and getNext:
        oid = getNextMadwifiOID(parameter, psize, rate, ifindex, ifindices)
        if oid == None:
            return None
        parameter, psize, rate, ifindex = oid[len(CRCNET_MadWifi_MIB):]
    else:
        oid = CRCNET_MadWifi_MIB + (parameter, psize, rate, ifindex)

    # Attempt to retrive stats, on a fail move to the next interface    
    while True:
        try:
            lines = open("/proc/net/madwifi/%s/ratestats_%s" % (iface["name"],\
                psize),"r").readlines()
            break
        except:
            if getNext:
                oid = getNextMadwifiOID(parameter, psize, rate, ifindex, 
                        ifindices)
                if oid == None:
                    return None
                parameter, psize, rate, ifindex = oid[len(CRCNET_MadWifi_MIB):]
                for tiface in ifaces:
                    if tiface["ifindex"] == ifindex:
                        iface = tiface
            else:
                return None

    return  (oid, dorate(lines, rate, parameter))
    
# Implement the ipAddrTable portion of the IP-MIB
IP_ADDRS_MIB = (1,3,6,1,2,1,4,20,1)
@registerDynamicOID(IP_ADDRS_MIB)
def ipaddrs(oid, getNext):
    
    iface = None
    # Get list of interfaces
    try:
        ifaces = getInterfaceDetails(True)
    except:
        log_error("Error fetching wireless interfaces for SNMP!", \
                sys.exc_info())
        ifaces = []
    
    # Indexes
    ifaces_ip = {} 
    for tiface in ifaces:
        if tiface["address"] != "":
            ifaces_ip[cidrToIP(tiface["address"])] = tiface
    indexes = ifaces_ip.keys()
    indexes.sort(ipcmp)
    
    # Strip off the base of the oid
    base = oid[:len(IP_ADDRS_MIB)]
    if base != IP_ADDRS_MIB:
        log_warn("Invalid base OID passed to ipaddr: %s" % str(oid))
        return None
    
    parts = oid[len(IP_ADDRS_MIB):]
    if len(parts) != 5:
        # Base OID specified only
        part = 1
        if len(parts)==0:
            if not getNext:
                # Invalid OID
                log_warn("Invalid OID passed to ipaddr: %s" % str(oid))
                return None
        else:
            part = parts[0]
        # Assume its the first request in a getNext stream
        ip = indexes[0]
        iptuple = tuple(map(int, ip.split(".")))
        oid = IP_ADDRS_MIB + (part,) + iptuple
    else:
        # Extract the string formatted IP from the request
        ip = "%s.%s.%s.%s" % (parts[1], parts[2], parts[3], parts[4])
        if ip not in ifaces_ip.keys():
            log_error("Request for IP details for non-existant " \
                    "interface: %s" % ip)
            return None
        part = parts[0]
    
        if getNext:
            # Advance
            newIdx = bisect(indexes, ip, cmpfunc=ipcmp)
            if newIdx == len(indexes):
                if part>=5:
                    # End of MIB
                    return None
                part+=1
                ip = indexes[0]
            else:
                ip = indexes[newIdx]
            # New oid
            iptuple = tuple(map(int, ip.split(".")))
            oid = IP_ADDRS_MIB + (part,) + iptuple
    
    # Decide what parameter we are dealing with
    iface = ifaces_ip[ip]
    if part == 1:
        # IP address
        return (oid, snmp.IpAddress(ip))
    elif part == 2:
        # Interface index
        return (oid, snmp.Integer(iface["ifindex"]))
    elif part == 3:
        # Netmask
        return (oid, snmp.IpAddress(cidrToNetmaskS(iface["address"])))
    elif part == 4:
        # Broadcast
        return (oid, snmp.Integer(cidrToBroadcast(iface["address"])&1))
    elif part == 5:
        # Largest Reassembly Size
        return (oid, snmp.Integer(65535))

    return None

# Provide information on the current configuration state of the host
CCS_REVISION_MIB = (1,3,6,1,4,1,15120,1,3,1)
CCS_REVISION_FILE = "/var/lib/ccsd/ccs-revision"
@registerDynamicOID(CCS_REVISION_MIB)
def ccsrevision(oid, getNext):
    
    # We return a single value, no getNext
    if getNext:
        return None

    # Check the incoming OID
    if oid != CCS_REVISION_MIB:
        log_warn("Invalid OID passed to ccsrevision: %s" % str(oid))
        return None

    # Return empty string if there is no revisino information
    if not os.path.exists(CCS_REVISION_FILE):
        return (oid, snmp.OctetString(""))

    try:
        # Retrieve the revision information
        revision = open(CCS_REVISION_FILE).read().strip()
        return (oid, snmp.OctetString(revision))
    except:
        log_error("Error retrieving configuration revision", sys.exc_info())
        return (oid, snmp.OctetString(""))
