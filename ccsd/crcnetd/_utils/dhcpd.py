#!/usr/bin/env python
# Copyright (C) 2006  Matt Brown <matt@mattb.net.nz>
#
# dhcpd.conf Python wrapper
#
# Author:       Matt Brown <matt@mattb.net.nz>
# Version:      $Id$
#
# This script is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation.
#
# This script is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this script; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import os

MODE_PASSTHRU=0
MODE_SUBNET=1
MODE_HOST=2

class dhcpd_conf:

    def __init__(self, inputfile="/etc/dhcp3/dhcpd.conf"):

        self._content = []
        self._subnets = {}
        self._hosts = {}
        self._filename = inputfile
        
        fp = open(inputfile, "r")
        lines = fp.readlines()
        fp.close()
        
        mode = MODE_PASSTHRU
        subnet = None
        host = None
        for line in lines:
            if mode == MODE_PASSTHRU:
                # Pass through all lines until we come to an subnet/host stanza
                if line.startswith("subnet"):
                    # Start an subnet stanza
                    parts = line.split()
                    if len(parts) != 5:
                        raise Exception("Bogus subnet stanza line: %s" % line)
                    subnet = {}
                    subnet["network"] = parts[1]
                    subnet["netmask"] = parts[3]
                    subnet["options"] = {}
                    subnet["keys"] = []
                    
                    # Go into subnet parsing mode
                    comment = []
                    mode = MODE_SUBNET
                    continue
                elif line.startswith("host"):
                    # Start a host stanza
                    parts = line.split()
                    if len(parts) != 3:
                        raise Exception("Bogus host stanza line: %s" % line)
                    host = {}
                    host["name"] = parts[1]
                    host["options"] = {}
                    host["keys"] = []

                    # Go into host parsing mode
                    comment = []
                    mode = MODE_HOST
                    continue

                # Just normal boring old content
                self._content.append(line)
            elif mode == MODE_SUBNET:
                # Look for an ending brace
                if line.strip().startswith("}"):
                    # End of subnet stanza
                    self._content.append(subnet)
                    self._subnets[subnet["network"]] = len(self._content)-1
                    if comment != []:
                        self._content.append("".join(comment))
                        comment = []
                    subnet = None
                    # Back to passthru mode
                    mode = MODE_PASSTHRU
                    continue
    
                # Store comments/blank lines to attach to the next option
                if line.strip().startswith("#") or line.strip()=="":
                    comment.append(line)
                    continue
                
                # Interface Option
                parts = line.strip().strip(";").split()
                if len(parts) < 2:
                    raise Exception("Bogus subnet option line: %s" % line)
                if parts[0] != "option":
                    subnet[parts[0]] = (comment, " ".join(parts[1:]))
                    subnet["keys"].append(parts[0])
                else:
                    if len(parts) < 3:
                        raise Exception("Bogus subnet option line: %s" % line)
                    subnet["options"][parts[1]] = (comment, \
                            " ".join(parts[2:]))
                    subnet["keys"].append("option %s" % parts[1])
                comment = []
            elif mode == MODE_HOST:
                # Look for an ending brance
                if line.strip().startswith("}"):
                    if "mac" not in host.keys():
                        raise Exception("Invalid host stanza. No hardware " \
                                "ethernet address specified!")
                    # End of host stanza
                    self._content.append(host)
                    self._hosts[host["mac"][1]] = len(self._content)-1
                    if comment != []:
                        self._content.append("".join(comment))
                        comment = []
                    host = None
                    # Back to passthru mode
                    mode = MODE_PASSTHRU
                    continue
                
                # Store comments/blank lines to attach to the next option
                if line.strip().startswith("#") or line.strip()=="":
                    comment.append(line)
                    continue
                
                # Host Option
                parts = line.strip().strip(";").split()
                if len(parts) < 2:
                    raise Exception("Bogus host option line: %s" % line)
                if parts[0] != "option":
                    if parts[0] == "hardware" and parts[1] == "ethernet":
                        host["mac"] = (comment, parts[2])
                        host["keys"].append("mac")
                    else:
                        host[parts[0]] = (comment, " ".join(parts[1:]))
                        host["keys"].append(parts[0])
                else:
                    if len(parts) < 3:
                        raise Exception("Bogus host option line: %s" % line)
                    host["options"][parts[1]] = (comment, \
                            " ".join(parts[2:]))
                    host["keys"].append("option %s" % parts[1])
                comment = []

            else:
                raise Exception("Invalid state while parsing subnets!")
            
        if subnet != None:
            # Finished parsing without seeing the end of a subnet
            raise Exception("Expected end of subnet not found!")
        if host != None:
            # Finishing parsing without seeing the end of a subnet
            raise Exception("Expected end of host not found!")
        
    def getSubnets(self):
        return self._subnets.keys()
    def getHosts(self):
        return self._hosts.keys()
    
    def _getPublicSubnetObject(self, subnet):
        """Strips the private data from the subnet object"""
        subnet2 = {"network":subnet["network"], "netmask":subnet["netmask"], \
                "options":{}}
        # Remove hidden information to return a nice clean object
        for key in subnet["keys"]:
            if key.startswith("option"):
                parts = key.split(" ")
                subnet2["options"][parts[1]] = subnet["options"][parts[1]][1]
            else:
                subnet2[key] = subnet[key][1]
        return subnet2
    def _getPublicHostObject(self, host):
        """Strips the private data from the host object"""
        host2 = {"name":host["name"], "mac":host["mac"]}
        # Remove hidden information to return a nice clean object
        for key in host["keys"]:
            if key.startswith("option"):
                parts = key.split(" ")
                host2["options"][parts[1]] = host["options"][parts[1]][1]
            else:
                host2[key] = host[key][1]
        return host2
        
    def keys(self): 
        keys = self._subnets.keys()
        keys.extend(self._hosts.keys())
        return keys
    
    def values(self):
        vals = []
        for key,pos in self._subnets.items():
            vals.append(self._getPublicSubnetObject(self._content[pos]))
        for key,pos in self._hosts.items():
            vals.append(self._getPublicHostObject(self._content[pos]))
        return vals
    
    def items(self):
        return zip(self.keys(), self.values())

    def __getitem__(self, key):
        if type(key) != type(""):
            return None
        if key.find(":") != -1:
            # Mac address ==  host
            if key not in self._hosts.keys():
                return None
            return self._getPublicHostObject(self._content[self._hosts[key]])
        else:
            # Subnet
            if key not in self._subnets.keys():
                return None
            return self._getPublicSubnetObject( \
                    self._content[self._subnets[key]])
    
    def __setitem__(self, key, item):

        if type(item) != type({}):
            raise TypeError("Invalid value for %s!" % key)

        if "mac" in item.keys():
            # Mac address  = host
            return self._setHost(key, item)
        else:
            return self._setSubnet(key, item)
        
    def __delitem__(self, key):
        if type(key) != type(""):
            return ""
        if key.find(":") != -1:
            # Mac address ==  host
            list = self._hosts
        else:
            # Subnet
            list = self._subnets
        # Remove the item
        del self._content[list[key]]
        # Reindex the rest of the list
        for mac, val in self._hosts.items():
            if val > list[key]:
                self._hosts[mac]=val-1
        for net, val in self._subnets.items():
            if val > list[key]:
                self._subnets[net]=val-1
        # Remove the item from its index list
        del list[key]

    def _setHost(self, key, item):
        if "mac" not in item.keys():
            raise TypeError("Host object missing critical values!")
        
        if key not in self._hosts.keys():
            # New subnet - Build new internal object
            item["keys"] = []
            for ikey,val in item.items():
                if ikey == "name" or ikey == "keys" or ikey == "comment":
                    continue
                if ikey == "options":
                    for okey,oval in item[ikey].items():
                        item[ikey][okey] = ([], oval)
                        item["keys"].append("option %s" % okey)
                else:
                    item[ikey] = ([], val)
                    item["keys"].append(ikey)
            # Store it
            self._content.append("\n")
            if "comment" in item.keys():
                self._content.append("# %s\n" % item["comment"])
            self._content.append(item)
            self._hosts[item["mac"][1]] = len(self._content)-1
            return

        # Check for changes to the object
        newitem = self._content[self._hosts[key]]
        keys = []
        for ikey,val in item.items():
            if ikey == "comment":
                continue
            if ikey == "name":
                newitem[ikey] = val
                continue
            if ikey == "options":
                for okey,oval in item["options"].items():
                    if "option %s" % okey in newitem["keys"]:
                        newitem[ikey][okey] = (newitem[ikey][okey][0], val)
                    else:
                        newitem[ikey][okey] = ([], val)
                        newitem["keys"].append("option %s" % okey)
                    keys.append("option %s" % okey)
                continue
            if ikey in newitem["keys"]:
                newitem[ikey] = (newitem[ikey][0], val)
            else:
                newitem[ikey] = ([], val)
                newitem["keys"].append(ikey)
            keys.append(ikey)
        for ikey in newitem["keys"]:
            if ikey not in keys:
                if ikey.startswith("option"):
                    parts = ikey.split(" ")
                    del newitem[ikey][parts[1]]
                else:
                    del newitem[ikey]
            
        # Store the subnet object
        self._content[self._hosts[key]] = newitem
        
    def _setSubnet(self, key, item):
        if "network" not in item.keys() or "netmask" not in item.keys():
            raise TypeError("Subnet object missing critical values!")
        
        if key not in self._subnets.keys():
            # New subnet - Build new internal object
            item["keys"] = []
            for ikey,val in item.items():
                if ikey == "network" or ikey == "netmask" or ikey == "keys":
                    continue
                if ikey == "options":
                    for okey,oval in item[ikey].items():
                        item[ikey][okey] = ([], oval)
                        item["keys"].append("option %s" % okey)
                else:
                    item[ikey] = ([], val)
                    item["keys"].append(ikey)
            # Store it
            self._content.append("\n")
            self._content.append(item)
            self._subnets[item["network"]] = len(self._content)-1
            return

        # Check for changes to the object
        newitem = self._content[self._subnets[key]]
        keys = []
        for ikey,val in item.items():
            if ikey == "network" or ikey == "netmask":
                newitem[ikey] = val
                continue
            if ikey == "options":
                for okey,oval in item["options"].items():
                    if "option %s" % okey in newitem["keys"]:
                        newitem[ikey][okey] = (newitem[ikey][okey][0], val)
                    else:
                        newitem[ikey][okey] = ([], val)
                        newitem["keys"].append("option %s" % okey)
                    keys.append("option %s" % okey)
                continue
            if ikey in newitem["keys"]:
                newitem[ikey] = (newitem[ikey][0], val)
            else:
                newitem[ikey] = ([], val)
                newitem["keys"].append(ikey)
            keys.append(ikey)
        for ikey in newitem["keys"]:
            if ikey not in keys:
                if ikey.startswith("option"):
                    parts = ikey.split(" ")
                    del newitem[ikey][parts[1]]
                else:
                    del newitem[ikey]
            
        # Store the subnet object
        self._content[self._subnets[key]] = newitem

    def __repr__(self):
        
        str = ""

        for line in self._content:
            if type(line) != type({}):
                str += line
                continue
            if "mac" in line.keys():
                # Got a host object, unpack
                str += "host %s {\n" % line["name"]
                keys = line["keys"]
                for name in keys:
                    if name.startswith("option"):
                        parts = name.split(" ")
                        val = line["options"][parts[1]]
                        name = "option %s" % parts[1]
                    else:
                        val = line[name]
                    if type(val) != type(()):
                        # Skip string members, (network, netmask)
                        continue
                    if name == "mac":
                        name = "hardware ethernet"
                    # Write out each subnet option
                    comment, value = val
                    if not value.endswith(";"): value += ";"
                    # With comments first if appropriate
                    for cline in comment: str += cline
                    # Then the meat
                    str += "\t%s %s\n" % (name, value)
                str += "}\n"
            else:
                # Got a subnet object, unpack
                str += "subnet %s netmask %s {\n" % \
                        (line["network"], line["netmask"])
                keys = line["keys"]
                for name in keys:
                    if name.startswith("option"):
                        parts = name.split(" ")
                        val = line["options"][parts[1]]
                        name = "option %s" % parts[1]
                    else:
                        val = line[name]
                    if type(val) != type(()):
                        # Skip string members, (network, netmask)
                        continue
                    # Write out each subnet option
                    comment, value = val
                    if not value.endswith(";"): value += ";"
                    # With comments first if appropriate
                    for cline in comment: str += cline
                    # Then the meat
                    str += "\t%s %s\n" % (name, value)
                str += "}\n"

        return str

    def write(self):
        """Writes back to the file that we read from"""

        fp = open("%s.tmp" % self._filename, "w")
        fp.write("%s" % self)
        fp.close()
        os.system("mv %s.tmp %s" % (self._filename, self._filename))

def nonmodtest():
    
    # Tests that it can read/parse and write out without causing change
    subnets = dhcpd_conf()
    (cin, cout) = os.popen2("diff -uw /etc/dhcp3/dhcpd.conf -", "w")
    cin.write("%s" % subnets)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) != 0:
        print "Non-modification test: FAILED"
        print "".join(output)
    else:
        print "Non-modification test: OK"
    
def addsubnettest():
    
    # Tests that it can add a new subnet ok
    subnets = dhcpd_conf()
    subnets["192.168.0.0"] = {"network":"192.168.0.0", \
            "netmask":"255.255.255.0", "range":"192.168.0.128 192.168.0.253", \
            "options":{"routers":"192.168.0.1"}}
    (cin, cout) = os.popen2("diff -uw /etc/dhcp3/dhcpd.conf -", "w")
    cin.write("%s" % subnets)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Add subnet test: FAILED"
    else:
        print "Add subnet test: Maybe OK - verify diff manually" 
        print "Add subnet test:          - should be a new 192.168.0.0 subnet"
        print "".join(output)
    
def addhosttest():
    
    # Tests that it can add a new host ok
    dhcp = dhcpd_conf()
    dhcp["00:02:2d:51:a1:b1"] = {"name":"matt", "mac":"00:02:2d:51:a1:b1", \
            "fixed-address":"10.230.2.2", \
            "options":{"routers":"192.168.0.1"}, "comment":"New Host"}
    (cin, cout) = os.popen2("diff -uw /etc/dhcp3/dhcpd.conf -", "w")
    cin.write("%s" % dhcp)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Add host test: FAILED"
    else:
        print "Add host test: Maybe OK - verify diff manually" 
        print "Add host test:          - should be a new host at 10.230.2.2"
        print "".join(output)
        
def deltest():
    
    # Tests that it can remove things
    subnets = dhcpd_conf()
    for name in subnets.keys():
        del subnets[name]
    (cin, cout) = os.popen2("diff -uw /etc/dhcp3/dhcpd.conf -", "w")
    cin.write("%s" % subnets)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Deletion test: FAILED"
    else:
        print "Deletion test: Maybe OK - verify diff manually" 
        print "Deletion test:          - should be no subnet or host entries"
        print "".join(output)

if __name__ == "__main__":

    print "Running Test Suite"
    print "=================="
    
    # Tests that it can read/parse and write out without causing change
    nonmodtest()
    addsubnettest()
    addhosttest()
    deltest()
