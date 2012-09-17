#!/usr/bin/python
# Copyright (C) 2006  The University of Waikato
#
# Helper functions for integrating with the Linux tc utility
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import sys
import os
from ccsd_log import *

# Classes used for filtering
FILTER_EGRESS = ""
FILTER_INGRESS = "root"

_log_commands = False
def tc_log(enabled=False):
    global _log_commands
    _log_commands=enabled

def tc_output_command(command):
    global _log_commands
    if _log_commands:
        log_debug(command)
    return os.popen(command, "r")
def tc_log_command(command):
    global _log_commands
    if _log_commands:
        log_debug(command)
    return log_command(command)

def retrieve_classnos(iface):
    """Return the classno's currently in use"""
    classnos = []
    
    fd = tc_output_command("/sbin/tc class ls dev %s" % iface)
    lines = fd.readlines()
    rv = fd.close()
    if rv != None:
        log_error("Cannot retrieve class no's on %s" % iface)
        return []
    
    for line in lines:
        if not line.startswith("class"):
            continue
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        temp = parts[2].split(":")
        if len(temp) != 2:
            continue
        try:
            t = int(temp[1])
        except ValueError:
            continue
        classnos.append(t)
        
    return classnos

def _iface_enforce(iface, listname, handle, type, params, modify=False):
    """Helper to ensure that the specified rule exists in the list"""

    # Does it exist?
    if _iface_match(iface, listname, handle, type):
        if not modify:
            return True
        # Change it
        if listname == "class":
            rv = tc_log_command("/sbin/tc %s change dev %s %s" %
                    (listname, iface, params))
            return rv
        else:
            # Remove it and re-add it to change
            tc_log_command("/sbin/tc %s del dev %s %s" % \
                    (listname, iface, params))

    # Add it
    rv = tc_log_command("/sbin/tc %s add dev %s %s" % \
            (listname, iface, params))
    
    return rv

def _iface_remove(iface, listname, params):
    """Helper to remove the specified rule exists in the list"""

    rv = tc_log_command("/sbin/tc %s del dev %s %s" % \
                    (listname, iface, params))
    return rv

def _iface_match(iface, listname, handle, type):
    """Helper to parse tc output and match qdisc/class lines"""
    
    # Read the list of from the interface
    fd = tc_output_command("/sbin/tc %s ls dev %s" % (listname, iface))
    lines = fd.readlines()
    rv = fd.close()
    if rv is not None:
        # Could not successfully read the list
        return False
    
    for line in lines:
        # Break the line into parts
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        # Check each entry
        if parts[2] == handle:
            if type is not None and type == parts[1]:
                # Found
                return True
    
    # Not Found
    return False

def _iface_remove_filter(iface, ftype, pref):
    """Removes the specified filter from the interface"""
    return tc_log_command("/sbin/tc filter del dev %s %s pref %s u32" %
                    (iface, ftype, pref))

def _enforce_filter(iface, m, ftype, params):
    """Helper to ensure that the specified filter exists"""
    
    # Remove existing filters for this mac address
    iface_remove_mac_filters(iface, m, ftype)
    
    # Add it
    return tc_log_command("/sbin/tc filter add dev %s %s %s" % \
            (iface, ftype, params))

def iface_has_qdisc(iface, handle, type=None):
    """Returns true if the specified qdisc exists"""
    return _iface_match(iface, "qdisc", handle, type)

def iface_has_class(iface, handle, type=None):
    """Returns true if the specified class exists"""       
    return _iface_match(iface, "class", handle, type)

def iface_enforce_qdisc(iface, handle, type, params, modify=False):
    """Ensure the specified qdisc exists"""
    return _iface_enforce(iface, "qdisc", handle, type, params, modify)

def iface_enforce_class(iface, handle, type, params, modify=False):
    """Ensure the specified class exists"""       
    return _iface_enforce(iface, "class", handle, type, params, modify)

def iface_remove_qdisc(iface, params):
    """Remove the specified qdisc"""
    return _iface_remove(iface, "qdisc", params)

def iface_remove_class(iface, params):
    """Remove the specified class"""
    return _iface_remove(iface, "class", params)

def iface_get_filters(iface, ftype):
    """Returns a list of all filters of the specified type on the iface"""
    
    filters = []
    
    # Read the list of from the interface
    fd = tc_output_command("/sbin/tc filter ls dev %s %s" % (iface, ftype))
    lines = fd.readlines()
    rv = fd.close()
    if rv is not None:
        # Could not successfully read the list
        return filters
    
    filter = None
    for line in lines:
        # Ignore blank lines
        if len(line.strip())==0:
            continue
        
        # Add info lines to the current filter
        if not line.startswith("filter"):
            if filter is not None:
                filter["info"].append(line.strip())
            continue

        # Throw away useless lines
        if len(line.strip().split()) < 13:
            continue
        
        # start new filter entry
        if filter is not None:
            filters.append(filter)
        filter = {"line":line.strip(),"info":[]}
        
    # Catch the last filter
    if filter is not None:
        filters.append(filter)
        
    return filters

def iface_get_mac_filters(iface, m, ftype):
    """Returns a list of filters matching the specified mac address"""
    filters = []
    matches = {}

    # Build a dictionary of the matches we want to find
    if ftype == FILTER_EGRESS:
        matches["-12"] = "%s%s%s%s/ffffffff" % (m[2], m[3], m[4], m[5])
        matches["-16"] = "0000%s%s/0000ffff" % (m[0], m[1])
    elif ftype == FILTER_INGRESS:
        matches["-4"] = "%s%s0800/ffffffff" % (m[4], m[5])
        matches["-8"] = "%s%s%s%s/ffffffff" % (m[0], m[1], m[2], m[3])
    else:
        # Invalid type
        return []
    
    # Get the filters and sort through them
    for filter in iface_get_filters(iface, ftype):
        mlevel = 0
        for line in filter["info"]:
            if not line.startswith("match"):
                continue
            parts = line.split()
            if parts[-1] in matches.keys():
                t = matches[parts[-1]]
            else:
                continue
            # Does it match?
            if parts[1] != t:
                break
            else:
                # Increase match count
                mlevel += 1
        # Did we match all the MAC?
        if mlevel == 2:
            filters.append(filter)
    
    return filters      
    
def iface_remove_mac_filters(iface, m, ftype):
    
    # Remove existing filters for this mac address
    filters = iface_get_mac_filters(iface, m, ftype)
    for filter in filters:
        t = filter.find("pref")
        pref = filter[t+5:filter.find(" ", t+5)]
        try:
            if pref.strip() == "" or int(pref) == 0:
                continue
        except ValueError:
            continue
        _iface_remove_filter(iface, ftype, pref)

def iface_enforce_egress_filter(iface, m, classhandle, prio=5000):
    """Ensures that a filter exists to queue traffic to the specified mac"""
    
    params = "prio %s protocol ip parent 1: u32 " \
            "match u16 0x0800 0xFFFF at -2 " \
            "match u32 0x%s%s%s%s 0xFFFFFFFF at -12 " \
            "match u16 0x%s%s 0xFFFF at -14 flowid %s" % \
            (prio, m[2], m[3], m[4], m[5], m[0], m[1], classhandle)
    
    return _enforce_filter(iface, m, FILTER_EGRESS, params)
    
def iface_enforce_ingress_filter(iface, m, rate, prio=5000):
    """Ensures that a filter exists to police traffic from the specified mac"""
    
    params = "prio %s protocol ip u32 " \
            "match u32 0x%s%s0800 0xFFFFFFFF at -4 " \
            "match u32 0x%s%s%s%s 0xFFFFFFFF at -8 " \
            "police rate %skbit burst 10k drop flowid :ffff" % \
            (prio, m[4], m[5], m[0], m[1], m[2], m[3], rate)
            
    return _enforce_filter(iface, m, FILTER_INGRESS, params)

def reset_interface_ratelimit(iface):
    """Removes the rate limits on an interface"""

    # Remove the root and ingress qdiscs, will cascade and remove filters
    # and classes
    iface_remove_qdisc(iface, "root")
    iface_remove_qdisc(iface, "ingress")
    log_info("Removed all rate limiting from %s" % iface)
