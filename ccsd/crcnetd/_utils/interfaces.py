#!/usr/bin/env python
# Copyright (C) 2006  Matt Brown <matt@mattb.net.nz>
#
# /etc/network/interfaces Python wrapper
#
# CRCnet Monitor Status Information Display
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
import sys

MODE_PASSTHRU=0
MODE_IFACE=1

class debian_interfaces:

    def __init__(self, inputfile="/etc/network/interfaces"):

        self._content = []
        self._ifnames = {}
        self._filename = inputfile
        
        fp = open(inputfile, "r")
        lines = fp.readlines()
        fp.close()
        
        mode = MODE_PASSTHRU
        iface = None
        autos = {}
        for line in lines:
            if mode == MODE_PASSTHRU:
                # Pass through all lines until we come to an iface stanza
                if not line.strip().startswith("iface"):
                    self._content.append(line)
                    if line.strip().startswith("auto"):
                        autos[line.split()[1]] = len(self._content)-1
                    continue
                
                # Start an iface stanza
                parts = line.split()
                if len(parts) != 4:
                    raise Exception("Bogus iface stanza line: %s" % line)
                iface = {}
                iface["name"] = parts[1]
                iface["family"] = parts[2]
                iface["method"] = parts[3]
                iface["auto"] = (False, -1)
                iface["keys"] = []
                
                # Go into iface parsing mode
                comment = []
                mode = MODE_IFACE
                continue
            elif mode == MODE_IFACE:
                # Check for the start of another stanza
                if line.strip().startswith("mapping") or \
                        line.strip().startswith("auto") or \
                        line.strip().startswith("allow-"):
                    # End of iface stanza
                    self._content.append(iface)
                    self._ifnames[iface["name"]] = len(self._content)-1
                    if comment != []:
                        self._content.append("".join(comment))
                        comment = []
                    iface = None
                    # Append line, back to passthru mode
                    self._content.append(line)
                    if line.startswith("auto"):
                        autos[line.split()[1]] = len(self._content)-1
                    mode = MODE_PASSTHRU
                    continue
                elif line.strip().startswith("iface"):
                    # Back to back iface stanza's!!
                    self._content.append(iface)
                    self._ifnames[iface["name"]] = len(self._content)-1
                    if comment != []:
                        self._content.append("".join(comment))
                        comment = []
                    iface = None
                    # Start an iface stanza
                    parts = line.split()
                    if len(parts) != 4:
                        raise Exception("Bogus iface stanza line: %s" % \
                                line)
                    iface = {}
                    iface["name"] = parts[1]
                    iface["family"] = parts[2]
                    iface["method"] = parts[3]
                    iface["auto"] = (False, -1)
                    iface["keys"] = []
                    comment = []
                    continue
    
                # Store comments/blank lines to attach to the next option
                if line.strip().startswith("#") or line.strip()=="":
                    comment.append(line)
                    continue
                
                # Interface Option
                parts = line.split()
                if len(parts) < 2:
                    raise Exception("Bogus interface option line: %s" % line)
                iface[parts[0]] = (comment, " ".join(parts[1:]))
                iface["keys"].append(parts[0])
                comment = []
            else:
                raise Exception("Invalid state while parsing interfaces!")
            
        if iface != None:
            # Finished parsing in an interface
            self._content.append(iface)
            self._ifnames[iface["name"]] = len(self._content)-1
            if comment != []:
                self._content.append("".join(comment))

        # Set the auto property on those interfaces an auto line was 
        # found for
        for iface, line in autos.items():
            if iface in self._ifnames.keys():
                self._content[self._ifnames[iface]]["auto"] = (True, line)
            
    def getInterfaceNames(self):
        return self._ifnames.keys()

    def _getPublicIfaceObject(self, iface):
        """Strips the private data from the iface object"""
        iface2 = {"name":iface["name"], "family":iface["family"], \
                "method":iface["method"], "auto":iface["auto"][0] }
        # Remove hidden information to return a nice clean object
        for key in iface["keys"]:
            iface2[key] = iface[key][1]
        return iface2
    
    def keys(self): return self._ifnames.keys()
    
    def values(self):
        vals = []
        for key,pos in self._ifnames.items():
            t = self._content[self._ifnames[key]]
            vals.append(self._getPublicIfaceObject(t))
        return vals
    
    def items(self):
        return zip(self.keys(), self.values())

    def __getitem__(self, key):
        if key not in self._ifnames.keys():
            return None
        return self._getPublicIfaceObject(self._content[self._ifnames[key]])
    
    def __setitem__(self, key, item):

        if type(item) != type({}):
            raise TypeError("Invalid value for %s!" % key)
        if "name" not in item.keys() or "family" not in item.keys() or \
                "method" not in item.keys():
            raise TypeError("Interface object missing critical values!")
        
        if key not in self._ifnames:
            # New interface
            if item["name"] in self._ifnames.keys():
                raise TypeError("Duplicate interface name!")
            # Build new internal interface object
            if "auto" in item.keys():
                item["auto"] = (item["auto"], -1)
            else:
                item["auto"] = (False, -1)
            item["keys"] = []
            for ikey,val in item.items():
                if ikey in ["name", "family", "method", "keys", "auto"]:
                    continue
                item[ikey] = ([], val)
                item["keys"].append(ikey)
            # Store it
            self._content.append("\n")
            self._content.append(item)
            self._ifnames[item["name"]] = len(self._content)-1
            return

        # Check for changes to the object
        newitem = self._content[self._ifnames[key]]
        keys = []
        for ikey,val in item.items():
            if ikey in ["name", "family", "method"]:
                newitem[ikey] = val
                continue
            if ikey == "auto":
                newitem[ikey] = (item[ikey], newitem[ikey][1])
                continue
            if ikey in newitem["keys"]:
                newitem[ikey] = (newitem[ikey][0], val)
            else:
                newitem[ikey] = ([], val)
                newitem["keys"].append(ikey)
            keys.append(ikey)
        for ikey in newitem["keys"]:
            if ikey not in keys:
                del newitem[ikey]
                newitem["keys"].remove(ikey)
            
        # Update the interface object
        self._content[self._ifnames[key]] = newitem
        
    def __delitem__(self, key):
        if key not in self._ifnames.keys():
            return None
        del self._content[self._ifnames[key]]
        for ifname, val in self._ifnames.items():
            if val > self._ifnames[key]:
                self._ifnames[ifname]=val-1
        del self._ifnames[key]

    def __repr__(self):
        
        str = ""

        for line in self._content:
            if type(line) != type({}):
                if line.startswith("auto"):
                    parts = line.split()
                    if parts[1] in self._ifnames.keys():
                        iface = self._content[self._ifnames[parts[1]]]
                        if not iface["auto"][0]:
                            # Skip auto if it has been disabled on the iface
                            continue
                    else:
                        # Interface does not exist
                        continue
                str += line
                continue
            
            # Got an interface object, unpack
            if line["auto"][1] == -1 and line["auto"][0]:
                str += "auto %s\n" % line["name"]
            str += "iface %s %s %s\n" % \
                    (line["name"], line["family"], line["method"])
            keys = line["keys"]
            for name in keys:
                val = line[name]
                if type(val) == type(""):
                    # Skip string members, (name, family, method)
                    continue
                # Write out each interface option
                comment, value = val
                # With comments first if appropriate
                for cline in comment: str += cline
                # Then the meat
                str += "\t%s %s\n" % (name, value)
                   
        return str

    def write(self):
        """Writes back to the file that we read from"""

        fp = open("%s.tmp" % self._filename, "w")
        fp.write("%s" % self)
        fp.close()
        os.system("mv %s.tmp %s" % (self._filename, self._filename))

def nonmodtest():
    
    # Tests that it can read/parse and write out without causing change
    ifaces = debian_interfaces()
    (cin, cout) = os.popen2("diff -uw /etc/network/interfaces -", "w")
    cin.write("%s" % ifaces)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) != 0:
        print "Non-modification test: FAILED"
        print "".join(output)
        return False
    else:
        print "Non-modification test: OK"
        return True
        
def addifacetest():
    
    # Tests that it can add a new interface ok
    ifaces = debian_interfaces()
    ifaces["eth1"] = {"name":"eth1","method":"static","family":"inet", \
            "address":"192.168.0.1", "netmask":"255.255.255.0", \
            "network":"192.168.0.0", "broadcast":"192.168.0.255"}
    (cin, cout) = os.popen2("diff -uw /etc/network/interfaces -", "w")
    cin.write("%s" % ifaces)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Add interface test: FAILED"
        return False
    else:
        print "Add interface test: Maybe OK - verify diff manually" 
        print "Add interface test:          - should be a new eth1 interface"
        print "".join(output)
        return True
    
def delifacetest():
    
    # Tests that it can delete an interface ok
    ifaces = debian_interfaces()
    print ifaces
    del ifaces["eth0"]
    (cin, cout) = os.popen2("diff -uw /etc/network/interfaces -", "w")
    cin.write("%s" % ifaces)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Delete interface test: FAILED"
        return False
    else:
        print "Delete interface test: Maybe OK - verify diff manually" 
        print "Delete interface test:          - should be a no eth0 interface"
        print "".join(output)
        return True
        
def modeth0test():
    
    # Tests that it can edit eth0
    ifaces = debian_interfaces()

    eth0 = ifaces["eth0"]
    eth0["family"] = "inet6"
    eth0["pre-up"] = "foo"
    del eth0["gateway"]

    ifaces["eth0"] = eth0

    (cin, cout) = os.popen2("diff -uw /etc/network/interfaces -", "w")
    cin.write("%s" % ifaces)
    cin.close()
    output = cout.readlines()
    rv = cout.close()
    if len(output) == 0:
        print "Modify eth0 test: FAILED"
        return False
    else:
        print "Modify eth0 test: Maybe OK - verify diff manually" 
        print "Modify eth0 test:          - eth0 should have family inet6,"
        print "Modify eth0 test:          - a new pre-up action and no"
        print "Modify eth0 test:          - default gateway set"
        print "".join(output)
        return True
    
def autotest():
    import re
    ifaces = debian_interfaces()
    iface = ifaces["eth0"]
    iface["auto"] = False
    ifaces["eth0"] = iface
    file = "%s" % ifaces
    if re.search("auto eth0", file) is not None:
        print "Auto removal test: FAILED"
        print file
        return False
    else:
        print "Auto removal test: OK"
    iface["auto"] = True
    ifaces["eth0"] = iface
    file = "%s" % ifaces
    if re.search("auto eth0", file) is None:
        print "Auto addition test: FAILED"
        print file
        return False
    else:
        print "Auto addition test: OK"
    ifaces["eth1"] = {"name":"eth1","method":"static","family":"inet", \
            "address":"192.168.0.1", "netmask":"255.255.255.0", \
            "network":"192.168.0.0", "broadcast":"192.168.0.255", \
            "auto":True}
    file = "%s" % ifaces
    if re.search("auto eth1", file) is None:
        print "Auto addition of new interface test: FAILED"
        print file
        return False
    else:
        print "Auto addition of new interface test: OK"

    return True
    
if __name__ == "__main__":

    print "Running Test Suite"
    print "=================="
    print "Note: This requires an /etc/network/interfaces that contains"
    print "      a stanza for eth0 or the tests will fail!"
    print "=================="
    
    # Tests that it can read/parse and write out without causing change
    for f in [nonmodtest, autotest, addifacetest, delifacetest, modeth0test]:
        if not f():
            sys.exit(1)

    print "=================="
    print "No Test Failures - check output for warnings"
    print "=================="

